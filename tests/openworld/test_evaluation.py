from __future__ import annotations

import numpy as np
import pytest

from plantdisease.openworld.evaluation import evaluate_open_set
from plantdisease.openworld.index import PrototypeIndex


def test_open_set_metrics_reward_known_separation_and_unknown_rejection() -> None:
    index = PrototypeIndex.fit(
        np.asarray([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]),
        ["grape", "tomato"],
        encoder_id="synthetic",
        max_prototypes_per_class=1,
        similarity_threshold=0.75,
        margin_threshold=0.20,
    )

    result = evaluate_open_set(
        index,
        np.asarray([[0.99, 0.01, 0.0], [0.01, 0.99, 0.0]]),
        ["grape", "tomato"],
        np.asarray([[0.0, 0.0, 1.0], [-0.70, -0.70, 0.0]]),
    )

    assert result.closed_set_top1_accuracy == 1.0
    assert result.known_correct_accept_rate == 1.0
    assert result.unknown_reject_rate == 1.0
    assert result.unknown_false_accept_rate == 0.0
    assert result.auroc_unknown == 1.0
    assert result.aupr_out == 1.0
    assert result.oscr_similarity == pytest.approx(1.0)
