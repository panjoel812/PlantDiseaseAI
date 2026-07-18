from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw

from plantdisease.serving.lesions import LESION_METHOD, analyze_lesions


def test_analyze_lesions_reports_scaled_geometry_and_overlay() -> None:
    image = Image.new("RGB", (240, 160), (28, 28, 30))
    draw = ImageDraw.Draw(image)
    draw.ellipse((22, 18, 218, 145), fill=(58, 151, 62))
    draw.ellipse((62, 52, 91, 73), fill=(190, 151, 96))
    draw.ellipse((132, 82, 180, 110), fill=(214, 187, 132))

    result = analyze_lesions(image)

    assert result.method == LESION_METHOD
    assert result.image_size == (240, 160)
    assert result.leaf_area_pixels > 0
    assert result.lesion_count >= 2
    assert result.lesion_coverage_percent > 0.0
    assert result.largest_lesion_area_percent > result.median_lesion_area_percent / 2
    assert result.regions
    assert result.dominant_colors
    assert result.overlay.size == image.size
    assert result.overlay.mode == "RGB"


def test_analyze_lesions_returns_explicit_empty_evidence_without_green_leaf() -> None:
    image = Image.new("RGB", (80, 64), (25, 25, 25))

    result = analyze_lesions(image)

    assert result.leaf_area_pixels == 0
    assert result.lesion_count == 0
    assert result.distribution == "leaf not isolated"


def test_analyze_lesions_accepts_a_precomputed_leaf_mask() -> None:
    image = Image.new("RGB", (100, 80), (25, 25, 25))
    draw = ImageDraw.Draw(image)
    draw.ellipse((15, 10, 85, 70), fill=(61, 151, 63))
    draw.ellipse((42, 32, 58, 46), fill=(198, 155, 98))
    mask_image = Image.new("L", image.size, 0)
    ImageDraw.Draw(mask_image).ellipse((15, 10, 85, 70), fill=255)

    result = analyze_lesions(image, leaf_mask=np.asarray(mask_image))

    assert result.leaf_area_pixels > 0
    assert result.lesion_count >= 1
