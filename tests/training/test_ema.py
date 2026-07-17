import pytest
import torch
from torch import nn

from plantdisease.training.ema import ModelEMA


def test_model_ema_updates_shadow_weights() -> None:
    model = nn.Linear(1, 1, bias=False)
    model.weight.data.fill_(1.0)
    ema = ModelEMA(model, decay=0.5)

    model.weight.data.fill_(3.0)
    ema.update(model)

    assert ema.shadow["weight"].item() == pytest.approx(2.0)


def test_model_ema_average_parameters_context_restores_weights() -> None:
    model = nn.Linear(1, 1, bias=False)
    model.weight.data.fill_(1.0)
    ema = ModelEMA(model, decay=0.5)
    ema.shadow["weight"].fill_(5.0)

    with ema.average_parameters(model):
        assert model.weight.item() == pytest.approx(5.0)

    assert model.weight.item() == pytest.approx(1.0)


def test_model_ema_state_dict_round_trip() -> None:
    model = nn.Linear(1, 1, bias=False)
    model.weight.data.fill_(2.0)
    ema = ModelEMA(model, decay=0.9)
    clone = ModelEMA(model, decay=0.1)

    clone.load_state_dict(ema.state_dict())

    assert clone.decay == pytest.approx(0.9)
    assert torch.equal(clone.shadow["weight"], ema.shadow["weight"])
