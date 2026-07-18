"""Independent lightweight crop inference for the hierarchical demo."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import torch
from PIL import Image
from torch import nn

from plantdisease.data.transforms import build_eval_transform
from plantdisease.inference import Prediction, predict_topk
from plantdisease.models.checkpoint import load_checkpoint


@dataclass(frozen=True)
class CropClassifier:
    """Loaded crop-only checkpoint with canonical preprocessing."""

    model: nn.Module
    class_names: list[str]
    image_size: int
    checkpoint_path: Path

    @classmethod
    def from_checkpoint(
        cls, checkpoint_path: Path, device: torch.device
    ) -> CropClassifier:
        model, class_names, config = load_checkpoint(checkpoint_path, device)
        if config.get("task") != "crop_classification":
            raise ValueError("crop checkpoint must declare task=crop_classification")
        return cls(
            model=model,
            class_names=class_names,
            image_size=int(config.get("image_size", 224)),
            checkpoint_path=Path(checkpoint_path),
        )

    def predict(self, image: Image.Image) -> list[Prediction]:
        transform = build_eval_transform(self.image_size)
        return predict_topk(
            self.model,
            transform(image),
            self.class_names,
            k=len(self.class_names),
        )
