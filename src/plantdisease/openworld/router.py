"""Plant-first routing that never runs a condition model for unknown plants."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

import numpy as np

from plantdisease.openworld.index import OpenSetDecision, PrototypeIndex


@dataclass(frozen=True)
class ConditionDecision:
    condition_id: str | None
    accepted: bool
    confidence: float
    reason: str


class ConditionPredictor(Protocol):
    def predict(self, image: Any) -> ConditionDecision: ...


@dataclass(frozen=True)
class HierarchicalDecision:
    plant: OpenSetDecision
    condition: ConditionDecision | None
    route_status: str


class HierarchicalRouter:
    """Route accepted plant identities to small host-specific condition models."""

    def __init__(
        self,
        plant_index: PrototypeIndex,
        condition_models: dict[str, ConditionPredictor] | None = None,
    ) -> None:
        self.plant_index = plant_index
        self.condition_models = dict(condition_models or {})

    def predict(self, plant_embedding: np.ndarray, image: Any = None) -> HierarchicalDecision:
        plant = self.plant_index.predict(plant_embedding)
        if not plant.accepted or plant.plant_id is None:
            return HierarchicalDecision(plant, None, "unknown_plant")
        condition_model = self.condition_models.get(plant.plant_id)
        if condition_model is None:
            return HierarchicalDecision(plant, None, "plant_known_condition_model_unavailable")
        condition = condition_model.predict(image)
        status = "condition_accepted" if condition.accepted else "condition_uncertain"
        return HierarchicalDecision(plant, condition, status)
