"""Host-specific low-compute condition models built from cached embeddings."""

from __future__ import annotations

import numpy as np

from plantdisease.openworld.index import PrototypeIndex
from plantdisease.openworld.router import ConditionDecision


class PrototypeConditionModel:
    """Recognize only the healthy/disease labels supported for one plant host."""

    def __init__(self, host_id: str, index: PrototypeIndex) -> None:
        if not host_id.strip():
            raise ValueError("host_id must be non-empty")
        self.host_id = host_id
        self.index = index

    @classmethod
    def fit(
        cls,
        host_id: str,
        embeddings: np.ndarray,
        condition_ids: list[str],
        *,
        encoder_id: str,
        max_prototypes_per_condition: int = 3,
        similarity_threshold: float = 0.70,
        margin_threshold: float = 0.05,
        seed: int = 42,
    ) -> PrototypeConditionModel:
        index = PrototypeIndex.fit(
            embeddings,
            condition_ids,
            encoder_id=encoder_id,
            max_prototypes_per_class=max_prototypes_per_condition,
            similarity_threshold=similarity_threshold,
            margin_threshold=margin_threshold,
            seed=seed,
        )
        return cls(host_id, index)

    def predict(self, image: object) -> ConditionDecision:
        """Treat `image` as a cached embedding supplied by the routing pipeline."""
        embedding = np.asarray(image, dtype=np.float32)
        decision = self.index.predict(embedding)
        return ConditionDecision(
            condition_id=decision.plant_id,
            accepted=decision.accepted,
            confidence=max(0.0, min(1.0, decision.similarity)),
            reason=(
                f"Host {self.host_id}; cosine evidence only, not a calibrated probability. "
                f"{decision.reason}"
            ),
        )
