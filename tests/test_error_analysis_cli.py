import json
from pathlib import Path

import pytest

from plantdisease.cli import error_analysis_main
from plantdisease.explainability.error_analysis import ErrorAnalysisResult


def test_error_analysis_main_prints_generated_artifact_paths(
    tmp_path: Path, monkeypatch, capsys: pytest.CaptureFixture[str]
) -> None:
    metrics_path = tmp_path / "metrics.json"
    predictions_path = tmp_path / "predictions.json"
    output_path = tmp_path / "error_analysis.json"
    report_path = tmp_path / "error_analysis.md"

    def fake_analyze_errors(**kwargs) -> ErrorAnalysisResult:
        assert kwargs == {
            "metrics_path": metrics_path,
            "predictions_path": predictions_path,
            "output_path": output_path,
            "report_path": report_path,
            "low_f1_count": 4,
            "confusion_pair_count": 5,
            "high_confidence_threshold": 0.8,
            "high_confidence_error_count": 6,
        }
        return ErrorAnalysisResult(
            error_analysis_path=output_path,
            report_path=report_path,
            class_count=3,
            sample_count=12,
            error_count=3,
            high_confidence_error_count=2,
        )

    monkeypatch.setattr("plantdisease.cli.analyze_error_patterns", fake_analyze_errors)

    error_analysis_main(
        [
            "--metrics",
            str(metrics_path),
            "--predictions",
            str(predictions_path),
            "--output",
            str(output_path),
            "--report",
            str(report_path),
            "--low-f1-count",
            "4",
            "--confusion-pair-count",
            "5",
            "--high-confidence-threshold",
            "0.8",
            "--high-confidence-error-count",
            "6",
        ]
    )

    summary = json.loads(capsys.readouterr().out)
    assert summary == {
        "status": "completed",
        "class_count": 3,
        "sample_count": 12,
        "error_count": 3,
        "high_confidence_error_count": 2,
        "error_analysis": str(output_path),
        "report": str(report_path),
    }
