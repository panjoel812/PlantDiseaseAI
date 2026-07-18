"""Host-conditioned lesion focus for visibly abnormal leaves.

The disease checkpoint was trained as a whole-image classifier. This module does
not pretend that OpenCV morphology is a disease label. It only vetoes a conflicting
``healthy`` candidate when visible lesion coverage exceeds a host-specific threshold
calibrated from healthy PlantVillage training leaves, then ranks that host's disease
classes using the two largest neutral-background lesion views.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
from PIL import Image

from plantdisease.inference import Prediction
from plantdisease.serving.hierarchy import TaxonomyHierarchy
from plantdisease.serving.knowledge import lookup_disease_knowledge
from plantdisease.serving.lesions import LesionAnalysis

LESION_FOCUS_METHOD = "opencv_healthy_veto_roi_ensemble_v1"
DISEASE_INPUT_LESION_FOCUS = "opencv_isolated_leaf_plus_lesion_rois_v2"
MAX_LESION_VIEWS = 2
MIN_LESION_COUNT = 2
MIN_LARGEST_LESION_PERCENT = 0.25

# 99th percentile of OpenCV lesion coverage on 323 accepted healthy Grape images
# from the PlantVillage official training split, seed 42. It produced no false veto
# among 100 accepted healthy Grape official-test images. Other hosts remain disabled
# because their held-out false-veto audits were not consistently below 1%.
HEALTHY_LESION_COVERAGE_THRESHOLDS = {
    "Grape": 1.2959,
}


@dataclass(frozen=True)
class LesionFocusEvidence:
    """Auditable evidence for one applied healthy-veto and ROI reranking."""

    method: str
    applied: bool
    selected_crop: str
    reason: str
    lesion_coverage_percent: float
    healthy_coverage_threshold: float
    lesion_count: int
    roi_count: int
    full_healthy_probability: float
    focused_predictions: tuple[Prediction, ...]
    best_view_index: int
    evidence_boundary: str


def should_focus_lesions(
    hierarchy: TaxonomyHierarchy,
    analysis: LesionAnalysis,
) -> tuple[bool, str, float | None]:
    """Decide whether healthy evidence conflicts with calibrated lesion evidence."""

    threshold = HEALTHY_LESION_COVERAGE_THRESHOLDS.get(hierarchy.selected_crop)
    if not hierarchy.crop_confident:
        return False, "Plant identity is not accepted.", threshold
    if not hierarchy.conditions:
        return False, "The selected plant has no local disease taxonomy.", threshold
    top = hierarchy.conditions[0]
    if top.condition.lower() != "healthy":
        return False, "The full-leaf top condition is not healthy.", threshold
    if threshold is None:
        return False, "No healthy-leaf calibration is available for this plant.", None
    if analysis.lesion_coverage_percent <= threshold:
        return (
            False,
            "Visible lesion coverage does not exceed the healthy calibration threshold.",
            threshold,
        )
    if analysis.lesion_count < MIN_LESION_COUNT:
        return False, "Too few stable lesion components support a healthy veto.", threshold
    if analysis.largest_lesion_area_percent < MIN_LARGEST_LESION_PERCENT:
        return False, "The largest lesion component is too small for a healthy veto.", threshold
    return (
        True,
        (
            f"Visible lesion coverage {analysis.lesion_coverage_percent:.2f}% exceeds "
            f"the {hierarchy.selected_crop} healthy threshold {threshold:.2f}%."
        ),
        threshold,
    )


def extract_lesion_views(
    image: Image.Image,
    leaf_mask: np.ndarray,
    analysis: LesionAnalysis,
    *,
    max_views: int = MAX_LESION_VIEWS,
    neutral_rgb: tuple[int, int, int] = (124, 124, 124),
) -> tuple[Image.Image, ...]:
    """Crop the largest lesion regions after neutralizing all non-leaf pixels."""

    if max_views <= 0:
        raise ValueError("max_views must be positive")
    rgb = np.asarray(image.convert("RGB"), dtype=np.uint8)
    mask = np.asarray(leaf_mask, dtype=np.uint8)
    if mask.shape != rgb.shape[:2]:
        raise ValueError("leaf_mask shape must match image")
    neutral = np.empty_like(rgb)
    neutral[:, :] = neutral_rgb
    neutral[mask > 0] = rgb[mask > 0]
    source = Image.fromarray(neutral, mode="RGB")
    views: list[Image.Image] = []
    for region in analysis.regions[:max_views]:
        padding = max(6, round(max(region.width, region.height) * 0.65))
        left = max(0, region.x - padding)
        top = max(0, region.y - padding)
        right = min(source.width, region.x + region.width + padding)
        bottom = min(source.height, region.y + region.height + padding)
        if right - left >= 16 and bottom - top >= 16:
            views.append(source.crop((left, top, right, bottom)))
    return tuple(views)


def fuse_lesion_predictions(
    full_predictions: Sequence[Prediction],
    roi_predictions: Sequence[Sequence[Prediction]],
    *,
    selected_crop: str,
    analysis: LesionAnalysis,
    healthy_coverage_threshold: float,
    reason: str,
) -> tuple[list[Prediction], LesionFocusEvidence]:
    """Replace a contradictory healthy rank with host-conditioned ROI evidence."""

    if len(roi_predictions) < 2:
        raise ValueError("at least two lesion views are required")
    full_by_index = {item.class_index: item for item in full_predictions}
    host_indices = [
        item.class_index
        for item in full_predictions
        if lookup_disease_knowledge(item.class_name).plant == selected_crop
    ]
    healthy_indices = [
        index
        for index in host_indices
        if lookup_disease_knowledge(full_by_index[index].class_name).is_healthy
    ]
    if not host_indices or len(healthy_indices) != 1:
        raise ValueError("selected crop must expose exactly one healthy class")
    healthy_index = healthy_indices[0]
    host_mass = sum(full_by_index[index].probability for index in host_indices)
    if host_mass <= 0.0:
        raise ValueError("selected crop probability mass must be positive")

    normalized_views: list[dict[int, float]] = []
    for view in roi_predictions:
        by_index = {item.class_index: item.probability for item in view}
        total = sum(by_index.get(index, 0.0) for index in host_indices)
        if total <= 0.0:
            raise ValueError("lesion view has no selected-crop probability mass")
        normalized_views.append(
            {index: by_index.get(index, 0.0) / total for index in host_indices}
        )

    averaged = {
        index: sum(view[index] for view in normalized_views) / len(normalized_views)
        for index in host_indices
    }
    full_healthy_probability = full_by_index[healthy_index].probability / host_mass
    averaged[healthy_index] = 0.0
    disease_mass = sum(averaged.values())
    if disease_mass <= 0.0:
        raise ValueError("lesion views contain no disease probability mass")
    focused = {index: value / disease_mass for index, value in averaged.items()}

    fused: list[Prediction] = []
    for item in full_predictions:
        probability = (
            host_mass * focused[item.class_index]
            if item.class_index in focused
            else item.probability
        )
        fused.append(Prediction(item.class_index, item.class_name, probability))
    fused.sort(key=lambda item: (-item.probability, item.class_name))

    ranked_focus = tuple(
        sorted(
            (
                Prediction(index, full_by_index[index].class_name, probability)
                for index, probability in focused.items()
            ),
            key=lambda item: (-item.probability, item.class_name),
        )
    )
    target_index = ranked_focus[0].class_index
    best_view_index = max(
        range(len(normalized_views)),
        key=lambda index: normalized_views[index][target_index],
    )
    evidence = LesionFocusEvidence(
        method=LESION_FOCUS_METHOD,
        applied=True,
        selected_crop=selected_crop,
        reason=reason,
        lesion_coverage_percent=analysis.lesion_coverage_percent,
        healthy_coverage_threshold=healthy_coverage_threshold,
        lesion_count=analysis.lesion_count,
        roi_count=len(normalized_views),
        full_healthy_probability=full_healthy_probability,
        focused_predictions=ranked_focus,
        best_view_index=best_view_index,
        evidence_boundary=(
            "Grape healthy-veto threshold is calibrated from accepted PlantVillage "
            "training healthy leaves and had 0/100 false vetoes on accepted healthy "
            "official-test images. ROI scores are weakly supervised, uncalibrated, and "
            "remain candidate evidence rather than a field diagnosis."
        ),
    )
    return fused, evidence


__all__ = [
    "DISEASE_INPUT_LESION_FOCUS",
    "HEALTHY_LESION_COVERAGE_THRESHOLDS",
    "LESION_FOCUS_METHOD",
    "LesionFocusEvidence",
    "extract_lesion_views",
    "fuse_lesion_predictions",
    "should_focus_lesions",
]
