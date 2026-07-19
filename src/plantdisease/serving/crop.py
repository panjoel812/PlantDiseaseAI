"""Independent lightweight crop inference for the hierarchical demo."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import torch
from PIL import Image
from torch import nn
from torch.nn import functional as F

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
    identity_source: str = "independent_mobilenet_v2_crop_checkpoint"

    @classmethod
    def from_checkpoint(
        cls, checkpoint_path: Path, device: torch.device
    ) -> CropClassifier:
        model, class_names, config = load_checkpoint(checkpoint_path, device)
        task = config.get("task")
        if task not in {"crop_classification", "plant_species_classification"}:
            raise ValueError(
                "crop checkpoint must declare a supported plant identity task"
            )
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
            identity_source=(
                "local_leaf114_checkpoint"
                if task == "plant_species_classification"
                else "independent_mobilenet_v2_crop_checkpoint"
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
        return self.predict_prepared(image)

    def predict_prepared(self, image: Image.Image) -> list[Prediction]:
        """Predict a crop from an image already prepared for this checkpoint."""
        transform = build_eval_transform(self.image_size)
        return predict_topk(
            self.model,
            transform(image),
            self.class_names,
            k=len(self.class_names),
        )

    def embed_prepared(self, image: Image.Image) -> torch.Tensor:
        """Return the frozen backbone embedding used by the prototype gate."""
        features = getattr(self.model, "features", None)
        if features is None:
            raise ValueError("crop checkpoint does not expose a feature backbone")
        transform = build_eval_transform(self.image_size)
        device = next(self.model.parameters(), torch.empty(0)).device
        inputs = transform(image).unsqueeze(0).to(device)
        self.model.eval()
        with torch.inference_mode():
            activations = features(inputs)
            pooled = F.adaptive_avg_pool2d(activations, (1, 1))
        return torch.flatten(pooled, 1)[0].cpu()
