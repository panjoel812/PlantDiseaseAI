"""Loss functions for Week 3 ablation experiments."""

from __future__ import annotations

import torch
from torch import nn
from torch.nn import functional as F

from plantdisease.config import LossConfig


def soft_cross_entropy(logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
    """Cross entropy for soft labels such as Mixup and CutMix targets."""
    if logits.shape != targets.shape:
        raise ValueError("soft targets must have the same shape as logits")
    log_probs = F.log_softmax(logits, dim=1)
    return -(targets * log_probs).sum(dim=1).mean()


class FocalLoss(nn.Module):
    """Focal Loss for focusing training on harder examples."""

    def __init__(
        self,
        gamma: float = 2.0,
        label_smoothing: float = 0.0,
        reduction: str = "mean",
    ) -> None:
        super().__init__()
        if gamma < 0.0:
            raise ValueError("gamma must be non-negative")
        if reduction not in {"mean", "none"}:
            raise ValueError("reduction must be mean or none")
        self.gamma = gamma
        self.label_smoothing = label_smoothing
        self.reduction = reduction

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        ce = F.cross_entropy(
            logits,
            targets,
            label_smoothing=self.label_smoothing,
            reduction="none",
        )
        pt = torch.exp(-ce)
        loss = ((1.0 - pt) ** self.gamma) * ce
        if self.reduction == "none":
            return loss
        return loss.mean()


def build_criterion(config: LossConfig) -> nn.Module:
    """Build the configured training loss."""
    if config.name == "cross_entropy":
        return nn.CrossEntropyLoss(label_smoothing=config.label_smoothing)
    if config.name == "focal":
        return FocalLoss(
            gamma=config.focal_gamma,
            label_smoothing=config.label_smoothing,
        )
    raise ValueError(f"unsupported loss: {config.name}")
