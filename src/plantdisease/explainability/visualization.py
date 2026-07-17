"""Visualization helpers for Grad-CAM heatmaps and atlas panels."""

from __future__ import annotations

import re
from collections.abc import Mapping
from pathlib import Path
from typing import cast

import numpy as np
import torch
from matplotlib import colormaps
from PIL import Image, ImageDraw


def safe_filename(value: object) -> str:
    """Return a filesystem-friendly name fragment."""
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(value)).strip("_")
    return cleaned or "item"


def _heatmap_array(heatmap: torch.Tensor | np.ndarray) -> np.ndarray:
    array = heatmap.detach().cpu().numpy() if isinstance(heatmap, torch.Tensor) else heatmap
    array = np.asarray(array, dtype=np.float32)
    if array.ndim == 3 and array.shape[0] == 1:
        array = array[0]
    if array.ndim != 2:
        raise ValueError("heatmap must be two-dimensional")
    if not np.isfinite(array).all():
        raise ValueError("heatmap must contain finite values")
    return np.clip(array, 0.0, 1.0)


def heatmap_to_image(
    heatmap: torch.Tensor | np.ndarray,
    *,
    colormap: str = "turbo",
) -> Image.Image:
    """Convert a normalized heatmap to an RGB color image."""
    array = _heatmap_array(heatmap)
    colored = colormaps[colormap](array)[..., :3]
    return Image.fromarray((colored * 255).astype(np.uint8))


def overlay_heatmap(
    image: Image.Image,
    heatmap: torch.Tensor | np.ndarray,
    *,
    alpha: float = 0.45,
    colormap: str = "turbo",
) -> Image.Image:
    """Blend a colorized heatmap over a resized RGB image."""
    if not 0.0 <= alpha <= 1.0:
        raise ValueError("alpha must be in [0, 1]")
    heatmap_image = heatmap_to_image(heatmap, colormap=colormap)
    base = image.convert("RGB").resize(heatmap_image.size, Image.Resampling.BILINEAR)
    return Image.blend(base, heatmap_image, alpha)


def save_gradcam_panel(
    *,
    original: Image.Image,
    heatmap_image: Image.Image,
    overlay: Image.Image,
    metadata: Mapping[str, object],
    output_path: Path,
) -> None:
    """Save a compact original/heatmap/overlay panel with sample metadata."""
    original = original.convert("RGB").resize(overlay.size, Image.Resampling.BILINEAR)
    heatmap_image = heatmap_image.convert("RGB").resize(overlay.size, Image.Resampling.BILINEAR)
    overlay = overlay.convert("RGB")
    width, height = overlay.size
    header_height = 86
    label_height = 24
    margin = 8
    canvas_width = max(width * 3 + margin * 4, 1100)
    canvas = Image.new(
        "RGB",
        (canvas_width, header_height + height + label_height + margin),
        "white",
    )
    draw = ImageDraw.Draw(canvas)
    header = [
        (
            f"group={metadata['group']} "
            f"sample={metadata['sample_id']} "
            f"test_index={metadata['test_index']}"
        ),
        f"true={metadata['true_class_name']}",
        (
            f"pred={metadata['predicted_class_name']} "
            f"confidence={float(cast(int | float | str, metadata['confidence'])):.4f} "
            f"target={metadata['target_class_name']}"
        ),
    ]
    y = margin
    for line in header:
        draw.text((margin, y), line, fill="black")
        y += 22
    for index, (label, panel) in enumerate(
        [
            ("original", original),
            ("heatmap", heatmap_image),
            ("overlay", overlay),
        ]
    ):
        x = margin + index * (width + margin)
        canvas.paste(panel, (x, header_height))
        draw.text((x, header_height + height + 3), label, fill="black")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path)
