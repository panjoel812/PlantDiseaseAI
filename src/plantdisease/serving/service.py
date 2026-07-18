"""UI-independent inference service for the Week 5 demo."""

from __future__ import annotations

import hashlib
import time
from collections.abc import Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from typing import TYPE_CHECKING, Any

import torch
from PIL import Image
from torch import nn

from plantdisease.data.transforms import build_eval_transform
from plantdisease.explainability.gradcam import GradCAM
from plantdisease.explainability.layers import resolve_target_layer
from plantdisease.explainability.visualization import heatmap_to_image, overlay_heatmap
from plantdisease.inference import Prediction, predict_topk
from plantdisease.models.checkpoint import load_checkpoint
from plantdisease.serving.abiotic import (
    CornAbioticEvidence,
    analyze_corn_abiotic_pattern,
)
from plantdisease.serving.crop import CropClassifier
from plantdisease.serving.disease_focus import (
    DISEASE_INPUT_LESION_FOCUS,
    LesionFocusEvidence,
    extract_lesion_views,
    fuse_lesion_predictions,
    should_focus_lesions,
)
from plantdisease.serving.hierarchy import (
    DEFAULT_CROP_CONFIDENCE_THRESHOLD,
    DEFAULT_CROP_MARGIN_THRESHOLD,
    TaxonomyHierarchy,
    build_taxonomy_hierarchy,
)
from plantdisease.serving.images import (
    DEFAULT_MAX_PIXELS,
    DEFAULT_MAX_UPLOAD_BYTES,
    InputValidationError,
    decode_rgb_image,
)
from plantdisease.serving.knowledge import DiseaseKnowledge, lookup_disease_knowledge
from plantdisease.serving.lesions import LesionAnalysis, analyze_lesions

if TYPE_CHECKING:
    from plantdisease.openworld.index import PrototypeIndex
    from plantdisease.openworld.leaf_pipeline import LeafIsolation, TargetPoint
    from plantdisease.serving.plant_identity import PlantIdentityResult

DEFAULT_CONFIDENCE_WARNING_THRESHOLD = 0.80
DISEASE_INPUT_ORIGINAL = "original_image_v1"
DISEASE_INPUT_ISOLATED_LEAF = "opencv_isolated_leaf_neutral_background_v1"

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
CROP_UNCERTAIN_WARNING = (
    "Crop identity did not pass the confidence gate; disease labels are withheld."
)
DISEASE_UNCERTAIN_WARNING = (
    "Disease evidence did not pass the confidence gate; diagnosis and management are withheld."
)
UNKNOWN_PLANT_WARNING = (
    "The experimental prototype gate did not accept this plant identity; "
    "disease labels are withheld."
)
PROXY_GATE_WARNING = (
    "Unknown-plant thresholds were calibrated with controlled outline proxies, "
    "not field photographs."
)
ISOLATED_DISEASE_INPUT_WARNING = (
    "Disease inference used the OpenCV-isolated leaf on a neutral background. "
    "This suppresses visible background context but does not establish field accuracy."
)
ABIOTIC_STRESS_WARNING = (
    "A conservative Corn morphology gate found evidence compatible with abiotic or "
    "nutrient stress; the infectious disease label is withheld. This does not identify "
    "a specific nutrient deficiency."
)


class InferenceServiceError(RuntimeError):
    """Raised when validated input fails during model inference or Grad-CAM."""


class LeafSelectionRequiredError(RuntimeError):
    """Raised before inference when a target leaf was not isolated safely."""

    def __init__(self, isolation: LeafIsolation) -> None:
        super().__init__(isolation.reason)
        self.isolation = isolation


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
class PlantNoveltyEvidence:
    """Auditable evidence from the optional prototype-based unknown-plant gate."""

    method: str
    accepted: bool
    candidate_plant: str
    classifier_agrees: bool
    similarity: float
    margin: float
    similarity_threshold: float
    margin_threshold: float
    alternatives: tuple[tuple[str, float], ...]
    reason: str
    evidence_boundary: str


@dataclass(frozen=True)
class InferenceResult:
    predictions: list[Prediction]
    hierarchy: TaxonomyHierarchy
    knowledge: DiseaseKnowledge | None
    model_name: str
    checkpoint_path: str
    checkpoint_id: str
    image_size: int
    input_size: tuple[int, int]
    target_layer_name: str | None
    timings: TimingBreakdown
    warnings: list[str]
    disease_input_method: str = DISEASE_INPUT_ORIGINAL
    disease_input_size: tuple[int, int] | None = None
    leaf_isolation: LeafIsolation | None = None
    plant_novelty: PlantNoveltyEvidence | None = None
    lesion_analysis: LesionAnalysis | None = None
    lesion_focus: LesionFocusEvidence | None = None
    abiotic_evidence: CornAbioticEvidence | None = None
    gradcam: GradCAMImages | None = None
    plant_identity: PlantIdentityResult | None = None


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
        crop_confidence_threshold: float = DEFAULT_CROP_CONFIDENCE_THRESHOLD,
        crop_margin_threshold: float = DEFAULT_CROP_MARGIN_THRESHOLD,
        crop_classifier: CropClassifier | None = None,
        prototype_index: PrototypeIndex | None = None,
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
        self.crop_confidence_threshold = crop_confidence_threshold
        self.crop_margin_threshold = crop_margin_threshold
        self.crop_classifier = crop_classifier
        self.prototype_index = prototype_index
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
        crop_checkpoint_path: Path | None = None,
        prototype_index_path: Path | None = None,
    ) -> InferenceService:
        model, class_names, config = load_checkpoint(checkpoint_path, device)
        model_name = str(config["model_name"])
        if target_layer_name is None:
            target = resolve_target_layer(model, model_name)
        else:
            target = _resolve_module_by_name(model, target_layer_name)
        crop_classifier = (
            CropClassifier.from_checkpoint(crop_checkpoint_path, device)
            if crop_checkpoint_path is not None and crop_checkpoint_path.is_file()
            else None
        )
        prototype_index = (
            _load_prototype_index(prototype_index_path)
            if prototype_index_path is not None
            and (prototype_index_path / "index.json").is_file()
            and (prototype_index_path / "prototypes.npz").is_file()
            else None
        )
        return cls(
            model=model,
            class_names=class_names,
            config=config,
            checkpoint_path=checkpoint_path,
            device=device,
            target_layer=target.module,
            target_layer_name=target.name,
            crop_classifier=crop_classifier,
            prototype_index=prototype_index,
        )

    def predict(
        self,
        image_bytes: bytes,
        *,
        top_k: int = 5,
        include_gradcam: bool = True,
        crop_predictions_override: Sequence[Prediction] | None = None,
        crop_prediction_source: str | None = None,
        target_point: TargetPoint | None = None,
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
            leaf_mask = None
            leaf_isolation = None
            prepared_crop_image = image
            prepared_disease_image = image
            disease_input_method = DISEASE_INPUT_ORIGINAL
            if (
                crop_predictions_override is not None
                or (
                    self.crop_classifier is not None
                    and self.crop_classifier.input_preprocessing
                    == "opencv_exg_single_leaf_v1"
                )
            ):
                from plantdisease.openworld.leaf_pipeline import isolate_leaf

                leaf_isolation = isolate_leaf(image, target_point=target_point)
                if not leaf_isolation.accepted or leaf_isolation.species_image is None:
                    raise LeafSelectionRequiredError(leaf_isolation)
                leaf_mask = leaf_isolation.mask
                prepared_crop_image = leaf_isolation.species_image
                prepared_disease_image = leaf_isolation.species_image
                disease_input_method = DISEASE_INPUT_ISOLATED_LEAF
            lesion_analysis = analyze_lesions(image, leaf_mask=leaf_mask)
            tensor = self._transform(prepared_disease_image)
            preprocess_ms = _elapsed_ms(step_started)

            step_started = time.perf_counter()
            all_predictions = predict_topk(
                self.model,
                tensor,
                self.class_names,
                k=len(self.class_names),
            )
            crop_predictions = (
                list(crop_predictions_override)
                if crop_predictions_override is not None
                else (
                    self.crop_classifier.predict_prepared(prepared_crop_image)
                    if self.crop_classifier is not None
                    else None
                )
            )
            resolved_crop_prediction_source = (
                crop_prediction_source
                or (
                    getattr(self.crop_classifier, "identity_source", None)
                    if crop_predictions_override is None
                    else None
                )
            )
            hierarchy = build_taxonomy_hierarchy(
                all_predictions,
                crop_predictions=crop_predictions,
                crop_prediction_source=resolved_crop_prediction_source,
                crop_confidence_threshold=self.crop_confidence_threshold,
                crop_margin_threshold=self.crop_margin_threshold,
            )
            abiotic_evidence = None
            if (
                hierarchy.crop_confident
                and leaf_mask is not None
                and hierarchy.selected_crop.lower().startswith("corn")
            ):
                try:
                    abiotic_evidence = analyze_corn_abiotic_pattern(image, leaf_mask)
                except (ValueError, RuntimeError):
                    abiotic_evidence = None
            abiotic_withhold = bool(
                abiotic_evidence is not None and abiotic_evidence.suspected
            )
            if abiotic_withhold:
                hierarchy = replace(
                    hierarchy,
                    selected_class_name=None,
                    disease_confident=False,
                    disease_decision_reason=(
                        "Visible morphology matched the conservative Corn abiotic-"
                        "stress gate; PlantVillage infectious-disease labels are "
                        "counterfactual evidence only."
                    ),
                )
            lesion_focus = None
            gradcam_image = prepared_disease_image
            if abiotic_withhold:
                focus_allowed, focus_reason, healthy_threshold = (
                    False,
                    "Corn abiotic-stress evidence withheld lesion-focused diagnosis.",
                    None,
                )
            else:
                focus_allowed, focus_reason, healthy_threshold = should_focus_lesions(
                    hierarchy,
                    lesion_analysis,
                )
            if focus_allowed and healthy_threshold is not None and leaf_mask is not None:
                lesion_views = extract_lesion_views(
                    image,
                    leaf_mask,
                    lesion_analysis,
                )
                if len(lesion_views) >= 2:
                    roi_predictions = [
                        predict_topk(
                            self.model,
                            self._transform(view),
                            self.class_names,
                            k=len(self.class_names),
                        )
                        for view in lesion_views
                    ]
                    all_predictions, lesion_focus = fuse_lesion_predictions(
                        all_predictions,
                        roi_predictions,
                        selected_crop=hierarchy.selected_crop,
                        analysis=lesion_analysis,
                        healthy_coverage_threshold=healthy_threshold,
                        reason=focus_reason,
                    )
                    hierarchy = build_taxonomy_hierarchy(
                        all_predictions,
                        crop_predictions=crop_predictions,
                        crop_prediction_source=resolved_crop_prediction_source,
                        crop_confidence_threshold=self.crop_confidence_threshold,
                        crop_margin_threshold=self.crop_margin_threshold,
                    )
                    hierarchy = replace(
                        hierarchy,
                        selected_class_name=None,
                        disease_confident=False,
                        disease_decision_reason=(
                            "OpenCV lesion evidence contradicted the healthy class and "
                            "reranked lesion-focused candidates. These ROI scores are "
                            "not field-calibrated, so diagnosis remains evidence only."
                        ),
                    )
                    gradcam_image = lesion_views[lesion_focus.best_view_index]
                    disease_input_method = DISEASE_INPUT_LESION_FOCUS
            plant_novelty = (
                None
                if crop_predictions_override is not None
                else self._plant_novelty(prepared_crop_image, crop_predictions)
            )
            if plant_novelty is not None and not plant_novelty.accepted:
                hierarchy = replace(
                    hierarchy,
                    selected_class_name=None,
                    conditions=[],
                    crop_confident=False,
                    disease_confident=False,
                    decision_reason=plant_novelty.reason,
                    disease_decision_reason=(
                        "Disease labels are withheld because the unknown-plant gate "
                        "did not accept the plant identity."
                    ),
                )
            predictions = all_predictions[: min(top_k, len(all_predictions))]
            selected_prediction = None
            candidate_prediction = None
            if hierarchy.conditions:
                selected_condition = hierarchy.conditions[0]
                candidate_prediction = Prediction(
                    class_index=selected_condition.class_index,
                    class_name=selected_condition.class_name,
                    probability=selected_condition.joint_probability,
                )
                if hierarchy.disease_confident:
                    selected_prediction = candidate_prediction
            prediction_ms = _elapsed_ms(step_started)

            gradcam = None
            gradcam_prediction = selected_prediction or (
                candidate_prediction if lesion_focus is not None else None
            )
            if include_gradcam and gradcam_prediction is not None:
                step_started = time.perf_counter()
                gradcam_tensor = (
                    tensor
                    if gradcam_image is prepared_disease_image
                    else self._transform(gradcam_image)
                )
                gradcam = self._generate_gradcam(
                    gradcam_image,
                    gradcam_tensor,
                    gradcam_prediction,
                )
                gradcam_ms = _elapsed_ms(step_started)

            warnings = self._warnings(selected_prediction, hierarchy)
            if abiotic_withhold:
                warnings.append(ABIOTIC_STRESS_WARNING)
            if disease_input_method in {
                DISEASE_INPUT_ISOLATED_LEAF,
                DISEASE_INPUT_LESION_FOCUS,
            }:
                warnings.append(ISOLATED_DISEASE_INPUT_WARNING)
            return InferenceResult(
                predictions=predictions,
                hierarchy=hierarchy,
                knowledge=(
                    lookup_disease_knowledge(selected_prediction.class_name)
                    if selected_prediction is not None
                    else None
                ),
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
                disease_input_method=disease_input_method,
                disease_input_size=prepared_disease_image.size,
                leaf_isolation=leaf_isolation,
                plant_novelty=plant_novelty,
                lesion_analysis=lesion_analysis,
                lesion_focus=lesion_focus,
                abiotic_evidence=abiotic_evidence,
                gradcam=gradcam,
            )
        except (InputValidationError, LeafSelectionRequiredError):
            raise
        except Exception as exc:  # noqa: BLE001 - stable service boundary for UI callers.
            raise InferenceServiceError("inference failed") from exc

    def _plant_novelty(
        self,
        image: Image.Image,
        crop_predictions: list[Prediction] | None,
    ) -> PlantNoveltyEvidence | None:
        if (
            self.prototype_index is None
            or self.crop_classifier is None
            or not crop_predictions
        ):
            return None
        embedding = self.crop_classifier.embed_prepared(image).numpy()
        decision = self.prototype_index.predict(embedding)
        head_candidate = crop_predictions[0].class_name
        classifier_agrees = decision.candidate_plant_id == head_candidate
        accepted = decision.accepted and classifier_agrees
        if not classifier_agrees:
            reason = (
                f"Classifier candidate {head_candidate} conflicts with prototype "
                f"candidate {decision.candidate_plant_id}; plant identity is withheld."
            )
        else:
            reason = decision.reason
        return PlantNoveltyEvidence(
            method="frozen_encoder_multi_prototype_cosine_v1",
            accepted=accepted,
            candidate_plant=decision.candidate_plant_id,
            classifier_agrees=classifier_agrees,
            similarity=decision.similarity,
            margin=decision.margin,
            similarity_threshold=self.prototype_index.similarity_threshold,
            margin_threshold=self.prototype_index.margin_threshold,
            alternatives=decision.alternatives,
            reason=reason,
            evidence_boundary=(
                "Experimental abstention gate. Thresholds use controlled outline-proxy "
                "unknowns and are not validated for general field imagery."
            ),
        )

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

    def _warnings(
        self,
        top_prediction: Prediction | None,
        hierarchy: TaxonomyHierarchy,
    ) -> list[str]:
        warnings = [EDUCATIONAL_WARNING, DOMAIN_WARNING]
        if self.prototype_index is not None:
            warnings.append(PROXY_GATE_WARNING)
        if not hierarchy.crop_confident:
            warnings.append(CROP_UNCERTAIN_WARNING)
            if self.prototype_index is not None:
                warnings.append(UNKNOWN_PLANT_WARNING)
        elif not hierarchy.disease_confident:
            warnings.append(DISEASE_UNCERTAIN_WARNING)
        elif (
            top_prediction is not None
            and top_prediction.probability < self.confidence_warning_threshold
        ):
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


def _load_prototype_index(path: Path) -> PrototypeIndex:
    from plantdisease.openworld.index import PrototypeIndex

    return PrototypeIndex.load(path)
