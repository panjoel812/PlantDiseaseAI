import pytest
import torch
from torch import nn

from plantdisease.config import LossConfig
from plantdisease.training.losses import FocalLoss, build_criterion, soft_cross_entropy


def test_soft_cross_entropy_matches_hard_cross_entropy_for_one_hot_targets() -> None:
    logits = torch.tensor([[2.0, 0.0], [0.0, 2.0]], requires_grad=True)
    labels = torch.tensor([0, 1])
    targets = torch.nn.functional.one_hot(labels, num_classes=2).float()

    actual = soft_cross_entropy(logits, targets)
    expected = nn.CrossEntropyLoss()(logits, labels)

    assert actual.item() == pytest.approx(expected.item())
    actual.backward()
    assert logits.grad is not None


def test_focal_loss_downweights_easy_examples() -> None:
    logits = torch.tensor([[5.0, -5.0], [0.2, -0.2]])
    labels = torch.tensor([0, 0])

    ce = nn.CrossEntropyLoss(reduction="none")(logits, labels)
    focal = FocalLoss(gamma=2.0, reduction="none")(logits, labels)

    assert focal[0] < ce[0]
    assert focal[1] < ce[1]
    assert (focal[0] / ce[0]) < (focal[1] / ce[1])


def test_build_criterion_supports_label_smoothing() -> None:
    criterion = build_criterion(LossConfig(name="cross_entropy", label_smoothing=0.1))

    assert isinstance(criterion, nn.CrossEntropyLoss)
    assert criterion.label_smoothing == pytest.approx(0.1)
