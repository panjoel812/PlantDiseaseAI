"""Minimal training and evaluation engine."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from contextlib import AbstractContextManager, nullcontext
from dataclasses import dataclass
from typing import Protocol

import torch
from torch import nn
from torch.utils.data import DataLoader

from plantdisease.evaluation.metrics import classification_metrics

Criterion = Callable[[torch.Tensor, torch.Tensor], torch.Tensor]
BatchMixer = Callable[[torch.Tensor, torch.Tensor], tuple[torch.Tensor, torch.Tensor]]


class ParameterAverager(Protocol):
    """Training helper that can update and temporarily expose averaged weights."""

    def update(self, model: nn.Module) -> None:
        """Update averaged parameters from the current model weights."""

    def average_parameters(self, model: nn.Module) -> AbstractContextManager[None]:
        """Temporarily swap averaged parameters into the model."""


@dataclass(frozen=True)
class EpochResult:
    loss: float
    sample_count: int


@dataclass(frozen=True)
class EvaluationResult:
    epoch: EpochResult
    metrics: dict[str, object]
    y_true: tuple[int, ...]
    y_pred: tuple[int, ...]


def train_one_epoch(
    model: nn.Module,
    loader: DataLoader,
    criterion: Criterion,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
    progress_prefix: str | None = None,
    log_every: int = 0,
    logger: Callable[[str], None] | None = None,
    batch_mixer: BatchMixer | None = None,
    scheduler: torch.optim.lr_scheduler.LRScheduler | None = None,
    ema: ParameterAverager | None = None,
) -> EpochResult:
    if log_every < 0:
        raise ValueError("log_every must be non-negative")
    model.train()
    total_loss = 0.0
    sample_count = 0
    total_batches = len(loader)
    for batch_index, (images, labels) in enumerate(loader, start=1):
        images = images.to(device)
        labels = labels.to(device)
        targets = labels
        if batch_mixer is not None:
            images, targets = batch_mixer(images, labels)
        optimizer.zero_grad(set_to_none=True)
        loss = criterion(model(images), targets)
        loss.backward()
        optimizer.step()
        if scheduler is not None:
            scheduler.step()
        if ema is not None:
            ema.update(model)
        batch_size = labels.shape[0]
        total_loss += float(loss.detach()) * batch_size
        sample_count += batch_size
        if logger is not None and log_every > 0:
            is_first = batch_index == 1
            is_interval = batch_index % log_every == 0
            is_last = batch_index == total_batches
            if is_first or is_interval or is_last:
                prefix = f"{progress_prefix} " if progress_prefix else ""
                logger(
                    f"{prefix}batch {batch_index}/{total_batches} "
                    f"samples={sample_count} loss={float(loss.detach()):.4f}"
                )
    if sample_count == 0:
        raise ValueError("cannot train with an empty DataLoader")
    return EpochResult(loss=total_loss / sample_count, sample_count=sample_count)


def evaluate(
    model: nn.Module,
    loader: DataLoader,
    criterion: Criterion,
    device: torch.device,
    class_names: Sequence[str],
    ema: ParameterAverager | None = None,
) -> EvaluationResult:
    total_loss = 0.0
    y_true: list[int] = []
    y_pred: list[int] = []
    parameter_context = ema.average_parameters(model) if ema is not None else nullcontext()
    with parameter_context:
        model.eval()
        with torch.inference_mode():
            for images, labels in loader:
                images = images.to(device)
                labels = labels.to(device)
                logits = model(images)
                loss = criterion(logits, labels)
                batch_size = labels.shape[0]
                total_loss += float(loss) * batch_size
                y_true.extend(int(label) for label in labels.cpu())
                y_pred.extend(int(label) for label in logits.argmax(dim=1).cpu())
    if not y_true:
        raise ValueError("cannot evaluate an empty DataLoader")
    epoch = EpochResult(loss=total_loss / len(y_true), sample_count=len(y_true))
    return EvaluationResult(
        epoch=epoch,
        metrics=classification_metrics(y_true, y_pred, class_names),
        y_true=tuple(y_true),
        y_pred=tuple(y_pred),
    )


def overfit_single_batch(
    model: nn.Module,
    batch: tuple[torch.Tensor, torch.Tensor],
    device: torch.device,
    steps: int,
    learning_rate: float,
) -> list[float]:
    if steps <= 0 or learning_rate <= 0:
        raise ValueError("steps and learning_rate must be positive")
    model.to(device).train()
    images, labels = (item.to(device) for item in batch)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.SGD(model.parameters(), lr=learning_rate)
    losses: list[float] = []
    for _ in range(steps):
        optimizer.zero_grad(set_to_none=True)
        loss = criterion(model(images), labels)
        loss.backward()
        optimizer.step()
        losses.append(float(loss.detach()))
    return losses
