import json
from pathlib import Path

import pytest

from plantdisease.cli import benchmark_main
from plantdisease.models.checkpoint import save_checkpoint
from plantdisease.models.factory import create_model


def test_benchmark_main_writes_report_and_prints_summary(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    checkpoint_path = tmp_path / "checkpoint.pt"
    output_path = tmp_path / "benchmark.json"
    model = create_model("mobilenet_v2", num_classes=2, pretrained=False)
    save_checkpoint(
        checkpoint_path,
        model,
        class_names=["healthy", "disease"],
        config={"model_name": "mobilenet_v2", "num_classes": 2, "image_size": 64},
    )

    benchmark_main(
        [
            "--checkpoint",
            str(checkpoint_path),
            "--output",
            str(output_path),
            "--device",
            "cpu",
            "--warmup",
            "0",
            "--iterations",
            "1",
            "--throughput-batch-size",
            "1",
        ]
    )

    summary = json.loads(capsys.readouterr().out)
    assert summary["status"] == "completed"
    assert summary["model_name"] == "mobilenet_v2"
    assert summary["output"] == str(output_path)
    assert output_path.exists()
