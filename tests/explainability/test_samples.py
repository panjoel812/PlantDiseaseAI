import json
from pathlib import Path

import pytest

from plantdisease.explainability.samples import freeze_sample_groups, save_frozen_samples

CHECKPOINT_PATH = "outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/checkpoint.pt"


def _prediction(test_index: int, confidence: float, correct: bool) -> dict[str, object]:
    true_index = 0 if correct else 1
    predicted_index = 0
    return {
        "test_index": test_index,
        "sample_id": f"hf-test-{test_index}",
        "true_class_index": true_index,
        "true_class_name": f"class-{true_index}",
        "predicted_class_index": predicted_index,
        "predicted_class_name": f"class-{predicted_index}",
        "confidence": confidence,
        "correct": correct,
    }


def _indices(group: list[dict[str, object]]) -> list[int]:
    return [int(sample["test_index"]) for sample in group]


def test_freeze_sample_groups_selects_four_confidence_quadrants_stably() -> None:
    predictions = [
        _prediction(0, 0.90, True),
        _prediction(1, 0.95, True),
        _prediction(2, 0.95, True),
        _prediction(3, 0.10, True),
        _prediction(4, 0.20, True),
        _prediction(5, 0.99, False),
        _prediction(6, 0.80, False),
        _prediction(7, 0.80, False),
        _prediction(8, 0.05, False),
        _prediction(9, 0.15, False),
    ]

    manifest = freeze_sample_groups(
        predictions,
        samples_per_group=2,
        checkpoint_path=CHECKPOINT_PATH,
        model_name="resnet50",
        target_layer="layer4.2",
    )

    assert manifest["schema_version"] == 1
    assert manifest["model"] == {
        "checkpoint_path": CHECKPOINT_PATH,
        "model_name": "resnet50",
        "target_layer": "layer4.2",
    }
    assert manifest["selection"]["samples_per_group"] == 2
    assert manifest["selection"]["groups"] == [
        "correct_high_confidence",
        "correct_low_confidence",
        "error_high_confidence",
        "error_low_confidence",
    ]
    assert manifest["selection"]["tie_breaker"] == "test_index_ascending"
    assert manifest["selection"]["available_counts"] == {"correct": 5, "error": 5}
    assert manifest["selection"]["selected_counts"] == {
        "correct_high_confidence": 2,
        "correct_low_confidence": 2,
        "error_high_confidence": 2,
        "error_low_confidence": 2,
    }
    assert _indices(manifest["groups"]["correct_high_confidence"]) == [1, 2]
    assert _indices(manifest["groups"]["correct_low_confidence"]) == [3, 4]
    assert _indices(manifest["groups"]["error_high_confidence"]) == [5, 6]
    assert _indices(manifest["groups"]["error_low_confidence"]) == [8, 9]


def test_freeze_sample_groups_uses_available_samples_when_group_is_small() -> None:
    predictions = [
        _prediction(0, 0.60, True),
        _prediction(1, 0.30, False),
    ]

    manifest = freeze_sample_groups(
        predictions,
        samples_per_group=6,
        checkpoint_path="checkpoint.pt",
        model_name="resnet50",
        target_layer="layer4.2",
    )

    assert manifest["selection"]["available_counts"] == {"correct": 1, "error": 1}
    assert manifest["selection"]["selected_counts"] == {
        "correct_high_confidence": 1,
        "correct_low_confidence": 1,
        "error_high_confidence": 1,
        "error_low_confidence": 1,
    }
    assert _indices(manifest["groups"]["correct_high_confidence"]) == [0]
    assert _indices(manifest["groups"]["correct_low_confidence"]) == [0]
    assert _indices(manifest["groups"]["error_high_confidence"]) == [1]
    assert _indices(manifest["groups"]["error_low_confidence"]) == [1]


def test_freeze_sample_groups_rejects_invalid_inputs() -> None:
    with pytest.raises(ValueError, match="samples_per_group"):
        freeze_sample_groups(
            [_prediction(0, 0.60, True)],
            samples_per_group=0,
            checkpoint_path="checkpoint.pt",
            model_name="resnet50",
            target_layer="layer4.2",
        )

    invalid = _prediction(0, 1.20, True)
    with pytest.raises(ValueError, match="confidence"):
        freeze_sample_groups(
            [invalid],
            samples_per_group=1,
            checkpoint_path="checkpoint.pt",
            model_name="resnet50",
            target_layer="layer4.2",
        )


def test_save_frozen_samples_writes_stable_json(tmp_path: Path) -> None:
    manifest = freeze_sample_groups(
        [_prediction(0, 0.60, True)],
        samples_per_group=1,
        checkpoint_path="checkpoint.pt",
        model_name="resnet50",
        target_layer="layer4.2",
    )
    output = tmp_path / "week4" / "frozen_samples.json"

    save_frozen_samples(manifest, output)

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["schema_version"] == 1
    assert payload["groups"]["correct_high_confidence"][0]["sample_id"] == "hf-test-0"
