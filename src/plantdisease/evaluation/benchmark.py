"""Inference efficiency benchmarking for project checkpoints."""

from __future__ import annotations

import json
import platform
import statistics
import sys
import time
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import torch
from fvcore.nn import FlopCountAnalysis
from torch import nn

from plantdisease.models.checkpoint import load_checkpoint


def count_parameters(model: nn.Module) -> dict[str, int]:
    """Return total and trainable parameter counts."""
    total = sum(parameter.numel() for parameter in model.parameters())
    trainable = sum(
        parameter.numel() for parameter in model.parameters() if parameter.requires_grad
    )
    return {"total": int(total), "trainable": int(trainable)}


def _model_device(model: nn.Module) -> torch.device:
    try:
        return next(model.parameters()).device
    except StopIteration:
        return torch.device("cpu")


def analyze_flops(model: nn.Module, image_size: int) -> dict[str, object]:
    """Analyze theoretical FLOPs for a single batch-1 forward pass."""
    if image_size <= 0:
        raise ValueError("image_size must be positive")

    model = model.eval()
    input_shape = [1, 3, int(image_size), int(image_size)]
    sample = torch.zeros(input_shape, device=_model_device(model))
    analysis = FlopCountAnalysis(model, sample)
    analysis.unsupported_ops_warnings(False)
    analysis.uncalled_modules_warnings(False)
    total = int(analysis.total())
    unsupported_ops = {str(name): int(count) for name, count in analysis.unsupported_ops().items()}

    return {
        "tool": "fvcore.nn.FlopCountAnalysis",
        "convention": "fvcore operator convention; multiply-add handling follows fvcore",
        "input_shape": input_shape,
        "total": total,
        "unsupported_ops": unsupported_ops,
        "uncalled_modules": sorted(analysis.uncalled_modules()),
    }


def validate_protocol(
    warmup_iterations: int,
    measured_iterations: int,
    latency_batch_size: int,
    throughput_batch_size: int,
) -> None:
    """Validate benchmark protocol knobs before doing expensive work."""
    if warmup_iterations < 0:
        raise ValueError("warmup_iterations must be non-negative")
    if measured_iterations <= 0:
        raise ValueError("measured_iterations must be positive")
    if latency_batch_size <= 0:
        raise ValueError("latency_batch_size must be positive")
    if throughput_batch_size <= 0:
        raise ValueError("throughput_batch_size must be positive")


def synchronize_device(device: torch.device) -> None:
    """Synchronize asynchronous accelerators before reading wall-clock time."""
    if device.type == "cuda":
        torch.cuda.synchronize(device)
    elif device.type == "mps" and hasattr(torch, "mps"):
        torch.mps.synchronize()


def summarize_timings_ms(samples_ms: Sequence[float]) -> dict[str, float]:
    """Return basic summary statistics for timing samples in milliseconds."""
    if not samples_ms:
        raise ValueError("samples_ms must be non-empty")

    samples = [float(sample) for sample in samples_ms]
    return {
        "mean": float(statistics.fmean(samples)),
        "median": float(statistics.median(samples)),
        "stdev": float(statistics.stdev(samples)) if len(samples) > 1 else 0.0,
        "min": float(min(samples)),
        "max": float(max(samples)),
    }


def measure_forward(
    model: nn.Module,
    device: torch.device,
    batch_size: int,
    image_size: int,
    warmup_iterations: int,
    measured_iterations: int,
    dtype: torch.dtype = torch.float32,
) -> dict[str, object]:
    """Measure forward-pass timings with preprocessing excluded."""
    validate_protocol(
        warmup_iterations=warmup_iterations,
        measured_iterations=measured_iterations,
        latency_batch_size=batch_size,
        throughput_batch_size=batch_size,
    )
    if image_size <= 0:
        raise ValueError("image_size must be positive")

    model = model.to(device=device, dtype=dtype).eval()
    sample = torch.zeros((batch_size, 3, image_size, image_size), device=device, dtype=dtype)

    with torch.inference_mode():
        for _ in range(warmup_iterations):
            model(sample)
        synchronize_device(device)

        raw_ms: list[float] = []
        for _ in range(measured_iterations):
            synchronize_device(device)
            start = time.perf_counter()
            model(sample)
            synchronize_device(device)
            raw_ms.append((time.perf_counter() - start) * 1000.0)

    return {
        "batch_size": int(batch_size),
        "raw_ms": raw_ms,
        "summary_ms": summarize_timings_ms(raw_ms),
    }


def resolve_device(requested: str) -> torch.device:
    """Resolve a requested device name, including project auto-selection order."""
    requested = requested.lower()
    if requested == "auto":
        if torch.cuda.is_available():
            return torch.device("cuda")
        if torch.backends.mps.is_available():
            return torch.device("mps")
        return torch.device("cpu")
    if requested == "cuda":
        if not torch.cuda.is_available():
            raise ValueError("requested device cuda is unavailable")
        return torch.device("cuda")
    if requested == "mps":
        if not torch.backends.mps.is_available():
            raise ValueError("requested device mps is unavailable")
        return torch.device("mps")
    if requested == "cpu":
        return torch.device("cpu")
    raise ValueError("device must be one of: auto, cpu, cuda, mps")


def _dtype_name(dtype: torch.dtype) -> str:
    return str(dtype).removeprefix("torch.")


def _throughput_report(batch_report: dict[str, object], measured_iterations: int) -> dict[str, Any]:
    raw_ms = [
        float(cast(int | float | str, sample))
        for sample in cast(Sequence[object], batch_report["raw_ms"])
    ]
    batch_size = int(cast(int | float | str, batch_report["batch_size"]))
    total_seconds = sum(raw_ms) / 1000.0
    images_per_second = (
        batch_size * measured_iterations / total_seconds if total_seconds > 0 else 0.0
    )
    return {
        "batch_size": batch_size,
        "raw_batch_ms": raw_ms,
        "summary_batch_ms": batch_report["summary_ms"],
        "total_seconds": float(total_seconds),
        "images_per_second": float(images_per_second),
    }


def run_checkpoint_benchmark(
    checkpoint_path: Path,
    output_path: Path,
    device_name: str = "auto",
    warmup_iterations: int = 10,
    measured_iterations: int = 50,
    throughput_batch_size: int = 32,
) -> dict[str, object]:
    """Benchmark a checkpoint and persist a versioned JSON report."""
    validate_protocol(
        warmup_iterations=warmup_iterations,
        measured_iterations=measured_iterations,
        latency_batch_size=1,
        throughput_batch_size=throughput_batch_size,
    )
    if not checkpoint_path.exists():
        raise FileNotFoundError(f"checkpoint not found: {checkpoint_path}")

    device = resolve_device(device_name)
    dtype = torch.float32
    model, class_names, config = load_checkpoint(checkpoint_path, torch.device("cpu"))
    image_size = int(cast(int | float | str, config["image_size"]))
    model_name = str(config["model_name"])
    num_classes = int(cast(int | float | str, config["num_classes"]))

    parameters = count_parameters(model)
    flops = analyze_flops(model, image_size=image_size)
    latency = measure_forward(
        model=model,
        device=device,
        batch_size=1,
        image_size=image_size,
        warmup_iterations=warmup_iterations,
        measured_iterations=measured_iterations,
        dtype=dtype,
    )
    throughput_batches = measure_forward(
        model=model,
        device=device,
        batch_size=throughput_batch_size,
        image_size=image_size,
        warmup_iterations=warmup_iterations,
        measured_iterations=measured_iterations,
        dtype=dtype,
    )

    report: dict[str, object] = {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(),
        "checkpoint": {
            "path": str(checkpoint_path.resolve()),
            "model_name": model_name,
            "num_classes": num_classes,
            "class_count": len(class_names),
            "image_size": image_size,
        },
        "environment": {
            "python": sys.version.split()[0],
            "torch": torch.__version__,
            "platform": platform.platform(),
            "device": str(device),
            "dtype": _dtype_name(dtype),
        },
        "measurement": {
            "warmup_iterations": int(warmup_iterations),
            "measured_iterations": int(measured_iterations),
            "latency_batch_size": 1,
            "throughput_batch_size": int(throughput_batch_size),
            "preprocessing_included": False,
            "peak_memory_measured": False,
            "peak_memory_note": "not measured; MPS peak memory reset/reporting is not used",
        },
        "parameters": parameters,
        "flops": flops,
        "latency": latency,
        "throughput": _throughput_report(throughput_batches, measured_iterations),
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return report
