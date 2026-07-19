"""Run a six-held-out-species OpenLeaf-14 rejection sanity check."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader

from plantdisease.data import huggingface as hf_data
from plantdisease.models.checkpoint import load_checkpoint
from plantdisease.openworld.evaluation import evaluate_open_set
from plantdisease.openworld.index import PrototypeIndex, calibrate_thresholds, save_calibration
from plantdisease.serving.knowledge import lookup_disease_knowledge
from plantdisease.training.crop import _CropDataset, _features

HELD_OUT_SPECIES = (
    "Blueberry",
    "Cherry (including sour)",
    "Peach",
    "Raspberry",
    "Soybean",
    "Squash",
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache-dir", type=Path, default=Path("data/huggingface"))
    parser.add_argument(
        "--pilot-dir",
        type=Path,
        default=Path("outputs/plantvillage/leaf14_opencv_pilot_seed42"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/plantvillage/leaf14_open_set_holdout6_seed42"),
    )
    parser.add_argument("--batch-size", type=int, default=64)
    args = parser.parse_args()

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

    features: dict[str, np.ndarray] = {}
    targets: dict[str, np.ndarray] = {}
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
        features[split_name] = split_features.numpy()
        targets[split_name] = split_targets.numpy()

    unknown_indices = np.asarray([crop_to_index[name] for name in HELD_OUT_SPECIES])
    known_names = [name for name in crop_names if name not in HELD_OUT_SPECIES]

    def known_mask(split_name: str) -> np.ndarray:
        return ~np.isin(targets[split_name], unknown_indices)

    train_known = known_mask("train")
    train_labels = [crop_names[index] for index in targets["train"][train_known]]
    index = PrototypeIndex.fit(
        features["train"][train_known],
        train_labels,
        encoder_id="leaf14-opencv-mobilenet-v2-imagenet1k-v2",
        max_prototypes_per_class=3,
        seed=42,
    )
    validation_known = known_mask("validation")
    calibration = calibrate_thresholds(
        index,
        features["validation"][validation_known],
        [crop_names[index] for index in targets["validation"][validation_known]],
        features["validation"][~validation_known],
    )
    calibrated_index = index.with_thresholds(calibration)
    test_known = known_mask("test")
    metrics = evaluate_open_set(
        calibrated_index,
        features["test"][test_known],
        [crop_names[index] for index in targets["test"][test_known]],
        features["test"][~test_known],
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    calibrated_index.save(args.output_dir / "index")
    save_calibration(calibration, args.output_dir / "calibration.json")
    result = {
        "schema_version": 1,
        "run_id": "leaf14-open-set-internal-holdout6-seed42",
        "status": "completed",
        "protocol": "internal species holdout sanity check; not external OOD",
        "known_species": known_names,
        "held_out_pseudo_unknown_species": list(HELD_OUT_SPECIES),
        "encoder_id": calibrated_index.encoder_id,
        "similarity_threshold": calibrated_index.similarity_threshold,
        "margin_threshold": calibrated_index.margin_threshold,
        "calibration": asdict(calibration),
        "metrics": metrics.to_dict(),
    }
    (args.output_dir / "metrics.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
