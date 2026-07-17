import random
from contextlib import contextmanager

import numpy as np
import pytest
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from plantdisease.training.engine import evaluate, overfit_single_batch, train_one_epoch
from plantdisease.training.losses import soft_cross_entropy
from plantdisease.training.seed import seed_everything


def make_loader() -> DataLoader:
    images = torch.tensor(
        [
            [[[0.0, 0.0], [0.0, 0.0]]],
            [[[1.0, 1.0], [1.0, 1.0]]],
            [[[0.1, 0.0], [0.0, 0.1]]],
            [[[0.9, 1.0], [1.0, 0.9]]],
        ]
    )
    labels = torch.tensor([0, 1, 0, 1])
    return DataLoader(TensorDataset(images, labels), batch_size=4, shuffle=False)


def make_model() -> nn.Module:
    return nn.Sequential(nn.Flatten(), nn.Linear(4, 2))


def test_seed_everything_reproduces_python_numpy_and_torch() -> None:
    seed_everything(13)
    first = (random.random(), np.random.rand(), torch.rand(1).item())
    seed_everything(13)
    second = (random.random(), np.random.rand(), torch.rand(1).item())

    assert first == second


def test_train_one_epoch_updates_parameters() -> None:
    model = make_model()
    before = [parameter.detach().clone() for parameter in model.parameters()]

    result = train_one_epoch(
        model,
        make_loader(),
        nn.CrossEntropyLoss(),
        torch.optim.SGD(model.parameters(), lr=0.2),
        torch.device("cpu"),
    )

    assert result.sample_count == 4
    assert result.loss > 0
    assert any(
        not torch.equal(old, new) for old, new in zip(before, model.parameters(), strict=True)
    )


def test_train_one_epoch_reports_batch_progress() -> None:
    model = make_model()
    messages: list[str] = []

    train_one_epoch(
        model,
        make_loader(),
        nn.CrossEntropyLoss(),
        torch.optim.SGD(model.parameters(), lr=0.2),
        torch.device("cpu"),
        progress_prefix="epoch 1/2",
        log_every=1,
        logger=messages.append,
    )

    assert messages
    assert "epoch 1/2 batch 1/1" in messages[0]
    assert "loss=" in messages[0]


def test_train_one_epoch_accepts_soft_label_batch_mixer() -> None:
    model = make_model()

    def mixer(
        images: torch.Tensor, labels: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor]:
        soft_labels = torch.nn.functional.one_hot(labels, num_classes=2).float()
        return images, soft_labels

    result = train_one_epoch(
        model,
        make_loader(),
        soft_cross_entropy,
        torch.optim.SGD(model.parameters(), lr=0.2),
        torch.device("cpu"),
        batch_mixer=mixer,
    )

    assert result.sample_count == 4
    assert result.loss > 0


def test_train_one_epoch_steps_scheduler_once_per_batch() -> None:
    model = make_model()
    optimizer = torch.optim.SGD(model.parameters(), lr=0.2)
    scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=1)

    train_one_epoch(
        model,
        make_loader(),
        nn.CrossEntropyLoss(),
        optimizer,
        torch.device("cpu"),
        scheduler=scheduler,
    )

    assert scheduler.last_epoch == 1


def test_evaluate_does_not_update_parameters() -> None:
    model = make_model()
    before = [parameter.detach().clone() for parameter in model.parameters()]

    result = evaluate(
        model,
        make_loader(),
        nn.CrossEntropyLoss(),
        torch.device("cpu"),
        ["healthy", "disease"],
    )

    assert result.epoch.sample_count == 4
    assert result.metrics["accuracy"] >= 0.0
    assert all(torch.equal(old, new) for old, new in zip(before, model.parameters(), strict=True))


def test_evaluate_uses_ema_average_parameters_context() -> None:
    class FakeEMA:
        def __init__(self) -> None:
            self.entered = False

        @contextmanager
        def average_parameters(self, model: nn.Module):
            self.entered = True
            yield

    model = make_model()
    ema = FakeEMA()

    evaluate(
        model,
        make_loader(),
        nn.CrossEntropyLoss(),
        torch.device("cpu"),
        ["healthy", "disease"],
        ema=ema,
    )

    assert ema.entered


def test_overfit_single_batch_reduces_loss() -> None:
    seed_everything(5)
    model = make_model()
    images, labels = next(iter(make_loader()))

    losses = overfit_single_batch(
        model,
        (images, labels),
        torch.device("cpu"),
        steps=40,
        learning_rate=0.5,
    )

    assert losses[-1] < losses[0] * 0.5


def test_train_one_epoch_rejects_empty_loader() -> None:
    model = make_model()
    loader = DataLoader(TensorDataset(torch.empty(0, 1, 2, 2), torch.empty(0, dtype=torch.long)))

    with pytest.raises(ValueError, match="empty"):
        train_one_epoch(
            model,
            loader,
            nn.CrossEntropyLoss(),
            torch.optim.SGD(model.parameters(), lr=0.1),
            torch.device("cpu"),
        )
