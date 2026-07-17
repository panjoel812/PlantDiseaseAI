# Week 3 Ablation Matrix

日期：2026-07-13

## 冻结协议

Week 3 消融以 Week 2 的最佳精度候选 ResNet50 为改进基线。所有单变量实验必须共享以下固定条件：

- 数据源：PlantVillage 官方 train/test split。
- 训练/验证划分：官方 train split 内部按 seed 42 做 stratified train/validation。
- 测试集：官方 test split，仅用于最终评估。
- 模型：ResNet50，TorchVision 预训练权重。
- 输入尺寸：224。
- batch size：16。
- epoch：5。
- optimizer：AdamW，learning rate 0.001。
- checkpoint 选择：validation Macro F1 最佳 epoch。
- 主指标：Macro F1，同时报告 Accuracy、Macro Precision、Macro Recall 和 per-class 指标。

限制仍与 Week 2 相同：官方 split 已发现 227 个重叠 `leaf_id`，因此结果只能表述为官方 split 消融，不能表述为严格叶片实体隔离的无泄漏结果。

## 单变量消融矩阵

| 编号 | 配置 | 改变因素 | 具体开关 | 输出目录建议 |
| --- | --- | --- | --- | --- |
| 00 | `configs/week3_ablation/00_resnet50_baseline.yaml` | 冻结基线 | 全部 Week 3 改进关闭 | `outputs/plantvillage/week3_ablation/00_resnet50_baseline_seed42/` |
| 01 | `configs/week3_ablation/01_label_smoothing.yaml` | Loss | CrossEntropy `label_smoothing=0.1` | `outputs/plantvillage/week3_ablation/01_label_smoothing_seed42/` |
| 02 | `configs/week3_ablation/02_focal_loss.yaml` | Loss | Focal Loss `gamma=2.0` | `outputs/plantvillage/week3_ablation/02_focal_loss_seed42/` |
| 03 | `configs/week3_ablation/03_cosine_scheduler.yaml` | Scheduler | CosineAnnealingLR，按 batch step，`eta_min=1e-5` | `outputs/plantvillage/week3_ablation/03_cosine_scheduler_seed42/` |
| 04 | `configs/week3_ablation/04_ema.yaml` | EMA | `decay=0.999`，验证/测试使用 EMA 权重 | `outputs/plantvillage/week3_ablation/04_ema_seed42/` |
| 05 | `configs/week3_ablation/05_randaugment.yaml` | Augmentation | RandAugment `num_ops=2, magnitude=9` | `outputs/plantvillage/week3_ablation/05_randaugment_seed42/` |
| 06 | `configs/week3_ablation/06_random_erasing.yaml` | Augmentation | RandomErasing `p=0.25` | `outputs/plantvillage/week3_ablation/06_random_erasing_seed42/` |
| 07 | `configs/week3_ablation/07_mixup.yaml` | Augmentation | Mixup `alpha=0.2` | `outputs/plantvillage/week3_ablation/07_mixup_seed42/` |
| 08 | `configs/week3_ablation/08_cutmix.yaml` | Augmentation | CutMix `alpha=1.0` | `outputs/plantvillage/week3_ablation/08_cutmix_seed42/` |

## 已完成结果

| 编号 | 方法 | Best epoch | Val Macro F1 | Test Acc | Test Macro F1 | 状态 |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| 00 | ResNet50 baseline，全部 Week 3 改进关闭 | 3 | 0.9775 | 0.9830 | 0.9743 | 已完成，复刻 Week 2 ResNet50 |
| 01 | Label Smoothing，CrossEntropy `label_smoothing=0.1` | 5 | 0.9860 | 0.9885 | 0.9865 | 已完成，seed 42 单次结果优于 00 |
| 02 | Focal Loss，`gamma=2.0` | 5 | 0.9776 | 0.9751 | 0.9652 | 已完成，测试集低于 00 |
| 03 | Cosine Scheduler，`eta_min=1e-5` | 5 | 0.9959 | 0.9935 | 0.9898 | 已完成，当前单变量最强 |
| 04 | EMA，`decay=0.999` | 5 | 0.9684 | 0.9752 | 0.9673 | 已完成，低于 00 baseline |
| 05 | RandAugment，`num_ops=2, magnitude=9` | 5 | 0.9784 | 0.9765 | 0.9698 | 已完成，测试集低于 00 |
| 06 | Random Erasing，`p=0.25` | 5 | 0.9718 | 0.9723 | 0.9683 | 已完成，验证和测试均低于 00 |
| 07 | Mixup，`alpha=0.2` | 5 | 0.9858 | 0.9837 | 0.9793 | 已完成，测试 Macro F1 高于 00 |
| 08 | CutMix，`alpha=1.0` | 5 | 0.9868 | 0.9893 | 0.9863 | 已完成，接近 Label Smoothing，低于 Cosine Scheduler |
| 09 | Label Smoothing `0.1` + Cosine Scheduler | 5 | 0.9968 | 0.9953 | 0.9941 | 已完成，当前 seed 42 官方 split 最强候选 |

完整记录见 `reports/week3_ablation_results.md`。`01` 到 `08` 的单变量实验均以 00 为参照物；`09` 是组合候选，以 00 和 03 共同作为解释参照。

## 组合候选

`configs/week3_ablation/09_combo_candidate.yaml` 是根据单变量结果修订后的候选组合实验。它只打开：

- Label Smoothing `0.1`；
- Cosine scheduler。

旧候选中包含 RandAugment、Random Erasing 和 EMA，但这些方法在 seed 42 单变量结果中均低于 00 baseline，因此不应直接进入第一版组合。CutMix 是正向方法，但它与 Label Smoothing 都会改变监督信号；第一版组合先测试机制更清晰的 `Label Smoothing + Cosine Scheduler`。

该组合已经完成，Test Accuracy 0.9953 / Test Macro F1 0.9941，是当前 Week 3 seed 42 官方 split 最强结果。它被选作 Week 4 可解释性和错误分析的冻结候选 checkpoint，但仍需保留单 seed、官方 split `leaf_id` 重叠和真实田间域差异等限制说明。

## 方法直觉

- Label Smoothing 把 one-hot 标签从“绝对确定”改成“主要相信真类，但给其他类少量概率”，可以降低过度自信。
- Focal Loss 用 \((1-p_t)^\gamma\) 放大困难样本的相对贡献，常用于类别不均衡或易样本过多的场景。
- Cosine scheduler 让学习率从初始值平滑下降到 `eta_min`，本项目按 optimizer step 更新，因此总步数为 `len(train_loader) * epochs`。
- EMA 使用 \(\theta_{\text{ema}} \leftarrow d\theta_{\text{ema}} + (1-d)\theta\) 平滑模型参数，验证和测试时临时切换到平均权重。
- Mixup/CutMix 都会生成软标签。Mixup 混合整张图；CutMix 替换局部 patch，并按 patch 面积修正标签混合比例。

## 当前实现证据

- 配置解析：`src/plantdisease/config.py`。
- 增强开关：`src/plantdisease/data/transforms.py`、`src/plantdisease/training/mix.py`。
- Loss：`src/plantdisease/training/losses.py`。
- Scheduler：`src/plantdisease/training/schedulers.py`。
- EMA：`src/plantdisease/training/ema.py`。
- 训练接线：`src/plantdisease/training/engine.py`、`src/plantdisease/training/baseline.py`。
- 配置审计测试：`tests/test_config.py`。
- 单元测试：`tests/training/test_losses.py`、`tests/training/test_mix.py`、`tests/training/test_schedulers.py`、`tests/training/test_ema.py`、`tests/data/test_transforms.py`、`tests/training/test_engine.py`、`tests/training/test_baseline_run.py`。

## 下一步运行顺序

`00_resnet50_baseline.yaml`、`01_label_smoothing.yaml`、`02_focal_loss.yaml`、`03_cosine_scheduler.yaml`、`04_ema.yaml`、`05_randaugment.yaml`、`06_random_erasing.yaml`、`07_mixup.yaml`、`08_cutmix.yaml` 和 `09_combo_candidate.yaml` 均已完成。下一步不再增加 Week 3 主表实验，转入 Week 4 的 Grad-CAM、混淆矩阵和错误分析。
