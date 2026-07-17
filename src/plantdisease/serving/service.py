"""UI-independent inference service for the Week 5 demo."""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import torch
from PIL import Image
from torch import nn

from plantdisease.data.transforms import build_eval_transform
from plantdisease.explainability.gradcam import GradCAM
from plantdisease.explainability.layers import resolve_target_layer
from plantdisease.explainability.visualization import heatmap_to_image, overlay_heatmap
from plantdisease.inference import Prediction, predict_topk
from plantdisease.models.checkpoint import load_checkpoint
from plantdisease.serving.images import (
    DEFAULT_MAX_PIXELS,
    DEFAULT_MAX_UPLOAD_BYTES,
    InputValidationError,
    decode_rgb_image,
)
from plantdisease.serving.knowledge import DiseaseKnowledge, lookup_disease_knowledge

DEFAULT_CONFIDENCE_WARNING_THRESHOLD = 0.80

EDUCATIONAL_WARNING = (
    "Educational demo only; this result is not a professional agricultural diagnosis."
)
DOMAIN_WARNING = (
    "PlantVillage closed-set model: results may not generalize to field images, unknown "
    "diseases, non-leaf images, or local growing conditions."
)
LOW_CONFIDENCE_WARNING = (
    "Low confidence prediction; do not treat this as a definitive diagnosis."
)


class InferenceServiceError(RuntimeError):
    """Raised when validated input fails during model inference or Grad-CAM."""


@dataclass(frozen=True)
class TimingBreakdown:
    preprocess_ms: float
    prediction_ms: float
    gradcam_ms: float
    total_ms: float


@dataclass(frozen=True)
class GradCAMImages:
    target_class_index: int
    target_class_name: str
    heatmap: Image.Image
    overlay: Image.Image


@dataclass(frozen=True)
class InferenceResult:
    predictions: list[Prediction]
    knowledge: DiseaseKnowledge
    model_name: str
    checkpoint_path: str
    checkpoint_id: str
    image_size: int
    input_size: tuple[int, int]
    target_layer_name: str | None
    timings: TimingBreakdown
    warnings: list[str]
    gradcam: GradCAMImages | None = None


class InferenceService:
    """Load once, then run canonical preprocessing, Top-5, and optional Grad-CAM."""

    def __init__(
        self,
        *,
        model: nn.Module,
        class_names: list[str],
        config: dict[str, Any],
        checkpoint_path: Path,
        device: torch.device,
        target_layer: nn.Module | None = None,
        target_layer_name: str | None = None,
        checkpoint_id: str | None = None,
        max_upload_bytes: int = DEFAULT_MAX_UPLOAD_BYTES,
        max_pixels: int = DEFAULT_MAX_PIXELS,
        confidence_warning_threshold: float = DEFAULT_CONFIDENCE_WARNING_THRESHOLD,
    ) -> None:
        if not class_names:
            raise ValueError("class_names must be non-empty")
        self.model = model.to(device)
        self.class_names = list(class_names)
        self.config = dict(config)
        self.checkpoint_path = Path(checkpoint_path)
        self.device = device
        self.target_layer = target_layer
        self.target_layer_name = target_layer_name
        self.checkpoint_id = checkpoint_id or _checkpoint_id(self.checkpoint_path)
        self.max_upload_bytes = max_upload_bytes
        self.max_pixels = max_pixels
        self.confidence_warning_threshold = confidence_warning_threshold
        self.model_name = str(self.config.get("model_name", "unknown"))
        self.image_size = int(self.config.get("image_size", 224))
        self._transform = build_eval_transform(self.image_size)

    @classmethod
    def from_checkpoint(
        cls,
        checkpoint_path: Path,
        *,
        device: torch.device,
        target_layer_name: str | None = None,
    ) -> InferenceService:
        model, class_names, config = load_checkpoint(checkpoint_path, device)
        model_name = str(config["model_name"])
        if target_layer_name is None:
            target = resolve_target_layer(model, model_name)
        else:
            target = _resolve_module_by_name(model, target_layer_name)
        return cls(
            model=model,
            class_names=class_names,
            config=config,
            checkpoint_path=checkpoint_path,
            device=device,
            target_layer=target.module,
            target_layer_name=target.name,
        )

    def predict(
        self,
        image_bytes: bytes,
        *,
        top_k: int = 5,
        include_gradcam: bool = True,
    ) -> InferenceResult:
        started = time.perf_counter()
        preprocess_ms = 0.0
        prediction_ms = 0.0
        gradcam_ms = 0.0
        try:
            image = decode_rgb_image(
                image_bytes,
                max_upload_bytes=self.max_upload_bytes,
                max_pixels=self.max_pixels,
            )

            step_started = time.perf_counter()
            tensor = self._transform(image)
            preprocess_ms = _elapsed_ms(step_started)

            step_started = time.perf_counter()
            predictions = predict_topk(self.model, tensor, self.class_names, k=top_k)
            prediction_ms = _elapsed_ms(step_started)

            gradcam = None
            if include_gradcam:
                step_started = time.perf_counter()
                gradcam = self._generate_gradcam(image, tensor, predictions[0])
                gradcam_ms = _elapsed_ms(step_started)

            warnings = self._warnings(predictions[0])
            return InferenceResult(
                predictions=predictions,
                knowledge=lookup_disease_knowledge(predictions[0].class_name),
                model_name=self.model_name,
                checkpoint_path=str(self.checkpoint_path),
                checkpoint_id=self.checkpoint_id,
                image_size=self.image_size,
                input_size=image.size,
                target_layer_name=self.target_layer_name,
                timings=TimingBreakdown(
                    preprocess_ms=preprocess_ms,
                    prediction_ms=prediction_ms,
                    gradcam_ms=gradcam_ms,
                    total_ms=_elapsed_ms(started),
                ),
                warnings=warnings,
                gradcam=gradcam,
            )
        except InputValidationError:
            raise
        except Exception as exc:  # noqa: BLE001 - stable service boundary for UI callers.
            raise InferenceServiceError("inference failed") from exc

    def _generate_gradcam(
        self,
        image: Image.Image,
        tensor: torch.Tensor,
        prediction: Prediction,
    ) -> GradCAMImages:
        if self.target_layer is None:
            raise InferenceServiceError("Grad-CAM target layer is not configured")
        inputs = tensor.unsqueeze(0).to(self.device)
        targets = torch.tensor([prediction.class_index], device=self.device)
        with GradCAM(self.model, self.target_layer) as gradcam:
            heatmap = gradcam.generate(inputs, targets)[0]
        return GradCAMImages(
            target_class_index=prediction.class_index,
            target_class_name=prediction.class_name,
            heatmap=heatmap_to_image(heatmap),
            overlay=overlay_heatmap(image, heatmap),
        )

    def _warnings(self, top_prediction: Prediction) -> list[str]:
        warnings = [EDUCATIONAL_WARNING, DOMAIN_WARNING]
        if top_prediction.probability < self.confidence_warning_threshold:
            warnings.append(LOW_CONFIDENCE_WARNING)
        return warnings


@dataclass(frozen=True)
class _ResolvedModule:
    name: str
    module: nn.Module


def _resolve_module_by_name(model: nn.Module, name: str) -> _ResolvedModule:
    modules = dict(model.named_modules())
    if name not in modules:
        raise ValueError(f"unknown target layer: {name}")
    return _ResolvedModule(name=name, module=modules[name])


def _checkpoint_id(path: Path) -> str:
    try:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return path.name
    return digest[:12]


def _elapsed_ms(started: float) -> float:
    return (time.perf_counter() - started) * 1000.0
