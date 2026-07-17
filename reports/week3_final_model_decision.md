# Week 3 Final Model Candidate Decision

日期：2026-07-13

## 决策结论

Week 4 的可解释性与错误分析阶段冻结使用 `09_combo_candidate` 作为当前分类候选模型：

- 配置：`configs/week3_ablation/09_combo_candidate.yaml`
- checkpoint：`outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/checkpoint.pt`
- 测试指标：`outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/metrics.json`
- 验证指标：`outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/validation_metrics.json`
- 训练曲线：`outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/training_curve.json`
- 运行清单：`outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/run_manifest.json`

该选择表示“当前项目内部的 Week 4 工作候选”，不表示真实田间最终模型，也不表示多随机种子稳定结论。

## 核心指标

| 候选 | Test Acc | Test Macro F1 | 相对 00 Test Macro F1 | 说明 |
| --- | ---: | ---: | ---: | --- |
| 00 ResNet50 baseline | 0.9830 | 0.9743 | 0.0000 | Week 2 ResNet50 的冻结复刻 |
| 03 Cosine Scheduler | 0.9935 | 0.9898 | +0.0154 | 最强单变量 |
| 09 Label Smoothing + Cosine Scheduler | 0.9953 | 0.9941 | +0.0198 | 当前最强组合候选 |

`09` 比最强单变量 `03` 的 Test Macro F1 继续高 0.0043。这个提升不大，但方向与单变量证据一致：Cosine Scheduler 单独有效，Label Smoothing 单独有效，二者组合后没有互相抵消。

## 保留与舍弃的方法

保留：

- Label Smoothing `0.1`：单变量 Test Macro F1 0.9865，高于 00 baseline。
- Cosine Scheduler：单变量 Test Macro F1 0.9898，是最强单变量。

不进入当前候选：

- Focal Loss：Test Macro F1 0.9652，低于 00 baseline。
- EMA `decay=0.999`：Test Macro F1 0.9673，低于 00 baseline。
- RandAugment：Test Macro F1 0.9698，低于 00 baseline。
- Random Erasing：Test Macro F1 0.9683，低于 00 baseline。
- Mixup：Test Macro F1 0.9793，高于 00 baseline 但弱于 Label Smoothing、CutMix 和 Cosine Scheduler。
- CutMix：Test Macro F1 0.9863，是正向方法，但与 Label Smoothing 同样改变监督信号；为保持候选模型机制清晰，本轮不纳入 09。

## 分类别观察

`09` 的最低 F1 类别仍集中在视觉相似类别：

| 类别 | Precision | Recall | F1 | Support |
| --- | ---: | ---: | ---: | ---: |
| Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot | 0.9712 | 0.9439 | 0.9573 | 107 |
| Corn_(maize)___Northern_Leaf_Blight | 0.9643 | 0.9818 | 0.9730 | 220 |
| Tomato___Target_Spot | 0.9726 | 0.9861 | 0.9793 | 288 |
| Tomato___Early_blight | 0.9952 | 0.9674 | 0.9811 | 215 |
| Potato___Late_blight | 0.9952 | 0.9717 | 0.9833 | 212 |

相对 00 baseline，`09` 改善最明显的类别包括：

| 类别 | 00 F1 | 09 F1 | Δ F1 |
| --- | ---: | ---: | ---: |
| Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot | 0.8216 | 0.9573 | +0.1357 |
| Peach___healthy | 0.8961 | 1.0000 | +0.1039 |
| Potato___healthy | 0.9118 | 1.0000 | +0.0882 |
| Tomato___Early_blight | 0.9112 | 0.9811 | +0.0699 |
| Strawberry___healthy | 0.9506 | 1.0000 | +0.0494 |

小幅下降最明显的是 `Apple___Black_rot`，F1 从 0.9898 降到 0.9861。后续 Week 4 应优先检查上述低 F1 和变化较大的类别。

## 训练稳定性与成本

训练曲线对比图：`reports/figures/week3_validation_macro_f1_curves.png`。

`09` 的 validation Macro F1 从 epoch 3 开始超过 03 Cosine Scheduler，并在 epoch 5 达到 0.9968。训练时长为 65.4 分钟，低于 00 baseline 的 85.7 分钟和 03 Cosine Scheduler 的 85.9 分钟；该差异可能受本机运行状态影响，不应解释为方法本身必然更快。

推理成本方面，`09` 与 Week 2 ResNet50 使用同一模型结构。Label Smoothing 和 Cosine Scheduler 都只影响训练，不增加推理阶段参数量、FLOPs 或额外模块。因此推理侧沿用 ResNet50 的效率记录：23.59M 参数、4.11G FLOPs、MPS batch-1 latency 7.42 ms、batch-32 throughput 165.9 img/s。峰值内存仍未测量，只能记录为未验证项。

## 限制

- 当前所有 Week 3 结果均为 seed 42 单次运行，没有多随机种子均值和标准差。
- 当前使用 PlantVillage 官方 split；已知 train/test 有 227 个重叠 `leaf_id`，不能写成严格实体隔离无泄漏结果。
- PlantVillage 背景受控，不能把高分直接解释为真实田间鲁棒性。
- 峰值内存未测量。
- Week 4 仍需生成混淆矩阵、固定错误样本、Grad-CAM 和错误类型分析，才能形成更完整的研究结论。
