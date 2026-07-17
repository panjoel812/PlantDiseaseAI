"""Audited Grad-CAM target-module selection for supported classifiers."""

from dataclasses import dataclass

from torch import nn


@dataclass(frozen=True)
class TargetLayer:
    """A stable layer name paired with the resolved model module."""

    name: str
    module: nn.Module


def resolve_target_layer(model: nn.Module, model_name: str) -> TargetLayer:
    """Resolve the audited final spatial module for a supported model."""
    layer_names = {
        "mobilenet_v2": "features.18.0",
        "resnet18": "layer4.1",
        "resnet50": "layer4.2",
        "efficientnet_b0": "features.8.0",
        "efficientnet_v2_s": "features.7.0",
    }
    if model_name not in layer_names:
        raise ValueError(f"unsupported model for Grad-CAM: {model_name}")
    layer_name = layer_names[model_name]
    return TargetLayer(layer_name, model.get_submodule(layer_name))
