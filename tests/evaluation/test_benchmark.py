import json
from pathlib import Path

import pytest
import torch
from torch import nn

from plantdisease.evaluation.benchmark import (
    analyze_flops,
    count_parameters,
    measure_forward,
    run_checkpoint_benchmark,
    summarize_timings_ms,
    validate_protocol,
)
from plantdisease.models.checkpoint import save_checkpoint
from plantdisease.models.factory import create_model


def test_count_parameters_reports_total_and_trainable() -> None:
    model = nn.Sequential(nn.Linear(4, 3), nn.Linear(3, 2))
    model[1].weight.requires_grad = False

    assert count_parameters(model) == {"total": 23, "trainable": 17}


def test_analyze_flops_reports_total_and_unsupported_ops() -> None:
    model = nn.Conv2d(3, 4, kernel_size=3, padding=1)

    report = analyze_flops(model, image_size=8)

    assert report["tool"] == "fvcore.nn.FlopCountAnalysis"
    assert report["input_shape"] == [1, 3, 8, 8]
    assert report["total"] == 6912
    assert report["unsupported_ops"] == {}


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"warmup_iterations": -1}, "warmup_iterations"),
        ({"measured_iterations": 0}, "measured_iterations"),
        ({"throughput_batch_size": 0}, "throughput_batch_size"),
    ],
)
def test_validate_protocol_rejects_invalid_values(
    kwargs: dict[str, int], message: str
) -> None:
    params = {
        "warmup_iterations": 0,
        "measured_iterations": 1,
        "latency_batch_size": 1,
        "throughput_batch_size": 1,
    }
    params.update(kwargs)

    with pytest.raises(ValueError, match=message):
        validate_protocol(**params)


def test_summarize_timings_ms_reports_expected_statistics() -> None:
    summary = summarize_timings_ms([1.0, 3.0])

    assert summary["mean"] == pytest.approx(2.0)
    assert summary["median"] == pytest.approx(2.0)
    assert summary["stdev"] == pytest.approx(1.41421356237)
    assert summary["min"] == pytest.approx(1.0)
    assert summary["max"] == pytest.approx(3.0)


def test_measure_forward_returns_raw_timings_on_cpu() -> None:
    model = nn.Conv2d(3, 2, kernel_size=1)

    report = measure_forward(
        model,
        torch.device("cpu"),
        batch_size=1,
        image_size=8,
        warmup_iterations=0,
        measured_iterations=2,
    )

    assert report["batch_size"] == 1
    assert len(report["raw_ms"]) == 2
    assert all(sample > 0 for sample in report["raw_ms"])
    assert report["summary_ms"]["mean"] > 0


def test_run_checkpoint_benchmark_writes_versioned_json(tmp_path: Path) -> None:
    checkpoint_path = tmp_path / "checkpoint.pt"
    output_path = tmp_path / "benchmark.json"
    model = create_model("mobilenet_v2", num_classes=2, pretrained=False)
    save_checkpoint(
        checkpoint_path,
        model,
        class_names=["healthy", "disease"],
        config={"model_name": "mobilenet_v2", "num_classes": 2, "image_size": 64},
    )

    report = run_checkpoint_benchmark(
        checkpoint_path=checkpoint_path,
        output_path=output_path,
        device_name="cpu",
        warmup_iterations=0,
        measured_iterations=1,
        throughput_batch_size=1,
    )

    saved = json.loads(output_path.read_text(encoding="utf-8"))
    assert saved == report
    assert saved["schema_version"] == 1
    assert saved["checkpoint"]["model_name"] == "mobilenet_v2"
    assert saved["checkpoint"]["image_size"] == 64
    assert saved["measurement"]["preprocessing_included"] is False
    assert saved["measurement"]["peak_memory_measured"] is False
    assert saved["latency"]["batch_size"] == 1
    assert saved["throughput"]["images_per_second"] > 0
