"""Crop-first views derived from a PlantVillage joint class distribution."""

from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass

from plantdisease.inference import Prediction
from plantdisease.serving.knowledge import lookup_disease_knowledge

HIERARCHY_METHOD = "crop_first_rejection_v2"
INDEPENDENT_HIERARCHY_METHOD = "independent_crop_then_disease_v3"
EXTERNAL_SPECIES_HIERARCHY_METHOD = "external_species_then_disease_v4"
LOCAL_CATALOG_HIERARCHY_METHOD = "local_catalog_then_disease_v4"
DEFAULT_CROP_CONFIDENCE_THRESHOLD = 0.60
DEFAULT_CROP_MARGIN_THRESHOLD = 0.10
DEFAULT_DISEASE_CONFIDENCE_THRESHOLD = 0.65
DEFAULT_DISEASE_MARGIN_THRESHOLD = 0.15


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
    crop_source: str = "joint_disease_distribution"
    disease_confident: bool = True
    disease_confidence: float = 1.0
    disease_margin: float = 1.0
    disease_confidence_threshold: float = DEFAULT_DISEASE_CONFIDENCE_THRESHOLD
    disease_margin_threshold: float = DEFAULT_DISEASE_MARGIN_THRESHOLD
    disease_decision_reason: str = "Disease gate accepted."


def build_taxonomy_hierarchy(
    predictions: Sequence[Prediction],
    *,
    crop_predictions: Sequence[Prediction] | None = None,
    crop_prediction_source: str | None = None,
    crop_confidence_threshold: float = DEFAULT_CROP_CONFIDENCE_THRESHOLD,
    crop_margin_threshold: float = DEFAULT_CROP_MARGIN_THRESHOLD,
    disease_confidence_threshold: float = DEFAULT_DISEASE_CONFIDENCE_THRESHOLD,
    disease_margin_threshold: float = DEFAULT_DISEASE_MARGIN_THRESHOLD,
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
    if not 0.0 <= disease_confidence_threshold <= 1.0:
        raise ValueError("disease_confidence_threshold must be between zero and one")
    if not 0.0 <= disease_margin_threshold <= 1.0:
        raise ValueError("disease_margin_threshold must be between zero and one")

    normalized: list[tuple[Prediction, str, str, float]] = []
    crop_totals: defaultdict[str, float] = defaultdict(float)
    for prediction in predictions:
        knowledge = lookup_disease_knowledge(prediction.class_name)
        joint_probability = prediction.probability / total_probability
        normalized.append(
            (prediction, knowledge.plant, knowledge.condition, joint_probability)
        )
        crop_totals[knowledge.plant] += joint_probability

    if crop_predictions is None:
        crops = sorted(
            (
                CropPrediction(plant=plant, probability=probability)
                for plant, probability in crop_totals.items()
            ),
            key=lambda item: (-item.probability, item.plant),
        )
        method = HIERARCHY_METHOD
        crop_source = "joint_disease_distribution"
    else:
        if not crop_predictions:
            raise ValueError("crop_predictions must not be empty")
        crop_total = sum(item.probability for item in crop_predictions)
        if crop_total <= 0.0:
            raise ValueError("crop prediction probability total must be positive")
        crops = [
            CropPrediction(item.class_name, item.probability / crop_total)
            for item in crop_predictions
        ]
        crops.sort(key=lambda item: (-item.probability, item.plant))
        if crop_prediction_source is None:
            method = INDEPENDENT_HIERARCHY_METHOD
            crop_source = "independent_mobilenet_v2_crop_checkpoint"
        elif crop_prediction_source == "local_leaf114_checkpoint":
            method = LOCAL_CATALOG_HIERARCHY_METHOD
            crop_source = crop_prediction_source
        else:
            method = EXTERNAL_SPECIES_HIERARCHY_METHOD
            crop_source = crop_prediction_source
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
                conditional_probability=0.0,
            )
            for prediction, plant, condition, joint_probability in normalized
            if plant == selected_crop.plant
        ),
        key=lambda item: (-item.joint_probability, item.class_name),
    )
    crop_disease_mass = sum(item.joint_probability for item in ranked_conditions)
    if crop_disease_mass > 0.0:
        ranked_conditions = [
            ConditionPrediction(
                class_index=item.class_index,
                class_name=item.class_name,
                plant=item.plant,
                condition=item.condition,
                joint_probability=item.joint_probability,
                conditional_probability=item.joint_probability / crop_disease_mass,
            )
            for item in ranked_conditions
        ]
    disease_confidence = (
        ranked_conditions[0].conditional_probability if ranked_conditions else 0.0
    )
    disease_margin = disease_confidence - (
        ranked_conditions[1].conditional_probability if len(ranked_conditions) > 1 else 0.0
    )
    independent_gate = crop_predictions is not None
    disease_confident = (
        crop_confident
        and bool(ranked_conditions)
        and (
            not independent_gate
            or (
                disease_confidence >= disease_confidence_threshold
                and disease_margin >= disease_margin_threshold
            )
        )
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
    elif not ranked_conditions:
        decision_reason = (
            "Plant identity accepted, but this species has no matching local "
            "PlantVillage disease taxonomy."
        )
    else:
        decision_reason = "Crop gate accepted; disease ranking is restricted to this crop."
    if not crop_confident:
        disease_decision_reason = "Disease labels are withheld until plant identity is accepted."
    elif not ranked_conditions:
        disease_decision_reason = (
            "Disease labels are withheld because this accepted species is outside "
            "the local PlantVillage disease catalog."
        )
    elif not disease_confident:
        disease_decision_reason = (
            f"Disease confidence {disease_confidence:.1%} or margin {disease_margin:.1%} "
            "did not pass the reliability gate; candidates are evidence only."
        )
    else:
        disease_decision_reason = "Disease gate accepted within the selected plant."
    return TaxonomyHierarchy(
        method=method,
        selected_crop=selected_crop.plant,
        selected_class_name=(conditions[0].class_name if disease_confident else None),
        crops=crops,
        conditions=conditions,
        crop_confident=crop_confident,
        crop_margin=crop_margin,
        confidence_threshold=crop_confidence_threshold,
        margin_threshold=crop_margin_threshold,
        decision_reason=decision_reason,
        crop_source=crop_source,
        disease_confident=disease_confident,
        disease_confidence=disease_confidence,
        disease_margin=disease_margin,
        disease_confidence_threshold=disease_confidence_threshold,
        disease_margin_threshold=disease_margin_threshold,
        disease_decision_reason=disease_decision_reason,
    )
