"""Train the independent lightweight crop classifier used by the demo."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import torch

from plantdisease.training.crop import train_crop_classifier


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache-dir", type=Path, default=Path("data/huggingface"))
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/plantvillage/crop_mobilenet_v2_seed42"),
    )
    parser.add_argument("--selected-per-crop", type=int, default=320)
    parser.add_argument("--validation-per-crop", type=int, default=64)
    parser.add_argument("--test-per-crop", type=int, default=128)
    parser.add_argument("--head-epochs", type=int, default=120)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    os.environ.setdefault("HF_HOME", str(args.cache_dir.resolve()))
    os.environ.setdefault(
        "HF_MODULES_CACHE", str((args.cache_dir / "modules").resolve())
    )
    result = train_crop_classifier(
        cache_dir=args.cache_dir,
        output_dir=args.output_dir,
        seed=args.seed,
        selected_per_crop=args.selected_per_crop,
        validation_per_crop=args.validation_per_crop,
        test_per_crop=args.test_per_crop,
        head_epochs=args.head_epochs,
        device=torch.device("cpu"),
    )
    print(json.dumps({"checkpoint": str(result.checkpoint), "metrics": result.metrics}))


if __name__ == "__main__":
    main()
