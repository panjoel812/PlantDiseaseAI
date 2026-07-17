import json
from pathlib import Path

import pytest

from plantdisease.explainability.error_analysis import analyze_error_patterns


def _metrics() -> dict[str, object]:
    return {
        "accuracy": 0.75,
        "macro_precision": 0.77,
        "macro_recall": 0.74,
        "macro_f1": 0.73,
        "sample_count": 12,
        "per_class": {
            "Apple___healthy": {
                "precision": 0.75,
                "recall": 0.5,
                "f1": 0.6,
                "support": 4,
            },
            "Tomato___Late_blight": {
                "precision": 0.8,
                "recall": 0.6,
                "f1": 0.685,
                "support": 5,
            },
            "Potato___Late_blight": {
                "precision": 1.0,
                "recall": 1.0,
                "f1": 1.0,
                "support": 3,
            },
        },
        "confusion_matrix": [
            [2, 1, 1],
            [0, 3, 2],
            [0, 0, 3],
        ],
    }


def _prediction(
    test_index: int,
    true_index: int,
    pred_index: int,
    confidence: float,
) -> dict[str, object]:
    class_names = [
        "Apple___healthy",
        "Tomato___Late_blight",
        "Potato___Late_blight",
    ]
    return {
        "test_index": test_index,
        "sample_id": f"hf-test-{test_index}",
        "true_class_index": true_index,
        "true_class_name": class_names[true_index],
        "predicted_class_index": pred_index,
        "predicted_class_name": class_names[pred_index],
        "confidence": confidence,
        "correct": true_index == pred_index,
        "top_k": [],
    }


def test_analyze_error_patterns_writes_json_and_report(tmp_path: Path) -> None:
    metrics_path = tmp_path / "metrics.json"
    predictions_path = tmp_path / "predictions.json"
    output_path = tmp_path / "error_analysis.json"
    report_path = tmp_path / "error_analysis.md"
    metrics_path.write_text(json.dumps(_metrics()), encoding="utf-8")
    predictions_path.write_text(
        json.dumps(
            [
                _prediction(10, 0, 0, 0.91),
                _prediction(11, 0, 1, 0.87),
                _prediction(12, 0, 2, 0.81),
                _prediction(13, 1, 1, 0.93),
                _prediction(14, 1, 2, 0.95),
                _prediction(15, 2, 2, 0.99),
            ]
        ),
        encoding="utf-8",
    )

    result = analyze_error_patterns(
        metrics_path=metrics_path,
        predictions_path=predictions_path,
        output_path=output_path,
        report_path=report_path,
        low_f1_count=2,
        confusion_pair_count=2,
        high_confidence_threshold=0.85,
        high_confidence_error_count=3,
    )

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    report = report_path.read_text(encoding="utf-8")
    assert result.error_analysis_path == output_path
    assert result.report_path == report_path
    assert result.error_count == 3
    assert result.high_confidence_error_count == 2
    assert payload["summary"]["macro_f1"] == pytest.approx(0.73)
    assert payload["summary"]["error_count"] == 3
    assert payload["low_f1_classes"][0]["class_name"] == "Apple___healthy"
    assert payload["low_f1_classes"][1]["class_name"] == "Tomato___Late_blight"
    assert payload["confusion_pairs"][0] == {
        "true_class_index": 1,
        "true_class_name": "Tomato___Late_blight",
        "predicted_class_index": 2,
        "predicted_class_name": "Potato___Late_blight",
        "count": 2,
        "true_class_error_rate": pytest.approx(0.4),
    }
    assert payload["normalized_confusion_matrix"][0] == pytest.approx([0.5, 0.25, 0.25])
    assert [item["test_index"] for item in payload["high_confidence_errors"]] == [14, 11]
    assert "## 重点混淆对" in report
    assert "Tomato___Late_blight → Potato___Late_blight" in report


def test_analyze_error_patterns_rejects_prediction_class_mismatch(tmp_path: Path) -> None:
    metrics_path = tmp_path / "metrics.json"
    predictions_path = tmp_path / "predictions.json"
    metrics_path.write_text(json.dumps(_metrics()), encoding="utf-8")
    bad_record = _prediction(10, 0, 1, 0.9)
    bad_record["true_class_name"] = "wrong"
    predictions_path.write_text(json.dumps([bad_record]), encoding="utf-8")

    with pytest.raises(ValueError, match="prediction class names do not match metrics"):
        analyze_error_patterns(
            metrics_path=metrics_path,
            predictions_path=predictions_path,
            output_path=tmp_path / "error_analysis.json",
        )
