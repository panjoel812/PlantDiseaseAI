import json
from pathlib import Path

import torch

from plantdisease.models.checkpoint import load_checkpoint
from plantdisease.smoke import run_smoke


def test_smoke_pipeline_writes_reproducible_evidence(tmp_path: Path) -> None:
    result = run_smoke(tmp_path, seed=17, image_size=32)

    assert result.status == "smoke_passed"
    assert result.run_id.endswith("seed17")
    expected_files = {
        "config.yaml",
        "split.json",
        "audit.json",
        "checkpoint.pt",
        "metrics.json",
        "predictions.json",
        "training_curve.json",
        "training_curve.png",
        "single_batch_overfit.json",
        "class_distribution.png",
        "image_size_distribution.png",
        "sample_grid.png",
        "example_input.png",
        "run_manifest.json",
    }
    assert expected_files.issubset({path.name for path in tmp_path.iterdir()})

    metrics = json.loads((tmp_path / "metrics.json").read_text(encoding="utf-8"))
    predictions = json.loads((tmp_path / "predictions.json").read_text(encoding="utf-8"))
    manifest = json.loads((tmp_path / "run_manifest.json").read_text(encoding="utf-8"))
    assert 0.0 <= metrics["accuracy"] <= 1.0
    assert len(predictions) == 2
    assert manifest["status"] == "smoke_passed"
    assert manifest["validation_scope"] == "synthetic_data_only"

    overfit = json.loads((tmp_path / "single_batch_overfit.json").read_text(encoding="utf-8"))
    assert overfit["steps"] >= 10
    assert overfit["final_loss"] < overfit["initial_loss"]
    curve = json.loads((tmp_path / "training_curve.json").read_text(encoding="utf-8"))
    assert 0.0 <= curve[0]["test_accuracy"] <= 1.0

    _, class_names, config = load_checkpoint(tmp_path / "checkpoint.pt", torch.device("cpu"))
    assert class_names == ["healthy", "synthetic_blight"]
    assert config["model_name"] == "mobilenet_v2"
