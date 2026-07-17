"""Crop-first views derived from a PlantVillage joint class distribution."""

from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass

from plantdisease.inference import Prediction
from plantdisease.serving.knowledge import lookup_disease_knowledge

HIERARCHY_METHOD = "single_model_taxonomy_aggregation_v1"


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
    selected_class_name: str
    crops: list[CropPrediction]
    conditions: list[ConditionPrediction]


def build_taxonomy_hierarchy(
    predictions: Sequence[Prediction],
) -> TaxonomyHierarchy:
    """Aggregate joint class probabilities by crop, then rank its conditions."""
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
    conditions = sorted(
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
    return TaxonomyHierarchy(
        method=HIERARCHY_METHOD,
        selected_crop=selected_crop.plant,
        selected_class_name=conditions[0].class_name,
        crops=crops,
        conditions=conditions,
    )
