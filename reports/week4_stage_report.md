# PlantDiseaseAI Week 1–4 Stage Report

日期：2026-07-13  
阶段：数据闭环、Benchmark、消融实验、Grad-CAM、错误分析与校准分析

## Abstract

本阶段围绕 PlantVillage 叶片病害分类任务，构建了一个可复现、可审计、可解释的 CNN 分类研究闭环。项目先完成数据审计、统一训练/评估/推理接口和五模型 Benchmark，再通过 Week 3 消融实验选择当前 Week 4 候选模型：ResNet50 + Label Smoothing `0.1` + Cosine Scheduler。该候选在 seed 42、PlantVillage 官方 test split 上达到 Test Accuracy `0.9953`、Macro F1 `0.9941`。Week 4 进一步冻结了 24 个四象限 Grad-CAM 样本、生成逐样本预测记录、错误分析、关注区域人工审阅、baseline/final 同样本 Grad-CAM 对比和 top-label 校准分析。错误分析显示测试集共有 `50/10709` 个错误样本，最常见混淆集中在玉米灰斑/北方叶枯、马铃薯/番茄晚疫病以及番茄早疫病/靶斑病等视觉相似类别。校准分析显示 top-label ECE 为 `0.0965`，高置信区整体准确率高于平均置信度，提示当前模型在该 split 上偏保守而非典型过度自信。

本报告只支持“受控 PlantVillage 官方 split 上的单 seed 结果”。由于数据背景受控、已记录 `227` 个 train/test 重叠 `leaf_id`，且尚未完成真实田间数据验证，不能将当前性能表述为真实田间泛化能力。

## 1. Research Question

本项目当前研究问题是：在 PlantVillage 受控图像数据上，能否建立一个可复现的植物病害分类基线，并通过统一 Benchmark、消融实验、Grad-CAM 与错误分析把模型表现转化为可解释、可审计的研究结论？

该问题拆成四个可验证子目标：

1. 建立稳定的训练、评估、推理与 checkpoint 接口。
2. 比较多种 CNN 架构，选择精度和成本均可解释的候选模型。
3. 用消融实验支持最终训练策略，避免只凭最高单次结果选型。
4. 用固定样本、Grad-CAM、混淆对、高置信错误和校准分析记录模型优势、失败模式与局限。

## 2. Related Work

PlantVillage 图像病害分类任务常用于验证深度学习在受控叶片图像上的可行性。Mohanty 等使用 PlantVillage 图像训练 CNN，并特别指出受控数据上的高精度不能直接等同于复杂真实环境下的泛化能力；他们在外部分布图像上的性能显著下降，这与本项目必须记录“受控背景限制”的原则一致 [1]。

模型结构上，本阶段最终候选使用 ResNet50。ResNet 的残差连接缓解深层网络优化困难，是本项目选择深层 CNN 作为强基线的重要依据 [2]。训练策略上，本项目 Week 3 消融保留 Label Smoothing 和 Cosine Scheduler。Label Smoothing 最早在 Inception 系列工作中作为分类正则化方法被系统使用 [5]，后续研究也讨论了它对泛化与校准的影响 [6]。Cosine 学习率调度与 warm restart 系列方法则来自 SGDR 工作 [7]，本项目采用的是无重启的 cosine scheduler 变体。

可解释性方面，本项目使用 Grad-CAM，对目标类别分数相对于目标空间模块的梯度进行通道加权，生成类别相关热力图 [3]。本项目的实现中特别修正了 ResNet50 目标层：从 bottleneck 内部 `layer4.2.conv3` 改为最后一个 residual block 输出 `layer4.2`，以捕获残差合并后的最终空间特征。校准方面，本项目采用 top-label ECE/MCE/Brier 和 reliability diagram；神经网络置信度校准的重要性及 ECE 类指标的常见用法可参考 Guo 等的校准研究 [4]。

## 3. Data and Protocol

数据源为 Hugging Face 上的 PlantVillage 数据集缓存，项目固定 loader revision 并在 Week 1 记录数据审计。当前正式比较使用 PlantVillage 官方 split 和 seed 42。项目记录到官方 split 存在 `227` 个跨 train/test 重叠 `leaf_id`，因此当前结果不能描述为严格实体隔离测试。

核心证据：

| 内容 | 路径 |
| --- | --- |
| 数据审计 | `reports/data_audit.md` |
| Week 3 final split manifest | `outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/split.json` |
| Week 3 final run manifest | `outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/run_manifest.json` |
| Week 3 final metrics | `outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/metrics.json` |
| Week 4 prediction records | `outputs/plantvillage/week4_explainability/predictions.json` |

## 4. Model Selection and Ablation Evidence

Week 2 Benchmark 显示 ResNet50 是五模型比较中精度最高的候选。Week 3 在 ResNet50 上进行单变量和组合消融，最终冻结 `09_combo_candidate`：Label Smoothing `0.1` + Cosine Scheduler。

| 候选 | Test Accuracy | Test Macro F1 | 说明 |
| --- | ---: | ---: | --- |
| Week 2/3 ResNet50 baseline | 0.9830 | 0.9743 | 冻结基线 |
| Cosine Scheduler | 0.9935 | 0.9898 | 最强单变量 |
| Label Smoothing + Cosine Scheduler | 0.9953 | 0.9941 | Week 4 冻结候选 |

本项目没有把所有增强都纳入最终候选。Focal Loss、EMA、RandAugment 和 Random Erasing 在 seed 42 下均低于 baseline；Mixup 与 CutMix 虽有部分正向效果，但未优于最终组合候选。完整证据见 `reports/week3_final_model_decision.md` 和 `reports/week3_ablation_results.md`。

## 5. Grad-CAM Method and Findings

Grad-CAM 核心模块位于 `src/plantdisease/explainability/gradcam.py`，目标层解析位于 `src/plantdisease/explainability/layers.py`。实现保证：

- 输出热力图对齐输入空间尺寸。
- 每张热力图独立归一化到 `[0, 1]`。
- 支持显式目标类别或默认预测类别。
- 在外层 `torch.inference_mode()` 下也能临时启用 autograd。
- 不污染模型参数已有 `.grad`，并在退出时清理 hook。

正式图集固定四组样本：正确高置信、正确低置信、错误高置信、错误低置信，各 6 张，共 24 张。图集 target mode 为 `predicted`，用于解释模型为什么给出该预测。

| 内容 | 路径 |
| --- | --- |
| 固定样本报告 | `reports/week4_frozen_samples.md` |
| Grad-CAM atlas report | `reports/week4_gradcam_atlas.md` |
| Atlas manifest | `outputs/plantvillage/week4_explainability/gradcam_atlas/gradcam_atlas_manifest.json` |
| Attention review report | `reports/week4_attention_review.md` |
| Grad-CAM reproducibility check | `reports/week4_gradcam_reproducibility.md` |
| Baseline/final same-sample comparison | `reports/week4_baseline_vs_final_gradcam.md` |

一个关键工程发现是：最初使用 `layer4.2.conv3` 时，`test_index=9750` 的高置信正确样本热力峰值落在叶片外背景区域。诊断对比显示，改用 ResNet 最后一个 residual block 输出 `layer4.2` 后，热点回到叶片主体区域。因此正式 Week 4 目标层修正为 `layer4.2`。这说明 Grad-CAM 的目标层选择本身会显著影响可视化结果，不能把单张热力图直接当作模型因果机制。

人工审阅 24 个固定样本后，关注区域统计为 lesion `14`、mixed `4`、leaf `4`、background `2`。12 个最终模型错误样本的主要错误类型为 visual_similarity `8/12`，另有 low_quality、background_bias、occlusion 和 possible_label_issue 等少量案例。Grad-CAM 复现性检查显示：同一 CPU 进程、同一 checkpoint、同一输入和目标类别下，24/24 个原始 heatmap 张量两次生成完全一致；atlas PNG 重新渲染时存在极小像素量化差异，但 24/24 个 panel 最大通道差均不超过 `5/255`。

## 6. Error Analysis

错误分析由 `plant-error-analysis` 从 `metrics.json` 和 `predictions.json` 生成，输出非归一化混淆矩阵、行归一化混淆矩阵、低 F1 类别、重点混淆对和高置信错误样本。

测试集共有 `10709` 个样本，其中错误 `50` 个。最低 F1 类别集中在视觉相似或跨作物相似病害上：

| 类别 | Precision | Recall | F1 | Support |
| --- | ---: | ---: | ---: | ---: |
| Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot | 0.9712 | 0.9439 | 0.9573 | 107 |
| Corn_(maize)___Northern_Leaf_Blight | 0.9643 | 0.9818 | 0.9730 | 220 |
| Tomato___Target_Spot | 0.9726 | 0.9861 | 0.9793 | 288 |
| Tomato___Early_blight | 0.9952 | 0.9674 | 0.9811 | 215 |
| Potato___Late_blight | 0.9952 | 0.9717 | 0.9833 | 212 |

重点混淆对如下：

| true → predicted | count | true-class share |
| --- | ---: | ---: |
| Corn gray leaf spot → Corn northern leaf blight | 6 | 0.0561 |
| Potato late blight → Tomato late blight | 6 | 0.0283 |
| Tomato early blight → Tomato target spot | 4 | 0.0186 |
| Apple scab → Apple healthy | 3 | 0.0236 |
| Apple black rot → Apple healthy | 3 | 0.0205 |

高置信错误阈值设为 `0.8` 时，仅有 2 个错误样本：

| test_index | true | predicted | confidence |
| ---: | --- | --- | ---: |
| 198 | Potato___Late_blight | Tomato___Late_blight | 0.8475 |
| 6270 | Apple___Apple_scab | Apple___healthy | 0.8322 |

这些样本已进入 attention review，并已人工查看原图、Grad-CAM overlay 与可能的标签问题。人工审阅结论显示，错误主要来自视觉相似病害或跨作物相似症状；但这些标签仍是观察性分类，不等价于已证明的因果机制。

在 12 个最终模型失败样本上，baseline/final 同样本对比显示 baseline top-1 正确 `4/12`、final top-1 正确 `0/12`，二者 top-1 完全相同 `5/12`。由于该集合是按 final 错误样本有意筛选的，不能用来声称 baseline 全局优于 final；它只用于定位训练策略改变后哪些失败样本的预测和关注区域发生变化。对比图见 `reports/figures/week4_baseline_vs_final_gradcam.png`。

## 7. Calibration Analysis

校准分析由 `plant-calibration-analysis` 从 `predictions.json` 生成。当前采用 top-label confidence：只比较预测类别置信度与该预测是否正确，不等价于完整多类别概率校准。

| 指标 | 数值 |
| --- | ---: |
| Sample count | 10709 |
| Accuracy | 0.9953 |
| Mean confidence | 0.8989 |
| Top-label ECE | 0.0965 |
| Top-label MCE | 0.3348 |
| Top-label Brier | 0.0140 |

Reliability diagram：`reports/figures/week4_reliability_diagram.png`。

当前模型在 `[0.80, 1.00]` 高置信区样本最多，且 bin accuracy 高于平均 confidence，表现为该 split 上偏保守；低置信区样本数量很少，不能过度解释其 MCE 峰值。由于 label smoothing 往往会降低模型输出置信度，这一现象与最终候选训练策略具有一致性，但本报告不把它当作已验证因果结论。

## 8. Limitations

1. **单 seed 限制**：Week 3–4 关键结论均来自 seed 42 单次正式运行，尚无多随机种子均值和标准差。
2. **数据泄漏风险**：官方 split 记录到 `227` 个跨 train/test 重叠 `leaf_id`，不能声称严格实体隔离泛化。
3. **受控背景限制**：PlantVillage 图像背景较受控，当前高精度不能代表真实田间环境。
4. **Grad-CAM 非因果**：Grad-CAM 只能表示目标类别分数与空间区域的相关性，不能证明模型“因果上依赖”某病斑或背景。
5. **人工审阅规模有限**：人工关注区域与错误类型审阅覆盖固定 24 个样本，其中错误样本 12 个，不能代表完整测试集所有失败模式。
6. **校准定义有限**：当前校准为 top-label calibration，不是完整多类别概率校准，也未执行 temperature scaling。
7. **峰值内存未验证**：Week 3 决策仍未包含正式峰值内存测量。

## 9. Conclusion and Next Step

截至 Week 4，本项目已经形成从数据审计、CNN Benchmark、训练策略消融到可解释性和错误分析的可复现闭环。当前最强候选 ResNet50 + Label Smoothing + Cosine Scheduler 在官方 test split 上达到 Macro F1 `0.9941`，主要失败集中在视觉相似病害类别和少量高置信错误。Grad-CAM 和校准分析为 Week 5 Demo 提供了稳定接口与展示材料，但报告必须保留受控背景、单 seed 和非因果解释边界。

下一步建议进入 Week 5：把预测、Top-5、Grad-CAM 和报告中的限制说明封装为 Streamlit Demo 服务层，并保留当前 Week 4 已审阅证据作为 Demo 的解释边界。

## References

[1] Sharada P. Mohanty, David P. Hughes, Marcel Salathé. “Using Deep Learning for Image-Based Plant Disease Detection.” Frontiers in Plant Science, 2016. https://arxiv.org/abs/1604.03169

[2] Kaiming He, Xiangyu Zhang, Shaoqing Ren, Jian Sun. “Deep Residual Learning for Image Recognition.” CVPR, 2016. https://arxiv.org/abs/1512.03385

[3] Ramprasaath R. Selvaraju, Michael Cogswell, Abhishek Das, Ramakrishna Vedantam, Devi Parikh, Dhruv Batra. “Grad-CAM: Visual Explanations from Deep Networks via Gradient-based Localization.” ICCV, 2017. https://arxiv.org/abs/1610.02391

[4] Chuan Guo, Geoff Pleiss, Yu Sun, Kilian Q. Weinberger. “On Calibration of Modern Neural Networks.” ICML, 2017. https://arxiv.org/abs/1706.04599

[5] Christian Szegedy, Vincent Vanhoucke, Sergey Ioffe, Jonathon Shlens, Zbigniew Wojna. “Rethinking the Inception Architecture for Computer Vision.” CVPR, 2016. https://arxiv.org/abs/1512.00567

[6] Rafael Müller, Simon Kornblith, Geoffrey Hinton. “When Does Label Smoothing Help?” NeurIPS, 2019. https://arxiv.org/abs/1906.02629

[7] Ilya Loshchilov, Frank Hutter. “SGDR: Stochastic Gradient Descent with Warm Restarts.” ICLR, 2017. https://arxiv.org/abs/1608.03983
