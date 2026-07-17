import pytest
import torch
from torch import nn

from plantdisease.config import SchedulerConfig
from plantdisease.training.schedulers import build_scheduler


def test_build_scheduler_returns_none_for_disabled_scheduler() -> None:
    model = nn.Linear(2, 2)
    optimizer = torch.optim.SGD(model.parameters(), lr=0.1)

    assert build_scheduler(optimizer, SchedulerConfig(name="none"), total_steps=10) is None


def test_cosine_scheduler_decreases_learning_rate() -> None:
    model = nn.Linear(2, 2)
    optimizer = torch.optim.SGD(model.parameters(), lr=0.1)
    scheduler = build_scheduler(
        optimizer,
        SchedulerConfig(name="cosine", eta_min=0.0),
        total_steps=4,
    )

    values = []
    for _ in range(4):
        optimizer.step()
        scheduler.step()
        values.append(optimizer.param_groups[0]["lr"])

    assert values[-1] < values[0]
    assert values[-1] == pytest.approx(0.0, abs=1e-8)
