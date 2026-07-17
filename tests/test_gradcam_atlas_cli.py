import json
from pathlib import Path

import pytest

from plantdisease.cli import gradcam_atlas_main
from plantdisease.explainability.atlas import GradCAMAtlasResult


def test_gradcam_atlas_main_prints_generated_artifact_paths(
    tmp_path: Path, monkeypatch, capsys: pytest.CaptureFixture[str]
) -> None:
    checkpoint_path = tmp_path / "checkpoint.pt"
    frozen_path = tmp_path / "frozen_samples.json"
    output_dir = tmp_path / "atlas"
    report_path = tmp_path / "report.md"
    cache_dir = tmp_path / "cache"

    def fake_generate_atlas(**kwargs) -> GradCAMAtlasResult:
        logger = kwargs.pop("logger")
        assert callable(logger)
        assert kwargs == {
            "checkpoint_path": checkpoint_path,
            "frozen_samples_path": frozen_path,
            "output_dir": output_dir,
            "cache_dir": cache_dir,
            "split_manifest_path": None,
            "report_path": report_path,
            "device_name": "cpu",
            "target_layer": "layer4.2",
            "target_mode": "predicted",
            "alpha": 0.4,
            "colormap": "turbo",
        }
        return GradCAMAtlasResult(
            output_dir=output_dir,
            manifest_path=output_dir / "gradcam_atlas_manifest.json",
            report_path=report_path,
            sample_count=24,
            target_layer="layer4.2",
            target_mode="predicted",
        )

    monkeypatch.setattr("plantdisease.cli.generate_gradcam_atlas", fake_generate_atlas)

    gradcam_atlas_main(
        [
            "--checkpoint",
            str(checkpoint_path),
            "--frozen-samples",
            str(frozen_path),
            "--output-dir",
            str(output_dir),
            "--cache-dir",
            str(cache_dir),
            "--report",
            str(report_path),
            "--device",
            "cpu",
            "--target-layer",
            "layer4.2",
            "--target-mode",
            "predicted",
            "--alpha",
            "0.4",
            "--colormap",
            "turbo",
        ]
    )

    summary = json.loads(capsys.readouterr().out)
    assert summary == {
        "status": "completed",
        "sample_count": 24,
        "target_layer": "layer4.2",
        "target_mode": "predicted",
        "manifest": str(output_dir / "gradcam_atlas_manifest.json"),
        "report": str(report_path),
    }
