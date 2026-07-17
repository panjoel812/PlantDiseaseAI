from pathlib import Path

import pytest

from plantdisease.vlm.schema import (
    VQASample,
    assert_entity_split_integrity,
    read_jsonl,
    write_jsonl,
)


def make_sample(
    sample_id: str = "q1",
    image_id: str = "img-1",
    split: str = "train",
    source: str = "plantvillage_label",
    audit_status: str = "passed",
) -> VQASample:
    return VQASample(
        sample_id=sample_id,
        image_id=image_id,
        image_ref="hf-test-1",
        question="Which plant is shown?",
        answer="Apple",
        question_type="plant",
        source=source,
        split=split,
        audit_status=audit_status,
        metadata={"class_name": "Apple___healthy"},
    )


def test_vqa_sample_rejects_invalid_split() -> None:
    with pytest.raises(ValueError, match="split"):
        make_sample(split="holdout")


def test_vqa_sample_rejects_invalid_audit_status() -> None:
    with pytest.raises(ValueError, match="audit_status"):
        make_sample(audit_status="unchecked")


def test_vqa_sample_rejects_invalid_source() -> None:
    with pytest.raises(ValueError, match="source"):
        make_sample(source="model_guess")


def test_jsonl_roundtrip_preserves_samples(tmp_path: Path) -> None:
    samples = [make_sample(), make_sample(sample_id="q2", image_id="img-2", split="test")]
    path = tmp_path / "vqa.jsonl"

    write_jsonl(path, samples)

    assert read_jsonl(path) == samples


def test_entity_split_integrity_allows_repeated_image_inside_one_split() -> None:
    samples = [
        make_sample(sample_id="q1", image_id="img-1", split="train"),
        make_sample(sample_id="q2", image_id="img-1", split="train"),
    ]

    assert_entity_split_integrity(samples)


def test_entity_split_integrity_rejects_same_image_across_splits() -> None:
    samples = [
        make_sample(sample_id="q1", image_id="img-1", split="train"),
        make_sample(sample_id="q2", image_id="img-1", split="test"),
    ]

    with pytest.raises(ValueError, match="image_id"):
        assert_entity_split_integrity(samples)
