from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from plantdisease.openworld.index import PrototypeIndex, calibrate_thresholds


def _training_vectors() -> tuple[np.ndarray, list[str]]:
    return (
        np.asarray(
            [
                [1.0, 0.02, 0.0],
                [0.98, 0.08, 0.0],
                [1.0, -0.04, 0.0],
                [0.02, 1.0, 0.0],
                [-0.05, 0.99, 0.0],
                [0.08, 1.0, 0.0],
            ],
            dtype=np.float32,
        ),
        ["grape", "grape", "grape", "tomato", "tomato", "tomato"],
    )


def test_prototype_index_accepts_known_and_rejects_ambiguous_query() -> None:
    embeddings, labels = _training_vectors()
    index = PrototypeIndex.fit(
        embeddings,
        labels,
        encoder_id="synthetic-encoder",
        max_prototypes_per_class=2,
        similarity_threshold=0.75,
        margin_threshold=0.20,
    )

    known = index.predict(np.asarray([0.99, 0.03, 0.0]))
    ambiguous = index.predict(np.asarray([0.70, 0.70, 0.0]))

    assert known.accepted is True
    assert known.plant_id == "grape"
    assert ambiguous.accepted is False
    assert ambiguous.plant_id is None
    assert "margin" in ambiguous.reason.lower()


def test_prototype_index_round_trip_preserves_predictions(tmp_path: Path) -> None:
    embeddings, labels = _training_vectors()
    index = PrototypeIndex.fit(
        embeddings,
        labels,
        encoder_id="synthetic-encoder",
        max_prototypes_per_class=2,
    )
    index.save(tmp_path)

    loaded = PrototypeIndex.load(tmp_path)

    assert loaded.predict(np.asarray([1.0, 0.0, 0.0])) == index.predict(
        np.asarray([1.0, 0.0, 0.0])
    )
    assert loaded.encoder_id == "synthetic-encoder"


def test_threshold_calibration_uses_explicit_unknown_examples() -> None:
    embeddings, labels = _training_vectors()
    index = PrototypeIndex.fit(
        embeddings,
        labels,
        encoder_id="synthetic-encoder",
        max_prototypes_per_class=1,
    )
    known = np.asarray([[1.0, 0.01, 0.0], [0.02, 1.0, 0.0]], dtype=np.float32)
    unknown = np.asarray([[0.70, 0.70, 0.0], [-0.70, -0.70, 0.0]], dtype=np.float32)

    calibration = calibrate_thresholds(index, known, ["grape", "tomato"], unknown)
    calibrated = index.with_thresholds(calibration)

    assert calibration.known_correct_accept_rate == pytest.approx(1.0)
    assert calibration.unknown_reject_rate == pytest.approx(1.0)
    assert calibrated.predict(known[0]).accepted is True
    assert calibrated.predict(unknown[0]).accepted is False
