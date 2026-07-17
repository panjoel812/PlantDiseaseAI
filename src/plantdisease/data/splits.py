"""Reproducible stratified dataset splitting and manifest persistence."""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass(frozen=True)
class SplitRatios:
    train: float = 0.7
    validation: float = 0.15
    test: float = 0.15

    def as_dict(self) -> dict[str, float]:
        return {"train": self.train, "validation": self.validation, "test": self.test}


@dataclass(frozen=True)
class SplitManifest:
    splits: dict[str, tuple[int, ...]]
    labels: tuple[int, ...]
    class_names: tuple[str, ...]
    seed: int
    schema_version: int = 1


def _validate_ratios(ratios: SplitRatios) -> dict[str, float]:
    values = ratios.as_dict()
    if any(value <= 0.0 for value in values.values()) or not math.isclose(
        sum(values.values()), 1.0, rel_tol=0.0, abs_tol=1e-9
    ):
        raise ValueError("split ratios must be positive and sum to 1.0")
    return values


def _allocate_counts(sample_count: int, ratios: Mapping[str, float]) -> dict[str, int]:
    raw = {name: sample_count * ratio for name, ratio in ratios.items()}
    counts = {name: max(1, math.floor(value)) for name, value in raw.items()}

    while sum(counts.values()) > sample_count:
        candidates = [name for name, count in counts.items() if count > 1]
        if not candidates:
            raise ValueError(f"cannot allocate {sample_count} samples across three splits")
        name = max(candidates, key=lambda item: (counts[item] - raw[item], counts[item]))
        counts[name] -= 1

    while sum(counts.values()) < sample_count:
        name = max(ratios, key=lambda item: (raw[item] - counts[item], ratios[item]))
        counts[name] += 1
    return counts


def stratified_split_indices(
    labels: Sequence[int], ratios: SplitRatios, seed: int
) -> dict[str, list[int]]:
    """Return exhaustive, disjoint, class-stratified indices."""

    ratio_values = _validate_ratios(ratios)
    if not labels:
        raise ValueError("labels must not be empty")
    if any(not isinstance(label, int) or label < 0 for label in labels):
        raise ValueError("labels must be non-negative integers")

    by_class: dict[int, list[int]] = defaultdict(list)
    for index, label in enumerate(labels):
        by_class[label].append(index)

    minimum = len(ratio_values)
    for label, count in sorted(Counter(labels).items()):
        if count < minimum:
            raise ValueError(
                f"class {label} has {count} samples; at least {minimum} are required "
                "for train/validation/test"
            )

    rng = np.random.default_rng(seed)
    result = {name: [] for name in ratio_values}
    for label in sorted(by_class):
        indices = np.asarray(by_class[label], dtype=np.int64)
        rng.shuffle(indices)
        counts = _allocate_counts(len(indices), ratio_values)
        start = 0
        for name in ratio_values:
            end = start + counts[name]
            result[name].extend(int(index) for index in indices[start:end])
            start = end

    for indices in result.values():
        rng.shuffle(indices)
    return result


def stratified_train_validation_indices(
    labels: Sequence[int], validation_ratio: float, seed: int
) -> dict[str, list[int]]:
    """Split one official training split into train/validation subsets."""

    if not 0.0 < validation_ratio < 1.0:
        raise ValueError("validation_ratio must be between 0 and 1")
    if not labels:
        raise ValueError("labels must not be empty")
    if any(not isinstance(label, int) or label < 0 for label in labels):
        raise ValueError("labels must be non-negative integers")

    by_class: dict[int, list[int]] = defaultdict(list)
    for index, label in enumerate(labels):
        by_class[label].append(index)

    for label, count in sorted(Counter(labels).items()):
        if count < 2:
            raise ValueError(
                f"class {label} has {count} samples; at least 2 are required for train/validation"
            )

    rng = np.random.default_rng(seed)
    result = {"train": [], "validation": []}
    for label in sorted(by_class):
        indices = np.asarray(by_class[label], dtype=np.int64)
        rng.shuffle(indices)
        validation_count = int(round(len(indices) * validation_ratio))
        validation_count = min(max(validation_count, 1), len(indices) - 1)
        result["validation"].extend(int(index) for index in indices[:validation_count])
        result["train"].extend(int(index) for index in indices[validation_count:])

    rng.shuffle(result["train"])
    rng.shuffle(result["validation"])
    return result


def save_split_manifest(
    path: Path,
    splits: Mapping[str, Sequence[int]],
    labels: Sequence[int],
    class_names: Sequence[str],
    seed: int,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "seed": seed,
        "class_names": list(class_names),
        "labels": list(labels),
        "splits": {name: list(indices) for name, indices in splits.items()},
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_split_manifest(path: Path) -> SplitManifest:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1:
        raise ValueError("unsupported split manifest schema_version")
    return SplitManifest(
        splits={name: tuple(indices) for name, indices in payload["splits"].items()},
        labels=tuple(payload["labels"]),
        class_names=tuple(payload["class_names"]),
        seed=int(payload["seed"]),
    )
