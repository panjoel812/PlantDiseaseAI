from __future__ import annotations

import numpy as np
import pytest
from PIL import Image

from plantdisease.inference import Prediction
from plantdisease.serving.disease_focus import (
    extract_lesion_views,
    fuse_lesion_predictions,
    should_focus_lesions,
)
from plantdisease.serving.hierarchy import build_taxonomy_hierarchy
from plantdisease.serving.lesions import LesionAnalysis, LesionRegion


def _analysis(coverage: float = 12.42) -> LesionAnalysis:
    regions = (
        LesionRegion(20, 18, 28, 24, 34.0, 30.0, 500, 2.0, 0.7, 1.2, "oval", "tan"),
        LesionRegion(55, 42, 20, 18, 65.0, 51.0, 350, 1.4, 0.6, 1.1, "oval", "tan"),
    )
    return LesionAnalysis(
        method="opencv_exg_hsv_components_v1",
        image_size=(100, 80),
        leaf_area_pixels=4_000,
        leaf_coverage_percent=50.0,
        lesion_area_pixels=850,
        lesion_coverage_percent=coverage,
        lesion_count=2,
        median_lesion_area_percent=1.7,
        largest_lesion_area_percent=2.0,
        mean_circularity=0.65,
        dominant_colors=(),
        distribution="distributed across leaf",
        regions=regions,
        overlay=Image.new("RGB", (100, 80)),
    )


def _full_predictions() -> list[Prediction]:
    return [
        Prediction(4, "Tomato___Late_blight", 0.90),
        Prediction(3, "Grape___healthy", 0.0616),
        Prediction(0, "Grape___Black_rot", 0.0307),
        Prediction(1, "Grape___Esca_(Black_Measles)", 0.0067),
        Prediction(2, "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)", 0.0010),
    ]


def _crop_predictions() -> list[Prediction]:
    return [Prediction(0, "Grape", 0.92), Prediction(1, "Apple", 0.08)]


def test_grape_healthy_veto_requires_calibrated_visible_lesions() -> None:
    hierarchy = build_taxonomy_hierarchy(
        _full_predictions(),
        crop_predictions=_crop_predictions(),
        crop_prediction_source="plantnet_api",
    )

    applies, reason, threshold = should_focus_lesions(hierarchy, _analysis())
    quiet, _, _ = should_focus_lesions(hierarchy, _analysis(coverage=0.4))

    assert applies is True
    assert quiet is False
    assert threshold == pytest.approx(1.2959)
    assert "12.42%" in reason


def test_lesion_views_neutralize_pixels_outside_the_leaf() -> None:
    image = Image.new("RGB", (100, 80), (240, 20, 30))
    mask = np.zeros((80, 100), dtype=np.uint8)
    mask[8:72, 10:90] = 255

    views = extract_lesion_views(image, mask, _analysis())

    assert len(views) == 2
    assert views[0].getpixel((0, 0)) == (124, 124, 124)


def test_roi_fusion_removes_conflicting_healthy_rank_within_grape_only() -> None:
    roi_predictions = [
        [
            Prediction(4, "Tomato___Late_blight", 0.80),
            Prediction(0, "Grape___Black_rot", 0.1185),
            Prediction(3, "Grape___healthy", 0.0527),
            Prediction(1, "Grape___Esca_(Black_Measles)", 0.0239),
            Prediction(2, "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)", 0.0049),
        ],
        [
            Prediction(4, "Tomato___Late_blight", 0.84),
            Prediction(0, "Grape___Black_rot", 0.0804),
            Prediction(3, "Grape___healthy", 0.0479),
            Prediction(1, "Grape___Esca_(Black_Measles)", 0.0263),
            Prediction(2, "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)", 0.0054),
        ],
    ]

    fused, evidence = fuse_lesion_predictions(
        _full_predictions(),
        roi_predictions,
        selected_crop="Grape",
        analysis=_analysis(),
        healthy_coverage_threshold=1.2959,
        reason="Visible lesions contradict healthy.",
    )
    hierarchy = build_taxonomy_hierarchy(
        fused,
        crop_predictions=_crop_predictions(),
        crop_prediction_source="plantnet_api",
    )

    assert hierarchy.selected_class_name == "Grape___Black_rot"
    assert hierarchy.conditions[0].conditional_probability > 0.65
    assert evidence.focused_predictions[0].class_name == "Grape___Black_rot"
    assert evidence.full_healthy_probability == pytest.approx(0.616, abs=0.002)
    assert sum(item.probability for item in fused) == pytest.approx(1.0)
