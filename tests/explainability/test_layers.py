import pytest
from torch import nn

from plantdisease.explainability.layers import TargetLayer, resolve_target_layer
from plantdisease.models.factory import create_model


@pytest.mark.parametrize(
    ("model_name", "expected_name"),
    [
        ("mobilenet_v2", "features.18.0"),
        ("resnet18", "layer4.1"),
        ("resnet50", "layer4.2"),
        ("efficientnet_b0", "features.8.0"),
        ("efficientnet_v2_s", "features.7.0"),
    ],
)
def test_resolve_target_layer_returns_audited_spatial_module(
    model_name: str,
    expected_name: str,
) -> None:
    model = create_model(model_name, num_classes=3, pretrained=False)

    target = resolve_target_layer(model, model_name)

    assert isinstance(target, TargetLayer)
    assert target.name == expected_name
    assert isinstance(target.module, nn.Module)


def test_resnet50_target_layer_is_frozen_to_last_bottleneck_output() -> None:
    model = create_model("resnet50", num_classes=3, pretrained=False)

    target = resolve_target_layer(model, "resnet50")

    assert target.name == "layer4.2"
    assert target.module is model.layer4[2]


def test_resolve_target_layer_rejects_unknown_model_name() -> None:
    model = create_model("resnet18", num_classes=3, pretrained=False)

    with pytest.raises(ValueError, match="unsupported model"):
        resolve_target_layer(model, "unknown")
