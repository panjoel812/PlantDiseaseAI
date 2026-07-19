from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from plantdisease.openworld.condition import PrototypeConditionModel
from plantdisease.openworld.index import PrototypeIndex
from plantdisease.openworld.router import (
    ConditionDecision,
    HierarchicalRouter,
)


@dataclass
class FakeConditionModel:
    calls: int = 0

    def predict(self, image: object) -> ConditionDecision:
        self.calls += 1
        return ConditionDecision("black_rot", True, 0.91, "accepted")


def _index() -> PrototypeIndex:
    return PrototypeIndex.fit(
        np.asarray([[1.0, 0.0], [0.99, 0.02], [0.0, 1.0], [0.02, 0.99]]),
        ["grape", "grape", "tomato", "tomato"],
        encoder_id="synthetic",
        max_prototypes_per_class=1,
        similarity_threshold=0.75,
        margin_threshold=0.20,
    )


def test_router_runs_only_the_accepted_plants_condition_model() -> None:
    grape_model = FakeConditionModel()
    router = HierarchicalRouter(_index(), {"grape": grape_model})

    result = router.predict(np.asarray([1.0, 0.01]), image=object())

    assert result.route_status == "condition_accepted"
    assert result.condition is not None
    assert result.condition.condition_id == "black_rot"
    assert grape_model.calls == 1


def test_router_never_runs_condition_model_for_unknown_plant() -> None:
    grape_model = FakeConditionModel()
    router = HierarchicalRouter(_index(), {"grape": grape_model})

    result = router.predict(np.asarray([0.70, 0.70]), image=object())

    assert result.route_status == "unknown_plant"
    assert result.condition is None
    assert grape_model.calls == 0


def test_router_can_use_a_host_specific_prototype_condition_model() -> None:
    condition_model = PrototypeConditionModel.fit(
        "grape",
        np.asarray([[1.0, 0.0], [0.98, 0.02], [0.0, 1.0], [0.02, 0.98]]),
        ["healthy", "healthy", "black_rot", "black_rot"],
        encoder_id="synthetic-condition",
        max_prototypes_per_condition=1,
        similarity_threshold=0.75,
        margin_threshold=0.20,
    )
    router = HierarchicalRouter(_index(), {"grape": condition_model})

    result = router.predict(
        np.asarray([1.0, 0.01]),
        image=np.asarray([0.01, 1.0]),
    )

    assert result.route_status == "condition_accepted"
    assert result.condition is not None
    assert result.condition.condition_id == "black_rot"
