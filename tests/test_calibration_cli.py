import json
from pathlib import Path

import pytest

from plantdisease.cli import calibration_main
from plantdisease.explainability.calibration import CalibrationResult


def test_calibration_main_prints_generated_artifact_paths(
    tmp_path: Path, monkeypatch, capsys: pytest.CaptureFixture[str]
) -> None:
    predictions_path = tmp_path / "predictions.json"
    output_path = tmp_path / "calibration.json"
    report_path = tmp_path / "calibration.md"
    figure_path = tmp_path / "reliability.png"

    def fake_analyze_calibration(**kwargs) -> CalibrationResult:
        assert kwargs == {
            "predictions_path": predictions_path,
            "output_path": output_path,
            "report_path": report_path,
            "figure_path": figure_path,
            "num_bins": 12,
        }
        return CalibrationResult(
            calibration_path=output_path,
            report_path=report_path,
            figure_path=figure_path,
            sample_count=10709,
            top_label_ece=0.02,
            top_label_mce=0.1,
        )

    monkeypatch.setattr("plantdisease.cli.analyze_calibration", fake_analyze_calibration)

    calibration_main(
        [
            "--predictions",
            str(predictions_path),
            "--output",
            str(output_path),
            "--report",
            str(report_path),
            "--figure",
            str(figure_path),
            "--bins",
            "12",
        ]
    )

    summary = json.loads(capsys.readouterr().out)
    assert summary == {
        "status": "completed",
        "sample_count": 10709,
        "top_label_ece": 0.02,
        "top_label_mce": 0.1,
        "calibration": str(output_path),
        "report": str(report_path),
        "figure": str(figure_path),
    }
