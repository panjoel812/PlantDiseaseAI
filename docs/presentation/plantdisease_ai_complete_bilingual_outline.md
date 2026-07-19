# PlantDiseaseAI 完整双语 PPT 大纲与逐页证据索引

# PlantDiseaseAI Complete Bilingual Deck Outline and Slide-by-Slide Evidence Index

> 用途 / Purpose：科研答辩、课程展示、项目面试或作品集演示。  
> 推荐规模 / Recommended scope：33 页主稿 + 12 页备答附录，约 25–30 分钟。  
> 精简方式 / Short version：隐藏标有“可隐藏 / Optional”的页面，可压缩为约 20–23 页。  
> 事实边界 / Evidence boundary：所有性能数字均来自仓库内机器可读证据；不得将官方 split 结果表述为实体隔离、真实田间或专业诊断性能。
> 新生成图表 / New chart set：[24 张英文透明 PNG + 可编辑 SVG / 24 English transparent PNGs + editable SVGs](charts/english-transparent/README.md)。

## 1. 演示目标 / Communication Goal

**中文：** 让老师、导师或面试官相信：作者不仅训练了一个高准确率分类模型，还独立完成了一套可复现、可解释、可部署、能够诚实说明局限的农业 AI 研究系统。

**English:** By the end of the presentation, the audience should understand that the author did more than train a high-accuracy classifier: the project delivers a reproducible, explainable, deployable agricultural AI research system with explicit evidence boundaries.

## 2. 推荐叙事 / Recommended Narrative

```text
研究问题 → 数据审计 → 公平 Benchmark → 受控消融 → 错误与解释
→ 服务与容器 → VLM 安全探索 → 复现审计 → 局限与后续研究

Research question → Data audit → Fair benchmark → Controlled ablation
→ Error analysis and explanation → Serving and containerization
→ Safety-bounded VLM exploration → Reproducibility audit → Limitations and next steps
```

## 3. 制作规则 / Production Rules

- 中文答辩可将中文作为主文案、英文作为小号副标题；英文答辩则反转层级。
- For a Chinese presentation, use Chinese as primary copy and English as a smaller subtitle; reverse the hierarchy for an English presentation.
- 每页只承担一个核心结论；详细表格、公式和命令放附录。
- Give each slide one primary claim; move dense tables, formulas, and commands to the appendix.
- 标题建议不小于 35 pt，正文不小于 16 pt；标题页主标题不小于 50 pt。
- Use at least 35 pt for slide titles, 16 pt for body copy, and 50 pt for the cover title.
- 图像优先于长段文字；不得为了塞内容而缩小字体。
- Prefer meaningful visuals over paragraphs; do not shrink type to fit excessive content.
- 所有 Accuracy、F1、FPS、延迟和 VLM 数字必须与限制条件同页出现。
- Keep protocol and limitation qualifiers on the same slide as every Accuracy, F1, FPS, latency, or VLM result.

---

# 主稿 / Main Deck

## Slide 1｜封面 / Cover

**中文标题**  
PlantDiseaseAI：可复现、可解释、可部署的植物病害识别系统

**English title**  
PlantDiseaseAI: A Reproducible, Explainable, and Deployable Plant-Disease Recognition System

**中文副标题**  
从数据审计、模型 Benchmark、受控消融到 Grad-CAM、部署与 VLM 安全探索

**English subtitle**  
From Data Auditing and Fair Benchmarking to Controlled Ablation, Grad-CAM, Deployment, and Safety-Bounded VLM Exploration

**页面任务 / Slide purpose**

- 中文：建立项目定位，传达这是一套完整研究系统，而不是单一模型 Demo。
- English: Position the project as an end-to-end research system rather than a single-model demo.

**上屏内容 / On-slide copy**

- 姓名 / Name
- 学校、专业或申请方向 / Institution, major, or target role
- 日期 / Date
- GitHub 或项目二维码 / GitHub or project QR code

**推荐版式 / Recommended layout**

- 全屏叶片图像，右侧或中央放标题；叠加一块半透明 Grad-CAM 热区。
- Use a full-bleed leaf image with the title centered or right-aligned and a subtle Grad-CAM overlay.

**可直接使用的图像 / Ready-to-use visuals**

- [现有答辩稿封面预览 / Existing defense cover preview](plantdisease_ai_week8_research_defense/slide-1.png)
- [田间玉米叶片样例 / Field corn leaf example](../../app/examples/field_corn_leaf.jpeg)
- [Grad-CAM 示例 / Grad-CAM example](../../outputs/plantvillage/week4_explainability/gradcam_atlas/correct_high_confidence/02_test-1175_target-9_Corn__maize____Northern_Leaf_Blight.png)

<!-- GENERATED-CHART-REFS:START -->
**生成图表参考 / Generated chart reference**

- `01-project-evidence-snapshot`: [PNG](charts/english-transparent/01-project-evidence-snapshot.png) · [SVG](charts/english-transparent/01-project-evidence-snapshot.svg)

**图表限定 / Chart context**

- Seed 42 · official split · 227 overlapping `leaf_id` values.
<!-- GENERATED-CHART-REFS:END -->

**证据 / Evidence**

- [项目 README / Project README](../../README.md)
- [最终实验报告 / Final experiment report](../../reports/final_experiment_report.md)

---

## Slide 2｜我完成的不只是一个分类模型 / I Built More Than a Classifier

**页面主张 / Primary claim**

- 中文：项目同时完成了科研实验、可信分析、工程部署与复现审计。
- English: The project combines scientific experimentation, trustworthy analysis, engineering deployment, and reproducibility auditing.

**中文上屏文案**

- 5 个模型统一 Benchmark
- 10 组受控消融实验
- 0.9953 Accuracy / 0.9941 Macro F1
- 50 / 10,709 个测试错误被逐样本审计
- 干净环境 226 tests passed

**English slide copy**

- 5 models under one benchmark protocol
- 10 controlled ablation runs
- 0.9953 Accuracy / 0.9941 Macro F1
- 50 errors audited across 10,709 test images
- 226 tests passed in a clean environment

**同页限制 / Same-slide qualifier**

> 中文：性能来自 seed 42 官方 split；该 split 存在 227 个重叠 `leaf_id`，不代表实体隔离或真实田间性能。  
> English: Performance is a seed-42 observation on the official split, which contains 227 overlapping `leaf_id` values; it is not entity-isolated or field-performance evidence.

**推荐版式 / Recommended layout**

- 用 5 个大数字形成视觉节奏，限制声明放底部，不做卡片式仪表盘。
- Use five large figures as the visual rhythm, with the limitation statement anchored at the bottom; avoid a dense dashboard-card layout.

**图像与数据 / Visuals and data**

- [现有研究问题页 / Existing framing slide](plantdisease_ai_week8_research_defense/slide-2.png)
- [最终指标 JSON / Final metrics JSON](../../outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/metrics.json)
- [Week 8 复现报告 / Week 8 reproducibility report](../../reports/week8_reproducibility.md)

<!-- GENERATED-CHART-REFS:START -->
**生成图表参考 / Generated chart reference**

- `01-project-evidence-snapshot`: [PNG](charts/english-transparent/01-project-evidence-snapshot.png) · [SVG](charts/english-transparent/01-project-evidence-snapshot.svg)
- `20-clean-reproducibility`: [PNG](charts/english-transparent/20-clean-reproducibility.png) · [SVG](charts/english-transparent/20-clean-reproducibility.svg)

**图表限定 / Chart context**

- Seed 42 · official split · 227 overlapping `leaf_id` values.
- Frozen RC snapshot; the current worktree audit may contain later claims.
<!-- GENERATED-CHART-REFS:END -->

---

## Slide 3｜高准确率是否等于可信诊断？ / Does High Accuracy Mean Trustworthy Diagnosis?

**中文上屏文案**

- 数据是否真正隔离？
- 模型比较是否公平？
- 改进是否有消融证据？
- 模型为何出错，置信度是否可信？
- 系统能否复现、解释与部署？
- 面对未知输入和高风险问题，是否会拒答？

**English slide copy**

- Is the data truly entity-isolated?
- Are model comparisons fair?
- Are improvements supported by controlled ablations?
- Why does the model fail, and is its confidence reliable?
- Can the system be reproduced, explained, and deployed?
- Will it refuse unknown inputs and high-risk requests?

**收束句 / Takeaway**

> 中文：研究重点不是得到一个漂亮数字，而是建立一条可以被重新检查的证据链。  
> English: The goal is not merely to obtain an impressive score, but to build an evidence chain that can be independently rechecked.

**图像参考 / Visual reference**

- [现有“高准确率”问题页 / Existing high-accuracy question slide](plantdisease_ai_week8_research_defense/slide-2.png)

<!-- GENERATED-CHART-REFS:START -->
**生成图表参考 / Generated chart reference**

- `03-split-and-overlap`: [PNG](charts/english-transparent/03-split-and-overlap.png) · [SVG](charts/english-transparent/03-split-and-overlap.svg)
- `12-error-audit`: [PNG](charts/english-transparent/12-error-audit.png) · [SVG](charts/english-transparent/12-error-audit.svg)
- `15-calibration`: [PNG](charts/english-transparent/15-calibration.png) · [SVG](charts/english-transparent/15-calibration.svg)

**图表限定 / Chart context**

- Seed 42 · official split · 227 overlapping `leaf_id` values.
<!-- GENERATED-CHART-REFS:END -->

**证据 / Evidence**

- [Week 4 阶段报告 / Week 4 stage report](../../reports/week4_stage_report.md)
- [模型卡 / Model card](../../reports/model_card.md)

---

## Slide 4｜项目的四个核心贡献 / Four Core Contributions

**中文上屏文案**

1. **科研实验：** 五模型统一 Benchmark，单变量消融与负结果记录。
2. **可信分析：** 错误分析、校准、Grad-CAM、固定样本与复现验证。
3. **工程闭环：** 目标叶片、植物身份、OpenCV 形态、作物内分类与 Apple container。
4. **责任与审计：** 数据泄漏披露、上游拒识、VLM/建议门控、claim ledger 与发布审计。

**English slide copy**

1. **Scientific experimentation:** A unified five-model benchmark with controlled ablations and retained negative results.
2. **Trustworthy analysis:** Error analysis, calibration, Grad-CAM, fixed samples, and reproducibility checks.
3. **Engineering closure:** Target-leaf selection, plant identity, OpenCV morphology, crop-specific conditions, and Apple container packaging.
4. **Responsibility and auditability:** Leakage disclosure, upstream abstention, VLM/guidance gates, a claim ledger, and release auditing.

**推荐版式 / Recommended layout**

- 四个贡献沿一条从“研究”到“交付”的路径排列，不要做四个独立产品卡片。
- Arrange the four contributions along a single research-to-delivery path rather than four unrelated product cards.

**图像参考 / Visual reference**

- [分层服务架构 PNG / Hierarchical serving architecture PNG](../media/week8_hierarchical_serving_architecture.png)
- [现有证据闭环页 / Existing evidence-loop slide](plantdisease_ai_week8_research_defense/slide-5.png)

<!-- GENERATED-CHART-REFS:START -->
**生成图表参考 / Generated chart reference**

- `21-eight-week-evidence-timeline`: [PNG](charts/english-transparent/21-eight-week-evidence-timeline.png) · [SVG](charts/english-transparent/21-eight-week-evidence-timeline.svg)
- `01-project-evidence-snapshot`: [PNG](charts/english-transparent/01-project-evidence-snapshot.png) · [SVG](charts/english-transparent/01-project-evidence-snapshot.svg)

**图表限定 / Chart context**

- Seed 42 · official split · 227 overlapping `leaf_id` values.
<!-- GENERATED-CHART-REFS:END -->

**证据 / Evidence**

- [成果索引 / Artifact index](../artifact-index.md)
- [Week 7 证据映射 / Week 7 evidence map](../week7_evidence_map.md)

---

## Slide 5｜八周形成一条完整研发链路 / An Eight-Week End-to-End Development Path

**状态 / Status:** 可隐藏 / Optional

**中文上屏文案**

- Week 1：数据审计与 MobileNetV2 最小基线
- Week 2：五模型公平 Benchmark
- Week 3：增强、Loss、Scheduler、EMA 消融
- Week 4：Grad-CAM、错误分析与校准
- Week 5：Streamlit 与 Apple container
- Week 6：Qwen3-VL 与安全助手探索
- Week 7：架构、博客、Demo、PPT
- Week 8：复现、论文、证据与发布审计

**English slide copy**

- Week 1: Data auditing and a minimal MobileNetV2 baseline
- Week 2: A fair five-model benchmark
- Week 3: Ablations for augmentation, loss, scheduling, and EMA
- Week 4: Grad-CAM, error analysis, and calibration
- Week 5: Streamlit and Apple container engineering
- Week 6: Qwen3-VL and a safety-bounded assistant prototype
- Week 7: Architecture, blog, demo media, and presentation assets
- Week 8: Reproducibility, papers, evidence, and release auditing

**推荐图像 / Recommended visual**

- 制作一条横向时间线；每周只放一个动词和一个产物。
- Create a horizontal timeline with one action and one deliverable per week.

<!-- GENERATED-CHART-REFS:START -->
**生成图表参考 / Generated chart reference**

- `21-eight-week-evidence-timeline`: [PNG](charts/english-transparent/21-eight-week-evidence-timeline.png) · [SVG](charts/english-transparent/21-eight-week-evidence-timeline.svg)

**图表限定 / Chart context**


<!-- GENERATED-CHART-REFS:END -->

**数据与证据 / Data and evidence**

- [八周任务清单 / Eight-week task ledger](../../TASKS.md)
- [最终成果索引 / Final artifact index](../artifact-index.md)

---

## Slide 6｜主线任务是 38 类闭集图像分类 / The Core Task Is 38-Class Closed-Set Image Classification

**中文上屏文案**

- 数据：PlantVillage 叶片图像
- 输入：单张 RGB 叶片图像，模型输入 224×224
- 输出：38 个作物—病害类别的 Top-5 概率
- 主指标：Macro F1，同时报告 Accuracy
- 不在验证范围：检测、分割、未知病害识别和专业诊断

**English slide copy**

- Data: PlantVillage leaf images
- Input: One RGB leaf image resized to 224×224
- Output: Top-5 probabilities over 38 crop-condition classes
- Primary metric: Macro F1, reported alongside Accuracy
- Outside the validated scope: Detection, segmentation, unknown-disease recognition, and professional diagnosis

**推荐版式 / Recommended layout**

```text
Leaf image → Canonical preprocessing → Classifier → Top-5 + confidence
```

**图像 / Visuals**

- [PlantVillage 样本网格 / PlantVillage sample grid](../../outputs/plantvillage/eda/sample_grid.png)
- [现有 38 类范围页 / Existing 38-class scope slide](plantdisease_ai_week8_research_defense/slide-3.png)

<!-- GENERATED-CHART-REFS:START -->
**生成图表参考 / Generated chart reference**

- `02-dataset-composition`: [PNG](charts/english-transparent/02-dataset-composition.png) · [SVG](charts/english-transparent/02-dataset-composition.svg)
- `04-class-distribution`: [PNG](charts/english-transparent/04-class-distribution.png) · [SVG](charts/english-transparent/04-class-distribution.svg)

**图表限定 / Chart context**


<!-- GENERATED-CHART-REFS:END -->

**证据 / Evidence**

- [数据卡 / Data card](../../reports/data_card.md)
- [最终模型配置 / Final model configuration](../../configs/week3_ablation/09_combo_candidate.yaml)

---

## Slide 7｜数据审计先于模型训练 / Data Auditing Comes Before Model Training

**中文上屏文案**

- 官方 train：43,596 张
- 官方 test：10,709 张
- 38 类，256×256 RGB
- train 内像素级精确重复组：14
- 非法标签：0
- 上游 loader revision 被固定，原始数据与缓存不提交 Git

**English slide copy**

- Official train split: 43,596 images
- Official test split: 10,709 images
- 38 classes, 256×256 RGB
- Exact duplicate groups in the audited train split: 14
- Invalid labels: 0
- The upstream loader revision is pinned; raw data and caches remain outside Git

**工程难点 / Engineering detail**

- 中文：将 `datasets` 固定为 `>=3.6,<4`，显式下载固定 revision 的 `plant_village.py`，解决上游脚本加载兼容问题。
- English: Pin `datasets>=3.6,<4` and explicitly load the fixed-revision `plant_village.py` script to avoid upstream loader incompatibility.

**可直接使用的图像 / Ready-to-use visuals**

- [类别分布 / Class distribution](../../outputs/plantvillage/eda/class_distribution.png)
- [尺寸分布 / Image-size distribution](../../outputs/plantvillage/eda/image_size_distribution.png)
- [样本网格 / Sample grid](../../outputs/plantvillage/eda/sample_grid.png)

<!-- GENERATED-CHART-REFS:START -->
**生成图表参考 / Generated chart reference**

- `04-class-distribution`: [PNG](charts/english-transparent/04-class-distribution.png) · [SVG](charts/english-transparent/04-class-distribution.svg)
- `02-dataset-composition`: [PNG](charts/english-transparent/02-dataset-composition.png) · [SVG](charts/english-transparent/02-dataset-composition.svg)

**图表限定 / Chart context**


<!-- GENERATED-CHART-REFS:END -->

**数据与证据 / Data and evidence**

- [数据审计 JSON / Data-audit JSON](../../outputs/plantvillage/audit.json)
- [数据审计报告 / Data-audit report](../../reports/data_audit.md)

---

## Slide 8｜数据划分可复现，但并非严格实体隔离 / The Split Is Reproducible but Not Entity-Isolated

**中文上屏文案**

- train：37,058
- validation：6,538
- official test：10,709
- seed 42，stratified split
- 重叠 `image_path`：0
- 重叠 `leaf_id`：227

**English slide copy**

- Train: 37,058
- Validation: 6,538
- Official test: 10,709
- Seed 42, stratified split
- Overlapping `image_path` values: 0
- Overlapping `leaf_id` values: 227

**结论 / Takeaway**

> 中文：结果只能描述为官方 split 表现，不能描述为严格无泄漏、实体隔离或真实田间泛化。  
> English: Results must be described as official-split performance, not as leakage-free, entity-isolated, or field-generalization evidence.

**图像参考 / Visual reference**

- [现有 227 风险页 / Existing “227” risk slide](plantdisease_ai_week8_research_defense/slide-4.png)
- 建议自制：两组叶片实体图标跨越 train/test 边界，并将 227 置于中央。
- Suggested custom visual: Two groups of leaf entities crossing the train/test boundary, with “227” centered.

<!-- GENERATED-CHART-REFS:START -->
**生成图表参考 / Generated chart reference**

- `03-split-and-overlap`: [PNG](charts/english-transparent/03-split-and-overlap.png) · [SVG](charts/english-transparent/03-split-and-overlap.svg)

**图表限定 / Chart context**

- Seed 42 · official split · 227 overlapping `leaf_id` values.
<!-- GENERATED-CHART-REFS:END -->

**数据与证据 / Data and evidence**

- [最终 split manifest / Final split manifest](../../outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/split.json)
- [数据审计报告 / Data-audit report](../../reports/data_audit.md)

---

## Slide 9｜训练、评估与 Demo 共享同一份语义 / Training, Evaluation, and Demo Share One Semantic Source

**中文上屏文案**

- split manifest 保存顺序固定的 38 类标签映射
- 训练、评估、推理和 Demo 从 checkpoint metadata 读取语义
- 训练增强仅作用于训练集
- validation、test、inference 和 Demo 使用确定性预处理
- 核心逻辑集中在 `src/plantdisease/`，CLI 只做稳定入口
- 冻结分类语义与新增服务门控分开：门控可拒答，但不能改写 Benchmark

**English slide copy**

- The split manifest stores one ordered 38-class label mapping
- Training, evaluation, inference, and the demo read semantics from checkpoint metadata
- Random augmentation is applied only to training data
- Validation, test, inference, and demo paths use deterministic preprocessing
- Core logic lives in `src/plantdisease/`; CLIs are stable entry points
- Frozen classifier semantics stay separate from serving gates: gates may abstain, but cannot rewrite the benchmark

**推荐图像 / Recommended visual**

- [分层服务架构图 / Hierarchical serving architecture](../media/week8_hierarchical_serving_architecture.png)
- [现有证据闭环页 / Existing evidence-loop slide](plantdisease_ai_week8_research_defense/slide-5.png)

<!-- GENERATED-CHART-REFS:START -->
**生成图表参考 / Generated chart reference**

- `02-dataset-composition`: [PNG](charts/english-transparent/02-dataset-composition.png) · [SVG](charts/english-transparent/02-dataset-composition.svg)
- `18-vqa-seed-composition`: [PNG](charts/english-transparent/18-vqa-seed-composition.png) · [SVG](charts/english-transparent/18-vqa-seed-composition.svg)

**图表限定 / Chart context**

- 5 images / 15 questions smoke study; no completed LoRA/QLoRA.
<!-- GENERATED-CHART-REFS:END -->

**证据 / Evidence**

- [项目架构说明 / Project architecture](../project-architecture.md)
- [Canonical transforms](../../src/plantdisease/data/transforms.py)
- [模型 checkpoint 接口 / Checkpoint interface](../../src/plantdisease/models/checkpoint.py)

---

## Slide 10｜可复现性被设计进每一次实验 / Reproducibility Is Designed into Every Run

**状态 / Status:** 可隐藏 / Optional

**中文上屏文案**

每次正式运行保存：

- 完整解析配置与 run ID
- seed、split 与标签映射
- Python、依赖、OS、设备和硬件
- checkpoint、metrics、日志与图表
- 运行状态：成功、失败、中止或 smoke

**English slide copy**

Every formal run records:

- The fully resolved configuration and run ID
- Seed, split, and label mapping
- Python, dependencies, OS, device, and hardware
- Checkpoint, metrics, logs, and figures
- Run status: completed, failed, aborted, or smoke-only

**推荐图像 / Recommended visual**

```text
outputs/runs/<run_id>/
├── resolved_config
├── run_manifest
├── checkpoint
├── metrics
└── figures
```

<!-- GENERATED-CHART-REFS:START -->
**生成图表参考 / Generated chart reference**

- `20-clean-reproducibility`: [PNG](charts/english-transparent/20-clean-reproducibility.png) · [SVG](charts/english-transparent/20-clean-reproducibility.svg)
- `03-split-and-overlap`: [PNG](charts/english-transparent/03-split-and-overlap.png) · [SVG](charts/english-transparent/03-split-and-overlap.svg)

**图表限定 / Chart context**

- Frozen RC snapshot; the current worktree audit may contain later claims.
- Seed 42 · official split · 227 overlapping `leaf_id` values.
<!-- GENERATED-CHART-REFS:END -->

**数据与证据 / Data and evidence**

- [最终 run manifest / Final run manifest](../../outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/run_manifest.json)
- [Week 8 复现报告 / Week 8 reproducibility report](../../reports/week8_reproducibility.md)

---

## Slide 11｜MobileNetV2 先验证了最小训练闭环 / MobileNetV2 First Validated the Minimal Training Loop

**状态 / Status:** 可隐藏 / Optional

**中文上屏文案**

- Dataset/DataLoader shape、dtype 与标签范围检查
- 单 batch 过拟合，验证模型—Loss—反向传播—优化器连接
- 小规模训练 smoke 与 checkpoint 保存
- Accuracy、Macro Precision、Recall、F1 与混淆矩阵
- checkpoint 重载与单图 Top-5 推理

**English slide copy**

- Dataset/DataLoader checks for shape, dtype, and label range
- Single-batch overfitting to validate model, loss, backpropagation, and optimizer wiring
- Small-scale training smoke and checkpoint persistence
- Accuracy, Macro Precision, Recall, F1, and confusion-matrix metrics
- Checkpoint reload and single-image Top-5 inference

**讲解重点 / Speaker takeaway**

- 中文：基线首先用于排除管线错误，而不是追求最高结果。
- English: The baseline first eliminates pipeline failures; it is not primarily a score-maximization exercise.

**图像与数据 / Visuals and data**

- [MobileNetV2 训练曲线 / MobileNetV2 training curve](../../outputs/plantvillage/baseline_mobilenet_v2_best_seed42/training_curve.png)
- [MobileNetV2 指标 / MobileNetV2 metrics](../../outputs/plantvillage/baseline_mobilenet_v2_best_seed42/metrics.json)
- [Week 1 报告 / Week 1 report](../../reports/week1.md)

<!-- GENERATED-CHART-REFS:START -->
**生成图表参考 / Generated chart reference**

- `05-model-accuracy-f1`: [PNG](charts/english-transparent/05-model-accuracy-f1.png) · [SVG](charts/english-transparent/05-model-accuracy-f1.svg)
- `07-model-latency`: [PNG](charts/english-transparent/07-model-latency.png) · [SVG](charts/english-transparent/07-model-latency.svg)

**图表限定 / Chart context**

- Seed 42 · official split · 227 overlapping `leaf_id` values.
- Fixed-example engineering observation; not a latency benchmark.
<!-- GENERATED-CHART-REFS:END -->

---

## Slide 12｜五个模型在同一协议下比较 / Five Models Were Compared Under One Protocol

**中文上屏文案**

- MobileNetV2
- ResNet18
- ResNet50
- EfficientNet-B0
- EfficientNetV2-S

统一条件：相同 official split、输入尺寸、归一化、预训练来源、训练预算、主指标与 checkpoint 选择规则。

**English slide copy**

- MobileNetV2
- ResNet18
- ResNet50
- EfficientNet-B0
- EfficientNetV2-S

Shared conditions: the same official split, input size, normalization, pretrained-weight source, training budget, primary metric, and checkpoint-selection rule.

**同页限制 / Same-slide qualifier**

- 中文：受本机资源限制，不同模型 batch size 不完全相同；test 仅用于最终评估。
- English: Batch sizes differ because of local resource limits; the test split is used only for final evaluation.

**图像参考 / Visual reference**

- [现有五模型页 / Existing five-model slide](plantdisease_ai_week8_research_defense/slide-6.png)

<!-- GENERATED-CHART-REFS:START -->
**生成图表参考 / Generated chart reference**

- `05-model-accuracy-f1`: [PNG](charts/english-transparent/05-model-accuracy-f1.png) · [SVG](charts/english-transparent/05-model-accuracy-f1.svg)

**图表限定 / Chart context**

- Seed 42 · official split · 227 overlapping `leaf_id` values.
<!-- GENERATED-CHART-REFS:END -->

**证据 / Evidence**

- [Week 2 Benchmark 报告 / Week 2 benchmark report](../../reports/week2_benchmark_progress.md)
- [五个基线配置 / Five baseline configurations](../../configs/baseline_resnet50.yaml)

---

## Slide 13｜ResNet50 精度最高，MobileNetV2 效率最好 / ResNet50 Leads Accuracy; MobileNetV2 Leads Efficiency

**核心表格 / Core table**

| Model / 模型 | Test Accuracy | Macro F1 | Params / 参数量 | FLOPs | MPS Throughput / 吞吐 |
| --- | ---: | ---: | ---: | ---: | ---: |
| MobileNetV2 | 0.9760 | 0.9674 | 2.27M | 0.31G | 644.3 img/s |
| ResNet18 | 0.9774 | 0.9661 | 11.20M | 1.82G | 564.5 img/s |
| ResNet50 | **0.9830** | **0.9743** | 23.59M | 4.11G | 165.9 img/s |
| EfficientNet-B0 | 0.9804 | 0.9703 | 4.06M | 0.40G | 305.6 img/s |
| EfficientNetV2-S | 0.9794 | 0.9708 | 20.23M | 2.88G | 133.4 img/s |

**方法脚注 / Method footnote**

- 中文：MPS、float32、224×224；10 次预热、50 次测量；吞吐不包含预处理；峰值内存未测量。
- English: MPS, float32, 224×224; 10 warm-up iterations and 50 measured iterations; throughput excludes preprocessing; peak memory was not measured.

**图像参考 / Visual reference**

- [现有双目标决策页 / Existing accuracy-efficiency decision slide](plantdisease_ai_week8_research_defense/slide-7.png)
- [Accuracy–efficiency Pareto 图 / Accuracy–efficiency Pareto plot](../../outputs/plantvillage/benchmarks/week2_accuracy_efficiency_pareto.png)

<!-- GENERATED-CHART-REFS:START -->
**生成图表参考 / Generated chart reference**

- `05-model-accuracy-f1`: [PNG](charts/english-transparent/05-model-accuracy-f1.png) · [SVG](charts/english-transparent/05-model-accuracy-f1.svg)
- `06-model-efficiency-pareto`: [PNG](charts/english-transparent/06-model-efficiency-pareto.png) · [SVG](charts/english-transparent/06-model-efficiency-pareto.svg)
- `07-model-latency`: [PNG](charts/english-transparent/07-model-latency.png) · [SVG](charts/english-transparent/07-model-latency.svg)

**图表限定 / Chart context**

- Seed 42 · official split · 227 overlapping `leaf_id` values.
- Fixed-example engineering observation; not a latency benchmark.
<!-- GENERATED-CHART-REFS:END -->

**数据与证据 / Data and evidence**

- [Week 2 Benchmark 报告 / Week 2 benchmark report](../../reports/week2_benchmark_progress.md)
- [各模型效率 JSON 目录 / Per-model benchmark JSON directory](../../outputs/plantvillage/benchmarks/)

---

## Slide 14｜模型选择是多目标决策 / Model Selection Is a Multi-Objective Decision

**状态 / Status:** 可隐藏 / Optional

**中文上屏文案**

- 高精度研究基线：ResNet50
- 轻量部署候选：MobileNetV2
- batch-1 最低平均延迟：ResNet18，2.82 ms
- Week 3 消融冻结 ResNet50 为高精度基线

**English slide copy**

- High-accuracy research baseline: ResNet50
- Lightweight deployment candidate: MobileNetV2
- Lowest mean batch-1 latency: ResNet18 at 2.82 ms
- Week 3 freezes ResNet50 as the high-accuracy ablation baseline

**核心结论 / Takeaway**

> 中文：没有单一模型同时在精度、参数量、FLOPs 和设备吞吐上占优。  
> English: No single model dominates accuracy, parameter count, FLOPs, and device throughput simultaneously.

**推荐图像 / Recommended visual**

- [Accuracy–efficiency Pareto 图 / Accuracy–efficiency Pareto plot](../../outputs/plantvillage/benchmarks/week2_accuracy_efficiency_pareto.png)

<!-- GENERATED-CHART-REFS:START -->
**生成图表参考 / Generated chart reference**

- `06-model-efficiency-pareto`: [PNG](charts/english-transparent/06-model-efficiency-pareto.png) · [SVG](charts/english-transparent/06-model-efficiency-pareto.svg)
- `07-model-latency`: [PNG](charts/english-transparent/07-model-latency.png) · [SVG](charts/english-transparent/07-model-latency.svg)

**图表限定 / Chart context**

- Seed 42 · official split · 227 overlapping `leaf_id` values.
- Fixed-example engineering observation; not a latency benchmark.
<!-- GENERATED-CHART-REFS:END -->

**证据 / Evidence**

- [Week 3 最终模型决策 / Week 3 final-model decision](../../reports/week3_final_model_decision.md)

---

## Slide 15｜消融实验一次只改变一个因素 / Each Ablation Changes One Factor at a Time

**中文上屏文案**

- Label Smoothing
- Focal Loss
- Cosine Scheduler
- EMA
- RandAugment
- Random Erasing
- Mixup
- CutMix
- Label Smoothing + Cosine 组合候选

**English slide copy**

- Label Smoothing
- Focal Loss
- Cosine Scheduler
- EMA
- RandAugment
- Random Erasing
- Mixup
- CutMix
- A Label Smoothing + Cosine combination candidate

**实验原则 / Experimental rules**

- 中文：固定模型、split、seed、优化器与预算；单变量和组合实验分开解释；保留失败结果。
- English: Freeze the model, split, seed, optimizer, and budget; interpret single-variable and combination runs separately; retain negative results.

**图像参考 / Visual reference**

- [现有冻结基线页 / Existing frozen-baseline slide](plantdisease_ai_week8_research_defense/slide-8.png)
- [消融矩阵报告 / Ablation matrix report](../../reports/week3_ablation_matrix.md)

**数据 / Data**

- [完整消融结果 / Full ablation results](../../reports/week3_ablation_results.md)
- [消融配置目录 / Ablation configuration directory](../../configs/week3_ablation/)

<!-- GENERATED-CHART-REFS:START -->
**生成图表参考 / Generated chart reference**

- `08-ablation-macro-f1`: [PNG](charts/english-transparent/08-ablation-macro-f1.png) · [SVG](charts/english-transparent/08-ablation-macro-f1.svg)
- `10-ablation-duration`: [PNG](charts/english-transparent/10-ablation-duration.png) · [SVG](charts/english-transparent/10-ablation-duration.svg)

**图表限定 / Chart context**

- Seed 42 · official split · 227 overlapping `leaf_id` values.
<!-- GENERATED-CHART-REFS:END -->

---

## Slide 16｜Cosine Scheduler 是最强单变量 / Cosine Scheduling Is the Strongest Single Variable

**建议图表数据 / Recommended chart data**

| Method / 方法 | Test Macro F1 |
| --- | ---: |
| Baseline | 0.9743 |
| Label Smoothing | 0.9865 |
| Focal Loss | 0.9652 |
| Cosine Scheduler | **0.9898** |
| EMA | 0.9673 |
| RandAugment | 0.9698 |
| Random Erasing | 0.9683 |
| Mixup | 0.9793 |
| CutMix | 0.9863 |

**中文结论**

在当前官方 split、ResNet50 与 seed 42 条件下，Cosine Scheduler 将 Test Macro F1 从 0.9743 提升到 0.9898，是最强单变量结果。

**English takeaway**

Under the current official-split, ResNet50, seed-42 protocol, cosine scheduling raises Test Macro F1 from 0.9743 to 0.9898, the strongest single-variable result.

**同页限制 / Same-slide qualifier**

- 中文：这是单次 seed 观察，不是普遍因果结论。
- English: This is a single-seed observation, not a universal causal conclusion.

**图像 / Visuals**

- [现有 Cosine Scheduler 页 / Existing cosine-scheduler slide](plantdisease_ai_week8_research_defense/slide-9.png)
- [验证 Macro F1 曲线叠图 / Validation Macro-F1 curve overlay](../../reports/figures/week3_validation_macro_f1_curves.png)

**数据 / Data**

- [消融结果报告 / Ablation-results report](../../reports/week3_ablation_results.md)

<!-- GENERATED-CHART-REFS:START -->
**生成图表参考 / Generated chart reference**

- `09-ablation-delta`: [PNG](charts/english-transparent/09-ablation-delta.png) · [SVG](charts/english-transparent/09-ablation-delta.svg)
- `08-ablation-macro-f1`: [PNG](charts/english-transparent/08-ablation-macro-f1.png) · [SVG](charts/english-transparent/08-ablation-macro-f1.svg)

**图表限定 / Chart context**

- Seed 42 · official split · 227 overlapping `leaf_id` values.
<!-- GENERATED-CHART-REFS:END -->

---

## Slide 17｜负结果同样决定最终方案 / Negative Results Also Shape the Final Design

**状态 / Status:** 可隐藏 / Optional

**中文上屏文案**

- Focal Loss：Δ Macro F1 = −0.0092
- EMA：Δ Macro F1 = −0.0071
- RandAugment：Δ Macro F1 = −0.0046
- Random Erasing：Δ Macro F1 = −0.0061

**English slide copy**

- Focal Loss: Δ Macro F1 = −0.0092
- EMA: Δ Macro F1 = −0.0071
- RandAugment: Δ Macro F1 = −0.0046
- Random Erasing: Δ Macro F1 = −0.0061

**可讲假设 / Defensible hypotheses**

- 中文：困难样本加权可能放大异常样本；强增强可能破坏细粒度病斑；EMA decay 与短训练预算可能不匹配。
- English: Hard-example weighting may amplify atypical samples; aggressive augmentation may damage fine-grained lesion cues; EMA decay may not match the short training budget.

**必须补充 / Required qualifier**

> 中文：以上是由结果启发的合理假设，不是已验证的因果机制。  
> English: These are evidence-inspired hypotheses, not validated causal mechanisms.

**图像与数据 / Visuals and data**

- [消融曲线叠图 / Ablation curve overlay](../../reports/figures/week3_validation_macro_f1_curves.png)
- [完整消融结果 / Full ablation results](../../reports/week3_ablation_results.md)

<!-- GENERATED-CHART-REFS:START -->
**生成图表参考 / Generated chart reference**

- `09-ablation-delta`: [PNG](charts/english-transparent/09-ablation-delta.png) · [SVG](charts/english-transparent/09-ablation-delta.svg)
- `10-ablation-duration`: [PNG](charts/english-transparent/10-ablation-duration.png) · [SVG](charts/english-transparent/10-ablation-duration.svg)

**图表限定 / Chart context**

- Seed 42 · official split · 227 overlapping `leaf_id` values.
<!-- GENERATED-CHART-REFS:END -->

---

## Slide 18｜Label Smoothing 与 Cosine 形成最终候选 / Label Smoothing and Cosine Form the Final Candidate

**中文上屏文案**

- ResNet50 baseline：0.9830 Accuracy / 0.9743 Macro F1
- 最终组合：0.9953 Accuracy / 0.9941 Macro F1
- Accuracy：+1.23 个百分点
- Macro F1：+1.98 个百分点
- 最佳 validation epoch：5
- 运行时长：65.4 min

**English slide copy**

- ResNet50 baseline: 0.9830 Accuracy / 0.9743 Macro F1
- Final combination: 0.9953 Accuracy / 0.9941 Macro F1
- Accuracy: +1.23 percentage points
- Macro F1: +1.98 percentage points
- Best validation epoch: 5
- Run duration: 65.4 minutes

**配置 / Configuration**

- Label Smoothing = 0.1
- Cosine Scheduler, `eta_min=1e-5`
- AdamW, seed 42, official split

**同页限制 / Same-slide qualifier**

> 中文：单 seed + 227 个重叠 `leaf_id`，不代表统计稳定、实体隔离或田间泛化。  
> English: A single seed plus 227 overlapping `leaf_id` values does not establish statistical stability, entity isolation, or field generalization.

**图像与数据 / Visuals and data**

- [现有最终指标页 / Existing final-metrics slide](plantdisease_ai_week8_research_defense/slide-10.png)
- [最终模型训练曲线 / Final-model training curve](../../outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/training_curve.png)
- [最终指标 JSON / Final metrics JSON](../../outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/metrics.json)
- [最终配置 / Final configuration](../../configs/week3_ablation/09_combo_candidate.yaml)

<!-- GENERATED-CHART-REFS:START -->
**生成图表参考 / Generated chart reference**

- `11-final-improvement`: [PNG](charts/english-transparent/11-final-improvement.png) · [SVG](charts/english-transparent/11-final-improvement.svg)

**图表限定 / Chart context**

- Seed 42 · official split · 227 overlapping `leaf_id` values.
<!-- GENERATED-CHART-REFS:END -->

---

## Slide 19｜0.9953 Accuracy 仍留下 50 个可审计错误 / 0.9953 Accuracy Still Leaves 50 Auditable Errors

**中文上屏文案**

- 测试样本：10,709
- 正确：10,659
- 错误：50
- 高于 0.80 置信度的错误：2

**English slide copy**

- Test samples: 10,709
- Correct predictions: 10,659
- Errors: 50
- Errors above 0.80 confidence: 2

<!-- GENERATED-CHART-REFS:START -->
**生成图表参考 / Generated chart reference**

- `12-error-audit`: [PNG](charts/english-transparent/12-error-audit.png) · [SVG](charts/english-transparent/12-error-audit.svg)

**图表限定 / Chart context**

- Seed 42 · official split · 227 overlapping `leaf_id` values.
<!-- GENERATED-CHART-REFS:END -->

**逐样本证据 / Per-sample evidence**

- test index / 测试索引
- true label / 真实标签
- predicted label / 预测标签
- Top-5 and confidence / Top-5 与置信度
- source image path / 原始图片路径

**核心结论 / Takeaway**

> 中文：高准确率不是停止分析的理由；剩余错误反而更值得逐个追踪。  
> English: High accuracy is not a reason to stop analysis; the remaining errors deserve closer inspection.

**图像与数据 / Visuals and data**

- [现有 50/10,709 页 / Existing 50/10,709 slide](plantdisease_ai_week8_research_defense/slide-11.png)
- [错误分析 JSON / Error-analysis JSON](../../outputs/plantvillage/week4_explainability/error_analysis.json)
- [逐样本预测 JSON / Per-sample predictions JSON](../../outputs/plantvillage/week4_explainability/predictions.json)

**证据 / Evidence**

- [错误分析报告 / Error-analysis report](../../reports/week4_error_analysis.md)

---

## Slide 20｜错误集中在视觉相似病害 / Errors Concentrate in Visually Similar Conditions

**中文上屏文案**

代表性混淆包括：

- 玉米灰斑病 vs 北方叶枯病
- 马铃薯或番茄晚疫病相关混淆
- 番茄早疫病 vs 靶斑病

**English slide copy**

Representative confusions include:

- Corn gray leaf spot vs northern leaf blight
- Late-blight-related confusions across potato or tomato classes
- Tomato early blight vs target spot

**解释边界 / Interpretation boundary**

- 中文：混淆矩阵证明错误共现，但不单独证明病斑形状或纹理是因果原因。
- English: The confusion matrix establishes error co-occurrence, but does not by itself prove that lesion shape or texture is the causal mechanism.

**可直接使用的图像 / Ready-to-use visuals**

- [现有混淆结论页 / Existing confusion slide](plantdisease_ai_week8_research_defense/slide-12.png)
- [玉米错误样本 / Corn error example](../../outputs/plantvillage/week4_explainability/gradcam_atlas/error_high_confidence/16_test-1099_target-7_Corn__maize____Cercospora_leaf_spot_Gray_leaf_spot.png)
- [番茄错误样本 / Tomato error example](../../outputs/plantvillage/week4_explainability/gradcam_atlas/error_low_confidence/24_test-6690_target-29_Tomato___Early_blight.png)

<!-- GENERATED-CHART-REFS:START -->
**生成图表参考 / Generated chart reference**

- `13-top-confusions`: [PNG](charts/english-transparent/13-top-confusions.png) · [SVG](charts/english-transparent/13-top-confusions.svg)
- `24-full-confusion-matrix`: [PNG](charts/english-transparent/24-full-confusion-matrix.png) · [SVG](charts/english-transparent/24-full-confusion-matrix.svg)

**图表限定 / Chart context**

- Seed 42 · official split · 227 overlapping `leaf_id` values.
<!-- GENERATED-CHART-REFS:END -->

**数据与证据 / Data and evidence**

- [错误分析 JSON / Error-analysis JSON](../../outputs/plantvillage/week4_explainability/error_analysis.json)
- [错误分析报告 / Error-analysis report](../../reports/week4_error_analysis.md)

---

## Slide 21｜准确率不等于置信度质量 / Accuracy Is Not Confidence Quality

**中文上屏文案**

- Top-label ECE：0.0965
- MCE：0.3348
- Brier：0.0140

**English slide copy**

- Top-label ECE: 0.0965
- MCE: 0.3348
- Brier score: 0.0140

**解释 / Explanation**

- 中文：Accuracy 回答“分对多少”；calibration 回答“预测 90% 时是否真的约有 90% 正确”。
- English: Accuracy asks “how often is the model correct?” Calibration asks “when the model says 90%, is it correct roughly 90% of the time?”

**同页限制 / Same-slide qualifier**

- 中文：当前只分析 top-label calibration，不是完整多类别校准，也不证明置信度适合高风险决策。
- English: This is top-label calibration rather than a complete multiclass calibration study, and it does not establish confidence safety for high-stakes decisions.

**图像 / Visuals**

- [Reliability diagram](../../reports/figures/week4_reliability_diagram.png)
- [现有校准页 / Existing calibration slide](plantdisease_ai_week8_research_defense/slide-13.png)

<!-- GENERATED-CHART-REFS:START -->
**生成图表参考 / Generated chart reference**

- `15-calibration`: [PNG](charts/english-transparent/15-calibration.png) · [SVG](charts/english-transparent/15-calibration.svg)

**图表限定 / Chart context**

- Seed 42 · official split · 227 overlapping `leaf_id` values.
<!-- GENERATED-CHART-REFS:END -->

**数据与证据 / Data and evidence**

- [校准 JSON / Calibration JSON](../../outputs/plantvillage/week4_explainability/calibration.json)
- [校准报告 / Calibration report](../../reports/week4_calibration.md)

---

## Slide 22｜Grad-CAM 的目标层会改变观察结果 / Grad-CAM Target-Layer Choice Changes the Observation

**中文上屏文案**

- 原目标层：`layer4.2.conv3`
- 修正目标层：residual block 输出 `layer4.2`
- 原因：避免只捕获残差合并前的中间张量
- 固定样本 `test_index=9750` 的热点由叶外背景回到叶片主体

**English slide copy**

- Original target layer: `layer4.2.conv3`
- Revised target layer: residual-block output `layer4.2`
- Rationale: avoid capturing only the pre-residual intermediate tensor
- For fixed sample `test_index=9750`, the hotspot moves from background regions back toward the leaf

**核心结论 / Takeaway**

> 中文：可解释性工具本身也需要实验设计、固定样本和复现验证。  
> English: Explainability tools themselves require experimental design, fixed samples, and reproducibility checks.

**图像 / Visuals**

- [现有 Grad-CAM 目标层页 / Existing Grad-CAM target-layer slide](plantdisease_ai_week8_research_defense/slide-14.png)
- [最终目标层样本 / Final-layer sample](../../outputs/plantvillage/week4_explainability/gradcam_atlas/correct_high_confidence/01_test-9750_target-31_Tomato___Leaf_Mold.png)
- [Baseline/最终模型对比图 / Baseline/final comparison figure](../../reports/figures/week4_baseline_vs_final_gradcam.png)

<!-- GENERATED-CHART-REFS:START -->
**生成图表参考 / Generated chart reference**

- `14-attention-review`: [PNG](charts/english-transparent/14-attention-review.png) · [SVG](charts/english-transparent/14-attention-review.svg)

**图表限定 / Chart context**

- Seed 42 · official split · 227 overlapping `leaf_id` values.
- Non-causal relevance visualization.
<!-- GENERATED-CHART-REFS:END -->

**证据 / Evidence**

- [Week 4 阶段报告 / Week 4 stage report](../../reports/week4_stage_report.md)
- [冻结样本报告 / Frozen-sample report](../../reports/week4_frozen_samples.md)

---

## Slide 23｜固定样本让解释分析可以重复 / Fixed Samples Make Explainability Reproducible

**状态 / Status:** 可隐藏 / Optional

**中文上屏文案**

- 正确、高置信：6
- 正确、低置信：6
- 错误、高置信：6
- 错误、低置信：6
- 总计：24 个固定样本

人工关注区域：lesion 14、mixed 4、leaf 4、background 2。  
错误样本主要失败类型：visual similarity 8/12。

**English slide copy**

- Correct, high confidence: 6
- Correct, low confidence: 6
- Incorrect, high confidence: 6
- Incorrect, low confidence: 6
- Total: 24 fixed samples

Manual attention review: lesion 14, mixed 4, leaf 4, background 2.  
Dominant failure type among reviewed errors: visual similarity, 8/12.

**复现性 / Reproducibility**

- direct heatmaps：24/24 精确一致 / 24/24 exactly identical
- atlas PNG：最大通道差 ≤ 5/255 / maximum channel difference ≤ 5/255

**同页限制 / Same-slide qualifier**

> Grad-CAM 是非因果相关性可视化，不是病理因果解释。  
> Grad-CAM is a non-causal relevance visualization, not a causal pathological explanation.

**图像 / Visuals**

- [四象限样本之一 / Example from the four-quadrant atlas](../../outputs/plantvillage/week4_explainability/gradcam_atlas/error_low_confidence/19_test-3453_target-9_Corn__maize____Northern_Leaf_Blight.png)
- [Baseline/最终模型对比 / Baseline/final comparison](../../reports/figures/week4_baseline_vs_final_gradcam.png)

<!-- GENERATED-CHART-REFS:START -->
**生成图表参考 / Generated chart reference**

- `16-gradcam-reproducibility`: [PNG](charts/english-transparent/16-gradcam-reproducibility.png) · [SVG](charts/english-transparent/16-gradcam-reproducibility.svg)
- `14-attention-review`: [PNG](charts/english-transparent/14-attention-review.png) · [SVG](charts/english-transparent/14-attention-review.svg)

**图表限定 / Chart context**

- Seed 42 · official split · 227 overlapping `leaf_id` values.
- Non-causal relevance visualization.
<!-- GENERATED-CHART-REFS:END -->

**数据与证据 / Data and evidence**

- [冻结样本 JSON / Frozen-samples JSON](../../outputs/plantvillage/week4_explainability/frozen_samples.json)
- [关注区域审阅 / Attention review](../../reports/week4_attention_review.md)
- [Grad-CAM 复现报告 / Grad-CAM reproducibility report](../../reports/week4_gradcam_reproducibility.md)

---

## Slide 24｜服务层先收集证据，再决定是否开放疾病路径 / The Service Collects Evidence Before Opening a Disease Path

**中文上屏文案**

- 目标叶片：自动选择优势叶片，或在原图上一键点选
- 植物身份：本地 114 类目录；不确定时才使用可选 Pl@ntNet
- 支持作物门控：不支持的身份保留 identity，但不开放病害
- OpenCV 形态：面积、主轴、形状、颜色和分布保持为独立证据
- Corn 先检查非生物胁迫形态；否则进入作物内 PlantVillage conditions
- Grad-CAM、Qwen 与管理建议只在各自上游门控允许时开放

**English slide copy**

- Target leaf: accept one dominant leaf or one source-image click
- Plant identity: local 114-class routing catalog; optional Pl@ntNet only when uncertain
- Supported-host gate: preserve identity evidence but withhold disease for unsupported plants
- OpenCV morphology: keep area, axis, shape, color, and distribution as separate evidence
- Accepted Corn checks abiotic-stress morphology before crop-specific PlantVillage conditions
- Grad-CAM, Qwen, and management guidance open only when their upstream gates permit them

**推荐版式 / Recommended layout**

```text
Target leaf → Plant identity → Supported host?
                              ├─ No: abstain
                              └─ Yes: OpenCV morphology
                                      ├─ Corn abiotic gate
                                      └─ Crop-specific conditions
                                               ↓
                              Grad-CAM / Qwen / optional guidance gates
```

**图像 / Visuals**

- [分层服务架构 PNG / Hierarchical serving architecture PNG](../media/week8_hierarchical_serving_architecture.png)
- [Demo 工程说明 / Demo engineering report](../../reports/week5_demo_engineering.md)

<!-- GENERATED-CHART-REFS:START -->
**生成图表参考 / Generated chart reference**

- `17-demo-timing-observations`: [PNG](charts/english-transparent/17-demo-timing-observations.png) · [SVG](charts/english-transparent/17-demo-timing-observations.svg)
- `20-clean-reproducibility`: [PNG](charts/english-transparent/20-clean-reproducibility.png) · [SVG](charts/english-transparent/20-clean-reproducibility.svg)

**图表限定 / Chart context**

- Fixed-example engineering observation; not a latency benchmark.
- Frozen RC snapshot; the current worktree audit may contain later claims.
<!-- GENERATED-CHART-REFS:END -->

**代码证据 / Code evidence**

- [推理服务 / Inference service](../../src/plantdisease/serving/service.py)
- [目标叶片 / Target leaf](../../src/plantdisease/serving/leaf_isolation.py)
- [分层路由 / Hierarchy](../../src/plantdisease/serving/hierarchy.py)
- [病斑聚焦 / Lesion focus](../../src/plantdisease/serving/lesion_focus.py)

---

## Slide 25｜Demo 先展示目标叶片，再完整展开证据与边界 / The Demo Shows the Target Leaf Before Expanding Evidence and Boundaries

**中文上屏文案**

- 顶部摄影卡上传图片；多叶歧义时直接在原图点选目标叶片
- Analyze 后自动移动到下方完整结果区，不用嵌套滚动
- Classifier 先显示植物身份，再显示支持作物内 conditions
- OpenCV 形态证据与 Grad-CAM 各自标明证据边界
- Qwen 只描述可见形态；管理建议需要用户手动选择并配置供应商
- 上游拒识或 Corn 非生物形态会锁定疾病知识与管理建议

**English slide copy**

- Upload in the top photography card; click the source image when multiple leaves are ambiguous
- Analyze moves to a fully expanded result region with no nested scrolling
- Classifier shows plant identity before supported-host conditions
- OpenCV morphology and Grad-CAM retain separate evidence boundaries
- Qwen describes visible morphology only; management requires a manually selected, configured provider
- Upstream abstention or Corn abiotic morphology locks disease knowledge and management guidance

**安全边界 / Safety boundary**

- 中文：114 类目录不是 114 物种田间准确率；OpenCV 不是病理分割；“疑似非生物/营养胁迫”不是确诊缺氮。
- English: The 114-class catalog is not 114-species field accuracy; OpenCV is not pathological segmentation; suspected abiotic/nutrient stress is not confirmed nitrogen deficiency.

**图像 / Visuals**

- [React Demo 截图 / React demo screenshot](../../reports/figures/week8_react_demo_desktop.png)
- [Demo poster](../media/week7_apple_demo_poster.png)
- [Demo GIF](../media/week7_apple_demo.gif)
- [现有 Demo 页 / Existing demo slide](plantdisease_ai_week8_research_defense/slide-15.png)

<!-- GENERATED-CHART-REFS:START -->
**生成图表参考 / Generated chart reference**

- `12-error-audit`: [PNG](charts/english-transparent/12-error-audit.png) · [SVG](charts/english-transparent/12-error-audit.svg)
- `17-demo-timing-observations`: [PNG](charts/english-transparent/17-demo-timing-observations.png) · [SVG](charts/english-transparent/17-demo-timing-observations.svg)

**图表限定 / Chart context**

- Seed 42 · official split · 227 overlapping `leaf_id` values.
- Fixed-example engineering observation; not a latency benchmark.
<!-- GENERATED-CHART-REFS:END -->

**证据 / Evidence**

- [目标叶片与非生物门控 QA / Target-leaf and abiotic-gate QA](../../reports/target-leaf-abiotic-qa.md)
- [React/FastAPI API](../../app/api.py)

---

## Slide 26｜Apple Container 验证了独立运行链路 / Apple Container Validates an Independent Runtime Path

**状态 / Status:** 可隐藏 / Optional

**中文上屏文案**

- Linux ARM64 CPU-only 镜像
- Streamlit health endpoint：`ok`
- 固定样例 Top-5 + Grad-CAM：通过
- Week 5 镜像约 909 MiB
- 一次运行时内存采样：821.67 MiB / 1 GiB
- Week 8 Apple container audit：passed

**English slide copy**

- Linux ARM64, CPU-only image
- Streamlit health endpoint: `ok`
- Fixed-example Top-5 + Grad-CAM: passed
- Week 5 image size: approximately 909 MiB
- One runtime memory sample: 821.67 MiB / 1 GiB
- Week 8 Apple container audit: passed

**同页限制 / Same-slide qualifier**

- 中文：129.8 ms 与 246.92 ms 均为固定合成输入的单次观测，不是通用延迟 Benchmark；目前没有公开部署或真实用户流量证据。
- English: The 129.8 ms and 246.92 ms values are single observations on a fixed synthetic input, not general latency benchmarks; there is no evidence of public deployment or production traffic.

**图像 / Visuals**

- [容器 E2E overlay / Container E2E overlay](../../outputs/plantvillage/week5_demo/container_e2e_overlay.png)
- [现有工程条件页 / Existing engineering-conditions slide](plantdisease_ai_week8_research_defense/slide-16.png)

<!-- GENERATED-CHART-REFS:START -->
**生成图表参考 / Generated chart reference**

- `22-apple-container-facts`: [PNG](charts/english-transparent/22-apple-container-facts.png) · [SVG](charts/english-transparent/22-apple-container-facts.svg)
- `17-demo-timing-observations`: [PNG](charts/english-transparent/17-demo-timing-observations.png) · [SVG](charts/english-transparent/17-demo-timing-observations.svg)

**图表限定 / Chart context**

- Fixed-example engineering observation; not a latency benchmark.
<!-- GENERATED-CHART-REFS:END -->

**数据与证据 / Data and evidence**

- [容器 E2E JSON / Container E2E JSON](../../outputs/plantvillage/week5_demo/container_e2e.json)
- [Week 8 复现报告 / Week 8 reproducibility report](../../reports/week8_reproducibility.md)
- [Containerfile](../../Containerfile)

---

## Slide 27｜VLM 只在分类主线完成后作为探索分支 / VLM Work Begins Only After the Classification Core Is Complete

**状态 / Status:** 可隐藏 / Optional

**中文上屏文案**

- 模型：`mlx-community/Qwen3-VL-4B-Instruct-4bit`
- 设备：Apple Silicon / MLX
- VQA seed：24 张图、72 个问题
- 问题类型：plant、condition、health status
- 答案来自数据标签，不使用模型生成结果作为真值
- 图片实体 split leakage：false
- 人工逐条审计：尚未完成

**English slide copy**

- Model: `mlx-community/Qwen3-VL-4B-Instruct-4bit`
- Runtime: Apple Silicon / MLX
- VQA seed: 24 images and 72 questions
- Question types: plant, condition, and health status
- Answers are grounded in dataset labels rather than model-generated pseudo-labels
- Image-entity split leakage: false
- Manual item-level audit: incomplete

**同页边界 / Same-slide boundary**

> 中文：这是小样本 smoke exploration，没有完成 LoRA/QLoRA。  
> English: This is a small-sample smoke exploration; LoRA/QLoRA was not completed.

**图像 / Visuals**

- [现有 VLM 分支页 / Existing VLM-branch slide](plantdisease_ai_week8_research_defense/slide-17.png)
- [VQA seed summary](../../outputs/plantvillage/week6_vlm/vqa_seed_summary.json)

<!-- GENERATED-CHART-REFS:START -->
**生成图表参考 / Generated chart reference**

- `18-vqa-seed-composition`: [PNG](charts/english-transparent/18-vqa-seed-composition.png) · [SVG](charts/english-transparent/18-vqa-seed-composition.svg)
- `21-eight-week-evidence-timeline`: [PNG](charts/english-transparent/21-eight-week-evidence-timeline.png) · [SVG](charts/english-transparent/21-eight-week-evidence-timeline.svg)

**图表限定 / Chart context**

- 5 images / 15 questions smoke study; no completed LoRA/QLoRA.
<!-- GENERATED-CHART-REFS:END -->

**证据 / Evidence**

- [VQA 数据卡 / VQA data card](../../reports/week6_vqa_datacard.md)
- [VLM 实验记录 / VLM experiment report](../../reports/week6_vlm_experiment.md)

---

## Slide 28｜约束输出减少幻觉，但没有解决细粒度识别 / Constrained Output Reduces Hallucination but Does Not Solve Fine-Grained Recognition

**核心表格 / Core table**

| Prompt / 提示方式 | Total exact match / 总严格匹配 | Condition |
| --- | ---: | ---: |
| Original | 0/15 | 0/5 |
| Short answer | 10/15 | 0/5 |
| Choice | **11/15** | **1/5** |
| Few-shot choice | **11/15** | **1/5** |

**中文结论**

- Short prompt 解决了 plant 和 health-status 的答案格式问题。
- Choice 减少自由生成漂移并消除自动风险词标记。
- Few-shot 没有继续提升总严格匹配。
- Condition 仍只有 1/5，Prompt engineering 不能替代模型能力。

**English takeaway**

- Short prompts fix answer-format failures for plant and health-status questions.
- Choice prompts reduce free-form drift and remove automatic risk-word flags.
- Few-shot choice does not improve the total exact-match score further.
- Condition recognition remains at 1/5; prompt engineering cannot replace model capability.

**图像 / Visuals**

- [现有 11/15 与 1/5 页 / Existing 11/15 and 1/5 slide](plantdisease_ai_week8_research_defense/slide-18.png)
- 建议自制：四列阶梯图，突出“格式改善”和“识别能力未改善”是两个不同结论。
- Suggested custom visual: A four-column progression separating format improvement from recognition capability.

<!-- GENERATED-CHART-REFS:START -->
**生成图表参考 / Generated chart reference**

- `19-vlm-prompt-comparison`: [PNG](charts/english-transparent/19-vlm-prompt-comparison.png) · [SVG](charts/english-transparent/19-vlm-prompt-comparison.svg)

**图表限定 / Chart context**

- 5 images / 15 questions smoke study; no completed LoRA/QLoRA.
<!-- GENERATED-CHART-REFS:END -->

**数据与证据 / Data and evidence**

- [Choice JSON](../../outputs/plantvillage/week6_vlm/qwen3_vl_choice_smoke.json)
- [Few-shot choice JSON](../../outputs/plantvillage/week6_vlm/qwen3_vl_few_shot_choice_smoke.json)
- [Prompt 比较报告 / Prompt-comparison report](../../reports/week6_vlm_prompt_compare.md)

---

## Slide 29｜拒答被设计为农业助手的正式功能 / Refusal Is a First-Class Feature of the Agricultural Assistant

**状态 / Status:** 可隐藏 / Optional

**中文上屏文案**

1. 高置信、域内输入 → 教育性摘要
2. 农药、剂量或稀释请求 → 拒绝高风险建议
3. 低置信分类上下文 → 拒绝确定诊断
4. 非叶片或域外输入 → 拒绝回答

**English slide copy**

1. High-confidence in-domain input → bounded educational summary
2. Pesticide, dosage, or dilution request → refuse high-risk advice
3. Low-confidence classifier context → refuse definitive diagnosis
4. Non-leaf or out-of-domain input → refuse the request

**来源记录 / Provenance**

- `classifier:<label>`
- `vqa:<experiment>`

**核心结论 / Takeaway**

> 中文：一个负责任的农业 AI 系统不仅要知道如何回答，还要知道什么时候不应回答。  
> English: A responsible agricultural AI system must know not only how to answer, but also when it should not answer.

<!-- GENERATED-CHART-REFS:START -->
**生成图表参考 / Generated chart reference**

- `19-vlm-prompt-comparison`: [PNG](charts/english-transparent/19-vlm-prompt-comparison.png) · [SVG](charts/english-transparent/19-vlm-prompt-comparison.svg)

**图表限定 / Chart context**

- 5 images / 15 questions smoke study; no completed LoRA/QLoRA.
<!-- GENERATED-CHART-REFS:END -->

**数据与证据 / Data and evidence**

- [助手固定场景 JSON / Fixed assistant scenarios](../../outputs/plantvillage/week6_vlm/vlm_assistant_demo.json)
- [安全助手报告 / Safety-assistant report](../../reports/week6_vlm_assistant.md)
- [助手实现 / Assistant implementation](../../src/plantdisease/vlm/assistant.py)

---

## Slide 30｜干净环境复现覆盖代码、包与命令行 / Clean Reproduction Covers Code, Packaging, and CLI Wiring

**中文上屏文案**

- Python 3.12.13，PyTorch 2.13.0
- Apple M5，24 GB 内存
- 仓库外干净虚拟环境
- 226 tests passed
- Ruff passed
- `ty` type check passed
- 7 个数值 claim、4 个边界 claim、0 个损坏链接
- synthetic smoke、package build、CLI help 全部通过

**English slide copy**

- Python 3.12.13 and PyTorch 2.13.0
- Apple M5 with 24 GB memory
- A clean virtual environment outside the repository
- 226 tests passed
- Ruff passed
- `ty` type checking passed
- 7 numerical claims, 4 boundary claims, and 0 broken links
- Synthetic smoke, package build, and CLI help all passed

**三条验证通道 / Three validation lanes**

- Clean lane：安装、测试、静态检查、包、合成 smoke
- Local evidence lane：冻结 checkpoint 指标重算、Top-5、MPS Grad-CAM
- Container lane：独立运行与 healthcheck

- Clean lane: installation, tests, static checks, packaging, and synthetic smoke
- Local evidence lane: frozen-checkpoint recomputation, Top-5, and MPS Grad-CAM
- Container lane: independent runtime and health check

**图像 / Visuals**

- [现有复现页 / Existing reproducibility slide](plantdisease_ai_week8_research_defense/slide-19.png)

<!-- GENERATED-CHART-REFS:START -->
**生成图表参考 / Generated chart reference**

- `20-clean-reproducibility`: [PNG](charts/english-transparent/20-clean-reproducibility.png) · [SVG](charts/english-transparent/20-clean-reproducibility.svg)

**图表限定 / Chart context**

- Frozen RC snapshot; the current worktree audit may contain later claims.
<!-- GENERATED-CHART-REFS:END -->

**数据与证据 / Data and evidence**

- [Week 8 复现报告 / Week 8 reproducibility report](../../reports/week8_reproducibility.md)
- [Release manifest](../../reports/release/week8_rc1_manifest.json)
- [Claim ledger](../../reports/release/week8_claim_evidence.json)

---

## Slide 31｜交付物形成可追溯的成果体系 / Deliverables Form a Traceable Research Portfolio

**状态 / Status:** 可隐藏 / Optional

**中文上屏文案**

- 可安装 Python 包与稳定 CLI
- 配置、checkpoint、metrics、日志和图表
- 数据卡、模型卡与最终实验报告
- 中英文各 12 页论文
- 20 页 PPTX 与原生 Keynote 答辩稿
- Streamlit Demo、GIF 与 MP4
- Release candidate manifest、哈希与 claim ledger
- 简历 bullet—证据映射

**English slide copy**

- Installable Python package and stable CLIs
- Configurations, checkpoint, metrics, logs, and figures
- Data card, model card, and final experiment report
- Twelve-page papers in both Chinese and English
- A 20-slide PPTX and a native Keynote defense deck
- Streamlit demo, GIF, and MP4
- Release-candidate manifest, hashes, and claim ledger
- Resume-bullet-to-evidence mapping

**边界 / Boundary**

> 中文：当前是本地 release candidate，不是公开发布、投稿、获奖或线上生产系统。  
> English: This is a local release candidate, not evidence of public release, publication, awards, or production deployment.

**图像 / Visuals**

- [Demo poster](../media/week7_apple_demo_poster.png)
- [现有完整 PPTX / Existing complete PPTX](plantdisease_ai_week8_research_defense.pptx)

<!-- GENERATED-CHART-REFS:START -->
**生成图表参考 / Generated chart reference**

- `01-project-evidence-snapshot`: [PNG](charts/english-transparent/01-project-evidence-snapshot.png) · [SVG](charts/english-transparent/01-project-evidence-snapshot.svg)
- `20-clean-reproducibility`: [PNG](charts/english-transparent/20-clean-reproducibility.png) · [SVG](charts/english-transparent/20-clean-reproducibility.svg)

**图表限定 / Chart context**

- Seed 42 · official split · 227 overlapping `leaf_id` values.
- Frozen RC snapshot; the current worktree audit may contain later claims.
<!-- GENERATED-CHART-REFS:END -->

**证据 / Evidence**

- [成果索引 / Artifact index](../artifact-index.md)
- [简历证据映射 / Resume evidence map](../resume/week8_resume_evidence.md)

---

## Slide 32｜最重要的研究缺口已被明确记录 / The Most Important Evidence Gaps Are Explicitly Recorded

**中文上屏文案**

当前限制：

- official split 存在 227 个重叠 `leaf_id`
- 只有 seed 42，没有多随机种子统计
- PlantVillage 背景受控、类别闭集
- 未验证未知病害和真实田间域偏移
- 峰值内存未统一测量
- Grad-CAM 非因果
- VQA 人工审计与 LoRA/QLoRA 未完成
- 无真实用户与专业农艺验证
- OpenCV 区域是启发式证据，不是专家病理 mask
- 114 类目录没有 114 物种田间准确率验证
- Corn 门控没有营养标签，不能确认缺氮
- 原缺氮附件已不在仓库，尚无该精确文件的外部 Benchmark

**English slide copy**

Current limitations:

- The official split contains 227 overlapping `leaf_id` values
- Only seed 42 has been evaluated; no multi-seed statistics are available
- PlantVillage uses controlled backgrounds and a closed label set
- Unknown diseases and real-field domain shift remain unvalidated
- Peak memory was not measured consistently
- Grad-CAM is non-causal
- Manual VQA audit and LoRA/QLoRA are incomplete
- No real-user or professional agronomic validation exists
- OpenCV regions are heuristic evidence, not expert pathological masks
- The 114-class catalog has no validated 114-species field accuracy
- The Corn gate has no nutrient labels and cannot confirm nitrogen deficiency
- The original deficiency attachment is absent, so no exact-file external benchmark exists

**下一步 / Next steps**

1. `leaf_id`-disjoint protocol
2. Multi-seed runs and uncertainty estimates
3. External field and unknown-class data
4. Calibration and refusal under domain shift
5. Expert-labeled biotic, abiotic, nutrient-stress, and region data
6. Region-supervised target-leaf and lesion evaluation
7. Expert human review
8. Separately specified LoRA experiment only if resources permit

**图像 / Visuals**

- [现有下一步页 / Existing next-steps slide](plantdisease_ai_week8_research_defense/slide-20.png)

<!-- GENERATED-CHART-REFS:START -->
**生成图表参考 / Generated chart reference**

- `03-split-and-overlap`: [PNG](charts/english-transparent/03-split-and-overlap.png) · [SVG](charts/english-transparent/03-split-and-overlap.svg)
- `19-vlm-prompt-comparison`: [PNG](charts/english-transparent/19-vlm-prompt-comparison.png) · [SVG](charts/english-transparent/19-vlm-prompt-comparison.svg)
- `22-apple-container-facts`: [PNG](charts/english-transparent/22-apple-container-facts.png) · [SVG](charts/english-transparent/22-apple-container-facts.svg)

**图表限定 / Chart context**

- Seed 42 · official split · 227 overlapping `leaf_id` values.
- 5 images / 15 questions smoke study; no completed LoRA/QLoRA.
<!-- GENERATED-CHART-REFS:END -->

**证据 / Evidence**

- [最终发布检查清单 / Final release checklist](../release/week8_release_checklist.md)
- [最终实验报告 / Final experiment report](../../reports/final_experiment_report.md)

---

## Slide 33｜我的核心能力是把模型结果变成可信系统 / My Core Strength Is Turning Model Results into a Trustworthy System

**中文上屏文案**

> 我完成了从数据、训练、评估到部署的端到端工程闭环。
> 我用 Benchmark、消融、错误分析与复现审计让结论能够被重新检查。
> 我让目标叶片、身份、形态、病害和建议各自保留证据门控，并主动披露数据泄漏、域偏移和 VLM 能力边界。
> 我没有把实验分数、启发式 mask 或 114 类目录包装成专业诊断能力。

**English slide copy**

> I completed an end-to-end engineering loop from data and training to evaluation and deployment.
> I made the conclusions recheckable through benchmarking, controlled ablations, error analysis, and reproducibility auditing.
> I kept target leaf, identity, morphology, disease, and guidance behind explicit evidence gates while disclosing leakage, domain-shift, and VLM limits.
> I did not present experimental scores, heuristic masks, or a 114-class catalog as professional diagnostic capability.

**页面元素 / Slide elements**

- GitHub 或项目二维码 / GitHub or project QR code
- Demo 或视频入口 / Demo or video link
- “欢迎就实验协议、错误案例和系统实现提问” / “Questions on the protocol, failure cases, and implementation are welcome.”

**推荐图像 / Recommended visual**

- [分层服务架构图 / Hierarchical serving architecture](../media/week8_hierarchical_serving_architecture.png)
- [Demo GIF](../media/week7_apple_demo.gif)

<!-- GENERATED-CHART-REFS:START -->
**生成图表参考 / Generated chart reference**

- `01-project-evidence-snapshot`: [PNG](charts/english-transparent/01-project-evidence-snapshot.png) · [SVG](charts/english-transparent/01-project-evidence-snapshot.svg)
- `11-final-improvement`: [PNG](charts/english-transparent/11-final-improvement.png) · [SVG](charts/english-transparent/11-final-improvement.svg)

**图表限定 / Chart context**

- Seed 42 · official split · 227 overlapping `leaf_id` values.
<!-- GENERATED-CHART-REFS:END -->

**证据 / Evidence**

- [导师沟通摘要 / Mentor summary](../mentor/week8_mentor_summary.md)
- [最终实验报告 / Final experiment report](../../reports/final_experiment_report.md)

---

# 备答附录 / Backup Appendix

## Appendix A1｜38 类标签与作物分布 / The 38-Class Label Taxonomy

**中文内容**

- 按作物分组列出 38 个 crop–condition 标签。
- 标注 healthy 与 disease 类别。
- 展示各类别 train 样本数，说明类别不均衡。
- 解释为什么主指标选择 Macro F1，而不只报告 Accuracy。

**English content**

- List all 38 crop–condition labels grouped by crop.
- Mark healthy and diseased classes.
- Show per-class training counts to expose class imbalance.
- Explain why Macro F1 is a primary metric alongside Accuracy.

**图像与数据 / Visuals and data**

- [类别分布图 / Class-distribution plot](../../outputs/plantvillage/eda/class_distribution.png)
- [数据审计 JSON / Data-audit JSON](../../outputs/plantvillage/audit.json)
- [最终 split manifest / Final split manifest](../../outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/split.json)

<!-- GENERATED-CHART-REFS:START -->
**生成图表参考 / Generated chart reference**

- `04-class-distribution`: [PNG](charts/english-transparent/04-class-distribution.png) · [SVG](charts/english-transparent/04-class-distribution.svg)
- `02-dataset-composition`: [PNG](charts/english-transparent/02-dataset-composition.png) · [SVG](charts/english-transparent/02-dataset-composition.svg)

**图表限定 / Chart context**


<!-- GENERATED-CHART-REFS:END -->

---

## Appendix A2｜完整数据审计与上游兼容问题 / Full Data Audit and Upstream Compatibility

**中文内容**

- Loader revision：`9e97599868962bd0079b8db4b7f1efa9185fa1e7`
- 上游许可声明：CC BY-SA 3.0
- Hub 文件名与自动发现不一致
- `datasets 4.x` 移除 dataset script 支持
- 项目固定 `datasets>=3.6,<4` 并显式加载脚本
- 数据约 2 GB，本地缓存，不提交原始图片

**English content**

- Loader revision: `9e97599868962bd0079b8db4b7f1efa9185fa1e7`
- Upstream license statement: CC BY-SA 3.0
- Hub filename mismatch with automatic discovery
- Dataset-script support removed in `datasets 4.x`
- The project pins `datasets>=3.6,<4` and loads the script explicitly
- Approximately 2 GB of data is cached locally; raw images are not committed

<!-- GENERATED-CHART-REFS:START -->
**生成图表参考 / Generated chart reference**

- `02-dataset-composition`: [PNG](charts/english-transparent/02-dataset-composition.png) · [SVG](charts/english-transparent/02-dataset-composition.svg)
- `03-split-and-overlap`: [PNG](charts/english-transparent/03-split-and-overlap.png) · [SVG](charts/english-transparent/03-split-and-overlap.svg)
- `04-class-distribution`: [PNG](charts/english-transparent/04-class-distribution.png) · [SVG](charts/english-transparent/04-class-distribution.svg)

**图表限定 / Chart context**

- Seed 42 · official split · 227 overlapping `leaf_id` values.
<!-- GENERATED-CHART-REFS:END -->

**图像与证据 / Visuals and evidence**

- [尺寸分布 / Image-size distribution](../../outputs/plantvillage/eda/image_size_distribution.png)
- [数据审计报告 / Data-audit report](../../reports/data_audit.md)
- [Hugging Face loader implementation](../../src/plantdisease/data/huggingface.py)

---

## Appendix A3｜最终训练配置 / Final Training Configuration

**中文与英文对照 / Bilingual configuration summary**

| Item / 项目 | Value / 数值 | Purpose / 作用 |
| --- | --- | --- |
| Input / 输入 | 224×224 | TorchVision pretrained-model input |
| RandomResizedCrop | scale 0.8–1.0 | Training-only spatial augmentation / 仅训练空间增强 |
| HorizontalFlip | enabled | Training-only symmetry augmentation / 仅训练翻转 |
| Rotation | 10° | Mild pose variation / 轻度姿态变化 |
| ColorJitter | 0.15 | Mild color variation / 轻度颜色变化 |
| Normalization | ImageNet | Match pretrained weights / 对齐预训练权重 |
| Optimizer | AdamW | Frozen optimization choice / 冻结优化器 |
| Label smoothing | 0.1 | Reduce overconfidence / 缓解过度自信 |
| Scheduler | Cosine, `eta_min=1e-5` | Smooth late-stage refinement / 后期平滑收敛 |
| Model selection | Best validation Macro F1 | Test remains final-only / test 仅最终评估 |

<!-- GENERATED-CHART-REFS:START -->
**生成图表参考 / Generated chart reference**

- `11-final-improvement`: [PNG](charts/english-transparent/11-final-improvement.png) · [SVG](charts/english-transparent/11-final-improvement.svg)
- `10-ablation-duration`: [PNG](charts/english-transparent/10-ablation-duration.png) · [SVG](charts/english-transparent/10-ablation-duration.svg)

**图表限定 / Chart context**

- Seed 42 · official split · 227 overlapping `leaf_id` values.
<!-- GENERATED-CHART-REFS:END -->

**数据与证据 / Data and evidence**

- [最终配置 YAML / Final configuration YAML](../../configs/week3_ablation/09_combo_candidate.yaml)
- [Canonical transforms](../../src/plantdisease/data/transforms.py)
- [最终 run manifest / Final run manifest](../../outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/run_manifest.json)

---

## Appendix A4｜五模型完整训练结果 / Full Five-Model Training Results

**中文说明：** 该表使用相同 official split 和 checkpoint 选择规则汇总五个正式模型运行；不同 batch size 是本地资源约束，必须在答辩中明确。  
**English note:** The table summarizes five formal model runs under the same official split and checkpoint-selection rule; batch-size differences reflect local resource constraints and must be disclosed.

| Model / 模型 | Batch | Duration / 时长 | Best epoch | Val Acc | Val Macro F1 | Test Acc | Test Macro F1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| MobileNetV2 | 32 | 26.6 min | 4 | 0.9821 | 0.9760 | 0.9760 | 0.9674 |
| ResNet18 | 32 | 22.7 min | 5 | 0.9810 | 0.9718 | 0.9774 | 0.9661 |
| ResNet50 | 16 | 66.0 min | 3 | 0.9868 | 0.9775 | 0.9830 | 0.9743 |
| EfficientNet-B0 | 32 | 43.0 min | 2 | 0.9881 | 0.9816 | 0.9804 | 0.9703 |
| EfficientNetV2-S | 8 | 101.0 min | 5 | 0.9812 | 0.9723 | 0.9794 | 0.9708 |

<!-- GENERATED-CHART-REFS:START -->
**生成图表参考 / Generated chart reference**

- `05-model-accuracy-f1`: [PNG](charts/english-transparent/05-model-accuracy-f1.png) · [SVG](charts/english-transparent/05-model-accuracy-f1.svg)
- `06-model-efficiency-pareto`: [PNG](charts/english-transparent/06-model-efficiency-pareto.png) · [SVG](charts/english-transparent/06-model-efficiency-pareto.svg)
- `07-model-latency`: [PNG](charts/english-transparent/07-model-latency.png) · [SVG](charts/english-transparent/07-model-latency.svg)

**图表限定 / Chart context**

- Seed 42 · official split · 227 overlapping `leaf_id` values.
- Fixed-example engineering observation; not a latency benchmark.
<!-- GENERATED-CHART-REFS:END -->

**图像与证据 / Visuals and evidence**

- [Pareto 图 / Pareto plot](../../outputs/plantvillage/benchmarks/week2_accuracy_efficiency_pareto.png)
- [Week 2 Benchmark 报告 / Week 2 benchmark report](../../reports/week2_benchmark_progress.md)

---

## Appendix A5｜效率 Benchmark 方法 / Efficiency-Benchmark Methodology

**中文内容**

- 设备：Apple MPS
- 精度：float32
- 输入：224×224
- 延迟：batch 1
- 吞吐：batch 32
- 预热：10 次
- 正式测量：50 次
- 不包含预处理
- FLOPs：`fvcore.nn.FlopCountAnalysis`
- 峰值内存：未测量

**English content**

- Device: Apple MPS
- Precision: float32
- Input: 224×224
- Latency: batch 1
- Throughput: batch 32
- Warm-up: 10 iterations
- Measurement: 50 iterations
- Preprocessing excluded
- FLOPs: `fvcore.nn.FlopCountAnalysis`
- Peak memory: not measured

**数据 / Data**

- [MobileNetV2 benchmark JSON](../../outputs/plantvillage/benchmarks/mobilenet_v2_seed42.json)
- [ResNet18 benchmark JSON](../../outputs/plantvillage/benchmarks/resnet18_seed42.json)
- [ResNet50 benchmark JSON](../../outputs/plantvillage/benchmarks/resnet50_seed42.json)
- [EfficientNet-B0 benchmark JSON](../../outputs/plantvillage/benchmarks/efficientnet_b0_seed42.json)
- [EfficientNetV2-S benchmark JSON](../../outputs/plantvillage/benchmarks/efficientnet_v2_s_seed42.json)

<!-- GENERATED-CHART-REFS:START -->
**生成图表参考 / Generated chart reference**

- `06-model-efficiency-pareto`: [PNG](charts/english-transparent/06-model-efficiency-pareto.png) · [SVG](charts/english-transparent/06-model-efficiency-pareto.svg)
- `07-model-latency`: [PNG](charts/english-transparent/07-model-latency.png) · [SVG](charts/english-transparent/07-model-latency.svg)
- `17-demo-timing-observations`: [PNG](charts/english-transparent/17-demo-timing-observations.png) · [SVG](charts/english-transparent/17-demo-timing-observations.svg)

**图表限定 / Chart context**

- Fixed-example engineering observation; not a latency benchmark.
<!-- GENERATED-CHART-REFS:END -->

---

## Appendix A6｜完整十组消融 / Full Ten-Run Ablation Matrix

**中文说明：** 00–08 为冻结协议下的基线与单变量实验，09 是由单变量结果支持后执行的组合候选；全部结果均为 seed 42 单次运行。  
**English note:** Runs 00–08 are the frozen baseline and single-variable experiments; run 09 is a combination candidate executed after reviewing the single-variable evidence. All results are single seed-42 runs.

| ID | Method / 方法 | Best epoch | Test Acc | Test Macro F1 | Duration / 时长 |
| --- | --- | ---: | ---: | ---: | ---: |
| 00 | ResNet50 baseline | 3 | 0.9830 | 0.9743 | 85.7 min |
| 01 | Label Smoothing 0.1 | 5 | 0.9885 | 0.9865 | 87.4 min |
| 02 | Focal Loss, γ=2.0 | 5 | 0.9751 | 0.9652 | 81.4 min |
| 03 | Cosine Scheduler | 5 | 0.9935 | 0.9898 | 85.9 min |
| 04 | EMA, decay=0.999 | 5 | 0.9752 | 0.9673 | 87.2 min |
| 05 | RandAugment | 5 | 0.9765 | 0.9698 | 92.8 min |
| 06 | Random Erasing | 5 | 0.9723 | 0.9683 | 79.9 min |
| 07 | Mixup, α=0.2 | 5 | 0.9837 | 0.9793 | 66.7 min |
| 08 | CutMix, α=1.0 | 5 | 0.9893 | 0.9863 | 65.3 min |
| 09 | Label Smoothing + Cosine | 5 | **0.9953** | **0.9941** | 65.4 min |

<!-- GENERATED-CHART-REFS:START -->
**生成图表参考 / Generated chart reference**

- `08-ablation-macro-f1`: [PNG](charts/english-transparent/08-ablation-macro-f1.png) · [SVG](charts/english-transparent/08-ablation-macro-f1.svg)
- `09-ablation-delta`: [PNG](charts/english-transparent/09-ablation-delta.png) · [SVG](charts/english-transparent/09-ablation-delta.svg)
- `10-ablation-duration`: [PNG](charts/english-transparent/10-ablation-duration.png) · [SVG](charts/english-transparent/10-ablation-duration.svg)

**图表限定 / Chart context**

- Seed 42 · official split · 227 overlapping `leaf_id` values.
<!-- GENERATED-CHART-REFS:END -->

**图像与证据 / Visuals and evidence**

- [验证 Macro F1 曲线叠图 / Validation Macro-F1 curve overlay](../../reports/figures/week3_validation_macro_f1_curves.png)
- [消融报告 / Ablation report](../../reports/week3_ablation_results.md)

---

## Appendix A7｜分类别指标与重点混淆 / Per-Class Metrics and Priority Confusions

**中文内容**

- 展示低 F1 类别和重点混淆对。
- 每个混淆对至少配一张真实样本或 Grad-CAM panel。
- 同时展示真实标签、预测标签、置信度与 test index。
- 明确区分“观察结果”和“可能解释”。

**English content**

- Show the lowest-F1 classes and priority confusion pairs.
- Pair each confusion with at least one real sample or Grad-CAM panel.
- Display the true label, predicted label, confidence, and test index.
- Separate observed evidence from possible explanations.

**图像与数据 / Visuals and data**

- [玉米高置信错误 / High-confidence corn error](../../outputs/plantvillage/week4_explainability/gradcam_atlas/error_high_confidence/16_test-1099_target-7_Corn__maize____Cercospora_leaf_spot_Gray_leaf_spot.png)
- [番茄低置信错误 / Low-confidence tomato error](../../outputs/plantvillage/week4_explainability/gradcam_atlas/error_low_confidence/24_test-6690_target-29_Tomato___Early_blight.png)
- [错误分析 JSON / Error-analysis JSON](../../outputs/plantvillage/week4_explainability/error_analysis.json)

<!-- GENERATED-CHART-REFS:START -->
**生成图表参考 / Generated chart reference**

- `23-per-class-f1`: [PNG](charts/english-transparent/23-per-class-f1.png) · [SVG](charts/english-transparent/23-per-class-f1.svg)
- `13-top-confusions`: [PNG](charts/english-transparent/13-top-confusions.png) · [SVG](charts/english-transparent/13-top-confusions.svg)
- `24-full-confusion-matrix`: [PNG](charts/english-transparent/24-full-confusion-matrix.png) · [SVG](charts/english-transparent/24-full-confusion-matrix.svg)

**图表限定 / Chart context**

- Seed 42 · official split · 227 overlapping `leaf_id` values.
<!-- GENERATED-CHART-REFS:END -->

---

## Appendix A8｜校准与 Grad-CAM 方法 / Calibration and Grad-CAM Methodology

**中文内容**

- ECE：分箱后预测置信度与实际准确率的加权偏差。
- MCE：最差置信区间的校准偏差。
- Brier：概率预测与真实结果之间的平方误差。
- Grad-CAM：使用目标类别梯度对特征图加权，仅说明空间相关性。
- 正式 ResNet50 目标层：`layer4.2`。

**English content**

- ECE: weighted discrepancy between confidence and empirical accuracy across bins.
- MCE: the maximum calibration gap among bins.
- Brier score: squared error between predicted probabilities and outcomes.
- Grad-CAM: target-class gradients weight feature maps to visualize spatial relevance only.
- Formal ResNet50 target layer: `layer4.2`.

<!-- GENERATED-CHART-REFS:START -->
**生成图表参考 / Generated chart reference**

- `15-calibration`: [PNG](charts/english-transparent/15-calibration.png) · [SVG](charts/english-transparent/15-calibration.svg)
- `14-attention-review`: [PNG](charts/english-transparent/14-attention-review.png) · [SVG](charts/english-transparent/14-attention-review.svg)
- `16-gradcam-reproducibility`: [PNG](charts/english-transparent/16-gradcam-reproducibility.png) · [SVG](charts/english-transparent/16-gradcam-reproducibility.svg)

**图表限定 / Chart context**

- Seed 42 · official split · 227 overlapping `leaf_id` values.
- Non-causal relevance visualization.
<!-- GENERATED-CHART-REFS:END -->

**图像与证据 / Visuals and evidence**

- [Reliability diagram](../../reports/figures/week4_reliability_diagram.png)
- [Grad-CAM 示例 / Grad-CAM example](../../outputs/plantvillage/week4_explainability/gradcam_atlas/correct_low_confidence/10_test-691_target-29_Tomato___Early_blight.png)
- [校准实现 / Calibration implementation](../../src/plantdisease/explainability/calibration.py)
- [Grad-CAM 实现 / Grad-CAM implementation](../../src/plantdisease/explainability/gradcam.py)

---

## Appendix A9｜Baseline 与最终模型同样本比较 / Baseline vs Final Model on the Same Samples

**中文上屏文案**

- 分析集合：12 个最终模型失败样本
- baseline Top-1 正确：4/12
- 两个模型 Top-1 相同：5/12
- 同时比较预测结果与 Grad-CAM 关注区域

**English slide copy**

- Analysis set: 12 samples failed by the final model
- Baseline Top-1 correct: 4/12
- Identical Top-1 predictions across models: 5/12
- Compare both predictions and Grad-CAM attention regions

**限制 / Limitation**

- 中文：该集合按最终模型失败筛选，不能代表整体测试集上的模型优劣。
- English: Because the set is selected from final-model failures, it cannot represent overall test-set superiority.

**图像与数据 / Visuals and data**

- [Baseline 与最终模型对比图 / Baseline vs final comparison](../../reports/figures/week4_baseline_vs_final_gradcam.png)
- [机器可读对比 JSON / Machine-readable comparison JSON](../../outputs/plantvillage/week4_explainability/baseline_vs_final_gradcam.json)
- [对比报告 / Comparison report](../../reports/week4_baseline_vs_final_gradcam.md)

<!-- GENERATED-CHART-REFS:START -->
**生成图表参考 / Generated chart reference**

- `11-final-improvement`: [PNG](charts/english-transparent/11-final-improvement.png) · [SVG](charts/english-transparent/11-final-improvement.svg)
- `12-error-audit`: [PNG](charts/english-transparent/12-error-audit.png) · [SVG](charts/english-transparent/12-error-audit.svg)

**图表限定 / Chart context**

- Seed 42 · official split · 227 overlapping `leaf_id` values.
<!-- GENERATED-CHART-REFS:END -->

---

## Appendix A10｜VLM 原始回答与风险词案例 / Raw VLM Answers and Risk-Word Cases

**中文内容**

- Original prompt 严格匹配为 0/15，主要问题是自由生成和格式漂移。
- Short prompt 将 plant 与 health status 提升至 5/5，但 condition 仍为 0/5。
- Original/short 回答出现 `virus`、`fungal`、`bacterial`、`pseudomonas` 等未受控解释词。
- Choice 与 few-shot choice 自动风险词标记为 0，但 condition 仍只有 1/5。

**English content**

- The original prompt scores 0/15 under strict exact match, largely because of free-form generation and format drift.
- The short prompt raises plant and health status to 5/5, while condition remains 0/5.
- Original/short responses include uncontrolled terms such as `virus`, `fungal`, `bacterial`, and `pseudomonas`.
- Choice and few-shot choice remove automatic risk-word flags, but condition remains only 1/5.

<!-- GENERATED-CHART-REFS:START -->
**生成图表参考 / Generated chart reference**

- `19-vlm-prompt-comparison`: [PNG](charts/english-transparent/19-vlm-prompt-comparison.png) · [SVG](charts/english-transparent/19-vlm-prompt-comparison.svg)
- `18-vqa-seed-composition`: [PNG](charts/english-transparent/18-vqa-seed-composition.png) · [SVG](charts/english-transparent/18-vqa-seed-composition.svg)

**图表限定 / Chart context**

- 5 images / 15 questions smoke study; no completed LoRA/QLoRA.
<!-- GENERATED-CHART-REFS:END -->

**数据与证据 / Data and evidence**

- [Original prompt JSON](../../outputs/plantvillage/week6_vlm/qwen3_vl_zero_shot_smoke.json)
- [Short prompt JSON](../../outputs/plantvillage/week6_vlm/qwen3_vl_zero_shot_smoke_short.json)
- [结果分析 / Result analysis](../../reports/week6_vlm_result_analysis.md)

---

## Appendix A11｜测试与 CLI 覆盖 / Test and CLI Coverage

**中文内容**

测试覆盖：

- 数据 split、Dataset、Transforms、EDA 与 audit
- 模型前向、反向、checkpoint 与 inference
- Accuracy、Macro F1、Benchmark
- Mixup/CutMix、Loss、Scheduler、EMA
- Grad-CAM、校准、错误分析和固定样本
- 服务层、Streamlit、E2E 与 container 配置
- 目标叶片点选、GrabCut 纯度、植物身份路由与支持作物拒识
- 病斑聚焦、Corn 中轴非生物形态门控与管理建议锁定
- VQA schema、baseline、assistant 与 audit
- release claims、manifest、论文和 PPT 合同测试

**English content**

Test coverage includes:

- Data splits, datasets, transforms, EDA, and audits
- Model forward/backward paths, checkpoints, and inference
- Accuracy, Macro F1, and benchmarking
- Mixup/CutMix, losses, schedulers, and EMA
- Grad-CAM, calibration, error analysis, and fixed samples
- Service layer, Streamlit, E2E, and container configuration
- Target-leaf clicks, GrabCut purity, plant-identity routing, and supported-host abstention
- Lesion focus, the Corn central-axis abiotic gate, and management-guidance locking
- VQA schema, baseline, assistant, and audit
- Release claims, manifest, papers, and presentation contracts

<!-- GENERATED-CHART-REFS:START -->
**生成图表参考 / Generated chart reference**

- `20-clean-reproducibility`: [PNG](charts/english-transparent/20-clean-reproducibility.png) · [SVG](charts/english-transparent/20-clean-reproducibility.svg)

**图表限定 / Chart context**

- Frozen RC snapshot; the current worktree audit may contain later claims.
<!-- GENERATED-CHART-REFS:END -->

**数据与证据 / Data and evidence**

- [测试目录 / Test directory](../../tests/)
- [Python 项目配置 / Python project configuration](../../pyproject.toml)
- [Week 8 复现报告 / Week 8 reproducibility report](../../reports/week8_reproducibility.md)

---

## Appendix A12｜证据路径与声明红线 / Evidence Paths and Claim Guardrails

**可安全使用的声明 / Defensible claims**

- 5-model official-split benchmark
- 0.9953 Accuracy / 0.9941 Macro F1 on seed 42 official split
- 50 errors among 10,709 test images
- ECE 0.0965 and a fixed 24-sample Grad-CAM atlas
- 226 tests passed in a clean environment
- Qwen3-VL choice/few-shot smoke: 11/15 overall and 1/5 condition

**禁止声明 / Claims to avoid**

- 多随机种子稳定性或统计显著性 / Multi-seed stability or statistical significance
- 实体隔离、严格无泄漏 / Entity isolation or leakage-free evaluation
- 真实田间鲁棒性 / Real-field robustness
- 专业农业诊断 / Professional agricultural diagnosis
- 完成 LoRA/QLoRA / Completed LoRA/QLoRA
- 公开部署、真实用户、论文录用、比赛成绩、专利或奖项 / Public deployment, real users, accepted publication, competition result, patent, or award
- Grad-CAM 因果解释 / Causal explanation from Grad-CAM
- 将单次固定样例耗时当成 Benchmark / Treating one fixed-example timing as a benchmark
- 114 类目录已经验证 114 物种田间准确率 / Validated 114-species field accuracy from the 114-class catalog
- OpenCV 输出是病理真值分割 / OpenCV output as pathological ground-truth segmentation
- Corn 门控确诊缺氮或具体营养元素 / Corn-gate confirmation of nitrogen deficiency or a specific nutrient

<!-- GENERATED-CHART-REFS:START -->
**生成图表参考 / Generated chart reference**

- `20-clean-reproducibility`: [PNG](charts/english-transparent/20-clean-reproducibility.png) · [SVG](charts/english-transparent/20-clean-reproducibility.svg)
- `03-split-and-overlap`: [PNG](charts/english-transparent/03-split-and-overlap.png) · [SVG](charts/english-transparent/03-split-and-overlap.svg)
- `19-vlm-prompt-comparison`: [PNG](charts/english-transparent/19-vlm-prompt-comparison.png) · [SVG](charts/english-transparent/19-vlm-prompt-comparison.svg)

**图表限定 / Chart context**

- Frozen RC snapshot; the current worktree audit may contain later claims.
- Seed 42 · official split · 227 overlapping `leaf_id` values.
- 5 images / 15 questions smoke study; no completed LoRA/QLoRA.
<!-- GENERATED-CHART-REFS:END -->

**核心证据 / Core evidence**

- [Claim configuration](../../configs/week8_claims.yaml)
- [Claim evidence ledger](../../reports/release/week8_claim_evidence.json)
- [Release manifest](../../reports/release/week8_rc1_manifest.json)
- [简历证据映射 / Resume evidence map](../resume/week8_resume_evidence.md)

---

# 快速删减方案 / Fast Shortening Guide

如果汇报时间只有 15–20 分钟，可隐藏以下主稿页面：  
If the presentation is limited to 15–20 minutes, hide the following main-deck slides:

- Slide 5：八周时间线 / Eight-week timeline
- Slide 10：运行记录结构 / Run-record structure
- Slide 11：最小基线闭环 / Minimal baseline loop
- Slide 14：多目标模型决策 / Multi-objective model decision
- Slide 17：负结果机制假设 / Negative-result hypotheses
- Slide 23：Grad-CAM 复现细节 / Grad-CAM reproducibility detail
- Slide 26：Container 资源细节 / Container resource details
- Slide 27：VQA seed 构建 / VQA-seed construction
- Slide 29：助手四种固定场景 / Four assistant scenarios
- Slide 31：成果体系 / Deliverable portfolio

删减后仍保留研究问题、数据边界、Benchmark、消融、最终模型、错误分析、校准、Grad-CAM、Demo、VLM 结果、复现审计和研究局限。

The shortened deck still preserves the research question, data boundary, benchmark, ablation, final model, error analysis, calibration, Grad-CAM, demo, VLM findings, reproducibility audit, and research limitations.

---

# 图像使用总表 / Visual Asset Master Index

| Purpose / 用途 | Asset / 素材 | Suggested slides / 推荐页面 |
| --- | --- | --- |
| Complete English chart kit / 完整英文图表包 | [24-chart SVG + transparent PNG index](charts/english-transparent/README.md) | Slides 1–33; Appendices A1–A12 |
| Dataset samples / 数据样例 | [sample_grid.png](../../outputs/plantvillage/eda/sample_grid.png) | 6, 7, A1 |
| Class distribution / 类别分布 | [class_distribution.png](../../outputs/plantvillage/eda/class_distribution.png) | 7, A1 |
| Image-size audit / 尺寸审计 | [image_size_distribution.png](../../outputs/plantvillage/eda/image_size_distribution.png) | 7, A2 |
| Current hierarchical architecture / 当前分层架构 | [week8_hierarchical_serving_architecture.png](../media/week8_hierarchical_serving_architecture.png) | 4, 9, 24, 25, 33 |
| Historical classifier-first architecture / 历史分类器主线架构 | [week7_apple_architecture.png](../media/week7_apple_architecture.png) | Week 7 historical reference |
| Accuracy–efficiency trade-off / 精度效率权衡 | [week2_accuracy_efficiency_pareto.png](../../outputs/plantvillage/benchmarks/week2_accuracy_efficiency_pareto.png) | 13, 14, A4 |
| Ablation curves / 消融曲线 | [week3_validation_macro_f1_curves.png](../../reports/figures/week3_validation_macro_f1_curves.png) | 16, 17, A6 |
| Final training curve / 最终训练曲线 | [training_curve.png](../../outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/training_curve.png) | 18 |
| Calibration / 校准 | [week4_reliability_diagram.png](../../reports/figures/week4_reliability_diagram.png) | 21, A8 |
| Grad-CAM comparison / Grad-CAM 对比 | [week4_baseline_vs_final_gradcam.png](../../reports/figures/week4_baseline_vs_final_gradcam.png) | 22, 23, A9 |
| Streamlit UI / Streamlit 界面 | [week5_streamlit_demo.jpg](../../reports/figures/week5_streamlit_demo.jpg) | 25 |
| Demo poster / Demo 海报 | [week7_apple_demo_poster.png](../media/week7_apple_demo_poster.png) | 25, 31 |
| Demo animation / Demo 动画 | [week7_apple_demo.gif](../media/week7_apple_demo.gif) | 25, 33 |
| Demo video / Demo 视频 | [week7_apple_demo.mp4](../media/week7_apple_demo.mp4) | 25, 33 |
| Container overlay / 容器叠加图 | [container_e2e_overlay.png](../../outputs/plantvillage/week5_demo/container_e2e_overlay.png) | 26 |

---

# 最终自检 / Final Self-Check

制作 PPT 前逐项确认：  
Before finalizing the deck, verify each item:

- [ ] 中英文数字完全一致 / Chinese and English numbers are identical.
- [ ] Accuracy、F1 与 FPS 均附协议 / Accuracy, F1, and FPS include protocol context.
- [ ] 0.9953 / 0.9941 与 seed 42、official split、227 overlap 同时出现 / 0.9953 / 0.9941 appears with seed 42, official split, and the 227-overlap qualifier.
- [ ] 129.8 ms 与 246.92 ms 未被称为 Benchmark / 129.8 ms and 246.92 ms are not called benchmarks.
- [ ] VLM 结果明确为 5 图 / 15 问 smoke / VLM results are explicitly scoped to a 5-image / 15-question smoke study.
- [ ] 未声称完成 LoRA/QLoRA / No claim of completed LoRA/QLoRA.
- [ ] Grad-CAM 被描述为非因果相关性可视化 / Grad-CAM is described as non-causal relevance visualization.
- [ ] Demo 包含教育用途与非专业诊断声明 / The demo includes educational-use and non-professional-diagnosis disclaimers.
- [ ] 114 类目录没有被写成 114 物种田间准确率 / The 114-class catalog is not presented as 114-species field accuracy.
- [ ] OpenCV 区域被描述为启发式证据 / OpenCV regions are described as heuristic evidence.
- [ ] Corn 门控没有被写成确诊缺氮 / The Corn gate is not presented as confirmed nitrogen deficiency.
- [ ] 没有公开发布、真实用户、论文录用、比赛或奖项等无证据声明 / No unsupported claim of public release, real users, publication acceptance, competition result, or award.
- [ ] 每张图都能回溯到仓库路径 / Every visual is traceable to a repository path.
