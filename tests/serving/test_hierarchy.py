from __future__ import annotations

import pytest

from plantdisease.inference import Prediction
from plantdisease.serving.hierarchy import build_taxonomy_hierarchy


def test_hierarchy_aggregates_crop_before_ranking_conditions() -> None:
    hierarchy = build_taxonomy_hierarchy(
        [
            Prediction(0, "Apple___Black_rot", 0.34),
            Prediction(1, "Grape___Black_rot", 0.15),
            Prediction(2, "Apple___healthy", 0.16),
            Prediction(3, "Grape___Leaf_blight", 0.21),
            Prediction(4, "Tomato___healthy", 0.14),
        ],
        crop_confidence_threshold=0.45,
    )

    assert hierarchy.selected_crop == "Apple"
    assert hierarchy.selected_class_name == "Apple___Black_rot"
    assert hierarchy.crops[0].probability == pytest.approx(0.50)
    assert hierarchy.conditions[0].conditional_probability == pytest.approx(0.68)
    assert {item.class_name for item in hierarchy.conditions} == {
        "Apple___Black_rot",
        "Apple___healthy",
    }
    assert hierarchy.crop_confident is True


def test_hierarchy_normalizes_partial_probability_mass() -> None:
    hierarchy = build_taxonomy_hierarchy(
        [
            Prediction(0, "Apple___Black_rot", 0.20),
            Prediction(1, "Apple___healthy", 0.10),
            Prediction(2, "Grape___Black_rot", 0.10),
        ]
    )

    assert sum(item.probability for item in hierarchy.crops) == pytest.approx(1.0)
    assert hierarchy.crops[0].probability == pytest.approx(0.75)
    assert hierarchy.conditions[0].joint_probability == pytest.approx(0.50)
    assert hierarchy.conditions[0].conditional_probability == pytest.approx(2 / 3)


def test_hierarchy_withholds_disease_when_crop_confidence_is_low() -> None:
    hierarchy = build_taxonomy_hierarchy(
        [
            Prediction(0, "Tomato___Late_blight", 0.381),
            Prediction(1, "Grape___Black_rot", 0.341),
            Prediction(2, "Strawberry___Leaf_scorch", 0.278),
        ]
    )

    assert hierarchy.selected_crop == "Tomato"
    assert hierarchy.crop_confident is False
    assert hierarchy.selected_class_name is None
    assert hierarchy.conditions == []
    assert "below the 60%" in hierarchy.decision_reason


def test_independent_crop_head_selects_plant_then_rejects_weak_disease() -> None:
    hierarchy = build_taxonomy_hierarchy(
        [
            Prediction(0, "Grape___healthy", 0.0304),
            Prediction(1, "Grape___Black_rot", 0.0128),
            Prediction(2, "Grape___Esca_(Black_Measles)", 0.0096),
            Prediction(3, "Grape___Leaf_blight", 0.0015),
            Prediction(4, "Tomato___Late_blight", 0.3331),
            Prediction(5, "Apple___Black_rot", 0.0699),
        ],
        crop_predictions=[
            Prediction(4, "Grape", 0.88),
            Prediction(13, "Tomato", 0.07),
            Prediction(0, "Apple", 0.05),
        ],
    )

    assert hierarchy.method == "independent_crop_then_disease_v3"
    assert hierarchy.selected_crop == "Grape"
    assert hierarchy.crop_confident is True
    assert hierarchy.disease_confident is False
    assert hierarchy.selected_class_name is None
    assert [item.class_name for item in hierarchy.conditions] == [
        "Grape___healthy",
        "Grape___Black_rot",
        "Grape___Esca_(Black_Measles)",
        "Grape___Leaf_blight",
    ]
    assert "evidence only" in hierarchy.disease_decision_reason


def test_broad_species_outside_local_taxonomy_is_identified_without_disease() -> None:
    hierarchy = build_taxonomy_hierarchy(
        [
            Prediction(0, "Tomato___Late_blight", 0.70),
            Prediction(1, "Grape___Black_rot", 0.30),
        ],
        crop_predictions=[
            Prediction(0, "Virginia creeper", 0.91),
            Prediction(1, "Grape", 0.09),
        ],
        crop_prediction_source="plantnet_api",
    )

    assert hierarchy.method == "external_species_then_disease_v4"
    assert hierarchy.crop_source == "plantnet_api"
    assert hierarchy.selected_crop == "Virginia creeper"
    assert hierarchy.crop_confident is True
    assert hierarchy.conditions == []
    assert hierarchy.disease_confident is False
    assert "no matching local" in hierarchy.decision_reason


def test_local_114_catalog_uses_same_safe_outside_taxonomy_routing() -> None:
    hierarchy = build_taxonomy_hierarchy(
        [
            Prediction(0, "Grape___Black_rot", 0.70),
            Prediction(1, "Apple___Black_rot", 0.30),
        ],
        crop_predictions=[
            Prediction(0, "Acer campestre", 0.86),
            Prediction(1, "Grape", 0.14),
        ],
        crop_prediction_source="local_leaf114_checkpoint",
    )

    assert hierarchy.method == "local_catalog_then_disease_v4"
    assert hierarchy.crop_source == "local_leaf114_checkpoint"
    assert hierarchy.selected_crop == "Acer campestre"
    assert hierarchy.crop_confident is True
    assert hierarchy.conditions == []
    assert hierarchy.disease_confident is False


@pytest.mark.parametrize(
    ("predictions", "message"),
    [
        ([], "must not be empty"),
        ([Prediction(0, "Apple___healthy", 0.0)], "positive"),
        ([Prediction(0, "Apple___healthy", -0.1)], "non-negative"),
    ],
)
def test_hierarchy_rejects_invalid_distributions(
    predictions: list[Prediction],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        build_taxonomy_hierarchy(predictions)
