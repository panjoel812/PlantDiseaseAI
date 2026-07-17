import json
from pathlib import Path

import pytest

from plantdisease.evaluation.metrics import classification_metrics, save_metrics


def test_classification_metrics_match_known_example(tmp_path: Path) -> None:
    metrics = classification_metrics(
        y_true=[0, 0, 1, 1],
        y_pred=[0, 1, 1, 1],
        class_names=["healthy", "disease"],
    )

    assert metrics["accuracy"] == pytest.approx(0.75)
    assert metrics["macro_precision"] == pytest.approx((1.0 + 2 / 3) / 2)
    assert metrics["macro_recall"] == pytest.approx((0.5 + 1.0) / 2)
    assert metrics["macro_f1"] == pytest.approx((2 / 3 + 0.8) / 2)
    assert metrics["confusion_matrix"] == [[1, 1], [0, 2]]
    assert metrics["per_class"]["healthy"]["support"] == 2
    assert metrics["per_class"]["disease"]["recall"] == pytest.approx(1.0)

    path = tmp_path / "metrics.json"
    save_metrics(metrics, path)
    assert json.loads(path.read_text(encoding="utf-8"))["accuracy"] == 0.75


def test_classification_metrics_reject_mismatched_lengths() -> None:
    with pytest.raises(ValueError, match="same non-zero length"):
        classification_metrics([0], [0, 1], ["healthy", "disease"])


def test_classification_metrics_reject_out_of_range_label() -> None:
    with pytest.raises(ValueError, match="outside class range"):
        classification_metrics([0, 2], [0, 1], ["healthy", "disease"])
