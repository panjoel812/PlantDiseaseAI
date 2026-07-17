"""Learning-rate scheduler builders for Week 3 ablations."""

from __future__ import annotations

import torch

from plantdisease.config import SchedulerConfig


def build_scheduler(
    optimizer: torch.optim.Optimizer,
    config: SchedulerConfig,
    total_steps: int,
) -> torch.optim.lr_scheduler.LRScheduler | None:
    """Build the configured optimizer-step scheduler."""
    if total_steps <= 0:
        raise ValueError("total_steps must be positive")
    if config.name == "none":
        return None
    if config.name == "cosine":
        return torch.optim.lr_scheduler.CosineAnnealingLR(
            optimizer,
            T_max=total_steps,
            eta_min=config.eta_min,
        )
    raise ValueError(f"unsupported scheduler: {config.name}")
