"""Dataset manifest contract for expandable plant and condition catalogs."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

VALID_SPLITS = frozenset({"train", "validation", "test", "ood_validation", "ood_test"})


@dataclass(frozen=True)
class OpenWorldRecord:
    """One licensed image entity with plant identity and optional condition."""

    image_id: str
    image_path: str
    plant_id: str
    condition_id: str | None
    split: str
    source: str
    license: str
    entity_id: str
    family_id: str | None = None
    genus_id: str | None = None
    site_id: str | None = None
    observer_id: str | None = None
    original_image_path: str | None = None
    leaf_mask_path: str | None = None
    lesion_crop_paths: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> OpenWorldRecord:
        required = ("image_id", "image_path", "plant_id", "split", "source", "license")
        missing = [name for name in required if not str(payload.get(name, "")).strip()]
        if missing:
            raise ValueError(f"manifest record missing non-empty fields: {', '.join(missing)}")
        split = str(payload["split"])
        if split not in VALID_SPLITS:
            raise ValueError(f"unsupported split: {split}")
        image_id = str(payload["image_id"])
        entity_id = str(payload.get("entity_id") or image_id)
        condition = payload.get("condition_id")
        return cls(
            image_id=image_id,
            image_path=str(payload["image_path"]),
            plant_id=str(payload["plant_id"]),
            condition_id=(str(condition) if condition is not None else None),
            split=split,
            source=str(payload["source"]),
            license=str(payload["license"]),
            entity_id=entity_id,
            family_id=_optional_string(payload.get("family_id")),
            genus_id=_optional_string(payload.get("genus_id")),
            site_id=_optional_string(payload.get("site_id")),
            observer_id=_optional_string(payload.get("observer_id")),
            original_image_path=_optional_string(payload.get("original_image_path")),
            leaf_mask_path=_optional_string(payload.get("leaf_mask_path")),
            lesion_crop_paths=_string_tuple(payload.get("lesion_crop_paths")),
        )


def _optional_string(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _string_tuple(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list) or any(not str(item).strip() for item in value):
        raise ValueError("lesion_crop_paths must be a list of non-empty strings")
    return tuple(str(item) for item in value)


def load_manifest(path: Path) -> list[OpenWorldRecord]:
    """Load JSONL and reject duplicate images or entity leakage across splits."""
    records: list[OpenWorldRecord] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON on manifest line {line_number}") from exc
        if not isinstance(payload, dict):
            raise ValueError(f"manifest line {line_number} must contain an object")
        records.append(OpenWorldRecord.from_dict(payload))
    if not records:
        raise ValueError("manifest must contain at least one record")
    image_ids = [record.image_id for record in records]
    if len(image_ids) != len(set(image_ids)):
        raise ValueError("manifest contains duplicate image_id values")
    entity_splits: dict[str, set[str]] = {}
    for record in records:
        entity_splits.setdefault(record.entity_id, set()).add(record.split)
    leaking = sorted(entity for entity, splits in entity_splits.items() if len(splits) > 1)
    if leaking:
        preview = ", ".join(leaking[:5])
        raise ValueError(f"entity_id values cross split boundaries: {preview}")
    return records
