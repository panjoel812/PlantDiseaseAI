"""Dataset statistics and exact duplicate detection."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

from plantdisease.data.dataset import ImageRecord


@dataclass(frozen=True)
class AuditReport:
    sample_count: int
    class_counts: dict[str, int]
    image_sizes: dict[str, int]
    color_modes: dict[str, int]
    duplicate_groups: tuple[tuple[str, ...], ...]
    invalid_samples: tuple[str, ...]


def _pixel_digest(record: ImageRecord) -> str:
    image = record.image.convert("RGB")
    digest = hashlib.sha256()
    digest.update(f"{image.width}x{image.height}:RGB".encode())
    digest.update(image.tobytes())
    return digest.hexdigest()


def audit_records(records: Sequence[ImageRecord], class_names: Sequence[str]) -> AuditReport:
    class_counts: Counter[str] = Counter()
    image_sizes: Counter[str] = Counter()
    color_modes: Counter[str] = Counter()
    hashes: dict[str, list[str]] = defaultdict(list)
    invalid_samples: list[str] = []

    for record in records:
        image_sizes[f"{record.image.width}x{record.image.height}"] += 1
        color_modes[record.image.mode] += 1
        hashes[_pixel_digest(record)].append(record.sample_id)
        if 0 <= record.label < len(class_names):
            class_counts[class_names[record.label]] += 1
        else:
            invalid_samples.append(f"{record.sample_id}: label {record.label} is out of range")

    duplicate_groups = tuple(
        sorted(tuple(sorted(sample_ids)) for sample_ids in hashes.values() if len(sample_ids) > 1)
    )
    return AuditReport(
        sample_count=len(records),
        class_counts=dict(sorted(class_counts.items())),
        image_sizes=dict(sorted(image_sizes.items())),
        color_modes=dict(sorted(color_modes.items())),
        duplicate_groups=duplicate_groups,
        invalid_samples=tuple(invalid_samples),
    )


def save_audit_report(report: AuditReport, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(asdict(report), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
