"""Download and isolate a small, licensed six-species external OOD leaf set."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import time
from collections import Counter
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from urllib.request import Request, urlopen

from PIL import Image, ImageDraw, UnidentifiedImageError

from plantdisease.openworld.inaturalist import (
    EXTERNAL_LEAF_SPECIES,
    LicensedObservationPhoto,
    build_observations_url,
    parse_observation_photos,
)
from plantdisease.openworld.leaf_pipeline import prepare_leaf

USER_AGENT = "PlantDiseaseAI-OpenLeaf-Research/0.1 (license-audited small batch)"
MAX_IMAGE_BYTES = 12 * 1024 * 1024


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/external_ood/inaturalist_leaf6"),
    )
    parser.add_argument("--accepted-per-species", type=int, default=12)
    parser.add_argument("--max-candidates-per-species", type=int, default=120)
    parser.add_argument("--cutoff-date", default="2025-12-31")
    parser.add_argument("--timeout", type=float, default=45.0)
    args = parser.parse_args()
    if args.accepted_per_species <= 0:
        raise ValueError("accepted-per-species must be positive")
    if args.max_candidates_per_species < args.accepted_per_species:
        raise ValueError("max-candidates-per-species must cover the accepted target")
    if (args.output_dir / "candidate_manifest.jsonl").exists():
        raise FileExistsError(
            "candidate manifest already exists; choose a new output directory to preserve the audit"
        )

    directories = {
        name: args.output_dir / name
        for name in (
            "raw",
            "species_inputs",
            "leaf_masks",
            "lesion_overlays",
            "contact_sheets",
        )
    }
    for directory in directories.values():
        directory.mkdir(parents=True, exist_ok=True)

    retrieved_at = datetime.now(UTC).isoformat()
    manifest_rows: list[dict[str, object]] = []
    source_rows: list[dict[str, object]] = []
    species_audits: list[dict[str, object]] = []
    for species_index, species in enumerate(EXTERNAL_LEAF_SPECIES):
        api_url = build_observations_url(
            species.scientific_name,
            cutoff_date=args.cutoff_date,
        )
        payload = _fetch_json(api_url, timeout=args.timeout)
        photos = parse_observation_photos(payload, expected_species=species.scientific_name)
        slug = _slug(species.scientific_name)
        accepted_rows: list[tuple[LicensedObservationPhoto, Image.Image]] = []
        rejection_reasons: Counter[str] = Counter()
        attempted = 0
        for photo in photos[: args.max_candidates_per_species]:
            attempted += 1
            try:
                image_bytes = _fetch_bytes(photo.image_url, timeout=args.timeout)
                with Image.open(io.BytesIO(image_bytes)) as opened:
                    image = opened.convert("RGB")
            except (OSError, UnidentifiedImageError, ValueError) as exc:
                rejection_reasons[f"download/decode: {type(exc).__name__}"] += 1
                continue
            prepared = prepare_leaf(image)
            if not prepared.isolation.accepted:
                rejection_reasons[prepared.isolation.reason] += 1
                continue

            suffix = Path(photo.image_url).suffix.lower()
            if suffix not in {".jpg", ".jpeg", ".png"}:
                suffix = ".jpg"
            raw_relative = Path("raw") / slug / f"{photo.photo_id}{suffix}"
            species_relative = Path("species_inputs") / slug / f"{photo.photo_id}.png"
            mask_relative = Path("leaf_masks") / slug / f"{photo.photo_id}.png"
            overlay_relative = Path("lesion_overlays") / slug / f"{photo.photo_id}.jpg"
            for relative in (raw_relative, species_relative, mask_relative, overlay_relative):
                (args.output_dir / relative).parent.mkdir(parents=True, exist_ok=True)
            (args.output_dir / raw_relative).write_bytes(image_bytes)
            assert prepared.isolation.species_image is not None
            assert prepared.isolation.shape is not None
            assert prepared.lesions is not None
            prepared.isolation.species_image.save(args.output_dir / species_relative)
            Image.fromarray(prepared.isolation.mask, mode="L").save(
                args.output_dir / mask_relative
            )
            prepared.lesions.overlay.save(args.output_dir / overlay_relative, quality=92)

            image_id = f"inaturalist-photo-{photo.photo_id}"
            manifest_rows.append(
                {
                    "image_id": image_id,
                    "entity_id": f"inaturalist-observation-{photo.observation_id}",
                    "image_path": species_relative.as_posix(),
                    "original_image_path": raw_relative.as_posix(),
                    "leaf_mask_path": mask_relative.as_posix(),
                    "plant_id": photo.scientific_name,
                    "condition_id": None,
                    "split": species.split,
                    "source": photo.observation_url,
                    "license": photo.license_code.upper(),
                }
            )
            source_rows.append(
                {
                    **asdict(photo),
                    "image_id": image_id,
                    "split": species.split,
                    "retrieved_at": retrieved_at,
                    "api_cutoff_date": args.cutoff_date,
                    "raw_sha256": hashlib.sha256(image_bytes).hexdigest(),
                    "leaf_isolation": {
                        "method": prepared.isolation.method,
                        "reason": prepared.isolation.reason,
                        "bounding_box": prepared.isolation.bounding_box,
                        "shape": asdict(prepared.isolation.shape),
                    },
                    "visible_lesion_candidate_count": len(prepared.lesions.regions),
                }
            )
            accepted_rows.append((photo, prepared.isolation.species_image.copy()))
            if len(accepted_rows) == args.accepted_per_species:
                break
        if len(accepted_rows) < args.accepted_per_species:
            raise RuntimeError(
                f"{species.scientific_name}: only {len(accepted_rows)} accepted leaves "
                f"from {attempted} candidates; target is {args.accepted_per_species}"
            )
        contact_path = Path("contact_sheets") / f"{species.split}-{slug}.jpg"
        _save_contact_sheet(
            accepted_rows,
            args.output_dir / contact_path,
            title=f"{species.scientific_name} | {species.split}",
        )
        species_audits.append(
            {
                **asdict(species),
                "api_url": api_url,
                "available_open_observations": int(payload.get("total_results", 0)),
                "parsed_licensed_photos": len(photos),
                "attempted": attempted,
                "accepted": len(accepted_rows),
                "rejected": attempted - len(accepted_rows),
                "acceptance_rate": len(accepted_rows) / attempted,
                "rejection_reasons": dict(rejection_reasons),
                "contact_sheet": contact_path.as_posix(),
            }
        )
        if species_index + 1 < len(EXTERNAL_LEAF_SPECIES):
            time.sleep(1.05)

    _write_jsonl(args.output_dir / "candidate_manifest.jsonl", manifest_rows)
    _write_jsonl(args.output_dir / "candidate_source_records.jsonl", source_rows)
    total_attempted = sum(int(row["attempted"]) for row in species_audits)
    total_accepted = sum(int(row["accepted"]) for row in species_audits)
    audit = {
        "schema_version": 1,
        "dataset_id": "inaturalist-external-leaf6-cutoff-2025-12-31-v1",
        "status": "candidate-only-requires-visual-audit",
        "source": "iNaturalist API v2 and iNaturalist Open Data image host",
        "retrieved_at": retrieved_at,
        "cutoff_date": args.cutoff_date,
        "license_allowlist": ["CC0", "CC-BY", "CC-BY-SA"],
        "selection_contract": (
            "research-grade exact species; one open photo per observation; "
            "deterministic ID order; OpenCV candidates only, not verified single leaves"
        ),
        "visual_audit_required": (
            "Field backgrounds can merge with the foreground mask. Do not rename the "
            "candidate manifest or use it for metrics before a recorded visual audit."
        ),
        "privacy": "No coordinates are requested or stored.",
        "validation_species": [
            item.scientific_name
            for item in EXTERNAL_LEAF_SPECIES
            if item.split == "ood_validation"
        ],
        "test_species": [
            item.scientific_name
            for item in EXTERNAL_LEAF_SPECIES
            if item.split == "ood_test"
        ],
        "attempted": total_attempted,
        "accepted": total_accepted,
        "rejected": total_attempted - total_accepted,
        "acceptance_rate": total_accepted / total_attempted,
        "species": species_audits,
    }
    (args.output_dir / "download_audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(audit, ensure_ascii=False))


def _fetch_json(url: str, *, timeout: float) -> dict[str, object]:
    payload = json.loads(_fetch_bytes(url, timeout=timeout))
    if not isinstance(payload, dict):
        raise ValueError("expected an object response from iNaturalist")
    return payload


def _fetch_bytes(url: str, *, timeout: float) -> bytes:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=timeout) as response:  # noqa: S310 - fixed HTTPS source
        content_length = response.headers.get("Content-Length")
        if content_length and int(content_length) > MAX_IMAGE_BYTES:
            raise ValueError("remote object exceeds the size limit")
        payload = response.read(MAX_IMAGE_BYTES + 1)
    if len(payload) > MAX_IMAGE_BYTES:
        raise ValueError("remote object exceeds the size limit")
    return payload


def _save_contact_sheet(
    rows: list[tuple[LicensedObservationPhoto, Image.Image]],
    path: Path,
    *,
    title: str,
) -> None:
    cell_width, cell_height = 280, 230
    columns = 4
    rows_count = (len(rows) + columns - 1) // columns
    canvas = Image.new("RGB", (columns * cell_width, 42 + rows_count * cell_height), "white")
    draw = ImageDraw.Draw(canvas)
    draw.text((12, 12), title, fill="black")
    for index, (photo, image) in enumerate(rows):
        column = index % columns
        row = index // columns
        left = column * cell_width
        top = 42 + row * cell_height
        preview = image.copy()
        preview.thumbnail((cell_width - 16, cell_height - 34))
        x = left + (cell_width - preview.width) // 2
        canvas.paste(preview, (x, top + 4))
        draw.text((left + 8, top + cell_height - 24), f"photo {photo.photo_id}", fill="black")
    path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(path, quality=92)


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
        encoding="utf-8",
    )


def _slug(value: str) -> str:
    return "-".join(value.lower().split())


if __name__ == "__main__":
    main()
