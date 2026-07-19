"""Train the low-compute local 114-class leaf identity catalog."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import torch

from plantdisease.training.leaf_catalog import train_leaf_catalog


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--uci-archive", type=Path, required=True)
    parser.add_argument("--cache-dir", type=Path, default=Path("data/huggingface"))
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/openleaf/leaf114_uci100_pv14_balanced_seed42"),
    )
    parser.add_argument("--head-epochs", type=int, default=80)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--device", choices=["cpu", "mps", "cuda"], default="cpu")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    os.environ.setdefault("HF_HOME", str(args.cache_dir.resolve()))
    os.environ.setdefault(
        "HF_MODULES_CACHE", str((args.cache_dir / "modules").resolve())
    )
    result = train_leaf_catalog(
        uci_archive=args.uci_archive,
        cache_dir=args.cache_dir,
        output_dir=args.output_dir,
        head_epochs=args.head_epochs,
        batch_size=args.batch_size,
        device=torch.device(args.device),
        seed=args.seed,
    )
    print(
        json.dumps(
            {
                "checkpoint": str(result.checkpoint),
                "accuracy": result.metrics["accuracy"],
                "macro_f1": result.metrics["macro_f1"],
                "source_accuracy": result.metrics["source_accuracy"],
            }
        )
    )


if __name__ == "__main__":
    main()
