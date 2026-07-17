# Week 1 阶段记录

## 研究问题

当前任务是单标签 image classification：输入一张叶片图片，输出一个植物—病害类别。数据没有病斑框，因此不是 object detection；也没有逐像素病斑 mask，因此不是 semantic segmentation。

## 已完成并验证的工程闭环

- Python 3.12 + uv 环境与锁文件。
- 固定随机种子的分层 train/validation/test 索引与 JSON manifest。
- 统一训练/评估 Transforms 和 PyTorch DataLoader。
- 类别、尺寸、颜色模式、非法标签和像素级重复审计。
- MobileNetV2 模型工厂与版本化 checkpoint。
- Accuracy、Macro Precision/Recall/F1、分类别指标和混淆矩阵。
- 训练、评估、单 batch 过拟合与 Top-k 推理。
- 合成数据端到端 smoke run 与 EDA 图表。

## 验证范围

基础端到端 smoke 使用 12 张程序生成的 RGB 图像、2 个合成类别和 CPU。它只证明接口、数据流、梯度、保存加载和证据生成能够工作。

合成 smoke 指标不代表 PlantVillage 效果，不用于比较模型，也不得写入简历。当前已完成 PlantVillage 官方 split baseline；但由于发现 `leaf_id` 层面的潜在泄漏风险，该结果不能表述为严格叶片实体隔离的无泄漏结果。

## PlantVillage 已完成进展

PlantVillage 已完成本地下载：

- 官方 train split：43,596 张。
- 官方 test split：10,709 张。
- 类别数：38。
- 字段包含 `leaf_id`，可用于后续泄漏检查。

train split 审计结果：

- 全部图像为 256×256 RGB。
- 非法标签：0。
- 像素级精确重复组：14。

真实训练入口已经支持：

- 官方 train/test split；
- 从官方 train 中划分 validation；
- 懒加载 Hugging Face 图片，避免一次性解码完整数据；
- `--log-every` 训练进度输出；
- `--samples-per-class` 按类别均衡抽样 probe。

## 已完成真实数据 probe

### 顺序 probe5000

命令：

```bash
uv run plant-train \
  --config configs/baseline_mobilenet_v2.yaml \
  --cache-dir data/huggingface \
  --output-dir outputs/plantvillage/baseline_mobilenet_v2_probe5000 \
  --max-samples 5000 \
  --log-every 20
```

结果摘要：

- train：4,250。
- validation：750。
- test：5,000。
- Accuracy：0.2918。
- Macro F1：0.1148。

该 probe 取每个 split 前 5,000 个样本，类别覆盖不均衡，只用于验证训练链路，不用于效果结论。

### 均衡 probe10

命令：

```bash
uv run plant-train \
  --config configs/baseline_mobilenet_v2.yaml \
  --cache-dir data/huggingface \
  --output-dir outputs/plantvillage/balanced_probe10_mobilenet_v2_seed42 \
  --samples-per-class 10 \
  --log-every 10
```

结果摘要：

- train：304。
- validation：76。
- test：380。
- Accuracy：0.8132。
- Macro F1：0.8044。

该 probe 每类 test 最多 10 张，适合教学、调试和检查 Macro F1 行为；样本量太小，不能作为正式简历指标。

## 完整 MobileNetV2 官方 split baseline

命令：

```bash
uv run plant-train \
  --config configs/baseline_mobilenet_v2.yaml \
  --cache-dir data/huggingface \
  --output-dir outputs/plantvillage/baseline_mobilenet_v2_seed42 \
  --log-every 50
```

运行摘要：

- 设备：MPS。
- 训练时长：1,601.26 秒。
- train：37,058。
- validation：6,538。
- official test：10,709。
- epoch 数：5。
- checkpoint：`outputs/plantvillage/baseline_mobilenet_v2_seed42/checkpoint.pt`。

测试集指标：

- Accuracy：0.9676。
- Macro Precision：0.9469。
- Macro Recall：0.9612。
- Macro F1：0.9491。

表现较弱的类别包括：

- `Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot`：F1 0.7260。
- `Potato___healthy`：F1 0.7356。
- `Corn_(maize)___Northern_Leaf_Blight`：F1 0.7701。
- `Tomato___Early_blight`：F1 0.8650。

checkpoint 重载与 Top-5 推理已验证：

```bash
uv run plant-predict \
  --checkpoint outputs/plantvillage/baseline_mobilenet_v2_seed42/checkpoint.pt \
  --image outputs/smoke/week1/example_input.png \
  --top-k 5
```

## 数据泄漏检查

检查字段：

- `leaf_id`：表示物理叶片实体或上游 fallback 实体标识；
- `image_path`：上游图片路径。

检查结果：

- 官方 train rows：43,596。
- 官方 test rows：10,709。
- train `leaf_id` 数：16,124。
- test `leaf_id` 数：4,118。
- train/test 重叠 `leaf_id`：227。
- train/test 重叠 `image_path`：0。

结论：官方 split 没有相同 `image_path` 交叉，但存在 `leaf_id` 交叉。当前 baseline 是“官方 split baseline”，可以作为复现实验结果，但不能作为严格无实体泄漏的最终研究结论。Week 2 Benchmark 应优先补充 leaf_id-disjoint split，或在对比表中显式标注该限制。

## 可复现性

smoke run 保存配置、seed、split、audit、checkpoint、metrics、predictions、Loss 曲线、EDA 图和运行环境。统一入口为：

```bash
uv run plant-smoke --output-dir outputs/smoke/week1 --seed 42 --image-size 32
```

## 数据集适配结论

PlantVillage 上游仓库的 loader 文件名与自动发现规则不一致，且 datasets 4.x 不再支持 dataset script。项目已锁定兼容的 datasets 3.x，并固定、检查和测试上游 loader revision。完整数据体积约 2 GB，本地 train split 审计、官方 split baseline 和 leaf_id 风险检查已完成。

## Week 1 关闭记录

截至 2026-07-11，Week 1 所有任务、交付物、验收标准和退出条件均已有仓库内证据或可复现命令：

- 环境与最小流程：`README.md`、`pyproject.toml`、`uv.lock`。
- 自动化验证：`uv run pytest -q`、`uv run ruff check .`、`uv run plant-smoke --output-dir outputs/smoke/week1 --seed 42 --image-size 32`。
- 合成 smoke 证据：`outputs/smoke/week1/`，本地生成且被 Git 忽略。
- PlantVillage 下载、审计和 EDA：`outputs/plantvillage/audit.json`、`outputs/plantvillage/eda/`、`reports/data_audit.md`。
- 官方 split MobileNetV2 baseline：`outputs/plantvillage/baseline_mobilenet_v2_seed42/`。
- checkpoint 推理：`plant-predict` 可加载 `outputs/plantvillage/baseline_mobilenet_v2_seed42/checkpoint.pt` 并输出 Top-5 结构化预测。
- 证据索引：`docs/artifact-index.md`。

因此 Week 1 可以视为工程闭环完成。后续工作不再是 Week 1 阻塞项，而是 Week 2+ 的可信 Benchmark 与研究深化。

## 后续优先事项

- 补齐官方 test split 审计。
- 为 Week 2 建立 leaf_id-disjoint split，或冻结“官方 split baseline”的限制说明。
- 将正式 baseline 的混淆矩阵可视化为图片，便于报告阅读。
- 补齐参数量、FLOPs、推理延迟、吞吐量和峰值内存测量。

Week 1 已形成官方 split 下的数据加载、训练、评估、checkpoint 与推理闭环；但实体隔离 split 和 test split 独立审计仍是后续可信 Benchmark 的优先任务。
