"""Deterministic sample freezing for Week 4 explainability analysis."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import cast

PredictionRecord = Mapping[str, object]


GROUP_NAMES = (
    "correct_high_confidence",
    "correct_low_confidence",
    "error_high_confidence",
    "error_low_confidence",
)

_REQUIRED_FIELDS = frozenset(
    {
        "test_index",
        "sample_id",
        "true_class_index",
        "true_class_name",
        "predicted_class_index",
        "predicted_class_name",
        "confidence",
        "correct",
    }
)


def _validated_records(predictions: Sequence[PredictionRecord]) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for position, prediction in enumerate(predictions):
        record = dict(prediction)
        missing = sorted(_REQUIRED_FIELDS.difference(record))
        if missing:
            raise ValueError(f"prediction record {position} missing fields: {missing}")
        test_index = int(cast(int | float | str, record["test_index"]))
        confidence = float(cast(int | float | str, record["confidence"]))
        if test_index < 0:
            raise ValueError("test_index must be non-negative")
        if not 0.0 <= confidence <= 1.0:
            raise ValueError("confidence must be in [0, 1]")
        record["test_index"] = test_index
        record["confidence"] = confidence
        record["correct"] = bool(record["correct"])
        records.append(record)
    return records


def _sorted_by_confidence(
    predictions: Sequence[PredictionRecord], *, descending: bool
) -> list[dict[str, object]]:
    return sorted(
        (dict(record) for record in predictions),
        key=lambda record: (
            -float(record["confidence"]) if descending else float(record["confidence"]),
            int(record["test_index"]),
        ),
    )


def freeze_sample_groups(
    predictions: Sequence[PredictionRecord],
    *,
    samples_per_group: int,
    checkpoint_path: str,
    model_name: str,
    target_layer: str,
) -> dict[str, object]:
    """Return deterministic confidence-quadrant sample groups."""
    if samples_per_group <= 0:
        raise ValueError("samples_per_group must be positive")

    records = _validated_records(predictions)
    correct = [record for record in records if bool(record["correct"])]
    errors = [record for record in records if not bool(record["correct"])]
    groups = {
        "correct_high_confidence": _sorted_by_confidence(correct, descending=True)[
            :samples_per_group
        ],
        "correct_low_confidence": _sorted_by_confidence(correct, descending=False)[
            :samples_per_group
        ],
        "error_high_confidence": _sorted_by_confidence(errors, descending=True)[
            :samples_per_group
        ],
        "error_low_confidence": _sorted_by_confidence(errors, descending=False)[
            :samples_per_group
        ],
    }

    return {
        "schema_version": 1,
        "model": {
            "checkpoint_path": checkpoint_path,
            "model_name": model_name,
            "target_layer": target_layer,
        },
        "selection": {
            "samples_per_group": samples_per_group,
            "groups": list(GROUP_NAMES),
            "tie_breaker": "test_index_ascending",
            "insufficient_group_policy": "use_available_samples_without_fabrication",
            "available_counts": {
                "correct": len(correct),
                "error": len(errors),
            },
            "selected_counts": {name: len(samples) for name, samples in groups.items()},
        },
        "groups": groups,
    }


def save_frozen_samples(manifest: Mapping[str, object], path: Path) -> None:
    """Write a frozen-sample manifest as stable, human-readable JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
