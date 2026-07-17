import torch

from plantdisease.config import AugmentationConfig
from plantdisease.training.mix import build_batch_mixer, cutmix_batch, mixup_batch, one_hot


def test_one_hot_returns_float_targets() -> None:
    labels = torch.tensor([0, 2])

    targets = one_hot(labels, num_classes=3)

    assert targets.dtype == torch.float32
    assert targets.tolist() == [[1.0, 0.0, 0.0], [0.0, 0.0, 1.0]]


def test_mixup_batch_preserves_shapes_and_soft_labels() -> None:
    torch.manual_seed(1)
    images = torch.arange(16, dtype=torch.float32).reshape(2, 1, 2, 4)
    labels = torch.tensor([0, 1])

    mixed_images, mixed_targets = mixup_batch(images, labels, num_classes=2, alpha=0.4)

    assert mixed_images.shape == images.shape
    assert mixed_targets.shape == (2, 2)
    assert torch.allclose(mixed_targets.sum(dim=1), torch.ones(2))
    assert torch.all((mixed_targets >= 0.0) & (mixed_targets <= 1.0))


def test_cutmix_batch_preserves_shapes_and_soft_labels() -> None:
    torch.manual_seed(2)
    images = torch.randn(2, 3, 8, 8)
    labels = torch.tensor([0, 1])

    mixed_images, mixed_targets = cutmix_batch(images, labels, num_classes=2, alpha=1.0)

    assert mixed_images.shape == images.shape
    assert mixed_targets.shape == (2, 2)
    assert torch.allclose(mixed_targets.sum(dim=1), torch.ones(2))


def test_build_batch_mixer_returns_none_when_disabled() -> None:
    assert build_batch_mixer(AugmentationConfig(), num_classes=2) is None


def test_build_batch_mixer_returns_mixup_callable() -> None:
    mixer = build_batch_mixer(AugmentationConfig(mixup_alpha=0.2), num_classes=2)
    images = torch.randn(2, 3, 4, 4)
    labels = torch.tensor([0, 1])

    assert mixer is not None
    mixed_images, mixed_targets = mixer(images, labels)

    assert mixed_images.shape == images.shape
    assert mixed_targets.shape == (2, 2)
