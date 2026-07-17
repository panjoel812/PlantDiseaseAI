"""Batch-level Mixup and CutMix transforms for Week 3 ablations."""

from __future__ import annotations

import math
from collections.abc import Callable

import torch

from plantdisease.config import AugmentationConfig

BatchMixer = Callable[[torch.Tensor, torch.Tensor], tuple[torch.Tensor, torch.Tensor]]


def one_hot(labels: torch.Tensor, num_classes: int) -> torch.Tensor:
    """Convert integer labels to float one-hot targets."""
    if num_classes <= 0:
        raise ValueError("num_classes must be positive")
    return torch.nn.functional.one_hot(labels, num_classes=num_classes).float()


def _sample_lambda(alpha: float, device: torch.device) -> float:
    if alpha <= 0.0:
        raise ValueError("alpha must be positive")
    distribution = torch.distributions.Beta(
        torch.tensor(alpha, device=device),
        torch.tensor(alpha, device=device),
    )
    return float(distribution.sample().item())


def mixup_batch(
    images: torch.Tensor,
    labels: torch.Tensor,
    num_classes: int,
    alpha: float,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Blend whole images and labels with a Beta-distributed mixing ratio."""
    if images.shape[0] != labels.shape[0]:
        raise ValueError("images and labels must have the same batch size")
    lam = _sample_lambda(alpha, images.device)
    permutation = torch.randperm(images.shape[0], device=images.device)
    targets = one_hot(labels, num_classes).to(images.device)
    mixed_images = lam * images + (1.0 - lam) * images[permutation]
    mixed_targets = lam * targets + (1.0 - lam) * targets[permutation]
    return mixed_images, mixed_targets


def _rand_bbox(
    width: int,
    height: int,
    lam: float,
    device: torch.device,
) -> tuple[int, int, int, int]:
    cut_ratio = math.sqrt(1.0 - lam)
    cut_width = int(width * cut_ratio)
    cut_height = int(height * cut_ratio)
    center_x = int(torch.randint(width, (1,), device=device).item())
    center_y = int(torch.randint(height, (1,), device=device).item())
    x1 = max(center_x - cut_width // 2, 0)
    y1 = max(center_y - cut_height // 2, 0)
    x2 = min(center_x + cut_width // 2, width)
    y2 = min(center_y + cut_height // 2, height)
    return x1, y1, x2, y2


def cutmix_batch(
    images: torch.Tensor,
    labels: torch.Tensor,
    num_classes: int,
    alpha: float,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Paste a rectangular patch from shuffled images and mix labels by area."""
    if images.ndim != 4:
        raise ValueError("images must have shape [batch, channels, height, width]")
    if images.shape[0] != labels.shape[0]:
        raise ValueError("images and labels must have the same batch size")

    lam = _sample_lambda(alpha, images.device)
    permutation = torch.randperm(images.shape[0], device=images.device)
    _, _, height, width = images.shape
    x1, y1, x2, y2 = _rand_bbox(width, height, lam, images.device)

    mixed_images = images.clone()
    mixed_images[:, :, y1:y2, x1:x2] = images[permutation, :, y1:y2, x1:x2]

    patch_area = (x2 - x1) * (y2 - y1)
    adjusted_lambda = 1.0 - patch_area / float(width * height)
    targets = one_hot(labels, num_classes).to(images.device)
    mixed_targets = adjusted_lambda * targets + (1.0 - adjusted_lambda) * targets[permutation]
    return mixed_images, mixed_targets


def build_batch_mixer(config: AugmentationConfig, num_classes: int) -> BatchMixer | None:
    """Create the configured batch mixer, or None when batch mixing is disabled."""
    if config.mixup_alpha > 0.0:
        return lambda images, labels: mixup_batch(
            images,
            labels,
            num_classes=num_classes,
            alpha=config.mixup_alpha,
        )
    if config.cutmix_alpha > 0.0:
        return lambda images, labels: cutmix_batch(
            images,
            labels,
            num_classes=num_classes,
            alpha=config.cutmix_alpha,
        )
    return None
