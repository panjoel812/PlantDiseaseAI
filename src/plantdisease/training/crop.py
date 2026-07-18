"""Train a lightweight, independent PlantVillage crop classifier."""

from __future__ import annotations

import json
import platform
import random
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset

from plantdisease.data import huggingface as hf_data
from plantdisease.data.transforms import build_eval_transform
from plantdisease.evaluation.metrics import classification_metrics, save_metrics
from plantdisease.models.checkpoint import save_checkpoint
from plantdisease.models.factory import create_model
from plantdisease.serving.knowledge import lookup_disease_knowledge
from plantdisease.training.seed import seed_everything


@dataclass(frozen=True)
class CropTrainingResult:
    """Auditable result paths and held-out metrics for one crop run."""

    output_dir: Path
    checkpoint: Path
    metrics: dict[str, object]


class _CropDataset(Dataset[tuple[torch.Tensor, int]]):
    def __init__(
        self,
        split,
        indices: list[int],
        disease_to_crop: list[int],
        image_size: int,
    ) -> None:
        self.split = split
        self.indices = indices
        self.disease_to_crop = disease_to_crop
        self.transform = build_eval_transform(image_size)

    def __len__(self) -> int:
        return len(self.indices)

    def __getitem__(self, index: int) -> tuple[torch.Tensor, int]:
        sample = self.split[self.indices[index]]
        return self.transform(sample["image"]), self.disease_to_crop[int(sample["label"])]


def _balanced_crop_indices(
    disease_labels: list[int],
    disease_to_crop: list[int],
    per_crop: int,
    seed: int,
) -> list[int]:
    by_crop: defaultdict[int, list[int]] = defaultdict(list)
    for index, disease_label in enumerate(disease_labels):
        by_crop[disease_to_crop[disease_label]].append(index)
    rng = random.Random(seed)
    selected: list[int] = []
    for crop_index in sorted(by_crop):
        candidates = list(by_crop[crop_index])
        rng.shuffle(candidates)
        selected.extend(candidates[:per_crop])
    return sorted(selected)


def _split_train_validation(
    selected: list[int],
    disease_labels: list[int],
    disease_to_crop: list[int],
    validation_per_crop: int,
    seed: int,
) -> tuple[list[int], list[int]]:
    by_crop: defaultdict[int, list[int]] = defaultdict(list)
    for index in selected:
        by_crop[disease_to_crop[disease_labels[index]]].append(index)
    rng = random.Random(seed + 1)
    train: list[int] = []
    validation: list[int] = []
    for crop_index in sorted(by_crop):
        candidates = list(by_crop[crop_index])
        rng.shuffle(candidates)
        validation.extend(candidates[:validation_per_crop])
        train.extend(candidates[validation_per_crop:])
    return sorted(train), sorted(validation)


def _features(model: nn.Module, loader: DataLoader, device: torch.device):
    feature_batches: list[torch.Tensor] = []
    label_batches: list[torch.Tensor] = []
    model.eval()
    with torch.inference_mode():
        for images, labels in loader:
            activations = model.features(images.to(device))  # type: ignore[attr-defined]
            pooled = torch.nn.functional.adaptive_avg_pool2d(activations, (1, 1))
            feature_batches.append(torch.flatten(pooled, 1).cpu())
            label_batches.append(labels.cpu())
    return torch.cat(feature_batches), torch.cat(label_batches)


def _predictions(head: nn.Module, features: torch.Tensor, batch_size: int = 512) -> list[int]:
    values: list[int] = []
    head.eval()
    with torch.inference_mode():
        for start in range(0, len(features), batch_size):
            batch_predictions = head(features[start : start + batch_size]).argmax(1)
            values.extend(int(value) for value in batch_predictions)
    return values


def train_crop_classifier(
    *,
    cache_dir: Path,
    output_dir: Path,
    seed: int = 42,
    image_size: int = 224,
    selected_per_crop: int = 320,
    validation_per_crop: int = 64,
    test_per_crop: int = 128,
    head_epochs: int = 120,
    batch_size: int = 64,
    device: torch.device | None = None,
) -> CropTrainingResult:
    """Fit a MobileNetV2 crop head on frozen ImageNet features.

    The official PlantVillage test split remains separate. Sampling is balanced
    by crop so the large Tomato group cannot dominate plant identity.
    """
    if validation_per_crop >= selected_per_crop:
        raise ValueError("validation_per_crop must be below selected_per_crop")
    started = perf_counter()
    seed_everything(seed)
    resolved_device = device or torch.device("cpu")
    splits, disease_names = hf_data.load_plantvillage_dataset_splits(cache_dir)
    crop_names = sorted({lookup_disease_knowledge(name).plant for name in disease_names})
    crop_to_index = {name: index for index, name in enumerate(crop_names)}
    disease_to_crop = [
        crop_to_index[lookup_disease_knowledge(name).plant] for name in disease_names
    ]
    train_labels = hf_data.labels_from_split(splits["train"])
    test_labels = hf_data.labels_from_split(splits["test"])
    selected = _balanced_crop_indices(
        train_labels, disease_to_crop, selected_per_crop, seed
    )
    train_indices, validation_indices = _split_train_validation(
        selected, train_labels, disease_to_crop, validation_per_crop, seed
    )
    test_indices = _balanced_crop_indices(
        test_labels, disease_to_crop, test_per_crop, seed + 2
    )

    loaders = {
        "train": DataLoader(
            _CropDataset(splits["train"], train_indices, disease_to_crop, image_size),
            batch_size=batch_size,
            shuffle=False,
            num_workers=0,
        ),
        "validation": DataLoader(
            _CropDataset(splits["train"], validation_indices, disease_to_crop, image_size),
            batch_size=batch_size,
            shuffle=False,
            num_workers=0,
        ),
        "test": DataLoader(
            _CropDataset(splits["test"], test_indices, disease_to_crop, image_size),
            batch_size=batch_size,
            shuffle=False,
            num_workers=0,
        ),
    }
    model = create_model("mobilenet_v2", len(crop_names), pretrained=True).to(resolved_device)
    for parameter in model.features.parameters():  # type: ignore[attr-defined]
        parameter.requires_grad_(False)
    train_features, train_targets = _features(model, loaders["train"], resolved_device)
    validation_features, validation_targets = _features(
        model, loaders["validation"], resolved_device
    )
    test_features, test_targets = _features(model, loaders["test"], resolved_device)
    model.cpu()
    head = model.classifier  # type: ignore[attr-defined]
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(head.parameters(), lr=0.01, weight_decay=1e-4)
    best_accuracy = -1.0
    best_state: dict[str, torch.Tensor] | None = None
    curve: list[dict[str, float | int]] = []
    for epoch in range(1, head_epochs + 1):
        head.train()
        order = torch.randperm(len(train_features))
        total_loss = 0.0
        for start in range(0, len(order), 256):
            indices = order[start : start + 256]
            optimizer.zero_grad(set_to_none=True)
            loss = criterion(head(train_features[indices]), train_targets[indices])
            loss.backward()
            optimizer.step()
            total_loss += float(loss.detach()) * len(indices)
        validation_pred = _predictions(head, validation_features)
        accuracy = sum(
            int(prediction == truth)
            for prediction, truth in zip(
                validation_pred, validation_targets.tolist(), strict=True
            )
        ) / len(validation_pred)
        curve.append(
            {
                "epoch": epoch,
                "train_loss": total_loss / len(train_features),
                "validation_accuracy": accuracy,
            }
        )
        if accuracy > best_accuracy:
            best_accuracy = accuracy
            best_state = {
                name: value.detach().cpu().clone() for name, value in head.state_dict().items()
            }
    if best_state is None:
        raise RuntimeError("crop head training produced no checkpoint")
    head.load_state_dict(best_state)
    test_pred = _predictions(head, test_features)
    metrics = classification_metrics(test_targets.tolist(), test_pred, crop_names)

    output_dir.mkdir(parents=True, exist_ok=True)
    checkpoint = output_dir / "checkpoint.pt"
    save_checkpoint(
        checkpoint,
        model,
        crop_names,
        {
            "model_name": "mobilenet_v2",
            "num_classes": len(crop_names),
            "image_size": image_size,
            "task": "crop_classification",
            "pretrained_backbone": "ImageNet1K_V2",
            "training_protocol": "frozen_backbone_balanced_crop_head_v1",
            "seed": seed,
        },
    )
    save_metrics(metrics, output_dir / "metrics.json")
    (output_dir / "training_curve.json").write_text(
        json.dumps(curve, indent=2), encoding="utf-8"
    )
    manifest = {
        "schema_version": 1,
        "run_id": f"crop-mobilenet-v2-frozen-seed{seed}",
        "status": "completed",
        "seed": seed,
        "device": str(resolved_device),
        "python": sys.version.split()[0],
        "torch": torch.__version__,
        "platform": platform.platform(),
        "crop_names": crop_names,
        "train_sample_count": len(train_indices),
        "validation_sample_count": len(validation_indices),
        "test_sample_count": len(test_indices),
        "best_validation_accuracy": best_accuracy,
        "duration_seconds": perf_counter() - started,
        "scope": "PlantVillage closed-set crop identity; not open-world recognition",
    }
    (output_dir / "run_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output_dir / "split.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "seed": seed,
                "train": train_indices,
                "validation": validation_indices,
                "test": test_indices,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return CropTrainingResult(output_dir, checkpoint, metrics)
