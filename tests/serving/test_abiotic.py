from __future__ import annotations

import numpy as np
import pytest
from PIL import Image, ImageDraw

from plantdisease.serving.abiotic import analyze_corn_abiotic_pattern


def _corn_leaf() -> tuple[Image.Image, np.ndarray]:
    image = Image.new("RGB", (360, 180), (26, 28, 31))
    mask_image = Image.new("L", image.size, 0)
    ImageDraw.Draw(mask_image).ellipse((18, 42, 342, 138), fill=255)
    mask = np.asarray(mask_image, dtype=np.uint8)
    rgb = np.asarray(image, dtype=np.uint8).copy()
    rgb[mask > 0] = (55, 148, 64)
    return Image.fromarray(rgb, mode="RGB"), mask


def _continuous_midrib_stress() -> tuple[Image.Image, np.ndarray]:
    image, mask = _corn_leaf()
    draw = ImageDraw.Draw(image)
    draw.polygon(
        ((38, 90), (88, 70), (320, 81), (340, 90), (320, 99), (88, 110)),
        fill=(221, 191, 61),
    )
    draw.polygon(
        ((82, 86), (310, 86), (336, 90), (310, 94), (82, 94)),
        fill=(150, 87, 43),
    )
    return image, mask


def _scattered_off_axis_spots() -> tuple[Image.Image, np.ndarray]:
    image, mask = _corn_leaf()
    draw = ImageDraw.Draw(image)
    for box in (
        (72, 54, 100, 68),
        (132, 112, 165, 128),
        (202, 51, 234, 67),
        (258, 111, 292, 128),
        (296, 60, 321, 74),
        (42, 106, 68, 122),
    ):
        draw.rounded_rectangle(box, radius=4, fill=(190, 150, 91))
    return image, mask


def test_continuous_midrib_pattern_is_flagged_as_suspected_abiotic_stress() -> None:
    image, mask = _continuous_midrib_stress()

    result = analyze_corn_abiotic_pattern(image, mask)

    assert result.status == "suspected_abiotic_nutrient_stress"
    assert result.suspected is True
    assert result.abnormal_coverage_percent >= 8.0
    assert result.central_axis_share >= 0.55
    assert result.longitudinal_continuity >= 0.60
    assert result.bilateral_similarity >= 0.50
    assert result.off_axis_lesion_coverage_percent < 5.0
    assert result.overlay.mode == "RGB"
    assert result.overlay.size == image.size
    assert "cannot identify a specific nutrient" in result.reason.lower()


def test_scattered_off_axis_spots_do_not_trigger_abiotic_gate() -> None:
    image, mask = _scattered_off_axis_spots()

    result = analyze_corn_abiotic_pattern(image, mask)

    assert result.suspected is False
    assert result.status == "unknown_visible_stress"
    assert (
        result.central_axis_share < result.central_axis_share_threshold
        or result.off_axis_lesion_coverage_percent
        >= result.off_axis_lesion_coverage_threshold
    )


def test_uniform_healthy_leaf_fails_abnormal_coverage_gate() -> None:
    image, mask = _corn_leaf()

    result = analyze_corn_abiotic_pattern(image, mask)

    assert result.suspected is False
    assert result.status == "unknown_visible_stress"
    assert result.abnormal_coverage_percent == 0.0
    assert "abnormal coverage" in result.reason.lower()


def test_empty_mask_returns_explicit_unknown_evidence() -> None:
    image = Image.new("RGB", (80, 64), (30, 32, 34))

    result = analyze_corn_abiotic_pattern(
        image,
        np.zeros((64, 80), dtype=np.uint8),
    )

    assert result.suspected is False
    assert result.status == "unknown_visible_stress"
    assert result.abnormal_coverage_percent == 0.0
    assert "empty" in result.reason.lower()


def test_mask_shape_must_match_image() -> None:
    image = Image.new("RGB", (80, 64), (30, 32, 34))

    with pytest.raises(ValueError, match="mask shape"):
        analyze_corn_abiotic_pattern(
            image,
            np.zeros((32, 40), dtype=np.uint8),
        )
