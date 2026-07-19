from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw

from plantdisease.openworld.manifest import OpenWorldRecord, load_manifest
from plantdisease.openworld.preparation import prepare_leaf_manifest


def test_batch_preparation_exports_only_accepted_leaf_inputs(tmp_path: Path) -> None:
    image_root = tmp_path / "raw"
    image_root.mkdir()
    leaf = Image.new("RGB", (180, 140), (25, 26, 28))
    draw = ImageDraw.Draw(leaf)
    draw.ellipse((24, 15, 158, 126), fill=(55, 150, 63))
    draw.ellipse((70, 56, 93, 75), fill=(194, 150, 92))
    leaf.save(image_root / "leaf.png")
    Image.new("RGB", (180, 140), (25, 26, 28)).save(image_root / "blank.png")
    records = [
        OpenWorldRecord(
            "leaf-1",
            "leaf.png",
            "vitis_vinifera",
            "black_rot",
            "train",
            "licensed-source",
            "CC-BY-4.0",
            "entity-1",
        ),
        OpenWorldRecord(
            "blank-1",
            "blank.png",
            "__unknown__",
            None,
            "ood_validation",
            "licensed-source",
            "CC-BY-4.0",
            "entity-2",
        ),
    ]
    output_dir = tmp_path / "prepared"

    summary = prepare_leaf_manifest(records, image_root=image_root, output_dir=output_dir)
    prepared_records = load_manifest(output_dir / "prepared_manifest.jsonl")
    report = json.loads((output_dir / "preparation_report.json").read_text())

    assert summary.accepted_count == 1
    assert summary.rejected_count == 1
    assert len(prepared_records) == 1
    assert prepared_records[0].original_image_path == "leaf.png"
    assert prepared_records[0].leaf_mask_path == "leaf_masks/000000.png"
    assert (output_dir / prepared_records[0].image_path).is_file()
    assert (output_dir / prepared_records[0].leaf_mask_path).is_file()
    assert report["records"][1]["accepted"] is False
