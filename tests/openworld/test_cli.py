from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from plantdisease.openworld.cli import (
    calibrate_main,
    index_main,
    predict_main,
    prepare_main,
)


def _write_embeddings(path: Path, embeddings: np.ndarray, labels: list[str]) -> None:
    np.savez_compressed(path, embeddings=embeddings, plant_ids=np.asarray(labels))


def test_index_calibrate_and_predict_cli_round_trip(
    tmp_path: Path, capsys
) -> None:
    train_path = tmp_path / "train.npz"
    known_path = tmp_path / "known.npz"
    unknown_path = tmp_path / "unknown.npz"
    index_dir = tmp_path / "index"
    query_path = tmp_path / "query.npy"
    _write_embeddings(
        train_path,
        np.asarray([[1.0, 0.0], [0.98, 0.03], [0.0, 1.0], [0.03, 0.98]]),
        ["grape", "grape", "tomato", "tomato"],
    )
    _write_embeddings(
        known_path,
        np.asarray([[1.0, 0.01], [0.01, 1.0]]),
        ["grape", "tomato"],
    )
    np.savez_compressed(
        unknown_path,
        embeddings=np.asarray([[0.70, 0.70], [-0.70, -0.70]]),
    )
    np.save(query_path, np.asarray([1.0, 0.01]))

    index_main(
        [
            "--embeddings",
            str(train_path),
            "--output-dir",
            str(index_dir),
            "--encoder-id",
            "synthetic",
            "--max-prototypes-per-class",
            "1",
        ]
    )
    calibrate_main(
        [
            "--index-dir",
            str(index_dir),
            "--known",
            str(known_path),
            "--unknown",
            str(unknown_path),
        ]
    )
    predict_main(
        [
            "--index-dir",
            str(index_dir),
            "--embedding",
            str(query_path),
        ]
    )

    output = capsys.readouterr().out
    assert output.count('"status": "completed"') == 2
    assert json.loads(output[output.rfind("{") :])["plant_id"] == "grape"


def test_prepare_cli_exports_a_leaf_only_manifest(tmp_path: Path, capsys) -> None:
    image = Image.new("RGB", (160, 120), (25, 26, 28))
    ImageDraw.Draw(image).ellipse((20, 12, 140, 108), fill=(55, 150, 63))
    image.save(tmp_path / "leaf.png")
    manifest = tmp_path / "manifest.jsonl"
    manifest.write_text(
        json.dumps(
            {
                "image_id": "leaf-1",
                "entity_id": "entity-1",
                "image_path": "leaf.png",
                "plant_id": "vitis_vinifera",
                "condition_id": "healthy",
                "split": "train",
                "source": "test",
                "license": "CC0",
            }
        ),
        encoding="utf-8",
    )
    output_dir = tmp_path / "prepared"

    prepare_main(
        [
            "--manifest",
            str(manifest),
            "--image-root",
            str(tmp_path),
            "--output-dir",
            str(output_dir),
        ]
    )

    result = json.loads(capsys.readouterr().out)
    assert result["accepted_count"] == 1
    assert (output_dir / "prepared_manifest.jsonl").is_file()
