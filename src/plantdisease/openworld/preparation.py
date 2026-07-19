"""Batch preparation of leaf-only species inputs and lesion-region crops."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from PIL import Image

from plantdisease.openworld.leaf_pipeline import prepare_leaf
from plantdisease.openworld.manifest import OpenWorldRecord


@dataclass(frozen=True)
class PreparationSummary:
    total_count: int
    accepted_count: int
    rejected_count: int
    output_manifest: str
    report_path: str


def prepare_leaf_manifest(
    records: list[OpenWorldRecord],
    *,
    image_root: Path,
    output_dir: Path,
) -> PreparationSummary:
    """Prepare a leaf-only dataset without modifying the original files."""

    if not records:
        raise ValueError("records must not be empty")
    output_dir.mkdir(parents=True, exist_ok=True)
    species_dir = output_dir / "species_inputs"
    mask_dir = output_dir / "leaf_masks"
    overlay_dir = output_dir / "lesion_overlays"
    crop_root = output_dir / "lesion_crops"
    for directory in (species_dir, mask_dir, overlay_dir, crop_root):
        directory.mkdir(parents=True, exist_ok=True)

    prepared_rows: list[dict[str, object]] = []
    report_rows: list[dict[str, object]] = []
    for index, record in enumerate(records):
        source_path = _resolve_inside(image_root, record.image_path)
        with Image.open(source_path) as source_image:
            prepared = prepare_leaf(source_image)
        row_id = f"{index:06d}"
        report_row: dict[str, object] = {
            "image_id": record.image_id,
            "accepted": prepared.isolation.accepted,
            "reason": prepared.isolation.reason,
            "method": prepared.isolation.method,
        }
        if prepared.isolation.shape is not None:
            report_row["shape"] = asdict(prepared.isolation.shape)
        if not prepared.isolation.accepted:
            report_rows.append(report_row)
            continue

        species_relative = Path("species_inputs") / f"{row_id}.png"
        mask_relative = Path("leaf_masks") / f"{row_id}.png"
        overlay_relative = Path("lesion_overlays") / f"{row_id}.jpg"
        assert prepared.isolation.species_image is not None
        assert prepared.lesions is not None
        prepared.isolation.species_image.save(output_dir / species_relative)
        Image.fromarray(prepared.isolation.mask, mode="L").save(output_dir / mask_relative)
        prepared.lesions.overlay.save(output_dir / overlay_relative, quality=92)

        crop_paths: list[str] = []
        sample_crop_dir = crop_root / row_id
        if prepared.lesion_crops:
            sample_crop_dir.mkdir(parents=True, exist_ok=True)
        for crop_index, crop in enumerate(prepared.lesion_crops, start=1):
            crop_relative = Path("lesion_crops") / row_id / f"{crop_index:02d}.jpg"
            crop.save(output_dir / crop_relative, quality=92)
            crop_paths.append(crop_relative.as_posix())

        prepared_rows.append(
            {
                "image_id": record.image_id,
                "entity_id": record.entity_id,
                "image_path": species_relative.as_posix(),
                "original_image_path": record.image_path,
                "leaf_mask_path": mask_relative.as_posix(),
                "lesion_crop_paths": crop_paths,
                "plant_id": record.plant_id,
                "family_id": record.family_id,
                "genus_id": record.genus_id,
                "condition_id": record.condition_id,
                "split": record.split,
                "source": record.source,
                "license": record.license,
                "site_id": record.site_id,
                "observer_id": record.observer_id,
            }
        )
        report_row.update(
            {
                "species_image_path": species_relative.as_posix(),
                "leaf_mask_path": mask_relative.as_posix(),
                "lesion_overlay_path": overlay_relative.as_posix(),
                "lesion_crop_count": len(crop_paths),
            }
        )
        report_rows.append(report_row)

    manifest_path = output_dir / "prepared_manifest.jsonl"
    manifest_path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in prepared_rows)
        + ("\n" if prepared_rows else ""),
        encoding="utf-8",
    )
    report_path = output_dir / "preparation_report.json"
    summary = PreparationSummary(
        total_count=len(records),
        accepted_count=len(prepared_rows),
        rejected_count=len(records) - len(prepared_rows),
        output_manifest=str(manifest_path),
        report_path=str(report_path),
    )
    report_path.write_text(
        json.dumps({"summary": asdict(summary), "records": report_rows}, indent=2),
        encoding="utf-8",
    )
    return summary


def _resolve_inside(root: Path, relative_path: str) -> Path:
    resolved_root = root.resolve()
    resolved = (resolved_root / relative_path).resolve()
    if not resolved.is_relative_to(resolved_root):
        raise ValueError("image_path must stay inside image_root")
    return resolved


__all__ = ["PreparationSummary", "prepare_leaf_manifest"]
