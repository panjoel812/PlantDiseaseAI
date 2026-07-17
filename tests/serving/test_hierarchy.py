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
        ]
    )

    assert hierarchy.selected_crop == "Apple"
    assert hierarchy.selected_class_name == "Apple___Black_rot"
    assert hierarchy.crops[0].probability == pytest.approx(0.50)
    assert hierarchy.conditions[0].conditional_probability == pytest.approx(0.68)
    assert {item.class_name for item in hierarchy.conditions} == {
        "Apple___Black_rot",
        "Apple___healthy",
    }


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
