# Week 2 Benchmark 报告

日期：2026-07-11

## 当前结论

五个候选模型的 PlantVillage 官方 split 正式训练、测试评估和效率测量均已完成。该报告可以作为 Week 2 官方 split benchmark 证据，但仍必须标注数据限制：官方 split 已发现 227 个重叠 `leaf_id`，因此不能表述为严格叶片实体隔离的无泄漏结果。

模型选择结论：

- 最佳精度候选：ResNet50，Test Accuracy 0.9830，Macro F1 0.9743。
- 默认轻量部署候选：MobileNetV2，2.27M 参数、0.31G FLOPs、batch-32 吞吐 644.3 img/s。
- 延迟优先备选：ResNet18，在本机 MPS 上 batch-1 平均延迟最低，为 2.82 ms，但参数量和 FLOPs 明显高于 MobileNetV2。

## 训练与测试结果

| 模型 | 运行目录 | Batch size | 训练时长 | 最佳验证 epoch | Val Acc | Val Macro F1 | Test Acc | Test Macro F1 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| MobileNetV2 | `outputs/plantvillage/baseline_mobilenet_v2_best_seed42/` | 32 | 26.6 min | 4 | 0.9821 | 0.9760 | 0.9760 | 0.9674 |
| ResNet18 | `outputs/plantvillage/baseline_resnet18_seed42/` | 32 | 22.7 min | 5 | 0.9810 | 0.9718 | 0.9774 | 0.9661 |
| ResNet50 | `outputs/plantvillage/baseline_resnet50_seed42/` | 16 | 66.0 min | 3 | 0.9868 | 0.9775 | 0.9830 | 0.9743 |
| EfficientNet-B0 | `outputs/plantvillage/baseline_efficientnet_b0_seed42/` | 32 | 43.0 min | 2 | 0.9881 | 0.9816 | 0.9804 | 0.9703 |
| EfficientNetV2-S | `outputs/plantvillage/baseline_efficientnet_v2_s_seed42/` | 8 | 101.0 min | 5 | 0.9812 | 0.9723 | 0.9794 | 0.9708 |

## 效率 Benchmark

测量协议：MPS、float32、输入尺寸 224、batch-1 延迟、batch-32 吞吐、10 次 warmup、50 次测量，不包含预处理。FLOPs 使用 `fvcore.nn.FlopCountAnalysis`，报告中保留 unsupported ops；因此 FLOPs 是统一工具下的理论估计，不应写成硬件实测耗时。

| 模型 | Benchmark JSON | Params | FLOPs | Latency mean | Throughput |
| --- | --- | ---: | ---: | ---: | ---: |
| MobileNetV2 | `outputs/plantvillage/benchmarks/mobilenet_v2_seed42.json` | 2.27M | 0.31G | 6.49 ms | 644.3 img/s |
| ResNet18 | `outputs/plantvillage/benchmarks/resnet18_seed42.json` | 11.20M | 1.82G | 2.82 ms | 564.5 img/s |
| ResNet50 | `outputs/plantvillage/benchmarks/resnet50_seed42.json` | 23.59M | 4.11G | 7.42 ms | 165.9 img/s |
| EfficientNet-B0 | `outputs/plantvillage/benchmarks/efficientnet_b0_seed42.json` | 4.06M | 0.40G | 7.25 ms | 305.6 img/s |
| EfficientNetV2-S | `outputs/plantvillage/benchmarks/efficientnet_v2_s_seed42.json` | 20.23M | 2.88G | 14.99 ms | 133.4 img/s |

Pareto 图：`outputs/plantvillage/benchmarks/week2_accuracy_efficiency_pareto.png`。

## 比较协议与限制

- 数据源：Hugging Face PlantVillage 官方 train/test split。
- 训练/验证划分：官方 train split 内部按 seed 42 做 stratified train/validation。
- 测试集：官方 test split，`sample_count = 10709`。
- 输入尺寸：224。
- 预训练权重：torchvision `Weights.DEFAULT`。
- 分类头：替换为项目类别数对应的线性分类头。
- Checkpoint 选择：按 validation Macro F1 保存最佳 epoch。
- 测试集使用：只用于最终评估和最终横向比较，不用于 checkpoint 选择或训练超参数调整。
- 预训练权重许可：来源为 TorchVision 预训练权重。TorchVision 官方文档说明预训练模型可能有来自训练数据集的许可证或条款，使用者需自行判断具体使用场景是否被允许。项目当前只记录来源与风险，不重新分发上游预训练权重。
- 主要限制：官方 split 已发现 227 个重叠 `leaf_id`，因此所有结果必须标注为“官方 split baseline/benchmark”，不能表述为严格叶片实体隔离的无泄漏结果。
- 公平性注意：由于本地 MacBook 内存与速度限制，不同模型 batch size 不完全相同。当前比较可作为统一协议初筛，但最终报告需要显式列出 batch size 差异。
- 峰值内存：未测量。MPS 不提供与 CUDA 相同的可靠 peak-reset/reporting 工作流，因此当前版本不报告峰值内存，避免误导。

## 复现命令

代码健康检查：

```bash
uv run pytest -q
uv run ruff check .
```

单模型效率测量模板：

```bash
uv run plant-benchmark \
  --checkpoint outputs/plantvillage/baseline_resnet50_seed42/checkpoint.pt \
  --output outputs/plantvillage/benchmarks/resnet50_seed42.json \
  --device auto \
  --warmup 10 \
  --iterations 50 \
  --throughput-batch-size 32
```

## Week 3 冻结决定

- 主指标：Macro F1，同时报告 Accuracy、Macro Precision、Macro Recall 和 per-class 指标。
- 改进/消融的高精度基线：ResNet50。
- 部署导向基线：MobileNetV2。
- 数据划分：继续使用当前官方 split 做可比实验，但所有报告保留 `leaf_id` 重叠限制；若后续新增叶片实体隔离 split，应作为新的协议版本，不与当前数字静默混表。
