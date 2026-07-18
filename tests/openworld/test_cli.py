from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from plantdisease.openworld.cli import calibrate_main, index_main, predict_main


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
