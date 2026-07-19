from __future__ import annotations

import json
from pathlib import Path

import pytest

from plantdisease.openworld.manifest import load_manifest


def _write(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")


def test_manifest_loads_plant_condition_and_license_fields(tmp_path: Path) -> None:
    path = tmp_path / "manifest.jsonl"
    _write(
        path,
        [
            {
                "image_id": "img-1",
                "entity_id": "observation-1",
                "image_path": "images/img-1.jpg",
                "plant_id": "vitis_vinifera",
                "family_id": "vitaceae",
                "genus_id": "vitis",
                "condition_id": "black_rot",
                "split": "train",
                "source": "example",
                "license": "CC-BY-4.0",
            }
        ],
    )

    records = load_manifest(path)

    assert records[0].plant_id == "vitis_vinifera"
    assert records[0].condition_id == "black_rot"
    assert records[0].entity_id == "observation-1"
    assert records[0].family_id == "vitaceae"
    assert records[0].genus_id == "vitis"


def test_manifest_rejects_entity_leakage_between_splits(tmp_path: Path) -> None:
    path = tmp_path / "manifest.jsonl"
    common = {
        "entity_id": "same-observation",
        "image_path": "image.jpg",
        "plant_id": "vitis_vinifera",
        "condition_id": None,
        "source": "example",
        "license": "CC-BY-4.0",
    }
    _write(
        path,
        [
            {**common, "image_id": "img-1", "split": "train"},
            {**common, "image_id": "img-2", "split": "test"},
        ],
    )

    with pytest.raises(ValueError, match="cross split"):
        load_manifest(path)
