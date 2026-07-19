from __future__ import annotations

from pathlib import Path

import pytest
import torch
from PIL import Image, ImageDraw
from torch import nn

from plantdisease.models.checkpoint import save_checkpoint
from plantdisease.models.factory import create_model
from plantdisease.serving.crop import LEAF_ISOLATION_METHOD, CropClassifier


class FixedCropModel(nn.Module):
    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        logits = torch.tensor([0.2, 1.4], dtype=inputs.dtype, device=inputs.device)
        return logits.repeat(len(inputs), 1)


def _classifier() -> CropClassifier:
    return CropClassifier(
        model=FixedCropModel(),
        class_names=["Grape", "Tomato"],
        image_size=32,
        checkpoint_path=Path("synthetic.pt"),
        input_preprocessing=LEAF_ISOLATION_METHOD,
    )


def test_leaf_checkpoint_applies_isolation_before_prediction() -> None:
    image = Image.new("RGB", (120, 96), (25, 26, 28))
    ImageDraw.Draw(image).ellipse((14, 8, 106, 88), fill=(55, 150, 63))

    predictions = _classifier().predict(image)

    assert predictions[0].class_name == "Tomato"


def test_leaf_checkpoint_rejects_non_leaf_input() -> None:
    image = Image.new("RGB", (120, 96), (25, 26, 28))

    with pytest.raises(ValueError, match="leaf isolation rejected"):
        _classifier().predict(image)


def test_local_100_plus_catalog_checkpoint_restores_identity_source(
    tmp_path: Path,
) -> None:
    checkpoint = tmp_path / "leaf114.pt"
    model = create_model("mobilenet_v2", 2, pretrained=False)
    save_checkpoint(
        checkpoint,
        model,
        ["Acer campestre", "Grape"],
        {
            "model_name": "mobilenet_v2",
            "num_classes": 2,
            "image_size": 32,
            "task": "plant_species_classification",
            "input_preprocessing": LEAF_ISOLATION_METHOD,
        },
    )

    classifier = CropClassifier.from_checkpoint(checkpoint, torch.device("cpu"))

    assert classifier.identity_source == "local_leaf114_checkpoint"
    assert classifier.class_names == ["Acer campestre", "Grape"]
