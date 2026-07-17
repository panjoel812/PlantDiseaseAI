"""Reproducible exploratory data analysis figures."""

from __future__ import annotations

import math
import os
from collections import Counter
from collections.abc import Sequence
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path.cwd() / ".cache" / "matplotlib"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from plantdisease.data.dataset import ImageRecord  # noqa: E402


def generate_eda(
    records: Sequence[ImageRecord],
    class_names: Sequence[str],
    output_dir: Path,
    max_samples: int = 12,
) -> dict[str, Path]:
    if not records:
        raise ValueError("records must not be empty")
    if max_samples <= 0:
        raise ValueError("max_samples must be positive")
    if any(record.label < 0 or record.label >= len(class_names) for record in records):
        raise ValueError("record label is outside class_names range")
    output_dir.mkdir(parents=True, exist_ok=True)

    artifacts = {
        "class_distribution": output_dir / "class_distribution.png",
        "image_size_distribution": output_dir / "image_size_distribution.png",
        "sample_grid": output_dir / "sample_grid.png",
    }

    counts = Counter(class_names[record.label] for record in records)
    names = [name for name in class_names if counts[name] > 0]
    figure, axis = plt.subplots(figsize=(max(7, len(names) * 0.35), 4))
    axis.bar(range(len(names)), [counts[name] for name in names], color="#4f8f57")
    axis.set_xticks(range(len(names)), names, rotation=75, ha="right")
    axis.set_ylabel("Samples")
    axis.set_title("Class distribution")
    figure.tight_layout()
    figure.savefig(artifacts["class_distribution"], dpi=160)
    plt.close(figure)

    widths = [record.image.width for record in records]
    heights = [record.image.height for record in records]
    figure, axis = plt.subplots(figsize=(6, 4))
    axis.scatter(widths, heights, alpha=0.45, color="#7d4e2d")
    axis.set_xlabel("Width (px)")
    axis.set_ylabel("Height (px)")
    axis.set_title("Image size distribution")
    figure.tight_layout()
    figure.savefig(artifacts["image_size_distribution"], dpi=160)
    plt.close(figure)

    selected = list(records[: min(max_samples, len(records))])
    columns = min(4, len(selected))
    rows = math.ceil(len(selected) / columns)
    figure, axes = plt.subplots(rows, columns, figsize=(columns * 3, rows * 3), squeeze=False)
    for axis, record in zip(axes.flat, selected, strict=False):
        axis.imshow(record.image.convert("RGB"))
        axis.set_title(class_names[record.label], fontsize=9)
        axis.axis("off")
    for axis in list(axes.flat)[len(selected) :]:
        axis.axis("off")
    figure.tight_layout()
    figure.savefig(artifacts["sample_grid"], dpi=160)
    plt.close(figure)
    return artifacts
