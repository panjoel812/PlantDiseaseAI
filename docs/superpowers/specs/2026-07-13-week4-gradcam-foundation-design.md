# Week 4 Grad-CAM Foundation Design

日期：2026-07-13

## 1. 目标与范围

本阶段为 Week 4 建立可复用、可测试的 Grad-CAM 基础能力。给定分类模型、目标空间模块、一个图像 batch 和每张图的目标类别，模块输出与输入空间尺寸一致、逐样本归一化到 `[0, 1]` 的热力图。

本设计只覆盖以下闭环：

- 原生 PyTorch Grad-CAM 计算。
- 已支持模型的稳定目标层解析。
- 热力图形状、范围、批处理、状态与 hook 生命周期测试。
- 冻结 Week 4 当前候选 checkpoint 和 ResNet50 目标层。

固定四象限样本索引、全测试集预测导出、错误分析、混淆矩阵、校准图、图集和阶段报告属于后续独立闭环。本阶段完成后，Week 3 的“样本索引已经冻结”退出项仍不能勾选。

## 2. 已冻结输入与研究边界

- 候选模型：`resnet50`。
- 配置：`configs/week3_ablation/09_combo_candidate.yaml`。
- checkpoint：`outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/checkpoint.pt`。
- 运行证据：`outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/run_manifest.json`。
- 数据协议：PlantVillage 官方 split，seed 42。
- 目标层：`layer4.2`，即 torchvision ResNet50 最后一个 residual block 的输出。该层位于残差合并之后，比 block 内部 `layer4.2.conv3` 更接近分类头实际使用的空间特征。
- 默认解释目标：模型预测类别；调用方也可显式传入每张图的目标类别。
- 输出含义：Grad-CAM 是输入区域与目标分数之间的相关性可视化，不是因果解释。

官方 split 已知存在 227 个跨 train/test 重叠 `leaf_id`，PlantVillage 背景也较受控。因此后续图表与报告不得把热力图或分类性能直接表述为真实田间泛化证据。

## 3. 方案选择

### 采用：原生 PyTorch 实现

在项目包内实现 Grad-CAM，只依赖现有 PyTorch。该方案可直接控制梯度计算、归一化、设备、批处理和 hook 清理，并能稳定复用于 Week 5 的服务层。

### 不采用：`pytorch-grad-cam`

该库功能丰富，但当前闭环只需要标准 Grad-CAM。新增依赖会增加版本、许可证和封装行为的审计成本，暂时没有必要。

### 不采用：一次性脚本

一次性脚本可以快速产图，但会让训练、离线分析和 Week 5 Demo 各自维护解释逻辑，不符合共享核心接口的仓库边界。

## 4. 模块边界

### `src/plantdisease/explainability/gradcam.py`

负责算法和生命周期，不负责数据集加载、checkpoint 选择、标签格式化、图像保存或报告排版。

公开接口：

```python
class GradCAM:
    def __init__(self, model: nn.Module, target_layer: nn.Module) -> None: ...
    def generate(
        self,
        inputs: torch.Tensor,
        target_classes: torch.Tensor | None = None,
    ) -> torch.Tensor: ...
    def close(self) -> None: ...
    def __enter__(self) -> "GradCAM": ...
    def __exit__(self, *args: object) -> None: ...
```

`generate` 接收 `NCHW` 浮点张量，返回 CPU 上的 `float32` 张量，形状为 `(N, H, W)`。`target_classes=None` 时逐样本使用 logits 的 `argmax`；显式类别张量必须为形状 `(N,)` 的整数索引。

### `src/plantdisease/explainability/layers.py`

负责把模型名映射为经过审计的目标层，避免 CLI、错误分析和 Demo 使用漂移的字符串或层选择副本。

公开接口：

```python
@dataclass(frozen=True)
class TargetLayer:
    name: str
    module: nn.Module

def resolve_target_layer(model: nn.Module, model_name: str) -> TargetLayer: ...
```

第一版支持项目模型工厂中的五个稳定名称：

| 模型名 | 目标层 |
| --- | --- |
| `mobilenet_v2` | `features.18.0` |
| `resnet18` | `layer4.1` |
| `resnet50` | `layer4.2` |
| `efficientnet_b0` | `features.8.0` |
| `efficientnet_v2_s` | `features.7.0` |

本轮正式证据只冻结和使用 ResNet50；其余映射用于保持现有模型工厂接口完整，并通过结构测试确认解析到稳定的空间模块。

### `src/plantdisease/explainability/__init__.py`

只导出 `GradCAM`、`TargetLayer` 和 `resolve_target_layer`，不包含实现副本。

## 5. Grad-CAM 数据流

1. 校验 `inputs` 为四维浮点张量，batch 非空。
2. 保存模型原有 `training` 状态并临时切换到 eval。
3. 通过目标层 forward hook 捕获激活张量 `A`。
4. 正常前向得到形状 `(N, C)` 的 logits。
5. 选择每张图的目标类别分数，并对分数之和调用 `torch.autograd.grad`，只求目标分数相对于激活 `A` 的梯度，不调用 `loss.backward()`，也不写入模型参数的 `.grad`。
6. 对梯度在空间维度求均值得到通道权重。
7. 计算通道加权激活和，经过 ReLU 得到粗热力图。
8. 使用双线性插值对齐到输入的 `(H, W)`。
9. 按每张图独立执行 min-max 归一化；常量或全零图返回全零，不能产生 NaN 或 Inf。
10. detach 后转换为 CPU `float32` 输出，并恢复模型原 `training` 状态。

对象注册一个目标层 forward hook。`close()` 必须可重复调用并移除 hook；上下文管理器退出时自动调用 `close()`。已关闭对象再次调用 `generate()` 时明确报错，避免静默产生无捕获激活的结果。

## 6. 状态、梯度与错误处理

- `generate` 内部用 `torch.inference_mode(False)` 和 `torch.enable_grad()` 临时建立 autograd 图，避免调用方外层推理模式阻断 Grad-CAM 梯度。
- 调用前已有的参数 `.grad` 内容必须保持不变；实现不主动清零或覆盖参数梯度。
- 无论成功或异常，模型的 train/eval 状态都恢复为调用前状态。
- 输入与模型必须位于同一设备；不在核心模块中隐式搬运模型或输入。
- 若目标层没有在前向中执行，抛出包含目标层问题的 `RuntimeError`。
- 若模型输出不是二维 logits，抛出明确的 `ValueError`。
- 若类别数量、dtype、形状或索引范围不合法，抛出 `ValueError`。
- 若 `close()` 后继续调用，抛出 `RuntimeError`。
- hook 必须在 `close()` 或上下文退出时移除；异常不得造成新的 hook 累积。

## 7. 测试设计

测试文件：

- `tests/explainability/test_gradcam.py`
- `tests/explainability/test_layers.py`

测试使用小型真实卷积网络或项目模型工厂，不加载预训练权重，不依赖 PlantVillage 数据或 90 MB checkpoint。

必须覆盖：

1. 单张输入输出为 `(1, H, W)`、CPU `float32`，数值有限且位于 `[0, 1]`。
2. 两张输入和两个不同目标类别可以批量生成热力图。
3. `target_classes=None` 等价于显式传入逐样本预测类别。
4. 常量或零贡献激活返回全零热力图，不出现 NaN。
5. 非 NCHW、非浮点、空 batch、错误类别形状、错误 dtype 和越界类别均被拒绝。
6. 模型原 train/eval 状态在成功和异常路径后都被恢复。
7. 参数已有 `.grad` 在调用后保持不变，未设置 `.grad` 的参数仍为 `None`。
8. 上下文退出后 hook 被移除；`close()` 可重复调用；关闭后调用失败。
9. 多次 `generate()` 不增加 hook 数量，也不复用上次调用的激活。
10. 五个模型名都解析到预期路径的空间模块；未知模型名被拒绝。
11. ResNet50 正式冻结层名称精确为 `layer4.2`。

TDD 顺序为：先写单个行为测试并观察预期失败，再写最小实现使其通过，然后运行相关测试；最后运行完整测试和 Ruff。

## 8. 完成证据与状态同步

本阶段只有在以下命令实际通过后才可更新状态：

```bash
uv run pytest tests/explainability -q
uv run pytest -q
uv run ruff check .
```

完成后同步：

- `TASKS.md`：只勾选 Grad-CAM 实现、Grad-CAM 测试以及已真实满足的局部验收；不提前勾选固定样本、图集、错误分析或 Week 4 退出条件。
- `README.md`：记录当前只有 Grad-CAM 核心模块通过测试，尚未生成正式图集。
- `docs/artifact-index.md`：记录代码、测试和验证命令。

如本阶段运行真实 checkpoint 冒烟验证，还需保存 checkpoint、目标层、目标类别、预处理、输入标识、设备和输出摘要；仅有单元测试时不得声称正式 Grad-CAM 图集已经完成。

## 9. 后续闭环

下一阶段将基于冻结 checkpoint 导出测试集逐样本预测，固定正确高置信、正确低置信、错误高置信和错误低置信四组样本索引。该阶段完成后，才能关闭 Week 3 最后一项退出条件，并继续生成 Grad-CAM 图集、基线对比、混淆分析和校准证据。
