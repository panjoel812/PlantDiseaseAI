"""Multi-prototype cosine index with explicit unknown-plant rejection."""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
from sklearn.cluster import KMeans


@dataclass(frozen=True)
class OpenSetDecision:
    """Ranked plant evidence and the final accept/reject decision."""

    accepted: bool
    plant_id: str | None
    candidate_plant_id: str
    similarity: float
    margin: float
    alternatives: tuple[tuple[str, float], ...]
    reason: str


@dataclass(frozen=True)
class ThresholdCalibration:
    """Thresholds selected from held-out known and explicit unknown samples."""

    similarity_threshold: float
    margin_threshold: float
    known_correct_accept_rate: float
    unknown_reject_rate: float
    wrong_known_reject_rate: float
    balanced_score: float
    known_count: int
    unknown_count: int


def _normalize_rows(values: np.ndarray) -> np.ndarray:
    matrix = np.asarray(values, dtype=np.float32)
    if matrix.ndim != 2 or matrix.shape[0] == 0 or matrix.shape[1] == 0:
        raise ValueError("embeddings must be a non-empty two-dimensional array")
    if not np.isfinite(matrix).all():
        raise ValueError("embeddings must contain only finite values")
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    if np.any(norms <= 0):
        raise ValueError("embeddings must not contain zero vectors")
    return matrix / norms


class PrototypeIndex:
    """Frozen-encoder index that adds classes without gradient training."""

    def __init__(
        self,
        *,
        prototypes: np.ndarray,
        prototype_labels: list[str],
        class_counts: dict[str, int],
        encoder_id: str,
        similarity_threshold: float = 0.70,
        margin_threshold: float = 0.05,
    ) -> None:
        normalized = _normalize_rows(prototypes)
        if len(prototype_labels) != len(normalized):
            raise ValueError("prototype_labels length must match prototypes")
        if not prototype_labels or any(not label.strip() for label in prototype_labels):
            raise ValueError("prototype labels must be non-empty")
        if not -1.0 <= similarity_threshold <= 1.0:
            raise ValueError("similarity_threshold must be between minus one and one")
        if not 0.0 <= margin_threshold <= 2.0:
            raise ValueError("margin_threshold must be between zero and two")
        self.prototypes = normalized
        self.prototype_labels = list(prototype_labels)
        self.class_counts = dict(class_counts)
        self.encoder_id = encoder_id
        self.similarity_threshold = similarity_threshold
        self.margin_threshold = margin_threshold
        self.plant_ids = sorted(set(self.prototype_labels))

    @classmethod
    def fit(
        cls,
        embeddings: np.ndarray,
        plant_ids: list[str],
        *,
        encoder_id: str,
        max_prototypes_per_class: int = 3,
        similarity_threshold: float = 0.70,
        margin_threshold: float = 0.05,
        seed: int = 42,
    ) -> PrototypeIndex:
        """Build up to K normalized centroids for each plant identity."""
        normalized = _normalize_rows(embeddings)
        if len(plant_ids) != len(normalized):
            raise ValueError("plant_ids length must match embeddings")
        if max_prototypes_per_class <= 0:
            raise ValueError("max_prototypes_per_class must be positive")
        if any(not label.strip() for label in plant_ids):
            raise ValueError("plant_ids must be non-empty")
        prototypes: list[np.ndarray] = []
        labels: list[str] = []
        counts: dict[str, int] = {}
        label_array = np.asarray(plant_ids)
        for plant_id in sorted(set(plant_ids)):
            samples = normalized[label_array == plant_id]
            counts[plant_id] = len(samples)
            cluster_count = min(max_prototypes_per_class, len(samples))
            if cluster_count == 1:
                centers = samples.mean(axis=0, keepdims=True)
            else:
                centers = KMeans(
                    n_clusters=cluster_count,
                    random_state=seed,
                    n_init=10,
                ).fit(samples).cluster_centers_
            prototypes.extend(centers)
            labels.extend([plant_id] * len(centers))
        return cls(
            prototypes=np.stack(prototypes),
            prototype_labels=labels,
            class_counts=counts,
            encoder_id=encoder_id,
            similarity_threshold=similarity_threshold,
            margin_threshold=margin_threshold,
        )

    def scores(self, embedding: np.ndarray) -> list[tuple[str, float]]:
        """Return maximum prototype cosine similarity for every plant."""
        query = _normalize_rows(np.asarray(embedding, dtype=np.float32).reshape(1, -1))[0]
        if query.shape[0] != self.prototypes.shape[1]:
            raise ValueError("query dimension does not match prototype dimension")
        similarities = self.prototypes @ query
        best: dict[str, float] = {}
        for label, similarity in zip(self.prototype_labels, similarities, strict=True):
            best[label] = max(best.get(label, -1.0), float(similarity))
        return sorted(best.items(), key=lambda item: (-item[1], item[0]))

    def predict(self, embedding: np.ndarray, *, top_k: int = 5) -> OpenSetDecision:
        if top_k <= 0:
            raise ValueError("top_k must be positive")
        ranked = self.scores(embedding)
        candidate, similarity = ranked[0]
        runner_up = ranked[1][1] if len(ranked) > 1 else -1.0
        margin = similarity - runner_up
        accepted = (
            similarity >= self.similarity_threshold and margin >= self.margin_threshold
        )
        if similarity < self.similarity_threshold:
            reason = (
                f"Similarity {similarity:.3f} is below the calibrated "
                f"threshold {self.similarity_threshold:.3f}."
            )
        elif margin < self.margin_threshold:
            reason = (
                f"Candidate margin {margin:.3f} is below the calibrated "
                f"threshold {self.margin_threshold:.3f}."
            )
        else:
            reason = "Plant identity passed similarity and margin gates."
        return OpenSetDecision(
            accepted=accepted,
            plant_id=candidate if accepted else None,
            candidate_plant_id=candidate,
            similarity=similarity,
            margin=margin,
            alternatives=tuple(ranked[: min(top_k, len(ranked))]),
            reason=reason,
        )

    def with_thresholds(self, calibration: ThresholdCalibration) -> PrototypeIndex:
        return PrototypeIndex(
            prototypes=self.prototypes,
            prototype_labels=self.prototype_labels,
            class_counts=self.class_counts,
            encoder_id=self.encoder_id,
            similarity_threshold=calibration.similarity_threshold,
            margin_threshold=calibration.margin_threshold,
        )

    def save(self, output_dir: Path) -> None:
        output_dir.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            output_dir / "prototypes.npz",
            prototypes=self.prototypes,
            prototype_labels=np.asarray(self.prototype_labels),
        )
        metadata = {
            "schema_version": 1,
            "method": "frozen_encoder_multi_prototype_cosine_v1",
            "encoder_id": self.encoder_id,
            "embedding_dimension": int(self.prototypes.shape[1]),
            "prototype_count": len(self.prototypes),
            "plant_count": len(self.plant_ids),
            "plant_ids": self.plant_ids,
            "class_counts": self.class_counts,
            "similarity_threshold": self.similarity_threshold,
            "margin_threshold": self.margin_threshold,
        }
        (output_dir / "index.json").write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    @classmethod
    def load(cls, output_dir: Path) -> PrototypeIndex:
        metadata = json.loads((output_dir / "index.json").read_text(encoding="utf-8"))
        if metadata.get("schema_version") != 1:
            raise ValueError("unsupported prototype index schema")
        arrays = np.load(output_dir / "prototypes.npz", allow_pickle=False)
        return cls(
            prototypes=arrays["prototypes"],
            prototype_labels=[str(value) for value in arrays["prototype_labels"]],
            class_counts={str(k): int(v) for k, v in metadata["class_counts"].items()},
            encoder_id=str(metadata["encoder_id"]),
            similarity_threshold=float(metadata["similarity_threshold"]),
            margin_threshold=float(metadata["margin_threshold"]),
        )


def calibrate_thresholds(
    index: PrototypeIndex,
    known_embeddings: np.ndarray,
    known_plant_ids: list[str],
    unknown_embeddings: np.ndarray,
) -> ThresholdCalibration:
    """Grid-search gates using held-out known identities and explicit OOD data."""
    known = _normalize_rows(known_embeddings)
    unknown = _normalize_rows(unknown_embeddings)
    if len(index.plant_ids) < 2:
        raise ValueError("threshold calibration requires at least two indexed plants")
    if len(known_plant_ids) != len(known):
        raise ValueError("known_plant_ids length must match known_embeddings")
    known_rows: list[tuple[float, float, bool]] = []
    for embedding, truth in zip(known, known_plant_ids, strict=True):
        ranked = index.scores(embedding)
        known_rows.append(
            (ranked[0][1], ranked[0][1] - ranked[1][1], ranked[0][0] == truth)
        )
    unknown_rows: list[tuple[float, float]] = []
    for embedding in unknown:
        ranked = index.scores(embedding)
        unknown_rows.append((ranked[0][1], ranked[0][1] - ranked[1][1]))
    similarity_candidates = np.unique(
        np.quantile(
            np.asarray([row[0] for row in known_rows + [(a, b, False) for a, b in unknown_rows]]),
            np.linspace(0.0, 1.0, 41),
        )
    )
    margin_candidates = np.unique(
        np.quantile(
            np.asarray([row[1] for row in known_rows + [(a, b, False) for a, b in unknown_rows]]),
            np.linspace(0.0, 1.0, 41),
        )
    )
    best: ThresholdCalibration | None = None
    for similarity_threshold in similarity_candidates:
        for margin_threshold in margin_candidates:
            known_accept = [
                similarity >= similarity_threshold and margin >= margin_threshold
                for similarity, margin, _ in known_rows
            ]
            correct_accept = sum(
                accepted and correct
                for accepted, (_, _, correct) in zip(known_accept, known_rows, strict=True)
            ) / len(known_rows)
            wrong_rows = [
                accepted
                for accepted, (_, _, correct) in zip(known_accept, known_rows, strict=True)
                if not correct
            ]
            wrong_reject = (
                1.0 - sum(wrong_rows) / len(wrong_rows) if wrong_rows else 1.0
            )
            unknown_reject = sum(
                similarity < similarity_threshold or margin < margin_threshold
                for similarity, margin in unknown_rows
            ) / len(unknown_rows)
            # Correct known acceptance already penalizes both rejected known samples
            # and accepted wrong known predictions. Adding wrong_reject to the
            # objective would reward rejection twice and select unusably conservative
            # gates. Keep it as a diagnostic, not an optimization term.
            score = (correct_accept + unknown_reject) / 2.0
            candidate = ThresholdCalibration(
                similarity_threshold=float(similarity_threshold),
                margin_threshold=float(margin_threshold),
                known_correct_accept_rate=correct_accept,
                unknown_reject_rate=unknown_reject,
                wrong_known_reject_rate=wrong_reject,
                balanced_score=score,
                known_count=len(known_rows),
                unknown_count=len(unknown_rows),
            )
            if best is None or (candidate.balanced_score, candidate.known_correct_accept_rate) > (
                best.balanced_score,
                best.known_correct_accept_rate,
            ):
                best = candidate
    if best is None or not math.isfinite(best.balanced_score):
        raise RuntimeError("threshold calibration failed")
    return best


def save_calibration(calibration: ThresholdCalibration, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(calibration), indent=2), encoding="utf-8")
