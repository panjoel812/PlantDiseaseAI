"""Evaluate OpenLeaf-14 rejection on disjoint external validation/test species."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from dataclasses import asdict
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from torch.utils.data import DataLoader, Dataset

from plantdisease.data import huggingface as hf_data
from plantdisease.data.transforms import build_eval_transform
from plantdisease.models.checkpoint import load_checkpoint
from plantdisease.openworld.evaluation import evaluate_open_set
from plantdisease.openworld.index import PrototypeIndex, calibrate_thresholds, save_calibration
from plantdisease.openworld.manifest import OpenWorldRecord, load_manifest
from plantdisease.serving.knowledge import lookup_disease_knowledge
from plantdisease.training.crop import _CropDataset, _features


class _PreparedExternalLeafDataset(Dataset[tuple[torch.Tensor, int]]):
    def __init__(self, root: Path, records: list[OpenWorldRecord], image_size: int) -> None:
        self.root = root.resolve()
        self.records = records
        self.transform = build_eval_transform(image_size)

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, index: int) -> tuple[torch.Tensor, int]:
        path = (self.root / self.records[index].image_path).resolve()
        if not path.is_relative_to(self.root):
            raise ValueError("external image path escapes the dataset root")
        with Image.open(path) as image:
            tensor = self.transform(image.convert("RGB"))
        return tensor, 0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache-dir", type=Path, default=Path("data/huggingface"))
    parser.add_argument(
        "--pilot-dir",
        type=Path,
        default=Path("outputs/plantvillage/leaf14_opencv_pilot_seed42"),
    )
    parser.add_argument(
        "--external-dir",
        type=Path,
        default=Path("data/external_ood/uci_leaf100_leaf6_shape"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/plantvillage/leaf14_external_ood_shape6_seed42"),
    )
    parser.add_argument("--batch-size", type=int, default=64)
    args = parser.parse_args()
    if (args.output_dir / "metrics.json").exists():
        raise FileExistsError("metrics already exist; use a new output directory")

    split_indices = json.loads((args.pilot_dir / "split.json").read_text())
    splits, disease_names = hf_data.load_plantvillage_dataset_splits(args.cache_dir)
    model, crop_names, checkpoint_config = load_checkpoint(
        args.pilot_dir / "checkpoint.pt",
        torch.device("cpu"),
    )
    expected_crop_names = sorted(
        {lookup_disease_knowledge(name).plant for name in disease_names}
    )
    if crop_names != expected_crop_names:
        raise ValueError("checkpoint crop names do not match the dataset taxonomy")
    crop_to_index = {name: index for index, name in enumerate(crop_names)}
    disease_to_crop = [
        crop_to_index[lookup_disease_knowledge(name).plant] for name in disease_names
    ]

    known_features: dict[str, np.ndarray] = {}
    known_targets: dict[str, np.ndarray] = {}
    split_sources = {"train": "train", "validation": "train", "test": "test"}
    for split_name, source_name in split_sources.items():
        loader = DataLoader(
            _CropDataset(
                splits[source_name],
                split_indices[split_name],
                disease_to_crop,
                int(checkpoint_config["image_size"]),
                leaf_isolation=True,
            ),
            batch_size=args.batch_size,
            shuffle=False,
            num_workers=0,
        )
        split_features, split_targets = _features(model, loader, torch.device("cpu"))
        known_features[split_name] = split_features.numpy()
        known_targets[split_name] = split_targets.numpy()

    manifest_path = args.external_dir / "prepared_manifest.jsonl"
    records = sorted(load_manifest(manifest_path), key=lambda record: record.image_id)
    validation_records = [record for record in records if record.split == "ood_validation"]
    test_records = [record for record in records if record.split == "ood_test"]
    expected_validation_species = {record.plant_id for record in validation_records}
    expected_test_species = {record.plant_id for record in test_records}
    if len(expected_validation_species) < 3 or len(expected_test_species) < 3:
        raise ValueError("external protocol requires at least three species per OOD split")
    if expected_validation_species & expected_test_species:
        raise ValueError("external species identities cross validation and test")
    if (expected_validation_species | expected_test_species) & set(crop_names):
        raise ValueError("external OOD species overlap the known crop taxonomy")

    external_features: dict[str, np.ndarray] = {}
    for name, subset in (("validation", validation_records), ("test", test_records)):
        loader = DataLoader(
            _PreparedExternalLeafDataset(
                args.external_dir,
                subset,
                int(checkpoint_config["image_size"]),
            ),
            batch_size=args.batch_size,
            shuffle=False,
            num_workers=0,
        )
        values, _ = _features(model, loader, torch.device("cpu"))
        external_features[name] = values.numpy()

    train_labels = [crop_names[index] for index in known_targets["train"]]
    index = PrototypeIndex.fit(
        known_features["train"],
        train_labels,
        encoder_id="leaf14-opencv-mobilenet-v2-imagenet1k-v2",
        max_prototypes_per_class=3,
        seed=42,
    )
    validation_labels = [crop_names[index] for index in known_targets["validation"]]
    calibration = calibrate_thresholds(
        index,
        known_features["validation"],
        validation_labels,
        external_features["validation"],
    )
    calibrated_index = index.with_thresholds(calibration)
    test_labels = [crop_names[index] for index in known_targets["test"]]
    metrics = evaluate_open_set(
        calibrated_index,
        known_features["test"],
        test_labels,
        external_features["test"],
    )

    per_species = _external_species_metrics(
        calibrated_index,
        test_records,
        external_features["test"],
    )
    dataset_audit_path = args.external_dir / "dataset_audit.json"
    dataset_audit = json.loads(dataset_audit_path.read_text(encoding="utf-8"))
    closed_set_metrics = json.loads(
        (args.pilot_dir / "metrics.json").read_text(encoding="utf-8")
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    calibrated_index.save(args.output_dir / "index")
    save_calibration(calibration, args.output_dir / "calibration.json")
    result = {
        "schema_version": 1,
        "run_id": "leaf14-external-uci-shape6-seed42",
        "status": "completed-controlled-outline-ood-stress-test",
        "protocol": (
            "14 known PlantVillage crops; 3 external species for threshold validation; "
            "3 identity-disjoint external silhouette species for final OOD test"
        ),
        "known_species": crop_names,
        "ood_validation_species": sorted(expected_validation_species),
        "ood_test_species": sorted(expected_test_species),
        "encoder_id": calibrated_index.encoder_id,
        "similarity_threshold": calibrated_index.similarity_threshold,
        "margin_threshold": calibrated_index.margin_threshold,
        "calibration": asdict(calibration),
        "open_set_test_metrics": metrics.to_dict(),
        "ood_test_per_species": per_species,
        "closed_set_head_reference": {
            "source_run_id": "leaf14-opencv-mobilenet-v2-frozen-pilot-seed42",
            "accepted_test_count": int(closed_set_metrics["sample_count"]),
            "conditional_accuracy": float(closed_set_metrics["accuracy"]),
            "conditional_macro_f1": float(closed_set_metrics["macro_f1"]),
            "note": "Carried forward from the same frozen 448-leaf official test split.",
        },
        "external_dataset": {
            "dataset_id": dataset_audit["dataset_id"],
            "modality": dataset_audit["modality"],
            "sample_count": dataset_audit["sample_count"],
            "license": dataset_audit["license"],
            "doi": dataset_audit["doi"],
        },
        "source_artifacts": {
            "prepared_manifest_sha256": _sha256(manifest_path),
            "source_records_sha256": _sha256(args.external_dir / "source_records.jsonl"),
            "dataset_audit_sha256": _sha256(dataset_audit_path),
            "known_checkpoint_sha256": _sha256(args.pilot_dir / "checkpoint.pt"),
            "known_split_sha256": _sha256(args.pilot_dir / "split.json"),
        },
        "limitations": [
            "External samples are controlled silhouettes, not field photographs.",
            "Canonical recoloring has no real color, texture, venation, or disease evidence.",
            "Known data are photographs while OOD data are outline-only proxies.",
            "Thresholds must not be described as universal open-world protection.",
        ],
    }
    metrics_path = args.output_dir / "metrics.json"
    metrics_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False))


def _external_species_metrics(
    index: PrototypeIndex,
    records: list[OpenWorldRecord],
    embeddings: np.ndarray,
) -> dict[str, dict[str, object]]:
    grouped: defaultdict[str, list[tuple[bool, float, float, str]]] = defaultdict(list)
    for record, embedding in zip(records, embeddings, strict=True):
        decision = index.predict(embedding)
        grouped[record.plant_id].append(
            (
                decision.accepted,
                decision.similarity,
                decision.margin,
                decision.candidate_plant_id,
            )
        )
    result: dict[str, dict[str, object]] = {}
    for species, rows in sorted(grouped.items()):
        result[species] = {
            "count": len(rows),
            "reject_rate": sum(not row[0] for row in rows) / len(rows),
            "false_accept_rate": sum(row[0] for row in rows) / len(rows),
            "mean_max_similarity": float(np.mean([row[1] for row in rows])),
            "mean_top1_top2_margin": float(np.mean([row[2] for row in rows])),
            "candidate_known_species": dict(Counter(row[3] for row in rows)),
        }
    return result


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


if __name__ == "__main__":
    main()
