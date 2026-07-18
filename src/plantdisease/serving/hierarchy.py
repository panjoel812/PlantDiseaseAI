"""Crop-first views derived from a PlantVillage joint class distribution."""

from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass

from plantdisease.inference import Prediction
from plantdisease.serving.knowledge import lookup_disease_knowledge

HIERARCHY_METHOD = "crop_first_rejection_v2"
DEFAULT_CROP_CONFIDENCE_THRESHOLD = 0.60
DEFAULT_CROP_MARGIN_THRESHOLD = 0.10


@dataclass(frozen=True)
class CropPrediction:
    """Aggregated probability for one plant in the joint label taxonomy."""

    plant: str
    probability: float


@dataclass(frozen=True)
class ConditionPrediction:
    """Condition probability within the selected crop."""

    class_index: int
    class_name: str
    plant: str
    condition: str
    joint_probability: float
    conditional_probability: float


@dataclass(frozen=True)
class TaxonomyHierarchy:
    """Crop-first projection of one closed-set classifier distribution."""

    method: str
    selected_crop: str
    selected_class_name: str | None
    crops: list[CropPrediction]
    conditions: list[ConditionPrediction]
    crop_confident: bool = True
    crop_margin: float = 1.0
    confidence_threshold: float = DEFAULT_CROP_CONFIDENCE_THRESHOLD
    margin_threshold: float = DEFAULT_CROP_MARGIN_THRESHOLD
    decision_reason: str = "Crop gate accepted."


def build_taxonomy_hierarchy(
    predictions: Sequence[Prediction],
    *,
    crop_confidence_threshold: float = DEFAULT_CROP_CONFIDENCE_THRESHOLD,
    crop_margin_threshold: float = DEFAULT_CROP_MARGIN_THRESHOLD,
) -> TaxonomyHierarchy:
    """Aggregate crop evidence, gate uncertainty, then rank crop-only conditions.

    The current checkpoint has a joint PlantVillage label space rather than an
    independent crop head.  A low-confidence crop is therefore treated as an
    abstention: disease labels are withheld instead of being projected through a
    weak or incorrect crop guess.
    """
    if not predictions:
        raise ValueError("predictions must not be empty")
    if any(
        not math.isfinite(item.probability) or item.probability < 0.0
        for item in predictions
    ):
        raise ValueError("prediction probabilities must be finite and non-negative")

    total_probability = sum(item.probability for item in predictions)
    if total_probability <= 0.0:
        raise ValueError("prediction probability total must be positive")
    if not 0.0 <= crop_confidence_threshold <= 1.0:
        raise ValueError("crop_confidence_threshold must be between zero and one")
    if not 0.0 <= crop_margin_threshold <= 1.0:
        raise ValueError("crop_margin_threshold must be between zero and one")

    normalized: list[tuple[Prediction, str, str, float]] = []
    crop_totals: defaultdict[str, float] = defaultdict(float)
    for prediction in predictions:
        knowledge = lookup_disease_knowledge(prediction.class_name)
        joint_probability = prediction.probability / total_probability
        normalized.append(
            (prediction, knowledge.plant, knowledge.condition, joint_probability)
        )
        crop_totals[knowledge.plant] += joint_probability

    crops = sorted(
        (
            CropPrediction(plant=plant, probability=probability)
            for plant, probability in crop_totals.items()
        ),
        key=lambda item: (-item.probability, item.plant),
    )
    selected_crop = crops[0]
    crop_margin = selected_crop.probability - (
        crops[1].probability if len(crops) > 1 else 0.0
    )
    crop_confident = (
        selected_crop.probability >= crop_confidence_threshold
        and crop_margin >= crop_margin_threshold
    )
    ranked_conditions = sorted(
        (
            ConditionPrediction(
                class_index=prediction.class_index,
                class_name=prediction.class_name,
                plant=plant,
                condition=condition,
                joint_probability=joint_probability,
                conditional_probability=(
                    joint_probability / selected_crop.probability
                ),
            )
            for prediction, plant, condition, joint_probability in normalized
            if plant == selected_crop.plant
        ),
        key=lambda item: (-item.joint_probability, item.class_name),
    )
    conditions = ranked_conditions if crop_confident else []
    if selected_crop.probability < crop_confidence_threshold:
        decision_reason = (
            f"Crop confidence {selected_crop.probability:.1%} is below the "
            f"{crop_confidence_threshold:.0%} acceptance threshold."
        )
    elif crop_margin < crop_margin_threshold:
        decision_reason = (
            f"Crop margin {crop_margin:.1%} is below the "
            f"{crop_margin_threshold:.0%} acceptance threshold."
        )
    else:
        decision_reason = "Crop gate accepted; disease ranking is restricted to this crop."
    return TaxonomyHierarchy(
        method=HIERARCHY_METHOD,
        selected_crop=selected_crop.plant,
        selected_class_name=(conditions[0].class_name if conditions else None),
        crops=crops,
        conditions=conditions,
        crop_confident=crop_confident,
        crop_margin=crop_margin,
        confidence_threshold=crop_confidence_threshold,
        margin_threshold=crop_margin_threshold,
        decision_reason=decision_reason,
    )
