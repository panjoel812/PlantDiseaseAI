"""Metrics for known-species recognition and unknown-species rejection."""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
from sklearn.metrics import auc, average_precision_score, roc_auc_score, roc_curve

from plantdisease.openworld.index import PrototypeIndex


@dataclass(frozen=True)
class OpenSetMetrics:
    known_count: int
    unknown_count: int
    closed_set_top1_accuracy: float
    known_accept_rate: float
    known_correct_accept_rate: float
    accepted_known_accuracy: float
    unknown_reject_rate: float
    unknown_false_accept_rate: float
    auroc_unknown: float
    aupr_out: float
    fpr_at_95_tpr: float
    oscr_similarity: float

    def to_dict(self) -> dict[str, int | float]:
        return asdict(self)


def evaluate_open_set(
    index: PrototypeIndex,
    known_embeddings: np.ndarray,
    known_plant_ids: list[str],
    unknown_embeddings: np.ndarray,
) -> OpenSetMetrics:
    """Evaluate calibrated gates; OOD ranking uses negative maximum similarity."""

    known = np.asarray(known_embeddings, dtype=np.float32)
    unknown = np.asarray(unknown_embeddings, dtype=np.float32)
    if known.ndim != 2 or unknown.ndim != 2 or not len(known) or not len(unknown):
        raise ValueError("known and unknown embeddings must be non-empty matrices")
    if known.shape[1] != unknown.shape[1]:
        raise ValueError("known and unknown embedding dimensions must match")
    if len(known_plant_ids) != len(known):
        raise ValueError("known_plant_ids length must match known_embeddings")

    known_similarity: list[float] = []
    known_margin: list[float] = []
    known_correct: list[bool] = []
    for embedding, truth in zip(known, known_plant_ids, strict=True):
        ranked = index.scores(embedding)
        known_similarity.append(ranked[0][1])
        known_margin.append(ranked[0][1] - ranked[1][1])
        known_correct.append(ranked[0][0] == truth)
    unknown_similarity: list[float] = []
    unknown_margin: list[float] = []
    for embedding in unknown:
        ranked = index.scores(embedding)
        unknown_similarity.append(ranked[0][1])
        unknown_margin.append(ranked[0][1] - ranked[1][1])

    known_similarity_array = np.asarray(known_similarity)
    known_margin_array = np.asarray(known_margin)
    known_correct_array = np.asarray(known_correct, dtype=bool)
    unknown_similarity_array = np.asarray(unknown_similarity)
    unknown_margin_array = np.asarray(unknown_margin)
    known_accept = (
        (known_similarity_array >= index.similarity_threshold)
        & (known_margin_array >= index.margin_threshold)
    )
    unknown_accept = (
        (unknown_similarity_array >= index.similarity_threshold)
        & (unknown_margin_array >= index.margin_threshold)
    )
    correct_accept = known_accept & known_correct_array

    ood_labels = np.concatenate(
        (np.zeros(len(known), dtype=np.int8), np.ones(len(unknown), dtype=np.int8))
    )
    ood_scores = -np.concatenate((known_similarity_array, unknown_similarity_array))
    false_positive_rates, true_positive_rates, _ = roc_curve(ood_labels, ood_scores)
    candidates = false_positive_rates[true_positive_rates >= 0.95]
    fpr95 = float(np.min(candidates)) if len(candidates) else 1.0

    accepted_known = int(np.count_nonzero(known_accept))
    return OpenSetMetrics(
        known_count=len(known),
        unknown_count=len(unknown),
        closed_set_top1_accuracy=float(np.mean(known_correct_array)),
        known_accept_rate=float(np.mean(known_accept)),
        known_correct_accept_rate=float(np.mean(correct_accept)),
        accepted_known_accuracy=(
            float(np.count_nonzero(correct_accept) / accepted_known)
            if accepted_known
            else 0.0
        ),
        unknown_reject_rate=float(np.mean(~unknown_accept)),
        unknown_false_accept_rate=float(np.mean(unknown_accept)),
        auroc_unknown=float(roc_auc_score(ood_labels, ood_scores)),
        aupr_out=float(average_precision_score(ood_labels, ood_scores)),
        fpr_at_95_tpr=fpr95,
        oscr_similarity=_oscr(
            known_similarity_array,
            known_correct_array,
            unknown_similarity_array,
        ),
    )


def _oscr(
    known_similarity: np.ndarray,
    known_correct: np.ndarray,
    unknown_similarity: np.ndarray,
) -> float:
    thresholds = np.concatenate(
        (
            np.asarray([np.inf]),
            np.unique(np.concatenate((known_similarity, unknown_similarity)))[::-1],
            np.asarray([-np.inf]),
        )
    )
    points: dict[float, float] = {}
    for threshold in thresholds:
        false_positive_rate = float(np.mean(unknown_similarity >= threshold))
        correct_classification_rate = float(
            np.mean((known_similarity >= threshold) & known_correct)
        )
        points[false_positive_rate] = max(
            points.get(false_positive_rate, 0.0),
            correct_classification_rate,
        )
    x = np.asarray(sorted(points))
    y = np.asarray([points[value] for value in x])
    return float(auc(x, y))


__all__ = ["OpenSetMetrics", "evaluate_open_set"]
