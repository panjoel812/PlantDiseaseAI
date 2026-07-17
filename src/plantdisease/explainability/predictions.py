"""Per-sample prediction records for explainability and error analysis."""

from __future__ import annotations

import json
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import TypedDict

import torch
from torch import nn
from torch.utils.data import DataLoader


class _TopKRecord(TypedDict):
    class_index: int
    class_name: str
    probability: float


def _model_device(model: nn.Module) -> torch.device:
    parameter = next(model.parameters(), None)
    if parameter is not None:
        return parameter.device
    buffer = next(model.buffers(), None)
    if buffer is not None:
        return buffer.device
    return torch.device("cpu")


def _topk_records(
    probabilities: torch.Tensor, class_names: Sequence[str], top_k: int
) -> list[_TopKRecord]:
    values, indices = torch.topk(probabilities, k=min(top_k, len(class_names)))
    return [
        {
            "class_index": int(index),
            "class_name": class_names[int(index)],
            "probability": float(value),
        }
        for value, index in zip(values.cpu(), indices.cpu(), strict=True)
    ]


def _progress_message(
    batch_index: int,
    total_batches: int,
    sample_count: int,
    total_samples: int,
) -> str:
    width = 24
    filled = int(width * sample_count / max(total_samples, 1))
    bar = "#" * filled + "-" * (width - filled)
    return (
        f"predict [{bar}] batch {batch_index}/{total_batches} "
        f"samples={sample_count}/{total_samples}"
    )


def collect_prediction_records(
    model: nn.Module,
    loader: DataLoader,
    class_names: Sequence[str],
    *,
    test_indices: Sequence[int],
    sample_id_prefix: str = "hf-test",
    top_k: int = 5,
    progress_logger: Callable[[str], None] | None = None,
    progress_log_every: int = 10,
) -> list[dict[str, object]]:
    """Collect JSON-serializable per-sample predictions from an ordered loader."""
    if not class_names:
        raise ValueError("class_names must not be empty")
    if top_k <= 0:
        raise ValueError("top_k must be positive")
    if progress_log_every <= 0:
        raise ValueError("progress_log_every must be positive")

    device = _model_device(model)
    records: list[dict[str, object]] = []
    cursor = 0
    total_batches = len(loader)
    total_samples = len(test_indices)
    model.eval()
    with torch.inference_mode():
        for batch_index, (images, labels) in enumerate(loader, start=1):
            images = images.to(device)
            labels = labels.to(device)
            logits = model(images)
            if (
                logits.ndim != 2
                or logits.shape[0] != labels.shape[0]
                or logits.shape[1] != len(class_names)
            ):
                raise ValueError("model logits shape must be (batch, classes)")
            probabilities = torch.softmax(logits, dim=1)
            for offset in range(labels.shape[0]):
                if cursor >= len(test_indices):
                    raise ValueError("test_indices length does not match loader samples")
                true_index = int(labels[offset].cpu())
                if true_index < 0 or true_index >= len(class_names):
                    raise ValueError("labels contain a value outside class range")
                top_k_predictions = _topk_records(probabilities[offset], class_names, top_k)
                predicted = top_k_predictions[0]
                predicted_index = int(predicted["class_index"])
                test_index = int(test_indices[cursor])
                records.append(
                    {
                        "test_index": test_index,
                        "sample_id": f"{sample_id_prefix}-{test_index}",
                        "true_class_index": true_index,
                        "true_class_name": class_names[true_index],
                        "predicted_class_index": predicted_index,
                        "predicted_class_name": class_names[predicted_index],
                        "confidence": float(predicted["probability"]),
                        "correct": predicted_index == true_index,
                        "top_k": top_k_predictions,
                    }
                )
                cursor += 1
            if progress_logger is not None and (
                batch_index == 1
                or batch_index % progress_log_every == 0
                or batch_index == total_batches
            ):
                progress_logger(
                    _progress_message(batch_index, total_batches, cursor, total_samples)
                )
    if cursor != len(test_indices):
        raise ValueError("test_indices length does not match loader samples")
    return records


def save_prediction_records(records: Sequence[dict[str, object]], path: Path) -> None:
    """Write per-sample prediction records as stable JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(list(records), ensure_ascii=False, indent=2), encoding="utf-8")
