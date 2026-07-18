from __future__ import annotations

from PIL import Image, ImageDraw

from plantdisease.openworld.leaf_pipeline import isolate_leaf, prepare_leaf


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


def test_multiple_similar_leaf_components_are_rejected() -> None:
    image = Image.new("RGB", (240, 160), (25, 25, 27))
    draw = ImageDraw.Draw(image)
    draw.ellipse((15, 30, 108, 135), fill=(52, 145, 61))
    draw.ellipse((132, 25, 225, 130), fill=(55, 151, 65))

    result = isolate_leaf(image)

    assert result.accepted is False
    assert "multiple" in result.reason.lower()
