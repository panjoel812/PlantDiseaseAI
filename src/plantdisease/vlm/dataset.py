"""Deterministic VQA seed dataset builders."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Any

from plantdisease.vlm.schema import VQASample, assert_entity_split_integrity


def parse_plantvillage_label(class_name: str) -> tuple[str, str, bool]:
    """Parse a PlantVillage class label into plant, condition, and healthy flag."""

    if "___" not in class_name:
        msg = f"PlantVillage class label must contain '___': {class_name!r}"
        raise ValueError(msg)
    plant_raw, condition_raw = class_name.split("___", maxsplit=1)
    plant = _clean_label_part(plant_raw)
    condition = _clean_label_part(condition_raw)
    is_healthy = condition.lower() == "healthy"
    return plant, condition, is_healthy


def build_samples_from_frozen_groups(frozen: Mapping[str, Any]) -> list[VQASample]:
    """Build source-grounded VQA records from Week 4 frozen sample evidence."""

    image_records = _extract_image_records(frozen)
    split_by_image = _assign_splits([record["image_id"] for record in image_records])

    samples: list[VQASample] = []
    for record in image_records:
        plant, condition, is_healthy = parse_plantvillage_label(record["class_name"])
        split = split_by_image[record["image_id"]]
        base_metadata = {
            "class_name": record["class_name"],
            "group": record["group"],
            "confidence": record.get("confidence"),
            "test_index": record.get("test_index"),
        }
        questions = [
            (
                "plant",
                "Which plant is shown according to the PlantVillage label?",
                plant,
            ),
            (
                "condition",
                "What labeled condition does this PlantVillage image show?",
                condition,
            ),
            (
                "health_status",
                "Is the labeled plant condition healthy or diseased?",
                "healthy" if is_healthy else "diseased",
            ),
        ]
        for question_type, question, answer in questions:
            samples.append(
                VQASample(
                    sample_id=f"vqa-{split}-{record['image_id']}-{question_type}",
                    image_id=record["image_id"],
                    image_ref=record["image_ref"],
                    question=question,
                    answer=answer,
                    question_type=question_type,
                    source="plantvillage_label",
                    split=split,
                    audit_status="pending",
                    metadata={**base_metadata, "plant": plant, "condition": condition},
                )
            )
    assert_entity_split_integrity(samples)
    return samples


def summarize_samples(samples: Sequence[VQASample]) -> dict[str, Any]:
    """Summarize a VQA sample collection for a data card."""

    try:
        assert_entity_split_integrity(samples)
        has_leakage = False
    except ValueError:
        has_leakage = True

    return {
        "schema_version": 1,
        "sample_count": len(samples),
        "image_count": len({sample.image_id for sample in samples}),
        "split_counts": dict(sorted(Counter(sample.split for sample in samples).items())),
        "question_type_counts": dict(
            sorted(Counter(sample.question_type for sample in samples).items())
        ),
        "source_counts": dict(sorted(Counter(sample.source for sample in samples).items())),
        "audit_status_counts": dict(
            sorted(Counter(sample.audit_status for sample in samples).items())
        ),
        "entity_split_leakage": has_leakage,
    }


def _clean_label_part(value: str) -> str:
    return value.strip("_").replace("_", " ")


def _extract_image_records(frozen: Mapping[str, Any]) -> list[dict[str, Any]]:
    groups = frozen.get("groups")
    if not isinstance(groups, Mapping):
        msg = "frozen samples payload must contain a 'groups' mapping"
        raise ValueError(msg)

    records: list[dict[str, Any]] = []
    for group_name in sorted(groups):
        group_records = groups[group_name]
        if not isinstance(group_records, Sequence):
            msg = f"group {group_name!r} must contain a sequence of records"
            raise ValueError(msg)
        for raw_record in group_records:
            if not isinstance(raw_record, Mapping):
                msg = f"group {group_name!r} contains a non-mapping record"
                raise ValueError(msg)
            image_id = str(raw_record.get("sample_id") or f"hf-test-{raw_record['test_index']}")
            class_name = str(raw_record["true_class_name"])
            records.append(
                {
                    "image_id": image_id,
                    "image_ref": image_id,
                    "class_name": class_name,
                    "group": str(group_name),
                    "confidence": raw_record.get("confidence"),
                    "test_index": raw_record.get("test_index"),
                }
            )
    records.sort(key=lambda record: record["image_id"])
    return records


def _assign_splits(image_ids: Sequence[str]) -> dict[str, str]:
    unique_ids = sorted(set(image_ids))
    total = len(unique_ids)
    if total == 0:
        return {}
    if total == 1:
        return {unique_ids[0]: "train"}
    if total == 2:
        return {unique_ids[0]: "train", unique_ids[1]: "test"}

    train_count = max(1, int(total * 0.70))
    validation_count = max(1, int(total * 0.15))
    if train_count + validation_count >= total:
        validation_count = 1
        train_count = total - 2

    split_by_image: dict[str, str] = {}
    for index, image_id in enumerate(unique_ids):
        if index < train_count:
            split = "train"
        elif index < train_count + validation_count:
            split = "validation"
        else:
            split = "test"
        split_by_image[image_id] = split
    return split_by_image
