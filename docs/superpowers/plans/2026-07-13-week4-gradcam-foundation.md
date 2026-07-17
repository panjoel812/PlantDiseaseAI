# Week 4 Grad-CAM Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a reusable, tested Grad-CAM core for the frozen Week 4 ResNet50 candidate without claiming that fixed analysis samples or the Week 3 exit condition are complete.

**Architecture:** Add a small `plantdisease.explainability` package. `layers.py` owns audited model-name-to-layer mappings, while `gradcam.py` owns activation capture, gradient weighting, per-sample normalization, state restoration, and hook cleanup. Dataset loading, overlays, sample selection, plots, and reports remain outside this first implementation.

**Tech Stack:** Python 3.12, PyTorch 2.5–2.x, torchvision 0.20–0.x, pytest 8–9, Ruff 0.9–0.x.

## Global Constraints

- Work on branch `codex/week4-explainability`, based on `be55979` through design commit `1074dc8`.
- Do not add a new dependency; use native PyTorch autograd and forward hooks.
- Freeze the formal Week 4 candidate to `outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/checkpoint.pt` and the ResNet50 target layer to `layer4.2`.
- Grad-CAM outputs are correlation visualizations, not causal explanations.
- Preserve the model's top-level train/eval state and every parameter's existing `.grad` value.
- Do not check `[ ] 可解释性分析所需的模型、层选择和样本索引已经冻结。`; the sample index is outside this plan and remains unfinished.
- Do not check the Week 4 implementation item that also requires an overlay method; this plan does not implement overlays.
- Only check the Week 4 Grad-CAM testing item after focused tests, the full suite, and Ruff all pass.
- Never represent unit-test output as a completed formal Grad-CAM atlas or PlantVillage explanation result.

---

### Task 0: Verify the Clean Baseline

**Files:**
- Inspect: `pyproject.toml`
- Inspect: `tests/`

**Interfaces:**
- Consumes: the repository state containing plan commit `f228531`.
- Produces: a recorded clean baseline before feature edits.

- [ ] **Step 1: Confirm branch and worktree state**

Run:

```bash
git status --short --branch
git log -2 --oneline --decorate
```

Expected: branch `codex/week4-explainability`, no changed paths, and recent history contains plan commit `f228531`.

- [ ] **Step 2: Run the existing test suite**

Run:

```bash
uv run pytest -q
```

Expected: exit code 0 with no failures. If it fails, stop implementation and report the exact pre-existing failures.

- [ ] **Step 3: Run the existing static checks**

Run:

```bash
uv run ruff check .
```

Expected: exit code 0.

---

### Task 1: Add Audited Target-Layer Resolution

**Files:**
- Create: `src/plantdisease/explainability/layers.py`
- Create: `src/plantdisease/explainability/__init__.py`
- Create: `tests/explainability/test_layers.py`

**Interfaces:**
- Consumes: `plantdisease.models.factory.create_model(name, num_classes, pretrained)`.
- Produces: `TargetLayer(name: str, module: nn.Module)` and `resolve_target_layer(model: nn.Module, model_name: str) -> TargetLayer`.

- [ ] **Step 1: Write the failing layer-resolution tests**

Create `tests/explainability/test_layers.py`:

```python
import pytest
from torch import nn

from plantdisease.explainability.layers import TargetLayer, resolve_target_layer
from plantdisease.models.factory import create_model


@pytest.mark.parametrize(
    ("model_name", "expected_name"),
    [
        ("mobilenet_v2", "features.18.0"),
        ("resnet18", "layer4.1"),
        ("resnet50", "layer4.2"),
        ("efficientnet_b0", "features.8.0"),
        ("efficientnet_v2_s", "features.7.0"),
    ],
)
def test_resolve_target_layer_returns_audited_spatial_module(
    model_name: str,
    expected_name: str,
) -> None:
    model = create_model(model_name, num_classes=3, pretrained=False)

    target = resolve_target_layer(model, model_name)

    assert isinstance(target, TargetLayer)
    assert target.name == expected_name
    assert isinstance(target.module, nn.Module)


def test_resnet50_target_layer_is_frozen_to_last_bottleneck_output() -> None:
    model = create_model("resnet50", num_classes=3, pretrained=False)

    target = resolve_target_layer(model, "resnet50")

    assert target.name == "layer4.2"
    assert target.module is model.layer4[2]


def test_resolve_target_layer_rejects_unknown_model_name() -> None:
    model = create_model("resnet18", num_classes=3, pretrained=False)

    with pytest.raises(ValueError, match="unsupported model"):
        resolve_target_layer(model, "unknown")
```

- [ ] **Step 2: Run the tests and verify the expected RED state**

Run:

```bash
uv run pytest tests/explainability/test_layers.py -q
```

Expected: collection fails with `ModuleNotFoundError` for `plantdisease.explainability` because production files do not exist.

- [ ] **Step 3: Implement the minimal audited resolver**

Create `src/plantdisease/explainability/layers.py`:

```python
"""Audited Grad-CAM target-layer selection for supported classifiers."""

from dataclasses import dataclass

from torch import nn


@dataclass(frozen=True)
class TargetLayer:
    """A stable layer name paired with the resolved model module."""

    name: str
    module: nn.Module


def resolve_target_layer(model: nn.Module, model_name: str) -> TargetLayer:
    """Resolve the audited final spatial module for a supported model."""
    if model_name == "mobilenet_v2":
        target = TargetLayer("features.18.0", model.features[18][0])
    elif model_name == "resnet18":
        target = TargetLayer("layer4.1", model.layer4[1])
    elif model_name == "resnet50":
        target = TargetLayer("layer4.2", model.layer4[2])
    elif model_name == "efficientnet_b0":
        target = TargetLayer("features.8.0", model.features[8][0])
    elif model_name == "efficientnet_v2_s":
        target = TargetLayer("features.7.0", model.features[7][0])
    else:
        raise ValueError(f"unsupported model for Grad-CAM: {model_name}")

    return target
```

Create `src/plantdisease/explainability/__init__.py`:

```python
"""Explainability interfaces shared by offline analysis and serving."""

from plantdisease.explainability.layers import TargetLayer, resolve_target_layer

__all__ = ["TargetLayer", "resolve_target_layer"]
```

- [ ] **Step 4: Run the focused tests and verify GREEN**

Run:

```bash
uv run pytest tests/explainability/test_layers.py -q
```

Expected: `7 passed`.

- [ ] **Step 5: Run Ruff on the new resolver files**

Run:

```bash
uv run ruff check src/plantdisease/explainability tests/explainability/test_layers.py
```

Expected: exit code 0.

- [ ] **Step 6: Commit the resolver checkpoint**

```bash
git add src/plantdisease/explainability tests/explainability/test_layers.py
git commit -m "feat: resolve gradcam target layers"
```

---

### Task 2: Implement Grad-CAM with Batch and Lifecycle Guarantees

**Files:**
- Create: `src/plantdisease/explainability/gradcam.py`
- Modify: `src/plantdisease/explainability/__init__.py`
- Create: `tests/explainability/test_gradcam.py`

**Interfaces:**
- Consumes: any classifier returning `(N, C)` logits and a target module returning `(N, K, h, w)` activations.
- Produces: `GradCAM.generate(inputs, target_classes=None) -> torch.Tensor` with CPU `float32` shape `(N, H, W)` and values in `[0, 1]`.

- [ ] **Step 1: Write the failing Grad-CAM behavior tests**

Create `tests/explainability/test_gradcam.py`:

```python
import pytest
import torch
from torch import nn

from plantdisease.explainability.gradcam import GradCAM


class TinyCamModel(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.conv = nn.Conv2d(3, 4, kernel_size=3, padding=1)
        self.relu = nn.ReLU()
        self.pool = nn.AdaptiveAvgPool2d(1)
        self.fc = nn.Linear(4, 3)

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        features = self.relu(self.conv(inputs))
        return self.fc(self.pool(features).flatten(1))


class InvalidOutputModel(TinyCamModel):
    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        return self.relu(self.conv(inputs))


class UnusedLayerModel(TinyCamModel):
    def __init__(self) -> None:
        super().__init__()
        self.unused = nn.Conv2d(3, 4, kernel_size=1)


def make_model() -> TinyCamModel:
    torch.manual_seed(7)
    return TinyCamModel()


def test_generate_returns_aligned_normalized_cpu_heatmaps() -> None:
    model = make_model()
    inputs = torch.randn(1, 3, 11, 13)

    with GradCAM(model, model.conv) as gradcam:
        heatmaps = gradcam.generate(inputs, torch.tensor([1]))

    assert heatmaps.shape == (1, 11, 13)
    assert heatmaps.device.type == "cpu"
    assert heatmaps.dtype == torch.float32
    assert torch.isfinite(heatmaps).all()
    assert float(heatmaps.min()) >= 0.0
    assert float(heatmaps.max()) <= 1.0


def test_generate_supports_per_sample_batch_targets() -> None:
    model = make_model()
    inputs = torch.randn(2, 3, 9, 7)

    with GradCAM(model, model.conv) as gradcam:
        heatmaps = gradcam.generate(inputs, torch.tensor([0, 2]))

    assert heatmaps.shape == (2, 9, 7)


def test_default_targets_match_explicit_predicted_classes() -> None:
    model = make_model().eval()
    inputs = torch.randn(2, 3, 8, 10)
    with torch.inference_mode():
        predicted_classes = model(inputs).argmax(dim=1)

    with GradCAM(model, model.conv) as gradcam:
        implicit = gradcam.generate(inputs)
        explicit = gradcam.generate(inputs, predicted_classes)

    assert torch.allclose(implicit, explicit)


def test_zero_activations_return_zero_heatmap_without_nan() -> None:
    model = make_model()
    nn.init.zeros_(model.conv.weight)
    nn.init.zeros_(model.conv.bias)

    with GradCAM(model, model.conv) as gradcam:
        heatmaps = gradcam.generate(torch.randn(1, 3, 6, 6), torch.tensor([0]))

    assert torch.equal(heatmaps, torch.zeros_like(heatmaps))
    assert torch.isfinite(heatmaps).all()


@pytest.mark.parametrize(
    ("inputs", "message"),
    [
        (torch.zeros(3, 8, 8), "NCHW"),
        (torch.zeros(1, 3, 8, 8, dtype=torch.long), "floating point"),
        (torch.zeros(0, 3, 8, 8), "non-empty"),
    ],
)
def test_generate_rejects_invalid_inputs(inputs: torch.Tensor, message: str) -> None:
    model = make_model()

    with GradCAM(model, model.conv) as gradcam:
        with pytest.raises(ValueError, match=message):
            gradcam.generate(inputs)


@pytest.mark.parametrize(
    ("targets", "message"),
    [
        (torch.tensor([[0]]), "shape"),
        (torch.tensor([0.0]), "integer"),
        (torch.tensor([3]), "range"),
    ],
)
def test_generate_rejects_invalid_target_classes(
    targets: torch.Tensor,
    message: str,
) -> None:
    model = make_model()

    with GradCAM(model, model.conv) as gradcam:
        with pytest.raises(ValueError, match=message):
            gradcam.generate(torch.randn(1, 3, 8, 8), targets)


def test_generate_rejects_non_logit_model_output() -> None:
    model = InvalidOutputModel()

    with GradCAM(model, model.conv) as gradcam:
        with pytest.raises(ValueError, match="two-dimensional logits"):
            gradcam.generate(torch.randn(1, 3, 8, 8))


def test_generate_rejects_target_layer_not_used_by_forward() -> None:
    model = UnusedLayerModel()

    with GradCAM(model, model.unused) as gradcam:
        with pytest.raises(RuntimeError, match="target layer was not executed"):
            gradcam.generate(torch.randn(1, 3, 8, 8))


def test_generate_preserves_parameter_gradients() -> None:
    model = make_model()
    first_parameter = next(model.parameters())
    first_parameter.grad = torch.ones_like(first_parameter)
    before = {
        name: None if parameter.grad is None else parameter.grad.clone()
        for name, parameter in model.named_parameters()
    }

    with GradCAM(model, model.conv) as gradcam:
        gradcam.generate(torch.randn(1, 3, 8, 8))

    for name, parameter in model.named_parameters():
        expected = before[name]
        if expected is None:
            assert parameter.grad is None
        else:
            assert torch.equal(parameter.grad, expected)


def test_generate_restores_training_state_after_success() -> None:
    model = make_model().train()

    with GradCAM(model, model.conv) as gradcam:
        gradcam.generate(torch.randn(1, 3, 8, 8))
        assert model.training


def test_generate_restores_training_state_after_error() -> None:
    model = make_model().train()

    with GradCAM(model, model.conv) as gradcam:
        with pytest.raises(ValueError, match="range"):
            gradcam.generate(torch.randn(1, 3, 8, 8), torch.tensor([9]))
        assert model.training


def test_context_removes_hook_without_accumulating_hooks() -> None:
    model = make_model()
    hook_count = len(model.conv._forward_hooks)

    with GradCAM(model, model.conv) as gradcam:
        assert len(model.conv._forward_hooks) == hook_count + 1
        gradcam.generate(torch.randn(1, 3, 8, 8))
        gradcam.generate(torch.randn(1, 3, 8, 8))
        assert len(model.conv._forward_hooks) == hook_count + 1

    assert len(model.conv._forward_hooks) == hook_count


def test_close_is_idempotent() -> None:
    model = make_model()
    hook_count = len(model.conv._forward_hooks)
    gradcam = GradCAM(model, model.conv)

    gradcam.close()
    gradcam.close()

    assert len(model.conv._forward_hooks) == hook_count


def test_closed_instance_rejects_generate() -> None:
    model = make_model()
    gradcam = GradCAM(model, model.conv)
    gradcam.close()

    with pytest.raises(RuntimeError, match="closed"):
        gradcam.generate(torch.randn(1, 3, 8, 8))


def test_generate_rejects_model_input_device_mismatch() -> None:
    model = make_model().to("meta")

    with GradCAM(model, model.conv) as gradcam:
        with pytest.raises(ValueError, match="same device"):
            gradcam.generate(torch.randn(1, 3, 8, 8))
```

- [ ] **Step 2: Run the tests and verify the expected RED state**

Run:

```bash
uv run pytest tests/explainability/test_gradcam.py -q
```

Expected: collection fails with `ModuleNotFoundError` for `plantdisease.explainability.gradcam`.

- [ ] **Step 3: Implement the minimal complete Grad-CAM core**

Create `src/plantdisease/explainability/gradcam.py`:

```python
"""Native PyTorch Grad-CAM with explicit lifecycle guarantees."""

from __future__ import annotations

import torch
from torch import nn
from torch.nn import functional as F
from torch.utils.hooks import RemovableHandle


class GradCAM:
    """Generate normalized class-activation heatmaps for a convolutional layer."""

    def __init__(self, model: nn.Module, target_layer: nn.Module) -> None:
        self.model = model
        self.target_layer = target_layer
        self._activation: torch.Tensor | None = None
        self._closed = False
        self._hook: RemovableHandle | None = target_layer.register_forward_hook(
            self._capture_activation
        )

    def _capture_activation(
        self,
        _module: nn.Module,
        _inputs: tuple[object, ...],
        output: object,
    ) -> None:
        if not isinstance(output, torch.Tensor) or output.ndim != 4:
            raise RuntimeError("Grad-CAM target layer must return an NCHW tensor")
        self._activation = output

    def _model_device(self) -> torch.device | None:
        parameter = next(self.model.parameters(), None)
        if parameter is not None:
            return parameter.device
        buffer = next(self.model.buffers(), None)
        return None if buffer is None else buffer.device

    def _validate_inputs(self, inputs: torch.Tensor) -> None:
        if inputs.ndim != 4:
            raise ValueError("inputs must be an NCHW tensor")
        if not torch.is_floating_point(inputs):
            raise ValueError("inputs must use a floating point dtype")
        if inputs.shape[0] == 0:
            raise ValueError("inputs batch must be non-empty")
        model_device = self._model_device()
        if model_device is not None and model_device != inputs.device:
            raise ValueError("model and inputs must be on the same device")

    @staticmethod
    def _validate_logits(logits: object, batch_size: int) -> torch.Tensor:
        if not isinstance(logits, torch.Tensor) or logits.ndim != 2:
            raise ValueError("model must return two-dimensional logits")
        if logits.shape[0] != batch_size or logits.shape[1] == 0:
            raise ValueError("model logits shape must be (batch, classes)")
        return logits

    @staticmethod
    def _select_targets(
        logits: torch.Tensor,
        target_classes: torch.Tensor | None,
    ) -> torch.Tensor:
        if target_classes is None:
            return logits.argmax(dim=1)
        if target_classes.shape != (logits.shape[0],):
            raise ValueError("target_classes shape must be (batch,)")
        integer_dtypes = {
            torch.uint8,
            torch.int8,
            torch.int16,
            torch.int32,
            torch.int64,
        }
        if target_classes.dtype not in integer_dtypes:
            raise ValueError("target_classes must use an integer dtype")
        targets = target_classes.to(device=logits.device, dtype=torch.long)
        if bool(((targets < 0) | (targets >= logits.shape[1])).any()):
            raise ValueError("target_classes values are outside the class range")
        return targets

    @staticmethod
    def _normalize(heatmaps: torch.Tensor) -> torch.Tensor:
        shifted = heatmaps - heatmaps.amin(dim=(1, 2), keepdim=True)
        maxima = shifted.amax(dim=(1, 2), keepdim=True)
        normalized = shifted / maxima.clamp_min(torch.finfo(shifted.dtype).eps)
        return torch.where(maxima > 0, normalized, torch.zeros_like(normalized))

    def generate(
        self,
        inputs: torch.Tensor,
        target_classes: torch.Tensor | None = None,
    ) -> torch.Tensor:
        """Return one input-aligned, normalized heatmap per batch item."""
        if self._closed:
            raise RuntimeError("GradCAM instance is closed")
        self._validate_inputs(inputs)
        original_training = self.model.training
        self._activation = None
        try:
            self.model.eval()
            with torch.inference_mode(False), torch.enable_grad():
                logits = self._validate_logits(self.model(inputs), inputs.shape[0])
                activation = self._activation
                if activation is None:
                    raise RuntimeError("Grad-CAM target layer was not executed")
                targets = self._select_targets(logits, target_classes)
                scores = logits.gather(1, targets.unsqueeze(1)).sum()
                gradients = torch.autograd.grad(scores, activation)[0]
                weights = gradients.mean(dim=(2, 3), keepdim=True)
                heatmaps = torch.relu((weights * activation).sum(dim=1, keepdim=True))
                heatmaps = F.interpolate(
                    heatmaps,
                    size=inputs.shape[-2:],
                    mode="bilinear",
                    align_corners=False,
                ).squeeze(1)
                heatmaps = self._normalize(heatmaps)
                return heatmaps.detach().to(device="cpu", dtype=torch.float32)
        finally:
            self.model.train(original_training)

    def close(self) -> None:
        """Remove the registered hook; repeated calls are safe."""
        if self._hook is not None:
            self._hook.remove()
            self._hook = None
        self._activation = None
        self._closed = True

    def __enter__(self) -> GradCAM:
        if self._closed:
            raise RuntimeError("GradCAM instance is closed")
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()
```

Replace `src/plantdisease/explainability/__init__.py` with:

```python
"""Explainability interfaces shared by offline analysis and serving."""

from plantdisease.explainability.gradcam import GradCAM
from plantdisease.explainability.layers import TargetLayer, resolve_target_layer

__all__ = ["GradCAM", "TargetLayer", "resolve_target_layer"]
```

- [ ] **Step 4: Run the Grad-CAM tests and verify GREEN**

Run:

```bash
uv run pytest tests/explainability/test_gradcam.py -q
```

Expected after inference-mode hardening: `20 passed` because the three invalid-input cases and three invalid-target cases are parameterized and one regression test covers an outer `torch.inference_mode()` context.

- [ ] **Step 5: Run all explainability tests together**

Run:

```bash
uv run pytest tests/explainability -q
```

Expected: `26 passed`.

- [ ] **Step 6: Run Ruff on implementation and tests**

Run:

```bash
uv run ruff check src/plantdisease/explainability tests/explainability
```

Expected: exit code 0.

- [ ] **Step 7: Commit the Grad-CAM core checkpoint**

```bash
git add src/plantdisease/explainability tests/explainability/test_gradcam.py
git commit -m "feat: add tested gradcam core"
```

---

### Task 3: Verify the Repository and Synchronize Honest Status

**Files:**
- Modify: `TASKS.md`
- Modify: `README.md`
- Modify: `docs/artifact-index.md`

**Interfaces:**
- Consumes: passing explainability tests and the complete repository verification output.
- Produces: documentation that distinguishes tested core capability from ungenerated formal evidence.

- [ ] **Step 1: Run the full test suite before changing status**

Run:

```bash
uv run pytest -q
```

Expected: exit code 0 with no failures.

- [ ] **Step 2: Run the full static check**

Run:

```bash
uv run ruff check .
```

Expected: exit code 0.

- [ ] **Step 3: Update `TASKS.md` without closing the sample freeze**

Add this Week 4 status paragraph immediately after the Week 4 goal:

```markdown
> 当前状态（2026-07-13）：原生 PyTorch Grad-CAM 核心与五模型目标层解析已实现并通过单元测试。Week 4 正式候选仍为 `09_combo_candidate`，ResNet50 目标层冻结为 `layer4.2`。当前尚未实现热力图叠加、导出全测试集逐样本预测或冻结四象限样本索引，因此 Week 3 最后一项退出条件、Week 4 图集和错误分析仍未完成。
```

Change only this Week 4 testing checkbox:

```markdown
- [x] 为 Grad-CAM 输出形状、数值范围、批处理、梯度状态和模型 hook 清理添加测试。
```

Keep both of these items unchecked:

```markdown
- [ ] 可解释性分析所需的模型、层选择和样本索引已经冻结。
- [ ] 实现或集成 Grad-CAM，明确目标层、类别目标、归一化和叠加方法。
```

- [ ] **Step 4: Update `README.md` with the tested capability boundary**

Add a short Week 4 section before `## 推理`:

```markdown
## Week 4：Grad-CAM 基础能力

项目已实现原生 PyTorch Grad-CAM 核心和统一目标层解析，单张及批量热力图会对齐输入尺寸并逐样本归一化到 `[0, 1]`。当前正式候选使用 `09_combo_candidate` ResNet50 checkpoint，目标层冻结为 `layer4.2`。

当前仅完成代码与单元测试验证；固定样本索引、热力图叠加、正式图集、错误分析和校准分析尚未完成。Grad-CAM 表示相关性，不能作为因果解释或真实田间泛化证据。
```

- [ ] **Step 5: Add a Week 4 foundation entry to `docs/artifact-index.md`**

Append:

```markdown
## Week 4

| 证据 | 路径或生成命令 | 状态 |
| --- | --- | --- |
| Grad-CAM 核心 | `src/plantdisease/explainability/gradcam.py`、`tests/explainability/test_gradcam.py` | 已验证，覆盖输入对齐、归一化、批处理、外层 `inference_mode`、梯度状态和 hook 生命周期 |
| 目标层解析 | `src/plantdisease/explainability/layers.py`、`tests/explainability/test_layers.py` | 已验证，正式 ResNet50 目标层为 `layer4.2` |
| Week 4 基础验证 | `uv run pytest tests/explainability -q`、`uv run pytest -q`、`uv run ruff check .` | 仅代码与单元测试；固定样本和正式图集未完成 |
```

- [ ] **Step 6: Check documentation consistency and whitespace**

Run:

```bash
rg -n "样本索引已经冻结|Grad-CAM 基础能力|layer4\.2\.conv3" TASKS.md README.md docs/artifact-index.md
git diff --check
```

Expected: the Week 3 sample-freeze checkbox remains `[ ]`, the new capability boundary appears in all three documents, and `git diff --check` exits 0.

- [ ] **Step 7: Re-run final verification after documentation edits**

Run:

```bash
uv run pytest -q
uv run ruff check .
git status --short --branch
```

Expected: tests and Ruff exit 0; status lists only the intended Week 4 source, tests, and documentation changes since the last checkpoint.

- [ ] **Step 8: Commit the verified status synchronization**

```bash
git add TASKS.md README.md docs/artifact-index.md
git commit -m "docs: record gradcam foundation status"
```

---

## Completion Audit

Before reporting completion, verify each statement against fresh command output:

- `resolve_target_layer` supports all five existing factory names.
- ResNet50 resolves exactly to `layer4.2`.
- `GradCAM.generate` returns CPU `float32` heatmaps shaped `(N, H, W)` in `[0, 1]`.
- Batch targets, default prediction targets, constant maps, state restoration, preserved parameter gradients, device mismatch, repeated calls, and hook cleanup are tested.
- `uv run pytest tests/explainability -q`, `uv run pytest -q`, and `uv run ruff check .` all pass in the final repository state.
- `TASKS.md` keeps the Week 3 model/layer/sample-index freeze item unchecked.
- `TASKS.md` keeps the Week 4 implementation-and-overlay item unchecked.
- No formal Grad-CAM atlas, fixed sample set, error analysis, or PlantVillage explanation result is claimed.
