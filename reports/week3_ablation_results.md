# Week 3 Ablation Results

日期：2026-07-13

## 当前进度

Week 3 已完成九个正式单变量消融运行和一个组合候选运行：关闭全部 Week 3 改进开关的 ResNet50 冻结基线、Label Smoothing、Focal Loss、Cosine Scheduler、EMA、RandAugment、Random Erasing、Mixup、CutMix，以及组合候选 `09_combo_candidate`。当前所有结果均为 seed 42 单次运行，尚不能写成多随机种子稳定结论。

当前最强的 seed 42 官方 split 候选是 `09_combo_candidate`：Label Smoothing `0.1` + Cosine Scheduler。它在官方 test split 上达到 Test Accuracy 0.9953 / Test Macro F1 0.9941。该结论仍受官方 split `leaf_id` 重叠风险和单随机种子限制约束。

## 结果表

| 编号 | 方法 | 输出目录 | Best epoch | Val Acc | Val Macro F1 | Test Acc | Test Macro F1 | 时长 |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 00 | ResNet50 baseline，全部 Week 3 改进关闭 | `outputs/plantvillage/week3_ablation/00_resnet50_baseline_seed42/` | 3 | 0.9868 | 0.9775 | 0.9830 | 0.9743 | 85.7 min |
| 01 | Label Smoothing，CrossEntropy `label_smoothing=0.1` | `outputs/plantvillage/week3_ablation/01_label_smoothing_seed42/` | 5 | 0.9899 | 0.9860 | 0.9885 | 0.9865 | 87.4 min |
| 02 | Focal Loss，`gamma=2.0` | `outputs/plantvillage/week3_ablation/02_focal_loss_seed42/` | 5 | 0.9820 | 0.9776 | 0.9751 | 0.9652 | 81.4 min |
| 03 | Cosine Scheduler，`eta_min=1e-5` | `outputs/plantvillage/week3_ablation/03_cosine_scheduler_seed42/` | 5 | 0.9980 | 0.9959 | 0.9935 | 0.9898 | 85.9 min |
| 04 | EMA，`decay=0.999` | `outputs/plantvillage/week3_ablation/04_ema_seed42/` | 5 | 0.9746 | 0.9684 | 0.9752 | 0.9673 | 87.2 min |
| 05 | RandAugment，`num_ops=2, magnitude=9` | `outputs/plantvillage/week3_ablation/05_randaugment_seed42/` | 5 | 0.9835 | 0.9784 | 0.9765 | 0.9698 | 92.8 min |
| 06 | Random Erasing，`p=0.25` | `outputs/plantvillage/week3_ablation/06_random_erasing_seed42/` | 5 | 0.9760 | 0.9718 | 0.9723 | 0.9683 | 79.9 min |
| 07 | Mixup，`alpha=0.2` | `outputs/plantvillage/week3_ablation/07_mixup_seed42/` | 5 | 0.9891 | 0.9858 | 0.9837 | 0.9793 | 66.7 min |
| 08 | CutMix，`alpha=1.0` | `outputs/plantvillage/week3_ablation/08_cutmix_seed42/` | 5 | 0.9913 | 0.9868 | 0.9893 | 0.9863 | 65.3 min |
| 09 | Label Smoothing `0.1` + Cosine Scheduler | `outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/` | 5 | 0.9982 | 0.9968 | 0.9953 | 0.9941 | 65.4 min |

## 相对 00 baseline 的变化

| 编号 | 方法 | Δ Val Macro F1 | Δ Test Acc | Δ Test Macro F1 | 当前观察 |
| --- | --- | ---: | ---: | ---: | --- |
| 01 | Label Smoothing | +0.0085 | +0.0055 | +0.0122 | 单次 seed 下明显优于 00，但仍需后续单变量和组合实验确认是否作为最终方案组成部分 |
| 02 | Focal Loss | +0.0002 | -0.0079 | -0.0092 | 验证 Macro F1 与 00 接近，但测试集明显下降；当前不支持把 Focal Loss 纳入默认组合 |
| 03 | Cosine Scheduler | +0.0185 | +0.0105 | +0.0154 | 当前 seed 42 下是已完成单变量中最强结果，但需警惕官方 split 泄漏限制和单次运行波动 |
| 04 | EMA | -0.0091 | -0.0078 | -0.0071 | `decay=0.999` 的 EMA 明显落后于当前模型；当前不支持直接纳入默认组合 |
| 05 | RandAugment | +0.0009 | -0.0065 | -0.0046 | 验证略高于 00，但测试集下降；当前不支持直接纳入默认组合 |
| 06 | Random Erasing | -0.0057 | -0.0107 | -0.0061 | 验证和测试均低于 00；当前不支持直接纳入默认组合 |
| 07 | Mixup | +0.0083 | +0.0007 | +0.0050 | 测试 Macro F1 高于 00，但低于 Label Smoothing 和 Cosine Scheduler；可作为组合候选继续观察 |
| 08 | CutMix | +0.0093 | +0.0063 | +0.0120 | 测试 Macro F1 明显高于 00，几乎追平 Label Smoothing，但仍低于 Cosine Scheduler |
| 09 | Label Smoothing + Cosine Scheduler | +0.0193 | +0.0123 | +0.0198 | 当前 seed 42 官方 split 最强结果；比单独 Cosine Scheduler 的 Test Macro F1 仍高 0.0043 |

## 与 Week 2 ResNet50 对照

Week 2 ResNet50 正式结果为 Test Accuracy 0.9830 / Test Macro F1 0.9743，最佳验证 epoch 为 3。Week 3 的 `00_resnet50_baseline` 得到相同测试指标和相同最佳 epoch，说明关闭全部改进开关时，Week 3 的训练入口接线与 Week 2 ResNet50 baseline 保持可比。

这一步不是性能提升实验，而是参照物校准。`01` 到 `08` 的单变量消融应与 `00` 比较；`09` 是组合候选，应单独解释为“由单变量证据支持后的组合验证”，不能和单变量实验混成同一类结论。

## Label Smoothing 初步观察

`01_label_smoothing` 只改变 Loss：从普通 CrossEntropy 改为 `label_smoothing=0.1`。测试 Macro F1 从 0.9743 提升到 0.9865，Accuracy 从 0.9830 提升到 0.9885。该结果说明在当前官方 split、ResNet50、seed 42 条件下，降低 one-hot 标签的过度自信对泛化有帮助。

但这仍是单次运行，不能直接写成最终结论。后续应比较 per-class F1，确认提升不是只来自少数容易类别或官方 split 偶然波动。

## Focal Loss 初步观察

`02_focal_loss` 只改变 Loss：从普通 CrossEntropy 改为 Focal Loss `gamma=2.0`。验证 Macro F1 为 0.9776，几乎等于 00 baseline 的 0.9775；但测试 Macro F1 从 0.9743 降到 0.9652，测试 Accuracy 也从 0.9830 降到 0.9751。

当前 seed 42 结果说明：在这个 ResNet50 + PlantVillage 官方 split 设置下，Focal Loss 没有带来稳定收益，反而可能损害测试泛化。合理假设是 PlantVillage 当前类别区分已经较容易，过度强调困难样本可能放大噪声、异常样本或边界样本的影响。该解释仍需后续 per-class F1 和错误分析验证。

## Cosine Scheduler 初步观察

`03_cosine_scheduler` 只改变学习率调度：optimizer 仍为 AdamW，初始 learning rate 仍为 0.001，但训练过程中按 batch step 使用 CosineAnnealingLR 平滑下降到 `eta_min=1e-5`。测试 Macro F1 从 0.9743 提升到 0.9898，Accuracy 从 0.9830 提升到 0.9935。

当前 seed 42 结果说明：相比固定学习率，平滑降低学习率明显改善了这个 ResNet50 baseline 的收敛和测试表现。直观上，固定学习率像全程用同样大的步子走路，后期可能在好位置附近来回晃；cosine scheduler 像先大步找方向，再逐渐小步精修。

但该结果仍然不能单独定义最终模型：后续需要在组合实验里检查 Cosine Scheduler 与 Label Smoothing 叠加后是否仍然稳定。

## EMA 初步观察

`04_ema` 只改变权重评估方式：训练仍然更新普通模型权重，同时维护一份 EMA 平滑权重，验证和测试时临时切换到 EMA 权重。该实验使用 `decay=0.999`。测试 Macro F1 从 0.9743 降到 0.9673，Accuracy 从 0.9830 降到 0.9752。

当前 seed 42 结果说明：这个 EMA 设置没有带来收益。直观原因是 `decay=0.999` 很“慢热”：它每一步只吸收很小一部分新模型参数，因此在 5 个 epoch 的预算下，EMA 权重可能长期落后于已经学好的当前模型。日志也支持这个现象：EMA 验证 Macro F1 从 epoch 1 的 0.6968 缓慢追到 epoch 5 的 0.9684，但仍低于 00 baseline。

这不代表 EMA 永远无用，只能说明当前固定矩阵里的 `decay=0.999` 不适合直接作为默认改进项。后续如果资源允许，可以把较低 decay（例如 0.99 或 0.995）作为探索性补充，但不能混入当前单变量主表。

## RandAugment 初步观察

`05_randaugment` 只改变训练集图像增强：在原有训练增强基础上打开 RandAugment `num_ops=2, magnitude=9`。验证 Macro F1 为 0.9784，略高于 00 baseline 的 0.9775；但测试 Macro F1 从 0.9743 降到 0.9698，测试 Accuracy 从 0.9830 降到 0.9765。

当前 seed 42 结果说明：更强的随机图像变换没有带来测试泛化提升。直观上，RandAugment 会把训练图片做更激进的颜色、几何或对比度变化；如果变化过强，模型学到的训练分布可能反而偏离 PlantVillage 官方测试集。该结果不代表 RandAugment 永远无用，只说明当前强度 `num_ops=2, magnitude=9` 不适合作为默认改进项。

## Random Erasing 初步观察

`06_random_erasing` 只改变训练集图像增强：在原有训练增强基础上打开 Random Erasing `p=0.25`。它会随机遮挡训练图片中的一块区域，目的相当于“别让模型只靠某一个局部纹理或背景线索做判断”。验证 Macro F1 从 00 baseline 的 0.9775 降到 0.9718，测试 Macro F1 从 0.9743 降到 0.9683，测试 Accuracy 从 0.9830 降到 0.9723。

当前 seed 42 结果说明：在这个官方 split 和 5 epoch 预算下，随机遮挡没有提升泛化，反而削弱了模型对病斑细节的学习。合理假设是植物病害分类往往依赖叶片局部斑点、霉层、坏死边缘等细粒度视觉证据；如果遮挡刚好覆盖关键病征，训练信号会变得更噪。该解释仍需后续 per-class F1 和错误样本检查验证。

## Mixup 初步观察

`07_mixup` 只改变训练 batch 构造方式：它把两张训练图像按比例线性混合，同时把两份标签也按同样比例混合。本实验使用 `alpha=0.2`。验证 Macro F1 从 00 baseline 的 0.9775 提升到 0.9858，测试 Macro F1 从 0.9743 提升到 0.9793，测试 Accuracy 从 0.9830 小幅提升到 0.9837。

当前 seed 42 结果说明：Mixup 在当前设置下有正收益，但提升幅度小于 Label Smoothing、CutMix 和 Cosine Scheduler。直观上，Mixup 让模型看到“介于两个样本之间”的训练点，等于把决策边界磨得更平滑，减少模型对单张训练图片细节的死记硬背。它没有改变网络结构，主要改变监督信号和训练样本分布。

## CutMix 初步观察

`08_cutmix` 只改变训练 batch 构造方式：它把一张训练图像的局部 patch 裁切到另一张图上，同时按 patch 面积混合标签。本实验使用 `alpha=1.0`。验证 Macro F1 从 00 baseline 的 0.9775 提升到 0.9868，测试 Macro F1 从 0.9743 提升到 0.9863，测试 Accuracy 从 0.9830 提升到 0.9893。

当前 seed 42 结果说明：CutMix 是一个明确正向的增强方法，效果明显强于 Mixup，并且几乎追平 Label Smoothing。直观上，植物病害分类往往依赖局部病斑、霉层、坏死边缘等区域；CutMix 通过“局部 patch + 面积比例标签”训练模型，有可能让模型更稳地利用局部视觉证据。它仍低于 Cosine Scheduler，因此不能单独定义最终模型，但值得作为后续组合实验或补充实验的候选。

## 组合候选观察

`09_combo_candidate` 打开 Label Smoothing `0.1` 和 Cosine Scheduler，关闭 EMA、RandAugment、Random Erasing、Mixup 和 CutMix。它的 Test Macro F1 为 0.9941，相比 00 baseline 提升 0.0198，相比单独 Cosine Scheduler 的 0.9898 继续提升 0.0043。

这个结果支持一个谨慎结论：在当前 ResNet50、官方 split、seed 42 和 5 epoch 预算下，“平滑学习率下降 + 降低标签过度自信”可以叠加产生收益。直观上，Cosine Scheduler 改善优化路径，Label Smoothing 改善监督信号；两者一个主要管“怎么走”，一个主要管“朝什么目标学”，机制相对独立，因此叠加后没有互相抵消。

`09` 被选作 Week 4 Grad-CAM 和错误分析的冻结候选 checkpoint，但不是公开最终结论。仍需在 Week 4 检查错误样本、类间混淆和可解释性，并在最终报告中明确单 seed 与官方 split 限制。

## 分类别初步观察

`09_combo_candidate` 的最低分类别 F1 仍集中在视觉相似类别：

- `Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot`：F1 0.9573；
- `Corn_(maize)___Northern_Leaf_Blight`：F1 0.9730；
- `Tomato___Target_Spot`：F1 0.9793；
- `Tomato___Early_blight`：F1 0.9811；
- `Potato___Late_blight`：F1 0.9833。

相比 00 baseline，`09` 对若干原本较弱类别提升明显：`Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot` 从 F1 0.8216 提升到 0.9573，`Peach___healthy` 从 0.8961 提升到 1.0000，`Potato___healthy` 从 0.9118 提升到 1.0000，`Tomato___Early_blight` 从 0.9112 提升到 0.9811。唯一明显小幅下降的是 `Apple___Black_rot`，从 F1 0.9898 降到 0.9861。

这说明 `09` 的整体提升不是只来自大类堆高 Accuracy，而是改善了部分原本困难或样本较少类别。不过这些解释仍需 Week 4 通过混淆矩阵和代表性错误样本复核。

## 训练曲线对比

训练曲线对比图见 `reports/figures/week3_validation_macro_f1_curves.png`。该图比较 00 baseline、03 Cosine Scheduler 和 09 Label Smoothing + Cosine Scheduler 的 validation Macro F1。`09` 在 epoch 3 后稳定超过 03，并在 epoch 5 达到最佳 validation Macro F1 0.9968。

## 机器可读证据

- 配置：`configs/week3_ablation/00_resnet50_baseline.yaml`
- 输出目录：`outputs/plantvillage/week3_ablation/00_resnet50_baseline_seed42/`
- 测试指标：`outputs/plantvillage/week3_ablation/00_resnet50_baseline_seed42/metrics.json`
- 验证指标：`outputs/plantvillage/week3_ablation/00_resnet50_baseline_seed42/validation_metrics.json`
- 训练曲线：`outputs/plantvillage/week3_ablation/00_resnet50_baseline_seed42/training_curve.json`
- 运行清单：`outputs/plantvillage/week3_ablation/00_resnet50_baseline_seed42/run_manifest.json`
- checkpoint：`outputs/plantvillage/week3_ablation/00_resnet50_baseline_seed42/checkpoint.pt`

### 01 Label Smoothing

- 配置：`configs/week3_ablation/01_label_smoothing.yaml`
- 输出目录：`outputs/plantvillage/week3_ablation/01_label_smoothing_seed42/`
- 测试指标：`outputs/plantvillage/week3_ablation/01_label_smoothing_seed42/metrics.json`
- 验证指标：`outputs/plantvillage/week3_ablation/01_label_smoothing_seed42/validation_metrics.json`
- 训练曲线：`outputs/plantvillage/week3_ablation/01_label_smoothing_seed42/training_curve.json`
- 运行清单：`outputs/plantvillage/week3_ablation/01_label_smoothing_seed42/run_manifest.json`
- checkpoint：`outputs/plantvillage/week3_ablation/01_label_smoothing_seed42/checkpoint.pt`

### 02 Focal Loss

- 配置：`configs/week3_ablation/02_focal_loss.yaml`
- 输出目录：`outputs/plantvillage/week3_ablation/02_focal_loss_seed42/`
- 测试指标：`outputs/plantvillage/week3_ablation/02_focal_loss_seed42/metrics.json`
- 验证指标：`outputs/plantvillage/week3_ablation/02_focal_loss_seed42/validation_metrics.json`
- 训练曲线：`outputs/plantvillage/week3_ablation/02_focal_loss_seed42/training_curve.json`
- 运行清单：`outputs/plantvillage/week3_ablation/02_focal_loss_seed42/run_manifest.json`
- checkpoint：`outputs/plantvillage/week3_ablation/02_focal_loss_seed42/checkpoint.pt`

### 03 Cosine Scheduler

- 配置：`configs/week3_ablation/03_cosine_scheduler.yaml`
- 输出目录：`outputs/plantvillage/week3_ablation/03_cosine_scheduler_seed42/`
- 测试指标：`outputs/plantvillage/week3_ablation/03_cosine_scheduler_seed42/metrics.json`
- 验证指标：`outputs/plantvillage/week3_ablation/03_cosine_scheduler_seed42/validation_metrics.json`
- 训练曲线：`outputs/plantvillage/week3_ablation/03_cosine_scheduler_seed42/training_curve.json`
- 运行清单：`outputs/plantvillage/week3_ablation/03_cosine_scheduler_seed42/run_manifest.json`
- checkpoint：`outputs/plantvillage/week3_ablation/03_cosine_scheduler_seed42/checkpoint.pt`

### 04 EMA

- 配置：`configs/week3_ablation/04_ema.yaml`
- 输出目录：`outputs/plantvillage/week3_ablation/04_ema_seed42/`
- 测试指标：`outputs/plantvillage/week3_ablation/04_ema_seed42/metrics.json`
- 验证指标：`outputs/plantvillage/week3_ablation/04_ema_seed42/validation_metrics.json`
- 训练曲线：`outputs/plantvillage/week3_ablation/04_ema_seed42/training_curve.json`
- 运行清单：`outputs/plantvillage/week3_ablation/04_ema_seed42/run_manifest.json`
- checkpoint：`outputs/plantvillage/week3_ablation/04_ema_seed42/checkpoint.pt`

### 05 RandAugment

- 配置：`configs/week3_ablation/05_randaugment.yaml`
- 输出目录：`outputs/plantvillage/week3_ablation/05_randaugment_seed42/`
- 测试指标：`outputs/plantvillage/week3_ablation/05_randaugment_seed42/metrics.json`
- 验证指标：`outputs/plantvillage/week3_ablation/05_randaugment_seed42/validation_metrics.json`
- 训练曲线：`outputs/plantvillage/week3_ablation/05_randaugment_seed42/training_curve.json`
- 运行清单：`outputs/plantvillage/week3_ablation/05_randaugment_seed42/run_manifest.json`
- checkpoint：`outputs/plantvillage/week3_ablation/05_randaugment_seed42/checkpoint.pt`

### 06 Random Erasing

- 配置：`configs/week3_ablation/06_random_erasing.yaml`
- 输出目录：`outputs/plantvillage/week3_ablation/06_random_erasing_seed42/`
- 测试指标：`outputs/plantvillage/week3_ablation/06_random_erasing_seed42/metrics.json`
- 验证指标：`outputs/plantvillage/week3_ablation/06_random_erasing_seed42/validation_metrics.json`
- 训练曲线：`outputs/plantvillage/week3_ablation/06_random_erasing_seed42/training_curve.json`
- 运行清单：`outputs/plantvillage/week3_ablation/06_random_erasing_seed42/run_manifest.json`
- checkpoint：`outputs/plantvillage/week3_ablation/06_random_erasing_seed42/checkpoint.pt`

### 07 Mixup

- 配置：`configs/week3_ablation/07_mixup.yaml`
- 输出目录：`outputs/plantvillage/week3_ablation/07_mixup_seed42/`
- 测试指标：`outputs/plantvillage/week3_ablation/07_mixup_seed42/metrics.json`
- 验证指标：`outputs/plantvillage/week3_ablation/07_mixup_seed42/validation_metrics.json`
- 训练曲线：`outputs/plantvillage/week3_ablation/07_mixup_seed42/training_curve.json`
- 运行清单：`outputs/plantvillage/week3_ablation/07_mixup_seed42/run_manifest.json`
- checkpoint：`outputs/plantvillage/week3_ablation/07_mixup_seed42/checkpoint.pt`

### 08 CutMix

- 配置：`configs/week3_ablation/08_cutmix.yaml`
- 输出目录：`outputs/plantvillage/week3_ablation/08_cutmix_seed42/`
- 测试指标：`outputs/plantvillage/week3_ablation/08_cutmix_seed42/metrics.json`
- 验证指标：`outputs/plantvillage/week3_ablation/08_cutmix_seed42/validation_metrics.json`
- 训练曲线：`outputs/plantvillage/week3_ablation/08_cutmix_seed42/training_curve.json`
- 运行清单：`outputs/plantvillage/week3_ablation/08_cutmix_seed42/run_manifest.json`
- checkpoint：`outputs/plantvillage/week3_ablation/08_cutmix_seed42/checkpoint.pt`

### 09 Label Smoothing + Cosine Scheduler

- 配置：`configs/week3_ablation/09_combo_candidate.yaml`
- 输出目录：`outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/`
- 测试指标：`outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/metrics.json`
- 验证指标：`outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/validation_metrics.json`
- 训练曲线：`outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/training_curve.json`
- 运行清单：`outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/run_manifest.json`
- checkpoint：`outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/checkpoint.pt`

## 运行上下文

- 数据：PlantVillage 官方 split。
- 训练/验证：官方 train split 内部 stratified split，seed 42。
- 测试：官方 test split，`sample_count = 10709`。
- 设备：MPS。
- 训练样本：37058。
- 验证样本：6538。
- 测试样本：10709。
- 00 改进开关：RandAugment、Random Erasing、Mixup、CutMix、Label Smoothing、Focal Loss、Cosine Scheduler、EMA 均关闭。
- 01 改进开关：仅打开 CrossEntropy `label_smoothing=0.1`。
- 02 改进开关：仅将 Loss 改为 Focal Loss `gamma=2.0`。
- 03 改进开关：仅打开 Cosine Scheduler，按 optimizer step 更新学习率。
- 04 改进开关：仅打开 EMA，`decay=0.999`，验证和测试使用 EMA 权重。
- 05 改进开关：仅打开 RandAugment，`num_ops=2, magnitude=9`。
- 06 改进开关：仅打开 Random Erasing，`p=0.25`。
- 07 改进开关：仅打开 Mixup，`alpha=0.2`。
- 08 改进开关：仅打开 CutMix，`alpha=1.0`。
- 09 改进开关：打开 Label Smoothing `0.1` 和 Cosine Scheduler，关闭 EMA、RandAugment、Random Erasing、Mixup 和 CutMix。

## 下一步

Week 3 的实验侧结论已经足以冻结 Week 4 候选 checkpoint：`outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/checkpoint.pt`。下一步进入 Week 4：围绕该 checkpoint 生成混淆矩阵、固定错误样本、Grad-CAM 图集和错误分析报告。
