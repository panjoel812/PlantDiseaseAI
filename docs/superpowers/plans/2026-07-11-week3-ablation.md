# Week 3 Ablation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现 Week 3 可配置消融训练系统，让 ResNet50 在固定官方 split、seed 42、5 epochs 下逐项测试 Label Smoothing、Focal Loss、RandAugment、Random Erasing、Mixup、CutMix、Cosine Scheduler 和 EMA。

**Architecture:** 新功能拆成小模块：`losses.py` 负责损失函数，`mix.py` 负责 batch 级标签混合，`schedulers.py` 负责学习率曲线，`ema.py` 负责权重移动平均，`config.py` 负责开关配置。训练入口 `baseline.py` 只做编排，训练循环 `engine.py` 只加最小 hook，避免变成不可维护的大脚本。

**Tech Stack:** Python 3.12, PyTorch, torchvision transforms, pytest, Ruff, uv, PlantVillage official split, ResNet50 baseline.

## Global Constraints

- Week 3 标准预算：ResNet50、seed 42、5 epochs、batch size 16、官方 split。
- 主指标：validation Macro F1 选择 checkpoint，test Macro F1 做最终横向比较。
- 所有开关默认关闭；关闭时训练行为应尽量等同 Week 2 baseline。
- 单变量实验每次只改变一个因素。
- Mixup 和 CutMix 在第一版不能同时开启。
- 正式结果必须来自 `metrics.json`，不能手填或估计。
- 单 seed 结果必须明确写为 single-seed ablation，不能声称统计稳健性。
- 官方 split 的 227 个重叠 `leaf_id` 限制必须保留在报告里。
- 每个实现步骤都要讲清数学对象：目标分布、损失权重、学习率函数或参数移动平均。

---

## File Structure

- Create `src/plantdisease/training/losses.py`: hard/soft CrossEntropy、Label Smoothing、Focal Loss。
- Create `src/plantdisease/training/mix.py`: Mixup、CutMix、混合标签。
- Create `src/plantdisease/training/schedulers.py`: cosine scheduler builder 和元数据。
- Create `src/plantdisease/training/ema.py`: EMA shadow weights、swap context、state dict。
- Modify `src/plantdisease/config.py`: 增加 `AugmentationConfig`、`LossConfig`、`SchedulerConfig`、`EMAConfig`。
- Modify `src/plantdisease/data/transforms.py`: 训练 transform 增加可选 RandAugment 和 RandomErasing。
- Modify `src/plantdisease/training/engine.py`: 支持 batch mixer、scheduler step、EMA update。
- Modify `src/plantdisease/training/baseline.py`: 根据配置创建 loss/mixer/scheduler/EMA，保存增强后的 manifest。
- Create `tests/training/test_losses.py`
- Create `tests/training/test_mix.py`
- Create `tests/training/test_schedulers.py`
- Create `tests/training/test_ema.py`
- Modify `tests/test_config.py`
- Modify `tests/data/test_pipeline.py` or create `tests/data/test_transforms.py`
- Modify `tests/training/test_engine.py`
- Modify `tests/training/test_baseline_run.py`
- Create `configs/week3/*.yaml`
- Create `reports/week3_ablation_plan.md`

---

### Task 1: Config Sections

**Files:**
- Modify: `src/plantdisease/config.py`
- Modify: `tests/test_config.py`

**Interfaces:**
- Produces: `AugmentationConfig`
- Produces: `LossConfig`
- Produces: `SchedulerConfig`
- Produces: `EMAConfig`
- Extends: `ExperimentConfig.augmentation`, `.loss`, `.scheduler`, `.ema`

**教学说明：** 这一步不是训练技巧本身，而是实验控制面板。数学上，一个消融实验要能说“只有一个变量变了”，前提是每个变量都有明确、可审计的配置字段。

- [ ] **Step 1: 写失败测试**

Add to `tests/test_config.py`:

```python
def test_experiment_config_loads_week3_sections(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    path.write_text(
        """
data:
  image_size: 64
model:
  name: resnet50
training:
  seed: 42
  epochs: 5
  learning_rate: 0.001
augmentation:
  randaugment_enabled: true
  randaugment_num_ops: 2
  randaugment_magnitude: 9
  random_erasing_enabled: true
  random_erasing_probability: 0.25
  mixup_alpha: 0.2
loss:
  name: cross_entropy
  label_smoothing: 0.1
scheduler:
  name: cosine
  eta_min: 0.00001
ema:
  enabled: true
  decay: 0.999
""".strip(),
        encoding="utf-8",
    )

    config = ExperimentConfig.from_yaml(path)

    assert config.augmentation.randaugment_enabled is True
    assert config.augmentation.random_erasing_enabled is True
    assert config.augmentation.mixup_alpha == pytest.approx(0.2)
    assert config.loss.label_smoothing == pytest.approx(0.1)
    assert config.scheduler.name == "cosine"
    assert config.ema.enabled is True
```

Add validation tests:

```python
def test_experiment_config_rejects_mixup_and_cutmix_together(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    path.write_text(
        """
augmentation:
  mixup_alpha: 0.2
  cutmix_alpha: 1.0
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="mixup_alpha and cutmix_alpha"):
        ExperimentConfig.from_yaml(path)
```

- [ ] **Step 2: 验证 RED**

Run: `uv run pytest tests/test_config.py -q`

Expected: fails because `ExperimentConfig` has no `augmentation`, `loss`, `scheduler`, or `ema` sections.

- [ ] **Step 3: 实现配置 dataclasses**

Add to `src/plantdisease/config.py`:

```python
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
```

Also add:

```python
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
```

Add equivalent small dataclasses for scheduler and EMA:

```python
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
```

Update `ExperimentConfig` allowed sections and constructor.

- [ ] **Step 4: 验证 GREEN**

Run: `uv run pytest tests/test_config.py -q`

Expected: all config tests pass.

- [ ] **Step 5: 提交**

```bash
git add src/plantdisease/config.py tests/test_config.py
git commit -m "feat: add week3 experiment config sections"
```

---

### Task 2: Loss Functions

**Files:**
- Create: `src/plantdisease/training/losses.py`
- Create: `tests/training/test_losses.py`

**Interfaces:**
- Produces: `soft_cross_entropy(logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor`
- Produces: `FocalLoss(gamma: float = 2.0, label_smoothing: float = 0.0)`
- Produces: `build_criterion(config: LossConfig) -> nn.Module`

**教学说明：** CrossEntropy 的核心是 `-log(p_y)`。Label Smoothing 改目标分布 `q`，Focal Loss 改每个样本的权重 `(1 - p_t)^gamma`。前者让模型别太自信，后者让模型多看难样本。

- [ ] **Step 1: 写失败测试**

Create `tests/training/test_losses.py`:

```python
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

    assert actual == pytest.approx(expected)
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
```

- [ ] **Step 2: 验证 RED**

Run: `uv run pytest tests/training/test_losses.py -q`

Expected: fails because `plantdisease.training.losses` does not exist.

- [ ] **Step 3: 实现 losses**

Create `src/plantdisease/training/losses.py`:

```python
"""Loss functions for Week 3 ablation experiments."""

from __future__ import annotations

import torch
from torch import nn
from torch.nn import functional as F

from plantdisease.config import LossConfig


def soft_cross_entropy(logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
    if logits.shape != targets.shape:
        raise ValueError("soft targets must have the same shape as logits")
    log_probs = F.log_softmax(logits, dim=1)
    return -(targets * log_probs).sum(dim=1).mean()


class FocalLoss(nn.Module):
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
    if config.name == "cross_entropy":
        return nn.CrossEntropyLoss(label_smoothing=config.label_smoothing)
    if config.name == "focal":
        return FocalLoss(
            gamma=config.focal_gamma,
            label_smoothing=config.label_smoothing,
        )
    raise ValueError(f"unsupported loss: {config.name}")
```

- [ ] **Step 4: 验证 GREEN**

Run: `uv run pytest tests/training/test_losses.py -q`

Expected: all loss tests pass.

- [ ] **Step 5: 提交**

```bash
git add src/plantdisease/training/losses.py tests/training/test_losses.py
git commit -m "feat: add week3 loss functions"
```

---

### Task 3: Mixup and CutMix

**Files:**
- Create: `src/plantdisease/training/mix.py`
- Create: `tests/training/test_mix.py`

**Interfaces:**
- Produces: `one_hot(labels: torch.Tensor, num_classes: int) -> torch.Tensor`
- Produces: `mixup_batch(images, labels, num_classes, alpha, generator=None)`
- Produces: `cutmix_batch(images, labels, num_classes, alpha, generator=None)`
- Produces: `build_batch_mixer(config: AugmentationConfig, num_classes: int)`

**教学说明：** Mixup/CutMix 都把 hard label 变成 soft label。训练时损失不再是单个 `-log(p_y)`，而是 `-sum q_k log(p_k)`。如果图像是 70% A + 30% B，标签也必须是 70% A + 30% B，否则数学上图像和监督信号就不一致。

- [ ] **Step 1: 写失败测试**

Create `tests/training/test_mix.py`:

```python
import pytest
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
```

- [ ] **Step 2: 验证 RED**

Run: `uv run pytest tests/training/test_mix.py -q`

Expected: fails because `plantdisease.training.mix` does not exist.

- [ ] **Step 3: 实现 batch mixing**

Create `src/plantdisease/training/mix.py` with deterministic-friendly torch operations. Use `torch.distributions.Beta(alpha, alpha).sample()` for lambda and `torch.randperm(batch_size, device=images.device)` for pairing.

Implementation must return `(mixed_images, soft_targets)`.

- [ ] **Step 4: 验证 GREEN**

Run: `uv run pytest tests/training/test_mix.py -q`

Expected: all Mixup/CutMix tests pass.

- [ ] **Step 5: 提交**

```bash
git add src/plantdisease/training/mix.py tests/training/test_mix.py
git commit -m "feat: add mixup and cutmix batch transforms"
```

---

### Task 4: Transforms for RandAugment and Random Erasing

**Files:**
- Modify: `src/plantdisease/data/transforms.py`
- Create or modify: `tests/data/test_transforms.py`

**Interfaces:**
- Extends: `build_train_transform(image_size: int, randaugment_enabled: bool = False, randaugment_num_ops: int = 2, randaugment_magnitude: int = 9, random_erasing_enabled: bool = False, random_erasing_probability: float = 0.25) -> transforms.Compose`

**教学说明：** RandAugment 是输入空间扰动：让同一类叶片在颜色、旋转、对比度上有更多变化。Random Erasing 是遮挡扰动：迫使模型不要只盯一个局部病斑或背景线索。

- [ ] **Step 1: 写失败测试**

Create `tests/data/test_transforms.py`:

```python
from PIL import Image
from torchvision import transforms

from plantdisease.data.transforms import build_train_transform


def test_build_train_transform_can_include_randaugment_and_random_erasing() -> None:
    transform = build_train_transform(
        32,
        randaugment_enabled=True,
        randaugment_num_ops=2,
        randaugment_magnitude=9,
        random_erasing_enabled=True,
        random_erasing_probability=0.5,
    )

    names = [type(item).__name__ for item in transform.transforms]

    assert "RandAugment" in names
    assert "RandomErasing" in names


def test_build_train_transform_outputs_tensor_with_expected_shape() -> None:
    image = Image.new("RGB", (40, 40), (80, 120, 40))
    transform = build_train_transform(32)

    tensor = transform(image)

    assert tensor.shape == (3, 32, 32)
```

- [ ] **Step 2: 验证 RED**

Run: `uv run pytest tests/data/test_transforms.py -q`

Expected: fails because `build_train_transform` does not accept the new keyword arguments.

- [ ] **Step 3: 实现可选 transform**

Modify `src/plantdisease/data/transforms.py`:

```python
def build_train_transform(
    image_size: int,
    randaugment_enabled: bool = False,
    randaugment_num_ops: int = 2,
    randaugment_magnitude: int = 9,
    random_erasing_enabled: bool = False,
    random_erasing_probability: float = 0.25,
) -> transforms.Compose:
    _validate_image_size(image_size)
    steps: list[object] = [
        transforms.Lambda(_convert_rgb),
        transforms.RandomResizedCrop(image_size, scale=(0.8, 1.0)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(10),
        transforms.ColorJitter(brightness=0.15, contrast=0.15, saturation=0.15),
    ]
    if randaugment_enabled:
        steps.append(
            transforms.RandAugment(
                num_ops=randaugment_num_ops,
                magnitude=randaugment_magnitude,
            )
        )
    steps.extend(
        [
            transforms.ToTensor(),
            transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
        ]
    )
    if random_erasing_enabled:
        steps.append(transforms.RandomErasing(p=random_erasing_probability))
    return transforms.Compose(steps)
```

- [ ] **Step 4: 验证 GREEN**

Run: `uv run pytest tests/data/test_transforms.py -q`

Expected: transform tests pass.

- [ ] **Step 5: 提交**

```bash
git add src/plantdisease/data/transforms.py tests/data/test_transforms.py
git commit -m "feat: add week3 train transform switches"
```

---

### Task 5: Scheduler and EMA

**Files:**
- Create: `src/plantdisease/training/schedulers.py`
- Create: `src/plantdisease/training/ema.py`
- Create: `tests/training/test_schedulers.py`
- Create: `tests/training/test_ema.py`

**Interfaces:**
- Produces: `build_scheduler(optimizer, config: SchedulerConfig, total_steps: int)`
- Produces: `ModelEMA(model: nn.Module, decay: float)`

**教学说明：** Cosine Scheduler 改的是学习率函数 `lr_t`，让更新步子逐渐变小。EMA 改的是评估用参数 `theta_ema`，它不是梯度更新，而是对历史模型参数做指数加权平均。

- [ ] **Step 1: 写失败测试**

Create scheduler test:

```python
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
```

Create EMA test:

```python
import torch
from torch import nn

from plantdisease.training.ema import ModelEMA


def test_model_ema_updates_shadow_weights() -> None:
    model = nn.Linear(1, 1, bias=False)
    model.weight.data.fill_(1.0)
    ema = ModelEMA(model, decay=0.5)

    model.weight.data.fill_(3.0)
    ema.update(model)

    assert ema.shadow["weight"].item() == pytest.approx(2.0)


def test_model_ema_average_parameters_context_restores_weights() -> None:
    model = nn.Linear(1, 1, bias=False)
    model.weight.data.fill_(1.0)
    ema = ModelEMA(model, decay=0.5)
    ema.shadow["weight"].fill_(5.0)

    with ema.average_parameters(model):
        assert model.weight.item() == pytest.approx(5.0)

    assert model.weight.item() == pytest.approx(1.0)
```

- [ ] **Step 2: 验证 RED**

Run:

```bash
uv run pytest tests/training/test_schedulers.py tests/training/test_ema.py -q
```

Expected: fails because scheduler and EMA modules do not exist.

- [ ] **Step 3: 实现 scheduler**

Use `torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=total_steps, eta_min=config.eta_min)` for `scheduler.name == "cosine"`.

- [ ] **Step 4: 实现 EMA**

Implement `ModelEMA` with:

```python
class ModelEMA:
    def __init__(self, model: nn.Module, decay: float) -> None: ...
    def update(self, model: nn.Module) -> None: ...
    @contextmanager
    def average_parameters(self, model: nn.Module): ...
    def state_dict(self) -> dict[str, torch.Tensor]: ...
    def load_state_dict(self, state_dict: Mapping[str, torch.Tensor]) -> None: ...
```

- [ ] **Step 5: 验证 GREEN**

Run:

```bash
uv run pytest tests/training/test_schedulers.py tests/training/test_ema.py -q
```

Expected: scheduler and EMA tests pass.

- [ ] **Step 6: 提交**

```bash
git add src/plantdisease/training/schedulers.py src/plantdisease/training/ema.py tests/training/test_schedulers.py tests/training/test_ema.py
git commit -m "feat: add scheduler and ema utilities"
```

---

### Task 6: Training Engine Hooks

**Files:**
- Modify: `src/plantdisease/training/engine.py`
- Modify: `tests/training/test_engine.py`

**Interfaces:**
- Extends: `train_one_epoch(..., batch_mixer=None, scheduler=None, ema=None, num_classes=None)`
- Extends: `evaluate(..., ema=None)`

**教学说明：** 训练循环里有三类 hook：batch 进入模型前可能被 Mixup/CutMix 改掉；optimizer 更新后 scheduler 改学习率；optimizer 更新后 EMA 更新影子参数。顺序不能乱。

- [ ] **Step 1: 写失败测试**

Add to `tests/training/test_engine.py`:

```python
def test_train_one_epoch_accepts_soft_label_batch_mixer() -> None:
    model = make_model()

    def mixer(images, labels):
        targets = torch.nn.functional.one_hot(labels, num_classes=2).float()
        return images, targets

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
    scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=1, gamma=0.5)

    train_one_epoch(
        model,
        make_loader(),
        nn.CrossEntropyLoss(),
        optimizer,
        torch.device("cpu"),
        scheduler=scheduler,
    )

    assert scheduler.last_epoch == 1
```

Import `soft_cross_entropy` from `plantdisease.training.losses`.

- [ ] **Step 2: 验证 RED**

Run: `uv run pytest tests/training/test_engine.py -q`

Expected: fails because `train_one_epoch` does not accept new hook arguments.

- [ ] **Step 3: 实现 engine hooks**

Modify `train_one_epoch`:

```python
if batch_mixer is not None:
    images, labels_for_loss = batch_mixer(images, labels)
else:
    labels_for_loss = labels
loss = criterion(model(images), labels_for_loss)
...
optimizer.step()
if scheduler is not None:
    scheduler.step()
if ema is not None:
    ema.update(model)
```

Keep `batch_size = labels.shape[0]` so mixed labels do not break sample counts.

For `evaluate`, if `ema` is passed, evaluate inside `with ema.average_parameters(model):`.

- [ ] **Step 4: 验证 GREEN**

Run: `uv run pytest tests/training/test_engine.py -q`

Expected: engine tests pass.

- [ ] **Step 5: 提交**

```bash
git add src/plantdisease/training/engine.py tests/training/test_engine.py
git commit -m "feat: add training engine hooks"
```

---

### Task 7: Baseline Orchestration

**Files:**
- Modify: `src/plantdisease/training/baseline.py`
- Modify: `tests/training/test_baseline_run.py`

**Interfaces:**
- Consumes all new config and utilities.
- Produces manifests with `week3` method metadata.

**教学说明：** 到这一步才把零件接进训练。它不是新增数学，而是保证实验产物可审计：配置、manifest、checkpoint 和指标都要说明本次到底开了什么。

- [ ] **Step 1: 写失败测试**

Add to `tests/training/test_baseline_run.py` a small config with label smoothing, cosine scheduler, and EMA enabled. Assert manifest records these settings:

```python
def test_baseline_training_records_week3_method_config(tmp_path: Path, monkeypatch) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
data:
  image_size: 32
  batch_size: 4
  num_workers: 0
  train_ratio: 0.75
  validation_ratio: 0.25
  test_ratio: 0.0
model:
  name: mobilenet_v2
  pretrained: false
training:
  seed: 13
  epochs: 1
  learning_rate: 0.05
  device: cpu
loss:
  name: cross_entropy
  label_smoothing: 0.1
scheduler:
  name: cosine
ema:
  enabled: true
  decay: 0.9
""".strip(),
        encoding="utf-8",
    )
    train_split = FakeLazySplit(_records("train", 6))
    test_split = FakeLazySplit(_records("test", 3))

    def fake_loader(cache_dir, max_samples_per_split=None):
        return {"train": train_split, "test": test_split}, ["healthy", "synthetic_blight"]

    monkeypatch.setattr(
        "plantdisease.training.baseline.hf_data.load_plantvillage_dataset_splits",
        fake_loader,
    )

    run_baseline_training(
        config_path=config_path,
        cache_dir=tmp_path / "cache",
        output_dir=tmp_path / "run",
        samples_per_class=2,
        log_every=0,
        logger=lambda _: None,
    )

    manifest = json.loads((tmp_path / "run" / "run_manifest.json").read_text())
    assert manifest["loss"]["label_smoothing"] == 0.1
    assert manifest["scheduler"]["name"] == "cosine"
    assert manifest["ema"]["enabled"] is True
```

- [ ] **Step 2: 验证 RED**

Run: `uv run pytest tests/training/test_baseline_run.py -q`

Expected: fails because baseline orchestration does not record or use Week 3 config.

- [ ] **Step 3: 接入 orchestration**

In `baseline.py`:

- call `build_train_transform(..., config.augmentation...)`;
- call `build_criterion(config.loss)`;
- call `build_batch_mixer(config.augmentation, len(class_names))`;
- call `build_scheduler(..., total_steps=len(train_loader) * config.training.epochs)`;
- create `ModelEMA` if `config.ema.enabled`;
- pass hooks into `train_one_epoch`;
- evaluate with EMA when enabled;
- save checkpoint from EMA weights when enabled;
- add `augmentation`, `loss`, `scheduler`, and `ema` to `run_manifest.json`.

- [ ] **Step 4: 验证 GREEN**

Run:

```bash
uv run pytest tests/training/test_baseline_run.py tests/training/test_engine.py -q
```

Expected: baseline and engine tests pass.

- [ ] **Step 5: 提交**

```bash
git add src/plantdisease/training/baseline.py tests/training/test_baseline_run.py
git commit -m "feat: wire week3 methods into training"
```

---

### Task 8: Week 3 Configs and Plan Report

**Files:**
- Create: `configs/week3/resnet50_label_smoothing.yaml`
- Create: `configs/week3/resnet50_focal_loss.yaml`
- Create: `configs/week3/resnet50_randaugment.yaml`
- Create: `configs/week3/resnet50_random_erasing.yaml`
- Create: `configs/week3/resnet50_mixup.yaml`
- Create: `configs/week3/resnet50_cutmix.yaml`
- Create: `configs/week3/resnet50_cosine_scheduler.yaml`
- Create: `configs/week3/resnet50_ema.yaml`
- Create: `reports/week3_ablation_plan.md`

**Interfaces:**
- Produces formal experiment matrix and commands.

**教学说明：** 配置文件是“实验假设”的物化版本。每个 yaml 都应该只有一个因素和 baseline 不同，这样结果变化才能解释。

- [ ] **Step 1: 创建 configs**

Each config copies Week 2 ResNet50 baseline:

```yaml
data:
  image_size: 224
  batch_size: 16
  num_workers: 0
  train_ratio: 0.85
  validation_ratio: 0.15
  test_ratio: 0.0
model:
  name: resnet50
  pretrained: true
training:
  seed: 42
  epochs: 5
  learning_rate: 0.001
  device: auto
```

Then each file adds only its one changed section. Example:

```yaml
loss:
  name: cross_entropy
  label_smoothing: 0.1
```

For EMA:

```yaml
ema:
  enabled: true
  decay: 0.999
```

- [ ] **Step 2: 创建中文计划报告**

Create `reports/week3_ablation_plan.md` with:

- baseline row: `outputs/plantvillage/baseline_resnet50_seed42/`;
- one-variable matrix;
- plain-language purpose;
- mathematical principle;
- formal command for each experiment;
- single-seed limitation.

- [ ] **Step 3: 验证 configs 可加载**

Run:

```bash
uv run python - <<'PY'
from pathlib import Path
from plantdisease.config import ExperimentConfig
for path in sorted(Path("configs/week3").glob("*.yaml")):
    ExperimentConfig.from_yaml(path)
    print(path)
PY
```

Expected: all Week 3 configs print with no exception.

- [ ] **Step 4: 提交**

```bash
git add configs/week3 reports/week3_ablation_plan.md
git commit -m "docs: add week3 ablation matrix"
```

---

### Task 9: Full Verification and Smoke Run

**Files:**
- No source file changes unless verification finds a bug.
- Generate: `outputs/plantvillage/week3_ablation/smoke_label_smoothing_resnet50_seed42/`

**Interfaces:**
- Confirms the implemented pipeline can run before formal training.

**教学说明：** 单元测试证明数学零件是对的；smoke run 证明这些零件接到真实数据管线后不会断。smoke 不算正式实验结果。

- [ ] **Step 1: 全量验证**

Run:

```bash
git diff --check
uv run ruff check .
uv run pytest -q
```

Expected: all pass.

- [ ] **Step 2: 小样本 smoke**

Run:

```bash
uv run plant-train \
  --config configs/week3/resnet50_label_smoothing.yaml \
  --cache-dir data/huggingface \
  --output-dir outputs/plantvillage/week3_ablation/smoke_label_smoothing_resnet50_seed42 \
  --samples-per-class 2 \
  --log-every 5
```

Expected: status completed and output artifacts exist.

- [ ] **Step 3: 记录 smoke 结果**

Update `reports/week3_ablation_plan.md` with the smoke output path and status.

- [ ] **Step 4: 提交**

```bash
git add reports/week3_ablation_plan.md
git commit -m "test: verify week3 ablation smoke run"
```

---

### Task 10: Formal Experiment Handoff

**Files:**
- Generate formal outputs under `outputs/plantvillage/week3_ablation/`
- Later update: `reports/week3_ablation_results.md`, `TASKS.md`, `README.md`, `docs/artifact-index.md`

**Interfaces:**
- Produces official single-seed Week 3 experiment evidence.

**教学说明：** 这里开始进入“花时间换证据”。每条命令都很贵，所以先跑单变量，不先跑组合。组合实验必须等单变量结果告诉我们哪些方法值得合并。

- [ ] **Step 1: 跑单变量正式实验**

Use this pattern:

```bash
uv run plant-train \
  --config configs/week3/resnet50_label_smoothing.yaml \
  --cache-dir data/huggingface \
  --output-dir outputs/plantvillage/week3_ablation/label_smoothing_resnet50_seed42 \
  --log-every 50
```

Repeat for:

```text
focal_loss
randaugment
random_erasing
mixup
cutmix
cosine_scheduler
ema
```

- [ ] **Step 2: 汇总结果**

After runs finish, parse:

```text
outputs/plantvillage/week3_ablation/*/metrics.json
outputs/plantvillage/week3_ablation/*/validation_metrics.json
outputs/plantvillage/week3_ablation/*/training_curve.json
outputs/plantvillage/week3_ablation/*/run_manifest.json
```

- [ ] **Step 3: 选择组合实验**

Only include methods that either improve Macro F1 or give a defensible stability/regularization reason without harming test Macro F1.

- [ ] **Step 4: 写结果报告**

Create `reports/week3_ablation_results.md` with:

- all positive, neutral, and negative results;
- delta vs ResNet50 baseline;
- per-class F1 discussion;
- final model decision;
- single-seed limitation.

---

## Self-Review

- Spec coverage: config, losses, Mixup, CutMix, RandAugment, Random Erasing, Cosine Scheduler, EMA, engine integration, configs, smoke, formal commands, reports, and teaching explanations are covered.
- 完整性检查：本计划不保留未决定的小节或等待后续补写的实现空位。
- Type consistency: function and class names introduced in early tasks are reused consistently in later tasks.
- Scope check: Grad-CAM, calibration, deployment, and leaf-entity split are outside this Week 3 implementation plan.
