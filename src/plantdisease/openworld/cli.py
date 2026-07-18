"""CLI entry points for the frozen-embedding open-world baseline."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path

import numpy as np
import torch

from plantdisease.openworld.encoder import MobileNetV2ImageNetEncoder, extract_embeddings
from plantdisease.openworld.index import (
    PrototypeIndex,
    calibrate_thresholds,
    save_calibration,
)
from plantdisease.openworld.manifest import load_manifest


def _load_embeddings(path: Path, *, labels_required: bool) -> tuple[np.ndarray, list[str]]:
    arrays = np.load(path, allow_pickle=False)
    if "embeddings" not in arrays:
        raise ValueError(f"{path} must contain an embeddings array")
    labels: list[str] = []
    if "plant_ids" in arrays:
        labels = [str(value) for value in arrays["plant_ids"]]
    elif labels_required:
        raise ValueError(f"{path} must contain a plant_ids array")
    return arrays["embeddings"], labels


def index_main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Build a multi-prototype plant index from frozen image embeddings"
    )
    parser.add_argument("--embeddings", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--encoder-id", required=True)
    parser.add_argument("--max-prototypes-per-class", type=int, default=3)
    parser.add_argument("--similarity-threshold", type=float, default=0.70)
    parser.add_argument("--margin-threshold", type=float, default=0.05)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args(argv)
    embeddings, plant_ids = _load_embeddings(args.embeddings, labels_required=True)
    index = PrototypeIndex.fit(
        embeddings,
        plant_ids,
        encoder_id=args.encoder_id,
        max_prototypes_per_class=args.max_prototypes_per_class,
        similarity_threshold=args.similarity_threshold,
        margin_threshold=args.margin_threshold,
        seed=args.seed,
    )
    index.save(args.output_dir)
    print(
        json.dumps(
            {
                "status": "completed",
                "plant_count": len(index.plant_ids),
                "prototype_count": len(index.prototypes),
                "output_dir": str(args.output_dir),
            }
        )
    )


def embed_main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Extract frozen MobileNetV2 embeddings from an open-world JSONL manifest"
    )
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--image-root", type=Path, required=True)
    parser.add_argument("--split", default="train")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--device", choices=["cpu", "mps", "cuda"], default="cpu")
    args = parser.parse_args(argv)
    records = [record for record in load_manifest(args.manifest) if record.split == args.split]
    if not records:
        raise ValueError(f"manifest contains no records for split {args.split}")
    device = torch.device(args.device)
    encoder = MobileNetV2ImageNetEncoder(device)
    transform = encoder.weights.transforms()
    embeddings, plant_ids, image_ids = extract_embeddings(
        records,
        image_root=args.image_root,
        encoder=encoder,
        transform=transform,
        batch_size=args.batch_size,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        args.output,
        embeddings=embeddings,
        plant_ids=np.asarray(plant_ids),
        image_ids=np.asarray(image_ids),
        encoder_id=np.asarray(encoder.encoder_id),
    )
    print(
        json.dumps(
            {
                "status": "completed",
                "sample_count": len(embeddings),
                "embedding_dimension": embeddings.shape[1],
                "encoder_id": encoder.encoder_id,
                "output": str(args.output),
            }
        )
    )


def calibrate_main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Calibrate unknown-plant rejection from known and OOD validation embeddings"
    )
    parser.add_argument("--index-dir", type=Path, required=True)
    parser.add_argument("--known", type=Path, required=True)
    parser.add_argument("--unknown", type=Path, required=True)
    args = parser.parse_args(argv)
    index = PrototypeIndex.load(args.index_dir)
    known_embeddings, known_plant_ids = _load_embeddings(args.known, labels_required=True)
    unknown_embeddings, _ = _load_embeddings(args.unknown, labels_required=False)
    calibration = calibrate_thresholds(
        index,
        known_embeddings,
        known_plant_ids,
        unknown_embeddings,
    )
    index.with_thresholds(calibration).save(args.index_dir)
    calibration_path = args.index_dir / "calibration.json"
    save_calibration(calibration, calibration_path)
    print(json.dumps({"status": "completed", **asdict(calibration)}))


def predict_main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Query a calibrated plant prototype index with one frozen embedding"
    )
    parser.add_argument("--index-dir", type=Path, required=True)
    parser.add_argument("--embedding", type=Path, required=True)
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args(argv)
    embedding = np.load(args.embedding, allow_pickle=False)
    decision = PrototypeIndex.load(args.index_dir).predict(embedding, top_k=args.top_k)
    print(json.dumps(asdict(decision), ensure_ascii=False, indent=2))
