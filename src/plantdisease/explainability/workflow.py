"""End-to-end Week 4 sample-freezing workflow."""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import torch
from torch.utils.data import DataLoader, Subset

from plantdisease.data import huggingface as hf_data
from plantdisease.data.dataset import HuggingFaceImageDataset
from plantdisease.data.transforms import build_eval_transform
from plantdisease.explainability.layers import resolve_target_layer
from plantdisease.explainability.predictions import (
    collect_prediction_records,
    save_prediction_records,
)
from plantdisease.explainability.samples import freeze_sample_groups, save_frozen_samples
from plantdisease.models.checkpoint import load_checkpoint


@dataclass(frozen=True)
class FrozenSampleResult:
    """Summary of generated Week 4 sample-freezing artifacts."""

    prediction_path: Path
    frozen_samples_path: Path
    prediction_count: int
    selected_counts: dict[str, int]
    target_layer: str


def _resolve_device(name: str) -> torch.device:
    if name == "auto":
        if torch.cuda.is_available():
            return torch.device("cuda")
        if torch.backends.mps.is_available():
            return torch.device("mps")
        return torch.device("cpu")
    device = torch.device(name)
    if device.type == "cuda" and not torch.cuda.is_available():
        raise ValueError("CUDA was requested but is not available")
    if device.type == "mps" and not torch.backends.mps.is_available():
        raise ValueError("MPS was requested but is not available")
    return device


def _load_split_manifest(path: Path) -> dict[str, object]:
    payload = cast(dict[str, object], json.loads(path.read_text(encoding="utf-8")))
    if payload.get("schema_version") != 1:
        raise ValueError("unsupported split manifest schema_version")
    if "test" not in cast(Mapping[object, object], payload.get("splits", {})):
        raise ValueError("split manifest must contain a test split")
    return payload


def _maybe_apply_test_source_sampling(test_split, split_manifest: dict[str, object]):
    sampling = split_manifest.get("sampling", {})
    if not isinstance(sampling, dict):
        return test_split
    source_indices = sampling.get("source_indices", {})
    if not isinstance(source_indices, dict) or "hf_test" not in source_indices:
        return test_split
    source_indices = cast(dict[str, object], source_indices)
    return test_split.select(
        [
            int(cast(int | float | str, index))
            for index in cast(Sequence[object], source_indices["hf_test"])
        ]
    )


def freeze_explainability_samples(
    *,
    checkpoint_path: Path,
    split_manifest_path: Path,
    output_dir: Path,
    cache_dir: Path | None = None,
    samples_per_group: int = 6,
    top_k: int = 5,
    batch_size: int = 64,
    num_workers: int = 0,
    device_name: str = "auto",
    target_layer: str | None = None,
    logger: Callable[[str], None] | None = None,
    progress_log_every: int = 10,
) -> FrozenSampleResult:
    """Generate prediction records and frozen confidence-quadrant samples."""
    if logger is not None:
        logger(f"load split manifest: {split_manifest_path}")
    split_manifest = _load_split_manifest(split_manifest_path)
    split_class_names = list(cast(list[str], split_manifest["class_names"]))
    split_groups = cast(Mapping[str, object], split_manifest["splits"])
    test_indices = [
        int(cast(int | float | str, index))
        for index in cast(Sequence[object], split_groups["test"])
    ]
    if logger is not None:
        logger(f"load checkpoint: {checkpoint_path}")
    device = _resolve_device(device_name)
    model, checkpoint_class_names, checkpoint_config = load_checkpoint(checkpoint_path, device)
    if checkpoint_class_names != split_class_names:
        raise ValueError("checkpoint class_names do not match split manifest")

    model_name = str(checkpoint_config["model_name"])
    image_size = int(cast(int | float | str, checkpoint_config["image_size"]))
    resolved_target = resolve_target_layer(model, model_name)
    if target_layer is not None and target_layer != resolved_target.name:
        raise ValueError(f"target_layer must be {resolved_target.name} for {model_name}")
    resolved_target_layer = resolved_target.name
    if logger is not None:
        logger(f"target layer: {resolved_target_layer}")

    if logger is not None:
        logger(f"load dataset: cache_dir={cache_dir}")
    splits, dataset_class_names = hf_data.load_plantvillage_dataset_splits(cache_dir)
    if dataset_class_names != split_class_names:
        raise ValueError("dataset class_names do not match split manifest")
    if "test" not in splits:
        raise ValueError("PlantVillage official test split is required")

    test_split = _maybe_apply_test_source_sampling(splits["test"], split_manifest)
    test_dataset = HuggingFaceImageDataset(test_split, build_eval_transform(image_size))
    test_loader = DataLoader(
        Subset(test_dataset, test_indices),
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
    )

    if logger is not None:
        logger(f"collect predictions: samples={len(test_indices)} batch_size={batch_size}")
    records = collect_prediction_records(
        model,
        test_loader,
        checkpoint_class_names,
        test_indices=test_indices,
        top_k=top_k,
        progress_logger=logger,
        progress_log_every=progress_log_every,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    prediction_path = output_dir / "predictions.json"
    frozen_samples_path = output_dir / "frozen_samples.json"
    if logger is not None:
        logger(f"write predictions: {prediction_path}")
    save_prediction_records(records, prediction_path)
    if logger is not None:
        logger("freeze confidence-quadrant samples")
    frozen_manifest = freeze_sample_groups(
        records,
        samples_per_group=samples_per_group,
        checkpoint_path=str(checkpoint_path),
        model_name=model_name,
        target_layer=resolved_target_layer,
    )
    frozen_manifest["inputs"] = {
        "split_manifest_path": str(split_manifest_path),
        "prediction_path": str(prediction_path),
        "top_k": top_k,
    }
    if logger is not None:
        logger(f"write frozen samples: {frozen_samples_path}")
    save_frozen_samples(frozen_manifest, frozen_samples_path)
    if logger is not None:
        logger("sample freezing completed")
    return FrozenSampleResult(
        prediction_path=prediction_path,
        frozen_samples_path=frozen_samples_path,
        prediction_count=len(records),
        selected_counts=dict(
            cast(
                Mapping[str, int],
                cast(Mapping[str, object], frozen_manifest["selection"])[
                    "selected_counts"
                ],
            )
        ),
        target_layer=resolved_target_layer,
    )
