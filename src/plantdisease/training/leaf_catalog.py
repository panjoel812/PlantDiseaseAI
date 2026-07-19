"""Low-compute local 100+ leaf identity training on UCI Leaf100 plus PlantVillage."""

from __future__ import annotations

import hashlib
import io
import json
import platform
import random
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from zipfile import ZipFile

import cv2
import numpy as np
import torch
from PIL import Image
from torch import nn
from torch.utils.data import DataLoader, Dataset

from plantdisease.data import huggingface as hf_data
from plantdisease.data.transforms import build_eval_transform
from plantdisease.evaluation.metrics import classification_metrics, save_metrics
from plantdisease.models.checkpoint import save_checkpoint
from plantdisease.models.factory import create_model
from plantdisease.openworld.leaf_pipeline import LEAF_ISOLATION_METHOD, isolate_leaf
from plantdisease.serving.knowledge import lookup_disease_knowledge
from plantdisease.training.seed import seed_everything

UCI_DATASET_URL = (
    "https://archive.ics.uci.edu/dataset/241/"
    "one%2Bhundred%2Bplant%2Bspecies%2Bleaves%2Bdata%2Bset"
)
UCI_ARCHIVE_SHA256 = "2313a70de450a8a6b81696174f52be1c037090af53b37c6a6313f11245e5fd4c"
UCI_ARCHIVE_PREFIX = "100 leaves plant species/data/"
CANONICAL_LEAF_RGB = (67, 145, 82)
NEUTRAL_BACKGROUND_RGB = (124, 124, 124)


@dataclass(frozen=True)
class LeafCatalogTrainingResult:
    """Auditable checkpoint and metrics for the mixed-source local catalog."""

    output_dir: Path
    checkpoint: Path
    metrics: dict[str, object]


@dataclass(frozen=True)
class _Record:
    source: str
    key: str | int
    label: int


class _LeafCatalogDataset(Dataset[tuple[torch.Tensor, int]]):
    def __init__(
        self,
        records: list[_Record],
        *,
        uci_images: dict[str, bytes],
        plantvillage_split: object,
        image_size: int,
    ) -> None:
        self.records = records
        self.uci_images = uci_images
        self.plantvillage_split = plantvillage_split
        self.transform = build_eval_transform(image_size)

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, index: int) -> tuple[torch.Tensor, int]:
        record = self.records[index]
        if record.source == "uci_leaf100":
            image = _prepare_uci_silhouette(self.uci_images[str(record.key)])
        else:
            sample = self.plantvillage_split[int(record.key)]  # type: ignore[index]
            isolation = isolate_leaf(sample["image"])
            if not isolation.accepted or isolation.species_image is None:
                raise RuntimeError(
                    "preselected PlantVillage leaf no longer passes isolation: "
                    f"{isolation.reason}"
                )
            image = isolation.species_image
        return self.transform(image), record.label


def train_leaf_catalog(
    *,
    uci_archive: Path,
    cache_dir: Path,
    output_dir: Path,
    seed: int = 42,
    image_size: int = 224,
    uci_train_per_species: int = 10,
    uci_validation_per_species: int = 3,
    uci_test_per_species: int = 3,
    plantvillage_train_per_crop: int = 64,
    plantvillage_validation_per_crop: int = 16,
    plantvillage_test_per_crop: int = 32,
    head_epochs: int = 80,
    batch_size: int = 64,
    device: torch.device | None = None,
) -> LeafCatalogTrainingResult:
    """Train one 100+ class frozen-MobileNet leaf identity head.

    UCI contributes shape-only silhouettes for 100 tree species. PlantVillage
    contributes isolated colour leaves for the 14 local disease hosts. Metrics are
    reported by source because the mixed domains are not a field benchmark.
    """

    if min(
        uci_train_per_species,
        uci_validation_per_species,
        uci_test_per_species,
        plantvillage_train_per_crop,
        plantvillage_validation_per_crop,
        plantvillage_test_per_crop,
    ) <= 0:
        raise ValueError("all per-class split sizes must be positive")
    if (
        uci_train_per_species
        + uci_validation_per_species
        + uci_test_per_species
        > 16
    ):
        raise ValueError("UCI Leaf100 publishes only 16 images per species")
    if head_epochs <= 0 or batch_size <= 0:
        raise ValueError("head_epochs and batch_size must be positive")
    if _sha256(uci_archive) != UCI_ARCHIVE_SHA256:
        raise ValueError("unexpected UCI Leaf100 archive SHA-256")

    started = perf_counter()
    seed_everything(seed)
    resolved_device = device or torch.device("cpu")
    splits, disease_names = hf_data.load_plantvillage_dataset_splits(cache_dir)
    crop_names = sorted({lookup_disease_knowledge(name).plant for name in disease_names})
    uci_images, uci_members = _load_uci_archive(uci_archive)
    uci_names = sorted(uci_members)
    class_names = sorted([*uci_names, *crop_names])
    if len(class_names) != 114 or len(set(class_names)) != 114:
        raise ValueError(
            f"expected 100 UCI species plus 14 PlantVillage crops; got {len(class_names)}"
        )
    class_to_index = {name: index for index, name in enumerate(class_names)}

    train_records: list[_Record] = []
    validation_records: list[_Record] = []
    test_records: list[_Record] = []
    rng = random.Random(seed)
    for species in uci_names:
        members = list(uci_members[species])
        rng.shuffle(members)
        train_end = uci_train_per_species
        validation_end = train_end + uci_validation_per_species
        test_end = validation_end + uci_test_per_species
        label = class_to_index[species]
        train_records.extend(_Record("uci_leaf100", key, label) for key in members[:train_end])
        validation_records.extend(
            _Record("uci_leaf100", key, label)
            for key in members[train_end:validation_end]
        )
        test_records.extend(
            _Record("uci_leaf100", key, label)
            for key in members[validation_end:test_end]
        )

    disease_to_crop = [lookup_disease_knowledge(name).plant for name in disease_names]
    train_labels = hf_data.labels_from_split(splits["train"])
    test_labels = hf_data.labels_from_split(splits["test"])
    pv_train, pv_validation, train_audit = _select_plantvillage_records(
        splits["train"],
        train_labels,
        disease_to_crop,
        class_to_index,
        train_count=plantvillage_train_per_crop,
        validation_count=plantvillage_validation_per_crop,
        seed=seed + 101,
    )
    pv_test, _, test_audit = _select_plantvillage_records(
        splits["test"],
        test_labels,
        disease_to_crop,
        class_to_index,
        train_count=plantvillage_test_per_crop,
        validation_count=0,
        seed=seed + 202,
    )
    train_records.extend(pv_train)
    validation_records.extend(pv_validation)
    test_records.extend(pv_test)

    loaders = {
        "train": DataLoader(
            _LeafCatalogDataset(
                train_records,
                uci_images=uci_images,
                plantvillage_split=splits["train"],
                image_size=image_size,
            ),
            batch_size=batch_size,
            shuffle=False,
            num_workers=0,
        ),
        "validation": DataLoader(
            _LeafCatalogDataset(
                validation_records,
                uci_images=uci_images,
                plantvillage_split=splits["train"],
                image_size=image_size,
            ),
            batch_size=batch_size,
            shuffle=False,
            num_workers=0,
        ),
        "test": DataLoader(
            _LeafCatalogDataset(
                test_records,
                uci_images=uci_images,
                plantvillage_split=splits["test"],
                image_size=image_size,
            ),
            batch_size=batch_size,
            shuffle=False,
            num_workers=0,
        ),
    }

    model = create_model("mobilenet_v2", len(class_names), pretrained=True).to(
        resolved_device
    )
    for parameter in model.features.parameters():  # type: ignore[attr-defined]
        parameter.requires_grad_(False)
    train_features, train_targets = _features(model, loaders["train"], resolved_device)
    validation_features, validation_targets = _features(
        model, loaders["validation"], resolved_device
    )
    test_features, test_targets = _features(model, loaders["test"], resolved_device)
    model.cpu()
    head = model.classifier  # type: ignore[attr-defined]
    class_counts = torch.bincount(train_targets, minlength=len(class_names)).float()
    class_weights = class_counts.sum() / (len(class_names) * class_counts)
    criterion = nn.CrossEntropyLoss(weight=class_weights)
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
        validation_predictions = _predictions(head, validation_features)
        validation_accuracy = _macro_class_accuracy(
            validation_predictions,
            validation_targets.tolist(),
            len(class_names),
        )
        curve.append(
            {
                "epoch": epoch,
                "train_loss": total_loss / len(train_features),
                "validation_accuracy": validation_accuracy,
            }
        )
        if validation_accuracy > best_accuracy:
            best_accuracy = validation_accuracy
            best_state = {
                name: value.detach().cpu().clone()
                for name, value in head.state_dict().items()
            }
    if best_state is None:
        raise RuntimeError("leaf catalog head training produced no checkpoint")
    head.load_state_dict(best_state)
    test_predictions = _predictions(head, test_features)
    metrics = classification_metrics(test_targets.tolist(), test_predictions, class_names)
    test_sources = [record.source for record in test_records]
    target_values = test_targets.tolist()
    metrics["source_accuracy"] = {
        source: _accuracy(
            _values_for_source(test_predictions, test_sources, source),
            _values_for_source(target_values, test_sources, source),
        )
        for source in sorted(set(test_sources))
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    checkpoint = output_dir / "checkpoint.pt"
    save_checkpoint(
        checkpoint,
        model,
        class_names,
        {
            "model_name": "mobilenet_v2",
            "num_classes": len(class_names),
            "image_size": image_size,
            "task": "plant_species_classification",
            "pretrained_backbone": "ImageNet1K_V2",
            "training_protocol": "frozen_backbone_balanced_uci100_pv14_leaf_catalog_v2",
            "input_preprocessing": LEAF_ISOLATION_METHOD,
            "seed": seed,
            "catalog_size": len(class_names),
            "catalog_sources": ["UCI Leaf100 CC BY 4.0", "PlantVillage"],
        },
    )
    save_metrics(metrics, output_dir / "metrics.json")
    (output_dir / "training_curve.json").write_text(
        json.dumps(curve, indent=2), encoding="utf-8"
    )
    split_payload = {
        "schema_version": 1,
        "seed": seed,
        "uci_archive_sha256": UCI_ARCHIVE_SHA256,
        "train": [_record_json(item, class_names) for item in train_records],
        "validation": [_record_json(item, class_names) for item in validation_records],
        "test": [_record_json(item, class_names) for item in test_records],
    }
    (output_dir / "split.json").write_text(
        json.dumps(split_payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    manifest = {
        "schema_version": 1,
        "run_id": f"leaf114-uci100-pv14-mobilenet-v2-frozen-seed{seed}",
        "status": "completed",
        "seed": seed,
        "device": str(resolved_device),
        "python": sys.version.split()[0],
        "torch": torch.__version__,
        "platform": platform.platform(),
        "catalog_size": len(class_names),
        "uci_species_count": len(uci_names),
        "plantvillage_crop_count": len(crop_names),
        "train_sample_count": len(train_records),
        "validation_sample_count": len(validation_records),
        "test_sample_count": len(test_records),
        "best_validation_accuracy": best_accuracy,
        "validation_selection_metric": "macro_class_accuracy",
        "duration_seconds": perf_counter() - started,
        "head_epochs": head_epochs,
        "batch_size": batch_size,
        "input_preprocessing": LEAF_ISOLATION_METHOD,
        "plantvillage_selection": {
            "train_validation": train_audit,
            "test": test_audit,
        },
        "sources": [
            {
                "id": "uci_leaf100",
                "url": UCI_DATASET_URL,
                "doi": "10.24432/C5RG76",
                "license": "CC BY 4.0",
                "modality": "controlled binary leaf silhouettes",
            },
            {
                "id": "plantvillage",
                "modality": "controlled-background crop leaves",
            },
        ],
        "scope": (
            "Local 114-class controlled-source leaf identity pilot. UCI metrics test "
            "silhouette discrimination; neither source establishes field accuracy."
        ),
    }
    (output_dir / "run_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return LeafCatalogTrainingResult(output_dir, checkpoint, metrics)


def _load_uci_archive(
    path: Path,
) -> tuple[dict[str, bytes], dict[str, list[str]]]:
    images: dict[str, bytes] = {}
    by_species: defaultdict[str, list[str]] = defaultdict(list)
    with ZipFile(path) as archive:
        for member in sorted(archive.namelist()):
            if not member.startswith(UCI_ARCHIVE_PREFIX) or not member.lower().endswith(".jpg"):
                continue
            relative = member[len(UCI_ARCHIVE_PREFIX) :]
            species_folder, _, _filename = relative.partition("/")
            if not species_folder:
                continue
            scientific_name = species_folder.replace("_", " ")
            images[member] = archive.read(member)
            by_species[scientific_name].append(member)
    if len(by_species) != 100 or any(len(items) != 16 for items in by_species.values()):
        raise ValueError("UCI Leaf100 archive must contain 100 species with 16 images each")
    return images, dict(by_species)


def _prepare_uci_silhouette(image_bytes: bytes) -> Image.Image:
    with Image.open(io.BytesIO(image_bytes)) as image:
        grayscale = np.asarray(image.convert("L"), dtype=np.uint8)
    mask = (grayscale >= 128).astype(np.uint8) * 255
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        raise ValueError("UCI silhouette contains no foreground leaf")
    clean = np.zeros_like(mask)
    cv2.drawContours(clean, [max(contours, key=cv2.contourArea)], -1, 255, cv2.FILLED)
    canvas = np.empty((*clean.shape, 3), dtype=np.uint8)
    canvas[:, :] = NEUTRAL_BACKGROUND_RGB
    canvas[clean > 0] = CANONICAL_LEAF_RGB
    return Image.fromarray(canvas, mode="RGB")


def _select_plantvillage_records(
    split: object,
    labels: list[int],
    disease_to_crop: list[str],
    class_to_index: dict[str, int],
    *,
    train_count: int,
    validation_count: int,
    seed: int,
) -> tuple[list[_Record], list[_Record], dict[str, object]]:
    by_crop: defaultdict[str, list[int]] = defaultdict(list)
    for index, disease_label in enumerate(labels):
        by_crop[disease_to_crop[disease_label]].append(index)
    rng = random.Random(seed)
    train: list[_Record] = []
    validation: list[_Record] = []
    audit: dict[str, object] = {}
    required = train_count + validation_count
    for crop in sorted(by_crop):
        candidates = list(by_crop[crop])
        rng.shuffle(candidates)
        accepted: list[int] = []
        reasons: Counter[str] = Counter()
        for candidate in candidates:
            isolation = isolate_leaf(split[candidate]["image"])  # type: ignore[index]
            if isolation.accepted:
                accepted.append(candidate)
                if len(accepted) == required:
                    break
            else:
                reasons[isolation.reason] += 1
        if len(accepted) != required:
            raise ValueError(
                f"{crop} has {len(accepted)} accepted leaves; {required} required"
            )
        label = class_to_index[crop]
        train.extend(
            _Record("plantvillage", index, label)
            for index in accepted[:train_count]
        )
        validation.extend(
            _Record("plantvillage", index, label)
            for index in accepted[train_count:]
        )
        audit[crop] = {
            "accepted": len(accepted),
            "attempted": len(accepted) + sum(reasons.values()),
            "rejection_reasons": dict(reasons),
        }
    return train, validation, audit


def _features(
    model: nn.Module,
    loader: DataLoader,
    device: torch.device,
) -> tuple[torch.Tensor, torch.Tensor]:
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


def _predictions(
    head: nn.Module,
    features: torch.Tensor,
    batch_size: int = 512,
) -> list[int]:
    values: list[int] = []
    head.eval()
    with torch.inference_mode():
        for start in range(0, len(features), batch_size):
            values.extend(
                int(value)
                for value in head(features[start : start + batch_size]).argmax(1)
            )
    return values


def _accuracy(predictions: list[int], targets: list[int]) -> float:
    if not predictions or len(predictions) != len(targets):
        raise ValueError("accuracy requires equal non-empty prediction and target lists")
    return sum(
        int(prediction == target)
        for prediction, target in zip(predictions, targets, strict=True)
    ) / len(targets)


def _macro_class_accuracy(
    predictions: list[int],
    targets: list[int],
    class_count: int,
) -> float:
    per_class: list[float] = []
    for label in range(class_count):
        label_predictions = [
            prediction
            for prediction, target in zip(predictions, targets, strict=True)
            if target == label
        ]
        if label_predictions:
            per_class.append(
                sum(int(prediction == label) for prediction in label_predictions)
                / len(label_predictions)
            )
    if len(per_class) != class_count:
        raise ValueError("macro class accuracy requires every class in validation")
    return sum(per_class) / len(per_class)


def _values_for_source(
    values: list[int],
    sources: list[str],
    selected_source: str,
) -> list[int]:
    return [
        value
        for value, source in zip(values, sources, strict=True)
        if source == selected_source
    ]


def _record_json(record: _Record, class_names: list[str]) -> dict[str, object]:
    return {
        "source": record.source,
        "key": record.key,
        "label": record.label,
        "class_name": class_names[record.label],
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


__all__ = [
    "LeafCatalogTrainingResult",
    "UCI_ARCHIVE_SHA256",
    "UCI_DATASET_URL",
    "train_leaf_catalog",
]
