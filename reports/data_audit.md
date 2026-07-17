# Week 1 数据审计记录

## 已验证：合成冒烟数据

运行 ID：`week1-synthetic-mobilenet_v2-seed42`

证据由以下命令生成：

```bash
uv run plant-smoke --output-dir outputs/smoke/week1 --seed 42 --image-size 32
```

本地审计结果：

- 样本数：12。
- 类别：`healthy` 与 `synthetic_blight`，各 6 张。
- 图像：全部为 32×32 RGB。
- 像素级精确重复组：0。
- 非法标签：0。

这些图片是程序生成的固定几何图案，只用于验证 Dataset、Transforms、DataLoader、模型、指标、checkpoint、推理和图表管线。其 Accuracy、F1 等结果没有科研或实际农业意义。

## 上游 PlantVillage 元数据

固定 loader revision：`9e97599868962bd0079b8db4b7f1efa9185fa1e7`。

上游 README 和 loader 声明：

- 38 个分类标签；
- `image`、`image_path`、`label`、`crop`、`disease`、`leaf_id` 字段；
- CC BY-SA 3.0；
- 预定义 train/test split，并用 `leaf_id` 表示物理叶片实体；
- 数据下载体积约 2 GB。

## 已验证：PlantVillage train split 本地审计

数据下载命令：

```bash
uv run python scripts/download_data.py --cache-dir data/huggingface
```

本地下载结果：

- 官方 train split：43,596 张。
- 官方 test split：10,709 张。
- 字段：`image`、`image_path`、`label`、`crop`、`disease`、`leaf_id`。

审计命令：

```bash
uv run plant-audit \
  --cache-dir data/huggingface \
  --output outputs/plantvillage/audit.json
```

当前审计覆盖 `load_plantvillage` 默认读取的 train split：

- 样本数：43,596。
- 类别数：38。
- 图像尺寸：全部 256×256。
- 颜色模式：全部 RGB。
- 像素级精确重复组：14。
- 非法标签：0。

EDA 命令：

```bash
uv run python scripts/eda.py \
  --cache-dir data/huggingface \
  --output-dir outputs/plantvillage/eda
```

生成图表：

- `outputs/plantvillage/eda/class_distribution.png`
- `outputs/plantvillage/eda/image_size_distribution.png`
- `outputs/plantvillage/eda/sample_grid.png`

## 官方 split 泄漏检查

检查字段：

- `leaf_id`：表示物理叶片实体或上游 fallback 实体标识；
- `image_path`：上游图片路径。

检查结果：

- train rows：43,596。
- test rows：10,709。
- train `leaf_id` 数：16,124。
- test `leaf_id` 数：4,118。
- train/test 重叠 `leaf_id`：227。
- train/test 重叠 `image_path`：0。

结论：官方 split 没有相同 `image_path` 交叉，但存在 `leaf_id` 交叉。当前 MobileNetV2 结果必须表述为官方 split baseline，不得表述为严格叶片实体隔离的无泄漏结果。

仍需补齐：官方 test split 的同等图像审计，以及 leaf_id-disjoint split 的生成与 baseline 对照。

## 已发现的上游兼容问题

Hub 仓库文件名为 `plant_village.py`，而自动发现按仓库名查找 `PlantVillage.py`。`datasets 4.x` 又移除了 dataset script 支持，导致 `load_dataset("mohanty/PlantVillage")` 把 `data.zip` 错误解析为 text 数据。

项目采取的可复现处理：

1. 锁定 `datasets>=3.6,<4`；
2. 用 `huggingface_hub` 下载固定 revision 的 `plant_village.py`；
3. 显式从该本地脚本加载 `default` 配置；
4. 用自动化测试验证 loader 路径、revision、配置和样本限制行为。
