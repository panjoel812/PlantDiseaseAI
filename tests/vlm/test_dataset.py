from plantdisease.vlm.dataset import (
    build_samples_from_frozen_groups,
    parse_plantvillage_label,
    summarize_samples,
)
from plantdisease.vlm.schema import assert_entity_split_integrity


def test_parse_plantvillage_label_normalizes_plant_and_condition() -> None:
    plant, condition, is_healthy = parse_plantvillage_label("Tomato___Leaf_Mold")

    assert plant == "Tomato"
    assert condition == "Leaf Mold"
    assert is_healthy is False


def test_parse_plantvillage_label_detects_healthy_class() -> None:
    plant, condition, is_healthy = parse_plantvillage_label("Apple___healthy")

    assert plant == "Apple"
    assert condition == "healthy"
    assert is_healthy is True


def test_build_samples_from_frozen_groups_creates_source_grounded_questions() -> None:
    frozen = {
        "groups": {
            "correct_high_confidence": [
                {
                    "sample_id": "hf-test-10",
                    "test_index": 10,
                    "true_class_name": "Tomato___Leaf_Mold",
                    "confidence": 0.99,
                }
            ],
            "error_low_confidence": [
                {
                    "sample_id": "hf-test-11",
                    "test_index": 11,
                    "true_class_name": "Apple___healthy",
                    "confidence": 0.41,
                }
            ],
        }
    }

    samples = build_samples_from_frozen_groups(frozen)

    assert len(samples) == 6
    assert_entity_split_integrity(samples)
    assert {sample.question_type for sample in samples} == {"plant", "condition", "health_status"}
    assert {sample.source for sample in samples} == {"plantvillage_label"}
    assert {sample.audit_status for sample in samples} == {"pending"}
    assert any(sample.answer == "Tomato" for sample in samples)
    assert any(sample.answer == "Leaf Mold" for sample in samples)
    assert any(sample.answer == "healthy" for sample in samples)


def test_summarize_samples_reports_counts_and_leakage_status() -> None:
    frozen = {
        "groups": {
            "correct_high_confidence": [
                {
                    "sample_id": "hf-test-10",
                    "test_index": 10,
                    "true_class_name": "Tomato___Leaf_Mold",
                    "confidence": 0.99,
                }
            ]
        }
    }
    samples = build_samples_from_frozen_groups(frozen)

    summary = summarize_samples(samples)

    assert summary["schema_version"] == 1
    assert summary["sample_count"] == 3
    assert summary["image_count"] == 1
    assert summary["entity_split_leakage"] is False
    assert summary["question_type_counts"] == {
        "condition": 1,
        "health_status": 1,
        "plant": 1,
    }
