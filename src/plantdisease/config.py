"""Strict experiment configuration loaded from YAML."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, cast

import yaml

from plantdisease.data.splits import SplitRatios


@dataclass(frozen=True)
class DataConfig:
    image_size: int = 224
    batch_size: int = 32
    num_workers: int = 0
    train_ratio: float = 0.7
    validation_ratio: float = 0.15
    test_ratio: float = 0.15

    def __post_init__(self) -> None:
        if self.image_size <= 0:
            raise ValueError("image_size must be positive")
        if self.batch_size <= 0:
            raise ValueError("batch_size must be positive")
        if self.num_workers < 0:
            raise ValueError("num_workers must be non-negative")
        values = (self.train_ratio, self.validation_ratio, self.test_ratio)
        if (
            self.train_ratio <= 0
            or self.validation_ratio <= 0
            or self.test_ratio < 0
            or abs(sum(values) - 1.0) > 1e-9
        ):
            raise ValueError(
                "data split ratios must use positive train/validation, "
                "non-negative test, and sum to 1.0"
            )

    @property
    def split_ratios(self) -> SplitRatios:
        return SplitRatios(self.train_ratio, self.validation_ratio, self.test_ratio)


@dataclass(frozen=True)
class ModelConfig:
    name: str = "mobilenet_v2"
    pretrained: bool = False

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("model name must not be empty")


@dataclass(frozen=True)
class TrainingConfig:
    seed: int = 42
    epochs: int = 1
    learning_rate: float = 0.01
    device: str = "cpu"

    def __post_init__(self) -> None:
        if self.epochs <= 0:
            raise ValueError("epochs must be positive")
        if self.learning_rate <= 0:
            raise ValueError("learning_rate must be positive")
        if self.device not in {"cpu", "mps", "cuda", "auto"}:
            raise ValueError("device must be cpu, mps, cuda, or auto")


@dataclass(frozen=True)
class AugmentationConfig:
    randaugment_enabled: bool = False
    randaugment_num_ops: int = 2
    randaugment_magnitude: int = 9
    random_erasing_enabled: bool = False
    random_erasing_probability: float = 0.25
    mixup_alpha: float = 0.0
    cutmix_alpha: float = 0.0

    def __post_init__(self) -> None:
        if self.randaugment_num_ops <= 0:
            raise ValueError("randaugment_num_ops must be positive")
        if self.randaugment_magnitude < 0:
            raise ValueError("randaugment_magnitude must be non-negative")
        if not 0.0 <= self.random_erasing_probability <= 1.0:
            raise ValueError("random_erasing_probability must be in [0.0, 1.0]")
        if self.mixup_alpha < 0.0 or self.cutmix_alpha < 0.0:
            raise ValueError("mixup_alpha and cutmix_alpha must be non-negative")
        if self.mixup_alpha > 0.0 and self.cutmix_alpha > 0.0:
            raise ValueError("mixup_alpha and cutmix_alpha cannot both be positive")


@dataclass(frozen=True)
class LossConfig:
    name: str = "cross_entropy"
    label_smoothing: float = 0.0
    focal_gamma: float = 2.0

    def __post_init__(self) -> None:
        if self.name not in {"cross_entropy", "focal"}:
            raise ValueError("loss name must be cross_entropy or focal")
        if not 0.0 <= self.label_smoothing < 1.0:
            raise ValueError("label_smoothing must be in [0.0, 1.0)")
        if self.focal_gamma < 0.0:
            raise ValueError("focal_gamma must be non-negative")


@dataclass(frozen=True)
class SchedulerConfig:
    name: str = "none"
    eta_min: float = 0.0

    def __post_init__(self) -> None:
        if self.name not in {"none", "cosine"}:
            raise ValueError("scheduler name must be none or cosine")
        if self.eta_min < 0.0:
            raise ValueError("eta_min must be non-negative")


@dataclass(frozen=True)
class EMAConfig:
    enabled: bool = False
    decay: float = 0.999

    def __post_init__(self) -> None:
        if not 0.0 <= self.decay < 1.0:
            raise ValueError("ema decay must be in [0.0, 1.0)")


@dataclass(frozen=True)
class ExperimentConfig:
    data: DataConfig = field(default_factory=DataConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    training: TrainingConfig = field(default_factory=TrainingConfig)
    augmentation: AugmentationConfig = field(default_factory=AugmentationConfig)
    loss: LossConfig = field(default_factory=LossConfig)
    scheduler: SchedulerConfig = field(default_factory=SchedulerConfig)
    ema: EMAConfig = field(default_factory=EMAConfig)

    @classmethod
    def from_yaml(cls, path: Path) -> ExperimentConfig:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(payload, Mapping):
            raise ValueError("config YAML must contain a mapping")
        allowed = {"data", "model", "training", "augmentation", "loss", "scheduler", "ema"}
        unknown = set(payload) - allowed
        if unknown:
            raise ValueError(f"unknown config sections: {sorted(unknown)}")
        return cls(
            data=DataConfig(**_mapping(payload.get("data", {}), "data")),
            model=ModelConfig(**_mapping(payload.get("model", {}), "model")),
            training=TrainingConfig(**_mapping(payload.get("training", {}), "training")),
            augmentation=AugmentationConfig(
                **_mapping(payload.get("augmentation", {}), "augmentation")
            ),
            loss=LossConfig(**_mapping(payload.get("loss", {}), "loss")),
            scheduler=SchedulerConfig(**_mapping(payload.get("scheduler", {}), "scheduler")),
            ema=EMAConfig(**_mapping(payload.get("ema", {}), "ema")),
        )

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _mapping(value: object, name: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} config must be a mapping")
    return dict(cast(Mapping[str, Any], value))
