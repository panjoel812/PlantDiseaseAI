import pytest
import torch
from torch import nn

from plantdisease.inference import predict_topk


class FixedLogitModel(nn.Module):
    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        return torch.tensor([[1.0, 3.0, 2.0]], device=inputs.device).repeat(inputs.shape[0], 1)


def test_predict_topk_orders_probabilities_and_clamps_k() -> None:
    predictions = predict_topk(
        FixedLogitModel(),
        torch.zeros(3, 16, 16),
        ["healthy", "late_blight", "early_blight"],
        k=5,
    )

    assert [item.class_name for item in predictions] == [
        "late_blight",
        "early_blight",
        "healthy",
    ]
    assert [item.class_index for item in predictions] == [1, 2, 0]
    assert sum(item.probability for item in predictions) == pytest.approx(1.0)
    assert all(0.0 <= item.probability <= 1.0 for item in predictions)


def test_predict_topk_rejects_label_count_mismatch() -> None:
    with pytest.raises(ValueError, match="class_names"):
        predict_topk(FixedLogitModel(), torch.zeros(3, 16, 16), ["a", "b"], k=2)
