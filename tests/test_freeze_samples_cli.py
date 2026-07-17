import json
from pathlib import Path

import pytest

from plantdisease.cli import freeze_samples_main
from plantdisease.explainability.workflow import FrozenSampleResult


def test_freeze_samples_main_prints_generated_artifact_paths(
    tmp_path: Path, monkeypatch, capsys: pytest.CaptureFixture[str]
) -> None:
    checkpoint_path = tmp_path / "checkpoint.pt"
    split_path = tmp_path / "split.json"
    output_dir = tmp_path / "week4"
    cache_dir = tmp_path / "cache"

    def fake_freeze_samples(**kwargs) -> FrozenSampleResult:
        logger = kwargs.pop("logger")
        assert callable(logger)
        assert kwargs == {
            "checkpoint_path": checkpoint_path,
            "split_manifest_path": split_path,
            "output_dir": output_dir,
            "cache_dir": cache_dir,
            "samples_per_group": 4,
            "top_k": 3,
            "batch_size": 2,
            "num_workers": 0,
            "device_name": "cpu",
            "target_layer": "layer4.2",
            "progress_log_every": 1,
        }
        return FrozenSampleResult(
            prediction_path=output_dir / "predictions.json",
            frozen_samples_path=output_dir / "frozen_samples.json",
            prediction_count=2,
            selected_counts={"error_high_confidence": 1},
            target_layer="layer4.2",
        )

    monkeypatch.setattr(
        "plantdisease.cli.freeze_explainability_samples",
        fake_freeze_samples,
    )

    freeze_samples_main(
        [
            "--checkpoint",
            str(checkpoint_path),
            "--split-manifest",
            str(split_path),
            "--output-dir",
            str(output_dir),
            "--cache-dir",
            str(cache_dir),
            "--samples-per-group",
            "4",
            "--top-k",
            "3",
            "--batch-size",
            "2",
            "--device",
            "cpu",
            "--target-layer",
            "layer4.2",
            "--progress-every",
            "1",
        ]
    )

    summary = json.loads(capsys.readouterr().out)
    assert summary == {
        "status": "completed",
        "prediction_count": 2,
        "target_layer": "layer4.2",
        "predictions": str(output_dir / "predictions.json"),
        "frozen_samples": str(output_dir / "frozen_samples.json"),
    }
