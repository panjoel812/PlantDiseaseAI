"""Hugging Face PlantVillage adapter."""

from __future__ import annotations

import random
from collections import defaultdict
from collections.abc import Sequence
from pathlib import Path

from plantdisease.data.dataset import ImageRecord

PLANTVILLAGE_REVISION = "9e97599868962bd0079b8db4b7f1efa9185fa1e7"


def plantvillage_script_path(cache_dir: Path | None = None) -> Path:
    """Download the inspected loader script pinned to a known revision."""

    from huggingface_hub import hf_hub_download

    return Path(
        hf_hub_download(
            repo_id="mohanty/PlantVillage",
            filename="plant_village.py",
            repo_type="dataset",
            revision=PLANTVILLAGE_REVISION,
            cache_dir=str(cache_dir) if cache_dir is not None else None,
        )
    )


def _records_from_split(split, split_name: str) -> list[ImageRecord]:
    if "image" not in split.column_names or "label" not in split.column_names:
        raise ValueError(
            f"PlantVillage fields changed; expected image/label, got {split.column_names}"
        )
    return [
        ImageRecord(sample["image"], int(sample["label"]), f"hf-{split_name}-{index}")
        for index, sample in enumerate(split)
    ]


def _class_names_from_split(split) -> list[str]:
    from datasets import ClassLabel

    feature = split.features["label"]
    if not isinstance(feature, ClassLabel) or not feature.names:
        raise ValueError("PlantVillage label feature does not expose class names")
    return list(feature.names)


def _load_dataset(cache_dir: Path | None = None):
    from datasets import load_dataset

    script_path = plantvillage_script_path(cache_dir)
    return load_dataset(
        str(script_path),
        name="default",
        trust_remote_code=True,
        cache_dir=str(cache_dir) if cache_dir is not None else None,
    )


def labels_from_split(split) -> list[int]:
    """Read labels from a Hugging Face split without decoding image payloads."""

    if "label" not in split.column_names:
        raise ValueError(f"expected a label column, got {split.column_names}")
    return [int(label) for label in split["label"]]


def balanced_indices_by_label(
    labels: Sequence[int], samples_per_class: int, seed: int
) -> list[int]:
    """Return deterministic indices with at most N samples per class."""

    if samples_per_class <= 0:
        raise ValueError("samples_per_class must be positive")
    if not labels:
        raise ValueError("labels must not be empty")
    by_label: dict[int, list[int]] = defaultdict(list)
    for index, label in enumerate(labels):
        if not isinstance(label, int) or label < 0:
            raise ValueError("labels must be non-negative integers")
        by_label[label].append(index)

    rng = random.Random(seed)
    selected: list[int] = []
    for label in sorted(by_label):
        candidates = list(by_label[label])
        rng.shuffle(candidates)
        selected.extend(candidates[:samples_per_class])
    return sorted(selected)


def load_plantvillage_dataset_splits(
    cache_dir: Path | None = None,
    max_samples_per_split: int | None = None,
):
    """Load raw PlantVillage splits for lazy image decoding during training."""

    if max_samples_per_split is not None and max_samples_per_split <= 0:
        raise ValueError("max_samples_per_split must be positive")
    dataset = _load_dataset(cache_dir)
    if "train" not in dataset:
        raise ValueError(f"PlantVillage dataset does not expose a train split: {list(dataset)}")

    class_names = _class_names_from_split(dataset["train"])
    splits = {}
    for split_name, split in dataset.items():
        if max_samples_per_split is not None:
            split = split.select(range(min(max_samples_per_split, len(split))))
        splits[split_name] = split
    return splits, class_names


def load_plantvillage_splits(
    cache_dir: Path | None = None,
    max_samples_per_split: int | None = None,
) -> tuple[dict[str, list[ImageRecord]], list[str]]:
    """Load PlantVillage while preserving upstream train/test split names."""

    dataset, class_names = load_plantvillage_dataset_splits(cache_dir, max_samples_per_split)
    splits: dict[str, list[ImageRecord]] = {}
    for split_name, split in dataset.items():
        splits[split_name] = _records_from_split(split, split_name)
    return splits, class_names


def load_plantvillage(
    cache_dir: Path | None = None, max_samples: int | None = None
) -> tuple[list[ImageRecord], list[str]]:
    """Load PlantVillage and normalize records to the project interface."""

    splits, class_names = load_plantvillage_splits(cache_dir, max_samples)
    split_name = "train" if "train" in splits else next(iter(splits))
    return splits[split_name], class_names
