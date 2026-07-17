import json
from pathlib import Path

import pytest

from plantdisease.cli import attention_review_main
from plantdisease.explainability.attention_review import AttentionReviewResult


def test_attention_review_main_prints_generated_artifact_paths(
    tmp_path: Path, monkeypatch, capsys: pytest.CaptureFixture[str]
) -> None:
    atlas_path = tmp_path / "atlas_manifest.json"
    error_analysis_path = tmp_path / "error_analysis.json"
    output_path = tmp_path / "attention_review.json"
    report_path = tmp_path / "attention_review.md"

    def fake_create_template(**kwargs) -> AttentionReviewResult:
        assert kwargs == {
            "atlas_manifest_path": atlas_path,
            "output_path": output_path,
            "error_analysis_path": error_analysis_path,
            "report_path": report_path,
        }
        return AttentionReviewResult(
            review_path=output_path,
            report_path=report_path,
            sample_count=24,
            needs_review_count=12,
            high_confidence_error_count=2,
        )

    monkeypatch.setattr(
        "plantdisease.cli.create_attention_review_template",
        fake_create_template,
    )

    attention_review_main(
        [
            "--atlas-manifest",
            str(atlas_path),
            "--error-analysis",
            str(error_analysis_path),
            "--output",
            str(output_path),
            "--report",
            str(report_path),
        ]
    )

    summary = json.loads(capsys.readouterr().out)
    assert summary == {
        "status": "completed",
        "sample_count": 24,
        "needs_review_count": 12,
        "high_confidence_error_count": 2,
        "attention_review": str(output_path),
        "report": str(report_path),
    }
