from __future__ import annotations

import math

import pytest
from PIL import Image, ImageDraw

from plantdisease.openworld.leaf_pipeline import TargetPoint, isolate_leaf, prepare_leaf


def _clear_leaf() -> Image.Image:
    image = Image.new("RGB", (240, 180), (27, 29, 31))
    draw = ImageDraw.Draw(image)
    draw.ellipse((30, 20, 210, 160), fill=(58, 156, 65))
    draw.ellipse((73, 62, 101, 82), fill=(188, 145, 89))
    draw.ellipse((142, 98, 182, 124), fill=(215, 185, 126))
    return image


def test_clear_leaf_isolated_before_lesion_crops_are_created() -> None:
    prepared = prepare_leaf(_clear_leaf())

    assert prepared.isolation.accepted is True
    assert prepared.isolation.species_image is not None
    assert prepared.isolation.cutout_rgba is not None
    assert prepared.isolation.shape is not None
    assert prepared.isolation.shape.component_dominance == 1.0
    assert prepared.isolation.mask.shape == (180, 240)
    assert prepared.lesions is not None
    assert prepared.lesions.lesion_count >= 2
    assert len(prepared.lesion_crops) >= 2


def test_non_leaf_image_is_rejected_before_any_condition_work() -> None:
    result = prepare_leaf(Image.new("RGB", (120, 96), (32, 32, 34)))

    assert result.isolation.accepted is False
    assert result.isolation.species_image is None
    assert result.lesions is None
    assert result.lesion_crops == ()


def test_automatic_isolation_requests_target_when_components_are_ambiguous() -> None:
    image = Image.new("RGB", (240, 160), (25, 25, 27))
    draw = ImageDraw.Draw(image)
    draw.ellipse((15, 30, 108, 135), fill=(52, 145, 61))
    draw.ellipse((132, 25, 225, 130), fill=(55, 151, 65))

    result = isolate_leaf(image)

    assert result.accepted is False
    assert result.selection_mode == "automatic"
    assert result.target_point is None
    assert result.purity.accepted is False
    assert result.purity.fragment_count == 2
    assert result.shape is not None
    assert result.shape.component_dominance < 0.90
    assert "select one target leaf" in result.reason.lower()


@pytest.mark.parametrize(
    ("x", "y"),
    [
        (-0.01, 0.5),
        (1.01, 0.5),
        (0.5, -0.01),
        (0.5, 1.01),
        (math.nan, 0.5),
        (0.5, math.inf),
    ],
)
def test_target_point_rejects_non_finite_or_out_of_range_coordinates(
    x: float,
    y: float,
) -> None:
    with pytest.raises(ValueError, match="finite numbers between 0 and 1"):
        TargetPoint(x=x, y=y)


def test_target_point_accepts_inclusive_image_edges() -> None:
    assert TargetPoint(x=0.0, y=0.0) == TargetPoint(x=0.0, y=0.0)
    assert TargetPoint(x=1.0, y=1.0) == TargetPoint(x=1.0, y=1.0)


def _overlapping_leaf_scene() -> Image.Image:
    image = Image.new("RGB", (320, 220), (25, 27, 31))
    draw = ImageDraw.Draw(image)
    draw.ellipse((205, 20, 295, 205), fill=(38, 112, 88))
    draw.polygon(
        ((25, 171), (41, 190), (270, 49), (252, 31)),
        fill=(64, 168, 68),
    )
    return image


def test_click_seed_selects_target_leaf_from_overlapping_scene() -> None:
    result = isolate_leaf(
        _overlapping_leaf_scene(),
        target_point=TargetPoint(x=0.38, y=0.52),
    )

    assert result.accepted is True
    assert result.selection_mode == "click_grabcut"
    assert result.target_point == TargetPoint(x=0.38, y=0.52)
    assert result.purity.accepted is True
    assert result.purity.click_contained is True
    assert result.purity.probable_foreground_retention is not None
    assert result.purity.probable_foreground_retention >= 0.60
    assert result.species_image is not None


def test_click_on_background_is_rejected_before_grabcut() -> None:
    result = isolate_leaf(
        _overlapping_leaf_scene(),
        target_point=TargetPoint(x=0.95, y=0.05),
    )

    assert result.accepted is False
    assert result.selection_mode == "click_grabcut"
    assert result.purity.click_contained is False
    assert result.species_image is None


def test_click_selected_leaf_truncated_by_border_is_rejected() -> None:
    image = Image.new("RGB", (240, 180), (25, 27, 31))
    draw = ImageDraw.Draw(image)
    draw.ellipse((-65, 35, 185, 155), fill=(59, 158, 66))

    result = isolate_leaf(image, target_point=TargetPoint(x=0.28, y=0.52))

    assert result.accepted is False
    assert result.purity.border_touch_ratio > 0.18
    assert "truncated" in result.reason.lower()


def test_click_selected_branched_mask_fails_axis_purity() -> None:
    image = Image.new("RGB", (820, 300), (25, 27, 31))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((20, 135, 800, 160), radius=12, fill=(58, 158, 66))
    draw.rounded_rectangle((500, 155, 600, 285), radius=18, fill=(58, 158, 66))

    result = isolate_leaf(image, target_point=TargetPoint(x=0.30, y=0.49))

    assert result.accepted is False
    assert result.purity.principal_axis_aspect_ratio >= 2.0
    assert result.purity.axis_band_retention is not None
    assert result.purity.axis_band_retention < 0.80
    assert "axis" in result.reason.lower()
