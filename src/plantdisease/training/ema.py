"""Exponential moving average utilities for model weights."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from typing import cast

import torch
from torch import nn


class ModelEMA:
    """Maintain an exponential moving average of model parameters."""

    def __init__(self, model: nn.Module, decay: float) -> None:
        if not 0.0 <= decay < 1.0:
            raise ValueError("decay must be in [0.0, 1.0)")
        self.decay = decay
        self.shadow = {
            name: parameter.detach().clone()
            for name, parameter in model.named_parameters()
            if parameter.requires_grad
        }

    def update(self, model: nn.Module) -> None:
        """Update shadow parameters from the current model parameters."""
        for name, parameter in model.named_parameters():
            if name not in self.shadow:
                continue
            self.shadow[name].mul_(self.decay).add_(
                parameter.detach(),
                alpha=1.0 - self.decay,
            )

    @contextmanager
    def average_parameters(self, model: nn.Module) -> Iterator[None]:
        """Temporarily swap EMA weights into a model and then restore originals."""
        backup: dict[str, torch.Tensor] = {}
        parameters = dict(model.named_parameters())
        for name, shadow_parameter in self.shadow.items():
            parameter = parameters[name]
            backup[name] = parameter.detach().clone()
            parameter.data.copy_(shadow_parameter.data)
        try:
            yield
        finally:
            for name, original in backup.items():
                parameters[name].data.copy_(original.data)

    def state_dict(self) -> dict[str, object]:
        """Return a portable EMA state dict."""
        return {
            "decay": self.decay,
            "shadow": {name: tensor.detach().clone() for name, tensor in self.shadow.items()},
        }

    def load_state_dict(self, state_dict: Mapping[str, object]) -> None:
        """Load EMA state from ``state_dict``."""
        self.decay = float(cast(int | float | str, state_dict["decay"]))
        shadow = state_dict["shadow"]
        if not isinstance(shadow, Mapping):
            raise ValueError("shadow must be a mapping")
        self.shadow = {
            str(name): cast(torch.Tensor, tensor).detach().clone()
            for name, tensor in shadow.items()
        }
