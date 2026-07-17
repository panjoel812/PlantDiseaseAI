"""Single-image classification inference."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import torch
from torch import Tensor, nn


@dataclass(frozen=True)
class Prediction:
    class_index: int
    class_name: str
    probability: float


def predict_topk(
    model: nn.Module,
    image_tensor: Tensor,
    class_names: Sequence[str],
    k: int = 5,
) -> list[Prediction]:
    if k <= 0:
        raise ValueError("k must be positive")
    if image_tensor.ndim == 3:
        image_tensor = image_tensor.unsqueeze(0)
    if image_tensor.ndim != 4 or image_tensor.shape[0] != 1:
        raise ValueError("image_tensor must contain exactly one CHW image")

    model.eval()
    device = next(model.parameters(), torch.empty(0)).device
    with torch.inference_mode():
        probabilities = torch.softmax(model(image_tensor.to(device)), dim=1).squeeze(0)
    if probabilities.numel() != len(class_names):
        raise ValueError("class_names length does not match model output")
    values, indices = torch.topk(probabilities, k=min(k, len(class_names)))
    return [
        Prediction(int(index), class_names[int(index)], float(value))
        for value, index in zip(values.cpu(), indices.cpu(), strict=True)
    ]
