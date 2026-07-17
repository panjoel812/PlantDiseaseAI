# PlantDiseaseAI 八周研发任务

> 项目定位：以 PlantVillage 为起点，完成一套可复现、可解释、可部署、可写入科研简历的农业 AI 项目。

## 使用规则

- 本文档是项目执行与验收的唯一任务清单，按 Week 1 → Week 8 顺序推进。
- 只有当对应代码、测试、日志、指标或文档证据真实存在时，才能勾选任务。
- 附件中的准确率示例不是项目结果；Accuracy、F1、FPS、参数量和提升幅度必须由真实实验产生。
- 完整训练暂时无法运行时，可完成小样本冒烟测试，但必须明确标记验证范围，不能把它写成正式实验结论。
- 每完成一项任务，记录产物路径；每完成一周，同步 README、实验索引和本周复盘。
- 图像分类是核心主线。Week 1–5 未达到退出条件前，不得把 VLM 包装为项目核心成果。
- 项目用于教育与研究。病害说明和防治建议不能替代农学专家、植保人员或当地监管机构的专业意见。

## 八周总览

| 阶段 | 核心主题 | 主要成果 |
| --- | --- | --- |
| Week 1 | 数据、环境与最小基线 | EDA、DataLoader、MobileNetV2 基线 |
| Week 2 | 公平模型 Benchmark | 五个模型的统一对比表 |
| Week 3 | 模型改进与消融 | 增强、Loss、Scheduler、EMA 消融 |
| Week 4 | 可解释性与错误分析 | Grad-CAM、混淆分析、阶段报告 |
| Week 5 | 工程化与部署 | Streamlit Demo、Apple container、使用文档 |
| Week 6 | VLM 农业助手探索 | VQA 数据、LoRA 实验或资源受限原型 |
| Week 7 | 研究成果表达 | GitHub 展示、技术博客、项目 PPT |
| Week 8 | 复现审计与发布 | 最终报告、成果索引、简历条目 |

## 全局完成标准

- [x] 从干净环境可以按照文档安装依赖并运行最小流程。证据：`reports/week8_reproducibility.md`，仓库外锁定环境通过 226 tests、静态检查、合成训练—评估—推理 smoke、package build 与 CLI help。
- [ ] 数据划分可复现，但 official train/test 已知存在 227 个重叠 `leaf_id`，因此“训练集、验证集和测试集不存在已知泄漏”不成立；风险已解释，实体隔离评估仍列为后续研究。证据：`reports/data_audit.md`、`reports/data_split_limitations.md`。
- [x] 训练、评估、推理共用同一标签映射、预处理定义和配置来源。证据：`reports/final_experiment_report.md`、`src/plantdisease/` 的统一公共模块与全量测试。
- [x] 每个正式实验记录配置、随机种子、代码版本、环境、硬件、开始时间和产物路径。证据：`reports/week8_reproducibility.md`、`reports/final_experiment_report.md` 与各 run manifest。
- [x] 指标既有机器可读文件，也有适合报告阅读的表格或图形。证据：`docs/artifact-index.md`、`reports/final_experiment_report.md`。
- [x] 至少有公平 Benchmark、消融实验、Grad-CAM 和错误分析四类科研证据。证据：`reports/week2_benchmark_progress.md`、`reports/week3_ablation_results.md`、`reports/week4_gradcam_atlas.md`、`reports/week4_error_analysis.md`。
- [x] Demo、Apple container、README 和最小测试可运行。证据：`reports/week5_demo_engineering.md`、`README.md`、`tests/test_container_config.py`、`outputs/plantvillage/week5_demo/container_e2e.json`。
- [x] 最终报告明确数据集局限、实验局限和真实田间泛化风险。证据：`reports/final_experiment_report.md`、`reports/data_card.md`、`reports/model_card.md`。
- [x] 所有简历数字都能追溯到仓库内的真实证据。证据：`docs/resume/week8_resume_evidence.md`、`reports/release/week8_claim_evidence.json`。
- [x] 数据、模型权重、密钥、本地缓存和大体积输出未被误提交到 Git。证据：`docs/release/week8_release_checklist.md`、`reports/release/week8_rc1_manifest.json` 与最终 tracked-file 扫描。

---

### Week 1：数据理解、环境与最小基线

#### 周目标

建立可复现的工程骨架，完成 PlantVillage 数据审计、EDA、PyTorch 数据管线和 MobileNetV2 最小基线，证明训练—评估—推理链路能够跑通。

> 当前状态（2026-07-11）：Week 1 已关闭。工程闭环、PlantVillage 下载、train split 审计、EDA、真实 MobileNetV2 官方 split baseline、checkpoint 推理和证据索引已验证。官方 split 检查发现 train/test 有 227 个重叠 `leaf_id`，因此结果必须标注为官方 split baseline，不能表述为严格实体隔离的无泄漏结果。

#### 研发任务

- [x] 初始化 Git 仓库，建立 `.gitignore`、开源许可证和基础 README。
- [x] 建立推荐目录：`configs/`、`src/plantdisease/`、`scripts/`、`tests/`、`notebooks/`、`app/`、`docs/`、`reports/`、`outputs/`。
- [x] 建立 Python 3.12 环境声明和锁定的依赖文件；记录 PyTorch、torchvision、datasets、timm、OpenCV、scikit-learn、matplotlib、TensorBoard 等版本。
- [x] 编写数据获取说明或脚本，默认从 Hugging Face 数据集源加载 PlantVillage，并支持本地缓存目录。
- [x] 审计数据集实际样本数、类别数、标签名称、图像尺寸、颜色模式、重复样本和损坏样本；不要直接沿用资料中的近似数字。
- [x] 设计固定且可复现的 train/validation/test 划分，使用 stratified split 或数据源已有的官方划分，并保存索引与随机种子。
- [x] 检查同源重复图像是否跨集合，记录潜在数据泄漏风险。
- [x] 完成 `notebooks/eda.ipynb` 或等价脚本：类别分布、样本图、尺寸分布、每类数量和异常样本。
- [x] 实现训练与评估预处理；仅训练集使用随机增强，验证集和测试集只使用确定性变换。
- [x] 实现 Dataset/DataLoader 冒烟测试，验证 batch 形状、标签范围、dtype、归一化和多进程加载。
- [x] 使用 torchvision 或 timm 的 MobileNetV2 预训练权重建立未经项目技巧改进的基线。
- [x] 完成单 batch 过拟合测试，确认模型、Loss、反向传播和优化器连接正确。
- [x] 完成小规模训练冒烟测试并保存 checkpoint、loss/accuracy 曲线和运行配置。
- [x] 实现 Accuracy、Macro Precision、Macro Recall、Macro F1、分类别指标和混淆矩阵。
- [x] 编写最小推理入口：输入单张图片，输出 Top-5 类别与置信度。
- [x] 添加数据管线、标签映射、指标计算、checkpoint 读写和推理输出的基础测试。
- [x] 写 Week 1 实验记录，解释为什么当前任务是 image classification，而不是 detection 或 segmentation。

#### 必须交付物

- [x] 可安装的项目环境与明确的启动命令。
- [x] 数据审计报告、固定划分文件和 EDA 图表。
- [x] 可运行的 DataLoader、训练、评估和单图推理入口。
- [x] MobileNetV2 基线配置、checkpoint、日志和基础指标文件。
- [x] Week 1 实验记录与 README 快速开始部分。

#### 验收标准

- [x] 干净环境按文档执行后，数据冒烟测试和单图推理能够运行。
- [x] 固定相同随机种子时，数据划分索引完全一致。
- [x] 一个 batch 的图像张量符合模型输入约定，标签均在合法范围内。
- [x] 单 batch 过拟合测试能明显降低训练 Loss，排除基础训练链路故障。
- [x] checkpoint 可被重新加载，并对同一图片产生结构一致的 Top-5 输出。
- [x] 指标文件、图表和运行配置均能追溯到同一次实验。

#### 科研与简历证据

- [x] `reports/data_audit.md` 或等价数据审计文件。
- [x] 类别分布、样本展示和训练曲线图片。
- [x] 基线实验配置与机器可读指标文件。
- [x] 数据划分与数据泄漏检查记录。
- [x] 可引用的证据索引：实验 ID、配置路径、日志路径、权重路径和图表路径。

#### 退出条件

- [x] 从数据加载到 checkpoint 推理的最小闭环已验证。
- [x] 基线实验可复现，且不存在阻塞 Week 2 公平 Benchmark 的接口问题。
- [x] 本周所有已勾选任务均有仓库内证据。

---

### Week 2：统一协议下的模型 Benchmark

#### 周目标

在完全相同的数据划分、预处理、训练预算和评估方法下，对 MobileNetV2、ResNet18、ResNet50、EfficientNet-B0、EfficientNetV2-S 进行公平比较。

> 当前状态（2026-07-11）：Week 2 官方 split Benchmark 已形成可审计结论。五模型 smoke、五个候选模型正式训练、参数/FLOPs、MPS 延迟/吞吐、Pareto 图和报告均已完成。ResNet50 是最佳精度候选，Accuracy 0.9830 / Macro F1 0.9743；MobileNetV2 是默认轻量部署候选，2.27M 参数、0.31G FLOPs、644.3 img/s。峰值内存未测量；官方 split 的 227 个重叠 `leaf_id` 风险仍适用于 Week 2 结果。

#### 研发任务

- [x] 抽象统一模型工厂，使用稳定模型名创建五种网络并校验输出类别数。
- [x] 为每个模型建立独立配置文件，但复用数据划分、输入尺寸、优化器策略和训练预算。
- [x] 明确预训练权重来源、许可证、输入归一化和分类头替换方式。
- [x] 在正式训练前，对五个模型逐一执行前向、反向和 checkpoint 冒烟测试。
- [x] 记录各模型可训练参数量、总参数量和理论计算量；注明计算工具与输入尺寸。
- [x] 在固定随机种子集合上训练全部候选模型；资源有限时先完成统一预算的初筛，再对入选模型执行完整预算。
- [x] 使用同一 test split 统一评估 Accuracy、Macro Precision、Macro Recall、Macro F1 和分类别指标。
- [x] 测量推理延迟与吞吐量，固定硬件、batch size、精度、输入尺寸、预热次数和统计区间。
- [x] 输出训练时间、参数量、计算量、准确性和速度对比表；峰值内存明确记录为未测量。
- [x] 分析性能—效率 Pareto 前沿，分别选出“最佳精度模型”和“最佳部署模型”。
- [x] 对每个正式结果执行日志、配置、checkpoint 和指标文件的一致性检查。
- [x] 编写 Benchmark 复现命令与 Week 2 研究小结。

#### 必须交付物

- [x] 五个模型的配置、训练日志、checkpoint 索引和测试指标。
- [x] 统一 Benchmark 表与性能—效率可视化。
- [x] 可重复运行的训练、批量评估和速度测试命令。
- [x] Week 2 Benchmark 报告，明确比较协议与资源限制。

#### 验收标准

- [x] 五个模型使用相同数据划分和明确可比的训练预算。
- [x] 每个模型至少通过小规模端到端验证；正式表格只包含完整运行成功的实验。
- [x] 测试集只用于最终评估，没有参与模型选择或超参数调优。
- [x] FPS 与延迟结果包含完整测量上下文，可在同类硬件上复测。
- [x] Benchmark 表中每一行都可追溯到唯一实验 ID 和机器可读指标。
- [x] 模型选择结论同时讨论精度、计算成本、内存和部署目标。

#### 科研与简历证据

- [x] 模型 Benchmark 表和 Pareto 图。
- [x] 五个模型的配置差异与公平性检查记录。
- [x] 硬件环境、速度测量方法和原始测量数据。
- [x] “最佳精度模型”与“最佳部署模型”的证据链和选择理由。
- [x] 可在简历中引用的真实模型数量、指标与效率数据来源。

#### 退出条件

- [x] 至少一个高精度候选模型和一个轻量部署候选模型已由实测结果选出。
- [x] Benchmark 的所有数据可复现、可追溯，且比较协议限制已记录。
- [x] Week 3 的改进基线、主指标和训练预算已经冻结。

---

### Week 3：模型改进与消融实验

#### 周目标

围绕固定基线，系统评估数据增强、损失函数、学习率调度和 EMA 的独立及组合贡献，形成可信的 Ablation Study。

> 当前状态（2026-07-13）：Week 3 工程能力、单变量消融和组合候选实验已完成。配置解析、Mixup/CutMix、RandAugment、Random Erasing、Label Smoothing、Focal Loss、Cosine Scheduler、EMA 和训练入口接线均已有测试覆盖；消融矩阵写入 `configs/week3_ablation/` 与 `reports/week3_ablation_matrix.md`。`00_resnet50_baseline` 复刻 Week 2 ResNet50，Test Accuracy 0.9830 / Macro F1 0.9743；最强单变量为 `03_cosine_scheduler`，Test Accuracy 0.9935 / Macro F1 0.9898；组合候选 `09_combo_candidate` 使用 Label Smoothing `0.1` + Cosine Scheduler，Test Accuracy 0.9953 / Macro F1 0.9941，是当前 seed 42 官方 split 最强候选。失败和负结果已记录：Focal Loss、EMA、RandAugment、Random Erasing 均低于 00 baseline。`09_combo_candidate`、ResNet50 目标层 `layer4.2` 与 Week 4 四象限样本索引已冻结，证据见 `reports/week4_frozen_samples.md`。

#### 研发任务

- [x] 冻结 Week 2 选出的改进基线、数据划分、主指标和默认训练预算。
- [x] 将 Mixup、CutMix、RandAugment、Random Erasing 实现为可配置、可关闭的独立开关。
- [x] 实现 Label Smoothing 与 Focal Loss，并为输入、目标格式和数值稳定性添加测试。
- [x] 实现 Cosine Scheduler，明确是否包含 warmup、更新粒度和总 step 计算方式。
- [x] 实现 EMA，验证参数更新、保存、加载和评估时权重切换。
- [x] 为 Mixup/CutMix 标签混合、增强概率、Loss 和 EMA 编写单元测试。
- [x] 设计单变量消融矩阵：每次只改变一个因素，其余配置保持一致。
- [x] 设计组合实验，但仅在单变量结果和资源预算支持时执行。
- [x] 每个关键实验使用固定随机种子集合；报告均值、标准差或明确说明只有单次运行。
- [x] 记录失败、无提升和不稳定实验，禁止只保留有利结果。
- [x] 比较总体指标之外的分类别 F1，检查改进是否只帮助多数类。
- [x] 分析训练稳定性、收敛速度、过拟合程度和额外计算成本。
- [x] 生成消融表、训练曲线叠图和改进方法说明。
- [x] 选择最终分类模型，并将选择理由写入决策记录。

#### 必须交付物

- [x] 可配置的增强、Loss、Scheduler 和 EMA 实现及测试。
- [x] 单变量消融矩阵、组合实验结果和原始指标文件。
- [x] 包含失败实验的完整实验索引。
- [x] 最终分类模型配置、checkpoint 索引和选择记录。

#### 验收标准

- [x] 关闭全部改进开关时，训练行为与冻结基线一致或差异得到解释。
- [x] 每个单变量实验只改变目标因素，配置差异可自动或人工审计。
- [x] 消融表中的结果均来自真实运行，不使用附件示例值或人工估计。
- [x] 至少验证增强标签、Loss 数值、Scheduler 边界和 EMA checkpoint 四类关键行为。
- [x] 最终模型选择同时考虑效果、方差、速度、内存和实现复杂度。
- [x] 对没有提升的方法给出数据或机制层面的合理分析。

#### 科研与简历证据

- [x] 单变量消融表和组合实验表。
- [x] 多随机种子统计或单次运行限制声明。
- [x] Baseline 与最终模型的训练曲线对比。
- [x] 失败实验、负结果和研究决策记录。
- [x] 可核验的性能变化与额外计算成本数据。

#### 退出条件

- [x] 最终分类模型已通过固定测试集评估并保存完整证据。
- [x] 每项保留的改进都能由消融实验支持，不依赖主观判断。
- [x] 可解释性分析所需的模型、层选择和样本索引已经冻结。

---

### Week 4：Grad-CAM、错误分析与阶段报告

#### 周目标

解释模型关注区域，识别易混淆类别、背景偏差和失败模式，把“模型效果”转化为可讨论的研究结论。

> 当前状态（2026-07-13）：Week 4 已收口。原生 PyTorch Grad-CAM 核心与五模型目标层解析已实现并通过单元测试。Week 4 正式候选仍为 `09_combo_candidate`，ResNet50 目标层冻结为最后一个 residual block 输出 `layer4.2`；该选择替代 block 内部 `layer4.2.conv3`，避免捕获残差合并前中间张量导致代表性热图偏离叶片。`plant-freeze-samples` 已在官方 test split 上导出 `10709` 条逐样本预测，并冻结正确高置信、正确低置信、错误高置信、错误低置信四组样本索引，证据见 `outputs/plantvillage/week4_explainability/frozen_samples.json` 与 `reports/week4_frozen_samples.md`。`plant-gradcam-atlas` 已按修正后的 `layer4.2` 重新生成固定 24 样本 Grad-CAM 图集和摘要报告，证据见 `outputs/plantvillage/week4_explainability/gradcam_atlas/` 与 `reports/week4_gradcam_atlas.md`。`plant-error-analysis` 已生成非归一化/行归一化混淆矩阵、低 F1 类别、重点混淆对和高置信错误报告，证据见 `outputs/plantvillage/week4_explainability/error_analysis.json` 与 `reports/week4_error_analysis.md`。固定 24 样本的关注区域和错误类型审阅已完成，证据见 `outputs/plantvillage/week4_explainability/attention_review.json` 与 `reports/week4_attention_review.md`。`plant-calibration-analysis` 已生成 top-label ECE/MCE/Brier 和 reliability diagram，证据见 `outputs/plantvillage/week4_explainability/calibration.json`、`reports/week4_calibration.md` 与 `reports/figures/week4_reliability_diagram.png`。Baseline 与最终模型在 12 个最终模型失败样本上的同样本预测/Grad-CAM 对比已完成，证据见 `outputs/plantvillage/week4_explainability/baseline_vs_final_gradcam.json`、`reports/week4_baseline_vs_final_gradcam.md` 与 `reports/figures/week4_baseline_vs_final_gradcam.png`。Grad-CAM 复现性验证显示 24/24 个 direct heatmap 精确一致，证据见 `outputs/plantvillage/week4_explainability/gradcam_reproducibility_direct.json` 与 `reports/week4_gradcam_reproducibility.md`。Week 1–4 阶段报告已同步并通过 20/20 一致性检查，证据见 `reports/week4_stage_report.md` 与 `reports/week4_consistency_audit.md`。

#### 研发任务

- [x] 实现或集成 Grad-CAM，明确目标层、类别目标、归一化和叠加方法。
- [x] 为 Grad-CAM 输出形状、数值范围、批处理、梯度状态和模型 hook 清理添加测试。
- [x] 从正确高置信、正确低置信、错误高置信、错误低置信四组中固定抽样。
- [x] 为每个重点类别生成原图、预测、真实标签、置信度和热力图组合图。
- [x] 检查模型关注叶片、病斑、背景、阴影、边框或数据集水印的程度。证据：`reports/week4_attention_review.md`。
- [x] 生成归一化与非归一化混淆矩阵。
- [x] 按混淆次数和分类别 F1 确定重点错误对。
- [x] 人工审阅代表性失败样本，建立错误类型标签：视觉相似、背景偏差、低质量图像、遮挡、标签疑问或域偏移。证据：`outputs/plantvillage/week4_explainability/attention_review.json`、`reports/week4_attention_review.md`。
- [x] 比较基线与最终模型在同一失败样本上的预测和 Grad-CAM 差异。证据：`reports/week4_baseline_vs_final_gradcam.md`、`reports/figures/week4_baseline_vs_final_gradcam.png`。
- [x] 检查置信度校准，绘制 reliability diagram，并在需要时报告 ECE 等校准指标。
- [x] 将关键结论与数据证据绑定，区分“观察到的现象”和“尚未验证的解释”。
- [x] 撰写阶段实验报告，覆盖问题定义、数据、方法、实验、消融、可解释性、错误分析、局限和下一步。

#### 必须交付物

- [x] 可重复生成 Grad-CAM 的脚本或模块及测试。
- [x] 固定样本索引、Grad-CAM 图集和重点错误案例图集。
- [x] 混淆矩阵、分类别指标、校准图和错误类型统计。
- [x] Week 1–4 阶段实验报告。

#### 验收标准

- [x] 对同一 checkpoint、输入和目标类别，Grad-CAM 结果可复现。证据：`reports/week4_gradcam_reproducibility.md`。
- [x] 热力图与原图空间尺寸正确对齐，且没有 hook 泄漏或梯度状态污染。
- [x] 错误分析至少覆盖最常见混淆对和高置信错误。
- [x] 报告中的每个关键结论均引用对应图表、指标或样本索引。
- [x] 明确说明 PlantVillage 背景较受控，结果不能直接代表真实田间泛化能力。
- [x] 报告不把相关性热力图描述成因果解释。

#### 科研与简历证据

- [x] Grad-CAM 代表性图集和生成配置。
- [x] Top 混淆类别及失败类型统计。证据：`reports/week4_error_analysis.md`、`reports/week4_attention_review.md`。
- [x] Baseline 与最终模型的同样本对比图。证据：`reports/figures/week4_baseline_vs_final_gradcam.png`。
- [x] 校准分析与高置信错误案例。
- [x] 可供导师阅读的阶段实验报告。

#### 退出条件

- [x] 最终分类模型的主要优势、失败模式和局限均有证据支持。
- [x] Demo 所需预测、Top-5 和 Grad-CAM 接口已经稳定。证据：`src/plantdisease/serving/service.py`、`tests/serving/test_service.py`、`reports/week5_demo_engineering.md`。
- [x] 阶段报告通过数据路径、图表编号和实验 ID 的一致性检查。证据：`reports/week4_consistency_audit.md`。

---

### Week 5：Streamlit Demo、Apple container 与工程化

#### 周目标

把稳定的分类与解释接口封装为可演示、可测试、可容器化运行的产品原型。

> 当前状态（2026-07-13）：Week 5 本地与 Apple `container` Demo 工程闭环已完成。新增 UI 无关服务层、Streamlit 页面、疾病知识卡、低置信/安全提示、服务缓存、固定合成样例、本地 ResNet50 checkpoint 端到端 Top-5 + Grad-CAM 验证和 Demo 截图。Apple `container` 已完成 CPU-only 镜像 build/run、healthcheck、容器内固定样例 Top-5 + Grad-CAM 验证、镜像大小记录和一次运行时资源采样；冷启动时间记录为单次日志观测值，不是重复 benchmark。

#### 研发任务

- [x] 将模型加载、预处理、预测和 Grad-CAM 封装为与 UI 无关的服务层。证据：`src/plantdisease/serving/service.py`、`tests/serving/test_service.py`。
- [x] 建立 Streamlit 页面：项目说明、图片上传、示例图片、预测按钮和结果区。证据：`app/streamlit_app.py`、`tests/test_streamlit_app.py`、`reports/figures/week5_streamlit_demo.jpg`。
- [x] 展示 Top-5 类别、置信度、Grad-CAM、推理耗时和模型版本。证据：`outputs/plantvillage/week5_demo/local_e2e.json`、`reports/week5_demo_engineering.md`。
- [x] 建立疾病知识映射，展示植物、病害、简要症状和教育用途的一般性建议。证据：`src/plantdisease/serving/knowledge.py`、`tests/serving/test_knowledge.py`。
- [x] 为未知图片、非图像文件、损坏文件、过大文件和推理异常提供清晰错误提示。证据：`tests/serving/test_service.py` 覆盖非法 bytes、过大文件、损坏文件和推理异常包装；闭集未知/域外图片通过 PlantVillage 范围警告与低置信提示处理。
- [x] 在界面显著位置加入非专业诊断和农业安全免责声明。证据：`src/plantdisease/serving/service.py`、`app/streamlit_app.py`。
- [x] 缓存模型资源，避免每次交互重复加载权重。证据：`src/plantdisease/serving/cache.py`、`tests/serving/test_cache.py`。
- [x] 添加服务层单元测试和 Streamlit 最小启动测试。证据：`tests/serving/`、`tests/test_streamlit_app.py`。
- [x] 编写 Apple `Containerfile`、`.dockerignore` 和健康检查；默认使用 CPU 可运行配置。证据：`Containerfile`、`.dockerignore`、`tests/test_container_config.py`、`reports/week5_demo_engineering.md`。
- [x] 使用固定示例图片完成本地与容器内的端到端验证。本地证据：`outputs/plantvillage/week5_demo/local_e2e.json`；容器内证据：`outputs/plantvillage/week5_demo/container_e2e.json`、`reports/week5_demo_engineering.md`。
- [x] 记录镜像大小、冷启动时间、内存占用和单图推理延迟。证据：`reports/week5_demo_engineering.md`；冷启动为单次日志观测，内存为 `container stats --no-stream` 采样。
- [x] 完善 README：功能、架构、安装、训练、评估、推理、Demo、Apple container、结果和局限。React 作物优先聚合语义与未实测 Windows/Linux Docker 兼容路径已补充。证据：`README.md`、`reports/week5_demo_engineering.md`、`reports/week8_react_demo_qa.md`。
- [x] 创建演示截图或短 GIF，但不得展示未经真实运行的指标。证据：`reports/figures/week5_streamlit_demo.jpg`、`reports/figures/week8_react_demo_desktop.png`。

#### 必须交付物

- [x] 可运行的 Streamlit Demo 和 UI 无关推理服务。
- [x] Apple `Containerfile`、容器运行命令和健康检查说明；容器实际运行已验证。证据：`reports/week5_demo_engineering.md`。
- [x] Demo 测试、固定示例图片和本地端到端验证记录。
- [x] 完整 README、截图或 GIF，以及农业安全免责声明。

#### 验收标准

- [x] 本地和 Apple container 环境均能对固定示例完成 Top-5 与 Grad-CAM 推理。证据：`outputs/plantvillage/week5_demo/local_e2e.json`、`outputs/plantvillage/week5_demo/container_e2e.json`、`reports/week5_demo_engineering.md`。
- [x] 模型只加载一次，连续推理不重复初始化全部资源。
- [x] 非法输入和推理失败不会使应用无提示崩溃。
- [x] Demo 显示的模型版本、标签和预处理与评估阶段一致。
- [x] Apple container 构建上下文不包含原始数据、密钥、本地缓存或非必要大文件。证据：`.dockerignore`、`tests/test_container_config.py`。
- [x] README 中的命令已实际执行验证，结果和局限表述真实。证据：`README.md`、`reports/week5_demo_engineering.md`。

#### 科研与简历证据

- [x] Demo 截图或短 GIF、运行命令和固定样例。
- [x] 容器构建与启动记录。证据：`reports/week5_demo_engineering.md`。
- [x] 本地/容器推理性能和资源占用数据。证据：`outputs/plantvillage/week5_demo/local_e2e.json`、`outputs/plantvillage/week5_demo/container_e2e.json`、`reports/week5_demo_engineering.md`；容器内存为单次采样。
- [x] 端到端测试结果和异常输入处理证据。
- [x] 可公开展示的项目架构与功能说明。证据：`docs/project-architecture.md`。

#### 退出条件

- [x] 分类核心成果可以在不阅读源码的情况下被安装、运行和演示。本地 Streamlit 和固定样例端到端已验证。
- [x] Demo 与离线评估共享同一推理实现，结果不存在已知漂移。
- [x] Week 1–5 已形成独立完整的科研与工程作品，即使不做 VLM 也可交付。证据：Week 1–4 阶段报告、Week 5 Demo 工程报告、README 和成果索引。

---

### Week 6：视觉语言模型与农业助手探索

#### 周目标

在不削弱分类主线的前提下，探索小型 VLM、PlantVillageVQA 数据和 LoRA 微调，形成可运行且诚实描述能力边界的农业助手原型。

#### 研发任务

- [x] 根据本机硬件、内存、许可证、中文能力和生态成熟度，对 Qwen 系列小型 VLM、SmolVLM、InternVL 小型版本等候选进行当前可用性调研。证据：`reports/week6_vlm_selection.md`。
- [x] 记录选型日期、模型版本、许可证、参数规模、量化方式、最低硬件需求和选择理由。证据：`reports/week6_vlm_selection.md`。
- [x] 明确 VLM 研究问题：识别病害、描述可见症状、回答数据集知识问题，还是生成一般性预防建议。证据：`reports/week6_vlm_selection.md`。
- [x] 设计 PlantVillageVQA schema，至少包含 image_id、question、answer、question_type、source、split 和审计状态。证据：`src/plantdisease/vlm/schema.py`、`tests/vlm/test_schema.py`。
- [x] 从已核验标签和可信知识源构建 VQA 样本，禁止把未经核验的模型生成内容直接当作真值。当前为 24 图/72 问 seed 数据，证据：`scripts/build_vqa_dataset.py`、`reports/week6_vqa_datacard.md`。
- [x] 按图片实体划分训练、验证和测试，避免同一图片的问题答案跨集合泄漏。seed 数据 `entity_split_leakage=false`，证据：`outputs/plantvillage/week6_vlm/vqa_seed_summary.json`、`reports/week6_vqa_datacard.md`。
- [ ] 抽样进行人工质量审计，记录问题重复、答案歧义、知识错误和语言质量。当前已完成自动质量审计与人工审计模板：72 条 seed VQA、24 图、3 个重复模板、空答案 0、7 条自动风险标记，审计模板仍为 `pending_human_review`，人工逐条审阅待完成。证据：`reports/week6_vlm_result_analysis.md`、`reports/week6_vqa_manual_audit_template.md`。
- [x] 建立未微调模型的 zero-shot/few-shot 基线。当前已完成 Qwen3-VL smoke：5 张测试图/15 问、失败 0；原始 prompt 严格 normalized exact-match 为 0/15，短答案 prompt 为 10/15，`choice` 与 `few_shot_choice` 均为 11/15；choice prompt 风险词降到 0，但 condition 仍只有 1/5。证据：`outputs/plantvillage/week6_vlm/qwen3_vl_zero_shot_smoke.json`、`outputs/plantvillage/week6_vlm/qwen3_vl_zero_shot_smoke_short.json`、`outputs/plantvillage/week6_vlm/qwen3_vl_choice_smoke.json`、`outputs/plantvillage/week6_vlm/qwen3_vl_few_shot_choice_smoke.json`、`reports/week6_vlm_prompt_compare.md`、`reports/week6_vlm_choice_prompt_scaffold.md`。
- [ ] 在硬件允许时实现 LoRA 微调；QLoRA 或低比特训练仅在当前平台真正支持时使用。
- [ ] 若本机无法稳定训练，执行小样本管线验证，并保留可在云端或更强硬件运行的配置与明确的未验证声明。
- [ ] 设计 VQA 评估：分类问题使用准确率，开放问题使用规则或语义指标并结合人工评分标准。当前已实现 closed-label exact-match 按题型拆解、混淆统计、风险词标记，以及 choice-style 选项映射评分；开放题/人工评分标准待完成。证据：`src/plantdisease/vlm/analysis.py`、`src/plantdisease/vlm/baseline.py`、`scripts/analyze_vlm_results.py`、`reports/week6_vlm_result_analysis.md`、`reports/week6_vlm_choice_prompt_scaffold.md`。
- [ ] 比较微调前后在固定测试集上的表现、幻觉、拒答和回答一致性。
- [x] 将分类器高置信结果作为可选结构化上下文，实验性构建农业助手，而不是让 VLM 无依据替代分类器。证据：`src/plantdisease/vlm/assistant.py`、`scripts/demo_vlm_assistant.py`、`reports/week6_vlm_assistant.md`。
- [x] 对低置信、非叶片图片和知识不足情况提供拒答或转介提示。证据：`tests/vlm/test_assistant.py`、`outputs/plantvillage/week6_vlm/vlm_assistant_demo.json`。
- [x] 为建议内容加入来源、适用范围和非专业诊断声明。证据：`src/plantdisease/vlm/assistant.py`、`reports/week6_vlm_assistant.md`。
- [x] 撰写 VLM 实验记录，明确它是探索性扩展还是已验证成果。证据：`reports/week6_vlm_experiment.md`。

#### 必须交付物

- [x] VLM 选型记录与硬件可行性结论。证据：`reports/week6_vlm_selection.md`。
- [ ] 版本化的 VQA schema、数据构建脚本、统计和质量审计结果。schema、脚本、统计、自动质量审计和人工审计模板已完成；人工逐条质量审计待完成。证据：`src/plantdisease/vlm/schema.py`、`scripts/build_vqa_dataset.py`、`reports/week6_vqa_datacard.md`、`reports/week6_vqa_manual_audit_template.md`。
- [x] zero-shot/few-shot 基线，以及 LoRA 结果或清晰标记的小样本管线验证。zero-shot、short、choice 和 few-shot choice smoke 已完成；LoRA 未完成，明确记录为未来工作。证据：`reports/week6_vlm_prompt_compare.md`。
- [x] 农业助手原型、固定评测集、能力边界和安全说明。证据：`src/plantdisease/vlm/assistant.py`、`scripts/demo_vlm_assistant.py`、`outputs/plantvillage/week6_vlm/vlm_assistant_demo.json`、`reports/week6_vlm_assistant.md`。

#### 验收标准

- [x] 训练、验证和测试按图片实体隔离，不存在已知 VQA 泄漏。当前 seed 数据已验证，证据：`outputs/plantvillage/week6_vlm/vqa_seed_summary.json`。
- [x] 每个正式答案都能追溯到标签、知识来源或人工审计记录。当前 seed 答案均来自 `plantvillage_label`，证据：`reports/week6_vqa_datacard.md`。
- [ ] LoRA 结果只有在完整训练与评估成功后才能写入成果；冒烟测试不得冒充微调效果。
- [ ] 微调前后比较使用同一固定评测集和明确评分方法。
- [x] 农业助手能识别低置信或超出知识边界的请求，并提供安全提示。证据：`tests/vlm/test_assistant.py`、`tests/vlm/test_assistant_demo.py`。
- [x] 报告明确区分分类器实测能力、VLM 实测能力和计划中的能力。证据：`reports/week6_vlm_selection.md`、`reports/week6_vlm_experiment.md`、`reports/week6_vlm_prompt_compare.md`。

#### 科研与简历证据

- [x] VLM 选型矩阵、模型与许可证信息。证据：`reports/week6_vlm_selection.md`。
- [ ] VQA 数据卡、schema、样本统计和人工审计记录。数据卡、schema、样本统计、自动质量审计和人工审计模板已完成；人工审计待完成。证据：`reports/week6_vqa_datacard.md`、`reports/week6_vlm_result_analysis.md`、`reports/week6_vqa_manual_audit_template.md`。
- [ ] 微调配置、训练日志、评估结果或资源限制证明。
- [x] 固定问答案例、失败案例和幻觉分析。证据：`reports/week6_vlm_result_analysis.md`、`reports/week6_vlm_prompt_compare.md`、`outputs/plantvillage/week6_vlm/vlm_result_analysis.json`、`outputs/plantvillage/week6_vlm/vlm_result_analysis_prompt_compare.json`。
- [x] 可核验的农业助手演示；若未完成完整训练，简历只描述原型和管线。证据：`scripts/demo_vlm_assistant.py`、`outputs/plantvillage/week6_vlm/vlm_assistant_demo.json`、`reports/week6_vlm_assistant.md`。

#### 退出条件

- [x] VLM 阶段有独立可验证产物，且没有覆盖或夸大分类主线结果。证据：`reports/week6_vlm_selection.md`、`reports/week6_vlm_experiment.md`、`reports/week6_vlm_result_analysis.md`、`reports/week6_vlm_prompt_compare.md`。
- [x] 数据、模型、许可证、硬件和安全限制均已记录。证据：`reports/week6_vlm_selection.md`、`reports/week6_vqa_datacard.md`、`reports/week6_vlm_experiment.md`、`reports/week6_vlm_result_analysis.md`、`reports/week6_vlm_prompt_compare.md`。
- [x] 后续展示材料能够准确区分“完成”“冒烟验证”和“未来工作”。证据：`reports/week6_vlm_assistant.md`、`README.md`、`TASKS.md`。

---

### Week 7：GitHub 展示、技术博客与项目 PPT

#### 周目标

把已有代码和科研证据组织成导师、评审或面试官能快速理解并复核的公开作品材料。

> 当前状态（2026-07-15）：Week 7 Apple Hybrid Nature 展示层已完成本地构建与审计，包括 README 首屏、架构图、真实本地 MPS 固定合成样例 Demo 媒体、12 页可编辑 PPT 与 12/12 双版本讲稿、技术博客和成果索引。最终审阅后修复了桌面/移动端主控件对比度，并将 VLM 改为 Serve 下方的探索性支线；受影响测试 `15 passed`，全仓 `175 passed`、Ruff 通过。内部实现计划已改为可移植工具与临时目录写法，严格 tracked-file 路径扫描无输出。干净环境快速开始仍留给 Week 8。证据：`reports/week7_apple_showcase.md`、`reports/week7_public_release_check.md`、`docs/media/week7_apple_demo.mp4`、`docs/media/week7_apple_demo.gif`、`docs/presentation/week7_apple_showcase_deck.pptx`。

#### 研发任务

- [x] 重构 README 信息层级：问题、亮点、Demo、结果、架构、快速开始、复现、局限、引用和许可证。证据：`README.md`。
- [x] 创建项目架构图，展示数据、训练、评估、解释、Demo 和 VLM 的依赖关系。证据：`docs/week7_showcase_architecture.md`。
- [x] 更新结果表，只引用 Week 2–6 已核验的指标和实验 ID。证据：`docs/week7_results_snapshot.md`。
- [x] 选择代表性训练曲线、混淆矩阵、Grad-CAM、错误案例和 Demo 截图。媒体清单与最终 Apple Demo 媒体均已核验。证据：`docs/week7_demo_media_inventory.md`、`reports/week7_apple_showcase.md`。
- [x] 制作短 GIF 或视频，覆盖上传图片、Top-5、热力图和安全说明。证据：`docs/media/week7_apple_demo.gif`、`docs/media/week7_apple_demo.mp4`、`docs/media/week7_apple_demo_poster.png`、`reports/week7_apple_showcase.md`。
- [x] 清理 Notebook 输出、临时文件、绝对路径、个人隐私和无效缓存。当前无 tracked `.ipynb` 输出或缓存目录；内部实现计划已改为环境变量、仓库相对路径和运行时临时根目录，严格 tracked-file 路径扫描无输出。证据：`reports/week7_public_release_check.md`。
- [x] 扫描仓库中的密钥、大文件、许可证冲突和无法复现命令。证据：`reports/week7_public_release_check.md`。
- [x] 撰写中文技术博客：问题背景、数据、基线、Benchmark、改进、消融、解释、部署、VLM、局限与反思。证据：`docs/blog/week7_technical_blog_zh.md`。
- [x] 确保博客图表与报告使用同一数据来源，不手工改写实验数字。证据：`docs/week7_evidence_map.md`、`docs/week7_results_snapshot.md`、`docs/blog/week7_technical_blog_zh.md`。
- [x] 制作 10–15 页项目 PPT：动机、任务、数据、方法、实验协议、结果、消融、解释、Demo、VLM、局限和下一步。已生成 12 页可编辑 PPT，并通过结构、讲稿和逐页视觉 QA。证据：`docs/presentation/week7_apple_showcase_deck.pptx`、`docs/presentation/week7_ppt_outline.md`、`reports/week7_apple_showcase.md`。
- [x] 为 PPT 准备 5 分钟与 10 分钟两版讲稿要点。证据：`docs/presentation/week7_ppt_outline.md`。
- [x] 建立 `docs/artifact-index.md`，统一索引代码、实验、图表、报告、博客、PPT 和演示。当前已扩展 Week7 展示材料索引；博客、PPT 大纲和发布检查已补入。证据：`docs/artifact-index.md`。
- [x] 邀请一次技术审阅或自查，修复无法理解、无法复现或证据不充分的表述。已完成 UI、媒体、PPT 和编辑材料的分任务审阅及最终本地审计；审计发现的内部计划路径便携性问题已修正并重新扫描。证据：`reports/week7_public_release_check.md`、`reports/week7_apple_showcase.md`。

#### 必须交付物

- [x] 高质量 README、架构图、结果图表和 Demo 媒体。证据：`README.md`、`docs/week7_showcase_architecture.md`、`docs/media/week7_apple_architecture.png`、`docs/week7_results_snapshot.md`、`docs/media/week7_apple_demo.gif`、`docs/media/week7_apple_demo.mp4`、`reports/week7_apple_showcase.md`。
- [x] 完整中文技术博客与引用来源。证据：`docs/blog/week7_technical_blog_zh.md`。
- [x] 10–15 页项目 PPT 和讲稿要点。证据：`docs/presentation/week7_apple_showcase_deck.pptx`、`docs/presentation/week7_ppt_outline.md`、`reports/week7_apple_showcase.md`。
- [x] 成果索引、许可证与公开发布检查记录。证据：`docs/artifact-index.md`、`LICENSE`、`reports/week7_public_release_check.md`。

#### 验收标准

- [x] 新读者能在 README 首页理解问题、方法、主要实测结果和项目局限。证据：`README.md`、`reports/week7_public_release_check.md`。
- [x] 快速开始命令在干净环境中完成验证。证据：`reports/week8_reproducibility.md`，仓库外锁定环境完整通过。
- [x] README、博客、PPT 和报告中的同一指标数值一致并可追溯。证据：`docs/week7_results_snapshot.md`、`docs/week7_evidence_map.md`、`reports/week7_public_release_check.md`。
- [x] 图表包含标题、坐标、单位、实验条件或必要说明。Week 7 使用的源图与 12 页最终 PPT 已完成逐页/全尺寸视觉检查，结构检查无溢出。证据：`docs/week7_demo_media_inventory.md`、`docs/presentation/week7_ppt_outline.md`、`reports/week7_apple_showcase.md`。
- [x] 公开材料不包含密钥、个人隐私、受限数据或未经许可的大文件。密钥、受限数据、非预期大文件和严格 tracked-file 个人路径扫描均通过；项目级许可证检查不构成法律意见。证据：`reports/week7_public_release_check.md`。
- [x] VLM 只按真实完成状态描述，不用“农业 Agent”名称掩盖未完成能力。证据：`docs/week7_evidence_map.md`、`reports/week7_public_release_check.md`。

#### 科研与简历证据

- [x] README 首屏、架构图和 Demo 媒体。证据：`README.md`、`docs/week7_showcase_architecture.md`、`docs/media/week7_apple_architecture.png`、`docs/media/week7_apple_demo.gif`、`docs/media/week7_apple_demo.mp4`。
- [x] 已核验结果表与图表来源清单。证据：`docs/week7_results_snapshot.md`、`docs/week7_demo_media_inventory.md`、`reports/week7_public_release_check.md`。
- [x] 技术博客、PPT 和讲稿。证据：`docs/blog/week7_technical_blog_zh.md`、`docs/presentation/week7_apple_showcase_deck.pptx`、`docs/presentation/week7_ppt_outline.md`、`reports/week7_apple_showcase.md`。
- [x] 成果索引与公开发布审计记录。证据：`docs/artifact-index.md`、`reports/week7_public_release_check.md`。
- [x] 面向导师或面试的项目亮点—证据映射表。证据：`docs/week7_evidence_map.md`、`docs/week7_results_snapshot.md`。

#### 退出条件

- [x] 项目核心成果可在 30 秒、3 分钟和 10 分钟三个层级被清楚讲解。证据：`README.md`、`docs/blog/week7_technical_blog_zh.md`、`docs/presentation/week7_ppt_outline.md`。
- [x] 所有公开材料与仓库证据一致，没有无法核验的宣传性数字。证据：`docs/week7_evidence_map.md`、`reports/week7_public_release_check.md`。
- [x] Week 8 可以只做复现、审计、修正和发布，不再新增大功能。剩余工作包括干净环境复现、发布候选冻结和最终声明审计；不需要新增 Week 7 展示大功能。证据：`reports/week7_apple_showcase.md`、`reports/week7_public_release_check.md`。

---

### Week 8：全流程复现、最终报告与简历成果

#### 周目标

从干净环境复现核心流程，审计所有研究与展示材料，定稿最终报告和可直接使用但不夸大的简历条目。

> 当前状态（2026-07-17）：Week 8 本地 release candidate `week8-rc1` 已完成。历史仓库外锁定环境通过 226 tests、Ruff、`ty`、claim/link audit、synthetic smoke、package build 与 CLI help；冻结 checkpoint 指标重算、Top-5、MPS Demo、24 样本 Grad-CAM atlas 和 Apple `container` linux/arm64 health probe 均有记录。当前交付 manifest 只记录刷新源码的环境、锁文件、checkpoint、claims 与 Git 跟踪交付物哈希，并把未在该提交复跑的 clean/package/local/container 通道明确标为 `not_run`。最终实验报告、模型卡、数据卡、中英文 12 页论文、20 页 PPTX/Keynote 答辩材料、简历证据和导师摘要均已审计。official split 的 227 个重叠 `leaf_id`、single-seed、田间验证、完整人工 VQA 审计与 LoRA/QLoRA 等未完成项保持显式；未创建 tag、未发布远程 release。GitHub 分支/PR 仅发布源码与小型交付物，不代表模型部署。证据：`reports/week8_reproducibility.md`、`reports/release/week8_rc1_manifest.json`、`docs/release/week8_release_checklist.md`、`docs/artifact-index.md`。

#### 研发任务

- [x] 冻结候选发布版本，记录代码版本、依赖版本、数据版本和模型 checkpoint 校验信息。证据：`reports/release/week8_rc1_manifest.json`。
- [x] 在干净环境执行安装、数据冒烟、测试、基线训练或最小训练、评估、推理、Grad-CAM、Demo 和 Apple container 流程。干净 lane 使用合成最小闭环；冻结本地 evidence lane 覆盖正式评估、推理、Grad-CAM 与 Demo；Apple container lane 覆盖 image build/health。证据：`reports/week8_reproducibility.md`。
- [x] 对正式核心实验执行可承受范围内的重复运行或结果重算，确认指标文件与图表一致。证据：`reports/week8_reproducibility.md`、`reports/final_experiment_report.md`。
- [x] 运行完整测试、静态检查、格式化、类型检查和文档链接检查。证据：`reports/week8_reproducibility.md`、`reports/release/week8_claim_evidence.json`。
- [x] 审计数据泄漏、测试集使用、随机种子、失败实验和模型选择过程。证据：`reports/final_experiment_report.md`、`reports/data_split_limitations.md`、`reports/week3_final_model_decision.md`。
- [x] 审计 README、博客、PPT、报告和 Demo 的所有数字、图表与能力声明。证据：`reports/release/week8_claim_evidence.json`、`reports/week8_presentation_qa.md`、`reports/release/week8_paper_audit.json`。
- [x] 定稿科研级实验报告：摘要、引言、相关方法、数据、方法、实验设置、结果、消融、解释、错误分析、部署、VLM、局限、伦理安全和未来工作。证据：`reports/final_experiment_report.md`、`paper/out/plantdisease_ai_zh.pdf`、`paper/out/plantdisease_ai_en.pdf`。
- [x] 创建模型卡和数据卡，记录预期用途、非预期用途、偏差、限制和安全注意事项。证据：`reports/model_card.md`、`reports/data_card.md`。
- [x] 整理可公开的小型示例与获取大文件的说明，确保仓库克隆后不会因缺失私有路径而失败。证据：`app/examples/synthetic_leaf.png`、`reports/model_card.md`、`README.md`。
- [x] 基于真实结果编写 2–3 条简历 bullet，并为每条建立证据链接。证据：`docs/resume/week8_resume_evidence.md`。
- [x] 准备导师沟通摘要：研究问题、个人贡献、最有价值发现、失败经验、下一步研究方向。证据：`docs/mentor/week8_mentor_summary.md`。
- [x] 创建 release checklist 和建议的版本标签；实际发布、推送或创建远程仓库前取得用户授权。建议标签 `v0.8.0-rc1` 未创建。证据：`docs/release/week8_release_checklist.md`。
- [x] 记录未完成项和后续研究路线，例如真实田间数据、域泛化、病斑检测或分割、多模态知识检索。证据：`docs/release/week8_release_checklist.md`、`docs/mentor/week8_mentor_summary.md`。

#### 必须交付物

- [x] 干净环境复现记录和完整验证报告。证据：`reports/week8_reproducibility.md`。
- [x] 最终实验报告、模型卡、数据卡和成果索引。证据：`reports/final_experiment_report.md`、`reports/model_card.md`、`reports/data_card.md`、`docs/artifact-index.md`。
- [x] 经证据审计的 README、博客、PPT、Demo 和 Apple container。React A+ 改版补充作物优先聚合测试、浏览器几何与交互证据。证据：`reports/release/week8_claim_evidence.json`、`reports/week8_presentation_qa.md`、`reports/week8_reproducibility.md`、`reports/week8_react_demo_qa.md`。
- [x] 简历条目、导师沟通摘要和后续研究路线。证据：`docs/resume/week8_resume_evidence.md`、`docs/mentor/week8_mentor_summary.md`。
- [x] 发布检查清单和明确的未完成项列表。证据：`docs/release/week8_release_checklist.md`。

#### 验收标准

- [x] 核心流程在文档声明的环境中可重复运行，所有失败均有明确记录。证据：`reports/week8_reproducibility.md`。
- [x] 正式指标与原始日志、机器可读结果、图表、表格和文字描述一致。证据：`reports/final_experiment_report.md`、`reports/release/week8_claim_evidence.json`。
- [x] 测试集没有被用于超参数选择，数据泄漏审计没有未解释的高风险问题。official split overlap 已解释且未包装成实体隔离结果。证据：`reports/week3_final_model_decision.md`、`reports/data_split_limitations.md`。
- [x] 所有公开材料明确区分 PlantVillage 受控环境与真实田间场景。证据：`reports/release/week8_claim_evidence.json`。
- [x] 简历中的每个技术动作、结果数字和能力声明都有直接证据链接。证据：`docs/resume/week8_resume_evidence.md`。
- [x] 实际未完成的训练、部署、投稿或获奖没有被描述为已完成。证据：`docs/release/week8_release_checklist.md`。

#### 科研与简历证据

- [x] 可复现性验证日志和发布版本信息。证据：`reports/week8_reproducibility.md`、`reports/release/week8_rc1_manifest.json`。
- [x] 最终实验报告、模型卡与数据卡。证据：`reports/final_experiment_report.md`、`reports/model_card.md`、`reports/data_card.md`。
- [x] 最终结果—实验 ID—产物路径映射表。证据：`docs/artifact-index.md`、`reports/final_experiment_report.md`。
- [x] 简历 bullet—证据链接映射表。证据：`docs/resume/week8_resume_evidence.md`。
- [x] 导师沟通摘要、项目讲稿和未来研究问题清单。证据：`docs/mentor/week8_mentor_summary.md`、`docs/presentation/plantdisease_ai_week8_research_defense.pptx`。

#### 退出条件

- [x] 全局完成标准逐项核验完毕，未完成项有清晰状态和原因。唯一未勾选的全局“无已知泄漏”标准因 official split 的 227 个重叠 `leaf_id` 明确不成立；替代研究路线已记录。
- [x] 项目可以被第三方安装、复现、理解、演示和审阅。证据：`README.md`、`reports/week8_reproducibility.md`、`docs/artifact-index.md`、`docs/release/week8_release_checklist.md`。
- [x] 项目成果可以诚实地用于简历、导师联系和科研申请材料。证据：`docs/resume/week8_resume_evidence.md`、`docs/mentor/week8_mentor_summary.md`、最终双语论文与答辩材料。

---

## 最终交付物清单

- [x] GitHub 级代码仓库：代码、配置、测试、许可证和规范文档。
- [x] 数据审计与 EDA：数据卡、划分、统计和泄漏检查。
- [x] 图像分类实验：基线、五模型 Benchmark、最终模型与 checkpoint 获取方式。
- [x] 科研分析：消融实验、Grad-CAM、错误分析、校准与局限性。
- [x] 工程演示：Streamlit、Apple container、固定示例、截图或 GIF。
- [x] VLM 扩展：选型、VQA 数据、基线和明确标记的资源受限 smoke 原型；LoRA/QLoRA 未完成且未被声明为完成。
- [x] 研究表达：最终实验报告、技术博客、20 页项目 PPTX/Keynote 和讲稿备注。
- [x] 申请材料：成果索引、简历条目、导师沟通摘要与证据映射。

## 简历证据模板

只有当方括号字段已由 Week 8 证据审计确认后，才能替换并用于简历。

- 构建基于 PlantVillage 的植物病害识别系统，统一复现并比较 `[已完成模型数量]` 个 CNN 架构；最终模型在固定测试集取得 `[Accuracy]` Accuracy、`[Macro-F1]` Macro-F1，证据见 `[实验 ID/结果路径]`。
- 设计 `[已完成改进方法]` 的受控消融实验，在 `[随机种子数量]` 个随机种子下验证 `[真实结论]`，并通过 Grad-CAM 与错误分析定位 `[有证据的失败模式]`。
- 将模型封装为 Streamlit 与 Apple container 演示，在 `[测试硬件]`、`[batch size]`、`[数值精度]` 条件下实现 `[实测延迟或吞吐]`，证据见 `[性能报告路径]`。
- 构建 `[VQA 样本数量]` 条经审计的 PlantVillageVQA 数据，并完成 `[zero-shot/few-shot/LoRA/管线验证中的真实状态]`；不得把小样本冒烟测试写成完整微调成果。

## 建议最终目录

```text
PlantDiseaseAI/
├── AGENTS.md
├── TASKS.md
├── README.md
├── configs/
├── src/plantdisease/
│   ├── data/
│   ├── models/
│   ├── training/
│   ├── evaluation/
│   ├── explainability/
│   └── vlm/
├── scripts/
├── tests/
├── notebooks/
├── app/
├── reports/
├── docs/
└── outputs/
    ├── logs/
    ├── metrics/
    ├── figures/
    └── checkpoints/
```
