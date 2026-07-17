import json
from pathlib import Path

import torch
from PIL import Image
from torch import nn

from plantdisease.explainability.atlas import generate_gradcam_atlas
from plantdisease.explainability.layers import TargetLayer


class FakeSplit:
    column_names = ["image", "label"]

    def __len__(self) -> int:
        return 2

    def __getitem__(self, index: int) -> dict[str, object]:
        color = (40, 120, 60) if index == 0 else (140, 80, 40)
        return {"image": Image.new("RGB", (32, 32), color), "label": index}


class FakeModel(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.conv = nn.Conv2d(3, 2, kernel_size=1)


class FakeGradCAM:
    target_classes: list[int] = []

    def __init__(self, _model: nn.Module, _target_layer: nn.Module) -> None:
        self.closed = False

    def __enter__(self) -> "FakeGradCAM":
        return self

    def __exit__(self, *_args: object) -> None:
        self.closed = True

    def generate(
        self,
        inputs: torch.Tensor,
        target_classes: torch.Tensor | None = None,
    ) -> torch.Tensor:
        assert target_classes is not None
        self.target_classes.append(int(target_classes[0]))
        height, width = inputs.shape[-2:]
        return torch.linspace(0, 1, height * width).reshape(1, height, width)


def _prediction(test_index: int, confidence: float, correct: bool) -> dict[str, object]:
    return {
        "test_index": test_index,
        "sample_id": f"hf-test-{test_index}",
        "true_class_index": test_index,
        "true_class_name": "healthy" if test_index == 0 else "disease",
        "predicted_class_index": 0 if correct else 1,
        "predicted_class_name": "healthy" if correct else "disease",
        "confidence": confidence,
        "correct": correct,
        "top_k": [],
    }


def test_generate_gradcam_atlas_writes_panels_manifest_and_report(
    tmp_path: Path, monkeypatch
) -> None:
    FakeGradCAM.target_classes = []
    checkpoint_path = tmp_path / "checkpoint.pt"
    split_path = tmp_path / "split.json"
    frozen_path = tmp_path / "frozen_samples.json"
    report_path = tmp_path / "report.md"
    split_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "class_names": ["healthy", "disease"],
                "splits": {"test": [0, 1]},
            }
        ),
        encoding="utf-8",
    )
    frozen_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "inputs": {"split_manifest_path": str(split_path)},
                "selection": {"groups": ["correct_high_confidence", "error_high_confidence"]},
                "groups": {
                    "correct_high_confidence": [_prediction(0, 0.95, True)],
                    "error_high_confidence": [_prediction(1, 0.90, False)],
                },
            }
        ),
        encoding="utf-8",
    )

    def fake_load_checkpoint(path: Path, device: torch.device):
        assert path == checkpoint_path
        assert device.type == "cpu"
        return FakeModel(), ["healthy", "disease"], {"model_name": "resnet50", "image_size": 32}

    def fake_load_splits(cache_dir: Path | None):
        assert cache_dir == tmp_path / "cache"
        return {"test": FakeSplit()}, ["healthy", "disease"]

    def fake_resolve_target_layer(model: nn.Module, model_name: str) -> TargetLayer:
        assert model_name == "resnet50"
        return TargetLayer("layer4.2", model.conv)

    monkeypatch.setattr("plantdisease.explainability.atlas.load_checkpoint", fake_load_checkpoint)
    monkeypatch.setattr(
        "plantdisease.explainability.atlas.hf_data.load_plantvillage_dataset_splits",
        fake_load_splits,
    )
    monkeypatch.setattr(
        "plantdisease.explainability.atlas.resolve_target_layer",
        fake_resolve_target_layer,
    )
    monkeypatch.setattr("plantdisease.explainability.atlas.GradCAM", FakeGradCAM)
    messages: list[str] = []

    result = generate_gradcam_atlas(
        checkpoint_path=checkpoint_path,
        frozen_samples_path=frozen_path,
        output_dir=tmp_path / "atlas",
        cache_dir=tmp_path / "cache",
        report_path=report_path,
        device_name="cpu",
        target_layer="layer4.2",
        logger=messages.append,
    )

    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert result.sample_count == 2
    assert result.target_layer == "layer4.2"
    assert result.target_mode == "predicted"
    assert FakeGradCAM.target_classes == [0, 1]
    assert len(manifest["samples"]) == 2
    assert Path(manifest["samples"][0]["panel_path"]).exists()
    assert "Target mode" in report_path.read_text(encoding="utf-8")
    assert any("gradcam 2/2" in message for message in messages)
