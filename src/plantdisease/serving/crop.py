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
from plantdisease.serving.images import InputValidationError

LEAF_ISOLATION_METHOD = "opencv_exg_single_leaf_v1"


@dataclass(frozen=True)
class CropClassifier:
    """Loaded crop-only checkpoint with canonical preprocessing."""

    model: nn.Module
    class_names: list[str]
    image_size: int
    checkpoint_path: Path
    input_preprocessing: str | None = None

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
            input_preprocessing=(
                str(config["input_preprocessing"])
                if config.get("input_preprocessing")
                else None
            ),
        )

    def predict(self, image: Image.Image) -> list[Prediction]:
        if self.input_preprocessing == LEAF_ISOLATION_METHOD:
            from plantdisease.openworld.leaf_pipeline import isolate_leaf

            isolation = isolate_leaf(image)
            if not isolation.accepted or isolation.species_image is None:
                raise InputValidationError(
                    f"leaf isolation rejected input: {isolation.reason}"
                )
            image = isolation.species_image
        transform = build_eval_transform(self.image_size)
        return predict_topk(
            self.model,
            transform(image),
            self.class_names,
            k=len(self.class_names),
        )
