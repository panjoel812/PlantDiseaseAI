"""Build a six-species outline-only OOD set from the CC BY 4.0 UCI Leaf100 archive."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from zipfile import ZipFile

import cv2
import numpy as np
from PIL import Image, ImageDraw

from plantdisease.openworld.leaf_pipeline import LeafShapeFeatures

UCI_DATASET_URL = (
    "https://archive.ics.uci.edu/dataset/241/"
    "one%2Bhundred%2Bplant%2Bspecies%2Bleaves%2Bdata%2Bset"
)
UCI_ARCHIVE_SHA256 = "2313a70de450a8a6b81696174f52be1c037090af53b37c6a6313f11245e5fd4c"
ARCHIVE_PREFIX = "100 leaves plant species/data/"
CANONICAL_LEAF_RGB = (67, 145, 82)
NEUTRAL_BACKGROUND_RGB = (124, 124, 124)


@dataclass(frozen=True)
class ShapeOODSpecies:
    archive_name: str
    scientific_name: str
    split: str


SPECIES = (
    ShapeOODSpecies("Acer_Campestre", "Acer campestre", "ood_validation"),
    ShapeOODSpecies("Ginkgo_Biloba", "Ginkgo biloba", "ood_validation"),
    ShapeOODSpecies("Betula_Pendula", "Betula pendula", "ood_validation"),
    ShapeOODSpecies("Fagus_Sylvatica", "Fagus sylvatica", "ood_test"),
    ShapeOODSpecies("Liquidambar_Styraciflua", "Liquidambar styraciflua", "ood_test"),
    ShapeOODSpecies("Liriodendron_Tulipifera", "Liriodendron tulipifera", "ood_test"),
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/external_ood/uci_leaf100_leaf6_shape"),
    )
    args = parser.parse_args()
    if (args.output_dir / "prepared_manifest.jsonl").exists():
        raise FileExistsError("prepared manifest already exists; choose a new output directory")
    archive_sha = _sha256(args.archive)
    if archive_sha != UCI_ARCHIVE_SHA256:
        raise ValueError(f"unexpected UCI archive SHA-256: {archive_sha}")

    for name in ("raw_silhouettes", "species_inputs", "leaf_masks", "contact_sheets"):
        (args.output_dir / name).mkdir(parents=True, exist_ok=True)
    manifest_rows: list[dict[str, object]] = []
    source_rows: list[dict[str, object]] = []
    species_audit: list[dict[str, object]] = []
    with ZipFile(args.archive) as archive:
        members = sorted(archive.namelist())
        for species in SPECIES:
            prefix = f"{ARCHIVE_PREFIX}{species.archive_name}/"
            selected = [
                member
                for member in members
                if member.startswith(prefix) and member.lower().endswith(".jpg")
            ]
            if len(selected) != 16:
                raise ValueError(
                    f"{species.archive_name} has {len(selected)} images; expected exactly 16"
                )
            previews: list[tuple[str, Image.Image]] = []
            shape_rows: list[dict[str, object]] = []
            slug = species.scientific_name.lower().replace(" ", "-")
            for sample_index, member in enumerate(selected, start=1):
                image_bytes = archive.read(member)
                with Image.open(io.BytesIO(image_bytes)) as image:
                    grayscale = np.asarray(image.convert("L"), dtype=np.uint8)
                mask, shape, species_image = _prepare_silhouette(grayscale)
                sample_id = f"{slug}-{sample_index:02d}"
                raw_relative = Path("raw_silhouettes") / slug / f"{sample_id}.jpg"
                image_relative = Path("species_inputs") / slug / f"{sample_id}.png"
                mask_relative = Path("leaf_masks") / slug / f"{sample_id}.png"
                for relative in (raw_relative, image_relative, mask_relative):
                    (args.output_dir / relative).parent.mkdir(parents=True, exist_ok=True)
                (args.output_dir / raw_relative).write_bytes(image_bytes)
                species_image.save(args.output_dir / image_relative)
                Image.fromarray(mask, mode="L").save(args.output_dir / mask_relative)

                image_id = f"uci-leaf100-{sample_id}"
                manifest_rows.append(
                    {
                        "image_id": image_id,
                        "entity_id": image_id,
                        "image_path": image_relative.as_posix(),
                        "original_image_path": raw_relative.as_posix(),
                        "leaf_mask_path": mask_relative.as_posix(),
                        "plant_id": species.scientific_name,
                        "condition_id": None,
                        "split": species.split,
                        "source": UCI_DATASET_URL,
                        "license": "CC-BY-4.0",
                    }
                )
                source_rows.append(
                    {
                        "image_id": image_id,
                        "archive_member": member,
                        "plant_id": species.scientific_name,
                        "split": species.split,
                        "source": UCI_DATASET_URL,
                        "license": "CC-BY-4.0",
                        "raw_sha256": hashlib.sha256(image_bytes).hexdigest(),
                        "shape": asdict(shape),
                        "transformation": {
                            "input": "binary single-leaf silhouette supplied by UCI",
                            "output": "canonical green fill on neutral gray background",
                            "purpose": "outline-only stress test; no color or texture evidence",
                        },
                    }
                )
                shape_rows.append(asdict(shape))
                previews.append((sample_id, species_image))
            contact_relative = Path("contact_sheets") / f"{species.split}-{slug}.jpg"
            _save_contact_sheet(
                previews,
                args.output_dir / contact_relative,
                title=f"{species.scientific_name} | UCI silhouette proxy | {species.split}",
            )
            species_audit.append(
                {
                    **asdict(species),
                    "count": len(selected),
                    "contact_sheet": contact_relative.as_posix(),
                    "mean_shape": {
                        key: float(np.mean([float(row[key]) for row in shape_rows]))
                        for key in shape_rows[0]
                    },
                }
            )

    _write_jsonl(args.output_dir / "prepared_manifest.jsonl", manifest_rows)
    _write_jsonl(args.output_dir / "source_records.jsonl", source_rows)
    audit = {
        "schema_version": 1,
        "dataset_id": "uci-leaf100-six-species-outline-proxy-v1",
        "status": "completed-controlled-outline-proxy",
        "source": UCI_DATASET_URL,
        "doi": "10.24432/C5RG76",
        "license": "CC BY 4.0",
        "archive_sha256": archive_sha,
        "modality": "binary single-leaf silhouettes recolored deterministically",
        "sample_count": len(manifest_rows),
        "validation_species": [
            item.scientific_name for item in SPECIES if item.split == "ood_validation"
        ],
        "test_species": [
            item.scientific_name for item in SPECIES if item.split == "ood_test"
        ],
        "identity_isolation": "No species identity appears in both OOD splits.",
        "selection_contract": "All 16 published samples from each frozen species are used.",
        "species": species_audit,
        "limitations": [
            "These are controlled binary silhouettes, not field photographs.",
            (
                "Canonical green recoloring contains no real color, venation, "
                "lesion, or texture evidence."
            ),
            "Results test outline sensitivity and must not be called field OOD performance.",
        ],
    }
    (args.output_dir / "dataset_audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(audit, ensure_ascii=False))


def _prepare_silhouette(
    grayscale: np.ndarray,
) -> tuple[np.ndarray, LeafShapeFeatures, Image.Image]:
    if grayscale.ndim != 2 or min(grayscale.shape) < 32:
        raise ValueError("expected a two-dimensional leaf silhouette")
    mask = (grayscale >= 128).astype(np.uint8) * 255
    raw_contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(raw_contours, key=cv2.contourArea, reverse=True)
    if not contours:
        raise ValueError("silhouette contains no foreground component")
    primary = contours[0]
    area = float(cv2.contourArea(primary))
    total_area = sum(float(cv2.contourArea(contour)) for contour in contours)
    if area / max(area, total_area) < 0.98:
        raise ValueError("silhouette contains multiple foreground components")
    clean_mask = np.zeros_like(mask)
    cv2.drawContours(clean_mask, [primary], -1, 255, cv2.FILLED)
    x, y, width, height = cv2.boundingRect(primary)
    perimeter = float(cv2.arcLength(primary, True))
    hull_area = float(cv2.contourArea(cv2.convexHull(primary)))
    image_height, image_width = clean_mask.shape
    points = primary.reshape(-1, 2)
    border_touch = (
        (points[:, 0] <= 1)
        | (points[:, 0] >= image_width - 2)
        | (points[:, 1] <= 1)
        | (points[:, 1] >= image_height - 2)
    )
    shape = LeafShapeFeatures(
        area_pixels=round(area),
        coverage_percent=100.0 * area / (image_width * image_height),
        aspect_ratio=max(width, height) / max(1, min(width, height)),
        circularity=(4.0 * math.pi * area / (perimeter * perimeter)),
        solidity=area / hull_area,
        extent=area / (width * height),
        border_touch_ratio=float(np.mean(border_touch)),
        component_dominance=area / max(area, total_area),
    )
    canvas = np.empty((image_height, image_width, 3), dtype=np.uint8)
    canvas[:, :] = NEUTRAL_BACKGROUND_RGB
    canvas[clean_mask > 0] = CANONICAL_LEAF_RGB
    return clean_mask, shape, Image.fromarray(canvas, mode="RGB")


def _save_contact_sheet(
    rows: list[tuple[str, Image.Image]], path: Path, *, title: str
) -> None:
    cell_width, cell_height, columns = 240, 210, 4
    rows_count = (len(rows) + columns - 1) // columns
    canvas = Image.new("RGB", (columns * cell_width, 42 + rows_count * cell_height), "white")
    draw = ImageDraw.Draw(canvas)
    draw.text((12, 12), title, fill="black")
    for index, (sample_id, image) in enumerate(rows):
        left = (index % columns) * cell_width
        top = 42 + (index // columns) * cell_height
        preview = image.copy()
        preview.thumbnail((cell_width - 16, cell_height - 30))
        canvas.paste(preview, (left + (cell_width - preview.width) // 2, top + 2))
        draw.text((left + 8, top + cell_height - 22), sample_id, fill="black")
    canvas.save(path, quality=92)


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
        encoding="utf-8",
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


if __name__ == "__main__":
    main()
