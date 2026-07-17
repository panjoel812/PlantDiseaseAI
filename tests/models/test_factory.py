from pathlib import Path

import pytest
import torch

from plantdisease.models.checkpoint import load_checkpoint, save_checkpoint
from plantdisease.models.factory import create_model


@pytest.mark.parametrize(
    "model_name",
    [
        "mobilenet_v2",
        "resnet18",
        "resnet50",
        "efficientnet_b0",
        "efficientnet_v2_s",
    ],
)
def test_model_factory_outputs_requested_number_of_classes(model_name: str) -> None:
    model = create_model(model_name, num_classes=3, pretrained=False).eval()

    with torch.inference_mode():
        output = model(torch.randn(1, 3, 64, 64))

    assert output.shape == (1, 3)


def test_model_factory_rejects_unknown_model() -> None:
    with pytest.raises(ValueError, match="unsupported model"):
        create_model("unknown", num_classes=2)


def test_checkpoint_round_trip_preserves_logits(tmp_path: Path) -> None:
    torch.manual_seed(3)
    model = create_model("mobilenet_v2", num_classes=2, pretrained=False).eval()
    sample = torch.randn(1, 3, 64, 64)
    with torch.inference_mode():
        expected = model(sample)
    path = tmp_path / "model.pt"

    save_checkpoint(
        path,
        model,
        class_names=["healthy", "disease"],
        config={"model_name": "mobilenet_v2", "num_classes": 2, "image_size": 64},
    )
    loaded, class_names, config = load_checkpoint(path, torch.device("cpu"))
    loaded.eval()
    with torch.inference_mode():
        actual = loaded(sample)

    assert class_names == ["healthy", "disease"]
    assert config["image_size"] == 64
    assert torch.allclose(expected, actual)
