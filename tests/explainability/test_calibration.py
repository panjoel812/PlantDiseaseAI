import json
from pathlib import Path

import pytest

from plantdisease.explainability.calibration import analyze_calibration


def _record(test_index: int, confidence: float, correct: bool) -> dict[str, object]:
    return {
        "test_index": test_index,
        "sample_id": f"hf-test-{test_index}",
        "true_class_index": 0 if correct else 1,
        "true_class_name": "healthy" if correct else "disease",
        "predicted_class_index": 0,
        "predicted_class_name": "healthy",
        "confidence": confidence,
        "correct": correct,
        "top_k": [],
    }


def test_analyze_calibration_writes_json_report_and_reliability_diagram(
    tmp_path: Path,
) -> None:
    predictions_path = tmp_path / "predictions.json"
    output_path = tmp_path / "calibration.json"
    report_path = tmp_path / "calibration.md"
    figure_path = tmp_path / "reliability.png"
    predictions_path.write_text(
        json.dumps(
            [
                _record(1, 0.91, True),
                _record(2, 0.84, False),
                _record(3, 0.62, True),
                _record(4, 0.35, False),
                _record(5, 0.15, True),
            ]
        ),
        encoding="utf-8",
    )

    result = analyze_calibration(
        predictions_path=predictions_path,
        output_path=output_path,
        report_path=report_path,
        figure_path=figure_path,
        num_bins=5,
    )

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    report = report_path.read_text(encoding="utf-8")
    assert result.calibration_path == output_path
    assert result.report_path == report_path
    assert result.figure_path == figure_path
    assert result.sample_count == 5
    assert payload["summary"]["accuracy"] == pytest.approx(0.6)
    assert payload["summary"]["mean_confidence"] == pytest.approx(0.574)
    assert payload["summary"]["top_label_ece"] == pytest.approx(0.466)
    assert payload["summary"]["top_label_mce"] == pytest.approx(0.85)
    assert payload["summary"]["top_label_brier"] == pytest.approx(0.34062)
    assert payload["bins"][0] == {
        "bin_index": 0,
        "lower": 0.0,
        "upper": 0.2,
        "count": 1,
        "accuracy": pytest.approx(1.0),
        "avg_confidence": pytest.approx(0.15),
        "gap": pytest.approx(0.85),
    }
    assert payload["bins"][2]["count"] == 0
    assert payload["bins"][2]["accuracy"] is None
    assert figure_path.exists()
    assert "Top-label ECE" in report
    assert "reliability diagram" in report


def test_analyze_calibration_rejects_invalid_confidence(tmp_path: Path) -> None:
    predictions_path = tmp_path / "predictions.json"
    predictions_path.write_text(json.dumps([_record(1, 1.2, True)]), encoding="utf-8")

    with pytest.raises(ValueError, match="confidence values must be in \\[0, 1\\]"):
        analyze_calibration(
            predictions_path=predictions_path,
            output_path=tmp_path / "calibration.json",
        )
