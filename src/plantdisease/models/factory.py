"""Model factory with explicit, stable model names."""

from torch import nn
from torchvision.models import (
    EfficientNet_B0_Weights,
    EfficientNet_V2_S_Weights,
    MobileNet_V2_Weights,
    ResNet18_Weights,
    ResNet50_Weights,
    efficientnet_b0,
    efficientnet_v2_s,
    mobilenet_v2,
    resnet18,
    resnet50,
)


def create_model(name: str, num_classes: int, pretrained: bool = False) -> nn.Module:
    if num_classes <= 0:
        raise ValueError("num_classes must be positive")

    if name == "mobilenet_v2":
        weights = MobileNet_V2_Weights.DEFAULT if pretrained else None
        model = mobilenet_v2(weights=weights)
        model.classifier[1] = nn.Linear(model.last_channel, num_classes)
        return model

    if name == "resnet18":
        weights = ResNet18_Weights.DEFAULT if pretrained else None
        model = resnet18(weights=weights)
        model.fc = nn.Linear(model.fc.in_features, num_classes)
        return model

    if name == "resnet50":
        weights = ResNet50_Weights.DEFAULT if pretrained else None
        model = resnet50(weights=weights)
        model.fc = nn.Linear(model.fc.in_features, num_classes)
        return model

    if name == "efficientnet_b0":
        weights = EfficientNet_B0_Weights.DEFAULT if pretrained else None
        model = efficientnet_b0(weights=weights)
        model.classifier[1] = nn.Linear(model.classifier[1].in_features, num_classes)
        return model

    if name == "efficientnet_v2_s":
        weights = EfficientNet_V2_S_Weights.DEFAULT if pretrained else None
        model = efficientnet_v2_s(weights=weights)
        model.classifier[1] = nn.Linear(model.classifier[1].in_features, num_classes)
        return model

    raise ValueError(f"unsupported model: {name}")
