from __future__ import annotations

from PIL import Image, ImageDraw

from plantdisease.training.crop import _balanced_isolated_leaf_indices


def _leaf() -> Image.Image:
    image = Image.new("RGB", (120, 96), (25, 26, 28))
    ImageDraw.Draw(image).ellipse((14, 8, 106, 88), fill=(55, 150, 63))
    return image


def test_balanced_leaf_selection_filters_failures_without_losing_classes() -> None:
    split = [
        {"image": Image.new("RGB", (120, 96), (25, 26, 28)), "label": 0},
        {"image": _leaf(), "label": 0},
        {"image": _leaf(), "label": 0},
        {"image": _leaf(), "label": 1},
        {"image": _leaf(), "label": 1},
    ]

    selected, audit = _balanced_isolated_leaf_indices(
        split,
        [0, 0, 0, 1, 1],
        [0, 1],
        ["Grape", "Tomato"],
        per_crop=2,
        seed=42,
    )

    assert len(selected) == 4
    assert sum(split[index]["label"] == 0 for index in selected) == 2
    assert sum(split[index]["label"] == 1 for index in selected) == 2
    assert audit["accepted"] == 4
    assert audit["rejected"] == 1
    assert audit["per_crop"]["Grape"]["rejected"] == 1
