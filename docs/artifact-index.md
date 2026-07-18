# PlantDiseaseAI 成果索引

## Week 1

| 证据 | 路径或生成命令 | 状态 |
| --- | --- | --- |
| 工程与依赖 | `pyproject.toml`、`uv.lock` | 已验证 |
| 自动化测试 | `uv run pytest -q` | 已验证 |
| 静态检查 | `uv run ruff check .` | 已验证 |
| 合成 smoke | `uv run plant-smoke --output-dir outputs/smoke/week1 --seed 42 --image-size 32` | 已验证 |
| smoke manifest | `outputs/smoke/week1/run_manifest.json` | 本地生成、Git 忽略 |
| 数据审计 | `outputs/smoke/week1/audit.json`、`reports/data_audit.md` | 合成数据已验证 |
| 单 batch 过拟合 | `outputs/smoke/week1/single_batch_overfit.json` | 合成数据已验证 |
| 模型 checkpoint | `outputs/smoke/week1/checkpoint.pt` | 合成数据已验证、Git 忽略 |
| 指标与预测 | `outputs/smoke/week1/metrics.json`、`predictions.json` | 合成数据已验证 |
| EDA 图 | `outputs/smoke/week1/*.png` | 合成数据已验证 |
| PlantVillage 下载 | `uv run python scripts/download_data.py --cache-dir data/huggingface` | 已验证，本地缓存 |
| PlantVillage train 审计 | `outputs/plantvillage/audit.json` | 已验证，train split |
| PlantVillage EDA | `outputs/plantvillage/eda/*.png` | 已验证，train split |
| PlantVillage 顺序 probe5000 | `outputs/plantvillage/baseline_mobilenet_v2_probe5000/` | 已验证，非正式指标 |
| PlantVillage 均衡 probe10 | `outputs/plantvillage/balanced_probe10_mobilenet_v2_seed42/` | 已验证，非正式指标 |
| PlantVillage 官方 split MobileNetV2 baseline | `outputs/plantvillage/baseline_mobilenet_v2_seed42/` | 已验证，Accuracy 0.9676 / Macro F1 0.9491 |
| PlantVillage checkpoint 推理 | `uv run plant-predict --checkpoint outputs/plantvillage/baseline_mobilenet_v2_seed42/checkpoint.pt --image outputs/smoke/week1/example_input.png --top-k 5` | 已验证 |
| leaf_id 泄漏检查 | `reports/data_audit.md` | 已记录，227 个重叠 leaf_id |
| Week 1 关闭记录 | `reports/week1.md`、`TASKS.md` | 已关闭，官方 split 限制已记录 |

## Week 2

| 证据 | 路径或生成命令 | 状态 |
| --- | --- | --- |
| 五模型模型工厂 | `src/plantdisease/models/factory.py`、`tests/models/test_factory.py` | 已验证，5 个模型输出类别数正确 |
| 五模型配置 | `configs/baseline_mobilenet_v2.yaml`、`configs/baseline_resnet18.yaml`、`configs/baseline_resnet50.yaml`、`configs/baseline_efficientnet_b0.yaml`、`configs/baseline_efficientnet_v2_s.yaml` | 已验证 |
| best checkpoint 训练逻辑 | `src/plantdisease/training/baseline.py`、`tests/training/test_baseline_run.py` | 已验证，按 validation Macro F1 保存 |
| 五模型 smoke | `outputs/plantvillage/smoke_mobilenet_v2_week2_seed42/`、`smoke_resnet18_seed42/`、`smoke_efficientnet_b0_seed42/`、`smoke_resnet50_seed42/`、`smoke_efficientnet_v2_s_seed42/` | 已验证，小样本端到端 |
| MobileNetV2 best-checkpoint 正式结果 | `outputs/plantvillage/baseline_mobilenet_v2_best_seed42/` | 已验证，Accuracy 0.9760 / Macro F1 0.9674 |
| ResNet18 正式结果 | `outputs/plantvillage/baseline_resnet18_seed42/` | 已验证，Accuracy 0.9774 / Macro F1 0.9661 |
| ResNet50 正式结果 | `outputs/plantvillage/baseline_resnet50_seed42/` | 已验证，Accuracy 0.9830 / Macro F1 0.9743 |
| EfficientNet-B0 正式结果 | `outputs/plantvillage/baseline_efficientnet_b0_seed42/` | 已验证，Accuracy 0.9804 / Macro F1 0.9703 |
| EfficientNetV2-S 正式结果 | `outputs/plantvillage/baseline_efficientnet_v2_s_seed42/` | 已验证，Accuracy 0.9794 / Macro F1 0.9708 |
| 效率 Benchmark CLI | `src/plantdisease/evaluation/benchmark.py`、`src/plantdisease/cli.py`、`tests/evaluation/test_benchmark.py`、`tests/test_benchmark_cli.py` | 已验证，`plant-benchmark` 可生成参数量/FLOPs/延迟/吞吐 JSON |
| MobileNetV2 效率 probe | `outputs/plantvillage/benchmarks/probe_mobilenet_v2.json` | 已验证，短测量用于确认真实 checkpoint 命令可运行 |
| 五模型效率 Benchmark | `outputs/plantvillage/benchmarks/*_seed42.json` | 已验证，MPS / float32 / warmup 10 / iterations 50 / throughput batch 32 |
| Week 2 Pareto 图 | `outputs/plantvillage/benchmarks/week2_accuracy_efficiency_pareto.png` | 已验证，Accuracy-efficiency 可视化 |
| Week 2 Benchmark 报告 | `reports/week2_benchmark_progress.md` | 已完成官方 split benchmark；ResNet50 为最佳精度候选，MobileNetV2 为默认部署候选 |

## Week 3

| 证据 | 路径或生成命令 | 状态 |
| --- | --- | --- |
| Week 3 配置结构 | `src/plantdisease/config.py`、`tests/test_config.py` | 已验证，augmentation/loss/scheduler/ema section 可解析和校验 |
| Loss 实现 | `src/plantdisease/training/losses.py`、`tests/training/test_losses.py` | 已验证，CrossEntropy label smoothing、Focal Loss、soft-label CE |
| Mixup/CutMix | `src/plantdisease/training/mix.py`、`tests/training/test_mix.py` | 已验证，软标签、Mixup、CutMix、互斥开关 |
| 训练增强开关 | `src/plantdisease/data/transforms.py`、`tests/data/test_transforms.py` | 已验证，RandAugment 与 Random Erasing 可配置 |
| Scheduler 与 EMA | `src/plantdisease/training/schedulers.py`、`src/plantdisease/training/ema.py`、`tests/training/test_schedulers.py`、`tests/training/test_ema.py` | 已验证，Cosine scheduler、EMA 更新与权重切换 |
| 训练入口接线 | `src/plantdisease/training/engine.py`、`src/plantdisease/training/baseline.py`、`tests/training/test_engine.py`、`tests/training/test_baseline_run.py` | 已验证，训练时接入 mixer/scheduler/EMA，manifest 与 checkpoint 记录方法配置 |
| 单变量消融与组合配置矩阵 | `configs/week3_ablation/*.yaml`、`reports/week3_ablation_matrix.md` | 已验证，00 baseline、01 Label Smoothing、02 Focal Loss、03 Cosine Scheduler、04 EMA、05 RandAugment、06 Random Erasing、07 Mixup、08 CutMix 和 09 组合候选均已完成 |
| Week 3 00 ResNet50 baseline | `outputs/plantvillage/week3_ablation/00_resnet50_baseline_seed42/`、`reports/week3_ablation_results.md` | 已验证，Best epoch 3，Test Accuracy 0.9830 / Macro F1 0.9743 |
| Week 3 01 Label Smoothing | `outputs/plantvillage/week3_ablation/01_label_smoothing_seed42/`、`reports/week3_ablation_results.md` | 已验证，Best epoch 5，Test Accuracy 0.9885 / Macro F1 0.9865 |
| Week 3 02 Focal Loss | `outputs/plantvillage/week3_ablation/02_focal_loss_seed42/`、`reports/week3_ablation_results.md` | 已验证，Best epoch 5，Test Accuracy 0.9751 / Macro F1 0.9652 |
| Week 3 03 Cosine Scheduler | `outputs/plantvillage/week3_ablation/03_cosine_scheduler_seed42/`、`reports/week3_ablation_results.md` | 已验证，Best epoch 5，Test Accuracy 0.9935 / Macro F1 0.9898 |
| Week 3 04 EMA | `outputs/plantvillage/week3_ablation/04_ema_seed42/`、`reports/week3_ablation_results.md` | 已验证，Best epoch 5，Test Accuracy 0.9752 / Macro F1 0.9673 |
| Week 3 05 RandAugment | `outputs/plantvillage/week3_ablation/05_randaugment_seed42/`、`reports/week3_ablation_results.md` | 已验证，Best epoch 5，Test Accuracy 0.9765 / Macro F1 0.9698 |
| Week 3 06 Random Erasing | `outputs/plantvillage/week3_ablation/06_random_erasing_seed42/`、`reports/week3_ablation_results.md` | 已验证，Best epoch 5，Test Accuracy 0.9723 / Macro F1 0.9683 |
| Week 3 07 Mixup | `outputs/plantvillage/week3_ablation/07_mixup_seed42/`、`reports/week3_ablation_results.md` | 已验证，Best epoch 5，Test Accuracy 0.9837 / Macro F1 0.9793 |
| Week 3 08 CutMix | `outputs/plantvillage/week3_ablation/08_cutmix_seed42/`、`reports/week3_ablation_results.md` | 已验证，Best epoch 5，Test Accuracy 0.9893 / Macro F1 0.9863 |
| Week 3 09 Label Smoothing + Cosine Scheduler | `outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/`、`reports/week3_ablation_results.md` | 已验证，Best epoch 5，Test Accuracy 0.9953 / Macro F1 0.9941 |
| Week 3 训练曲线对比 | `reports/figures/week3_validation_macro_f1_curves.png` | 已生成，比较 00 baseline、03 Cosine Scheduler 和 09 组合候选 |
| Week 3 最终候选决策记录 | `reports/week3_final_model_decision.md` | 已记录，09 作为 Week 4 Grad-CAM 与错误分析的冻结候选 checkpoint；单 seed、官方 split 和峰值内存限制已说明 |
| Week 3 工程验证 | `uv run pytest tests/test_config.py tests/training/test_losses.py tests/training/test_mix.py tests/training/test_schedulers.py tests/training/test_ema.py tests/data/test_transforms.py tests/data/test_pipeline.py tests/training/test_engine.py tests/training/test_baseline_run.py -q` | 上一次验证：35 passed |

## Week 4

| 证据 | 路径或生成命令 | 状态 |
| --- | --- | --- |
| Grad-CAM 核心 | `src/plantdisease/explainability/gradcam.py`、`tests/explainability/test_gradcam.py` | 已验证，覆盖输入对齐、归一化、批处理、外层 `inference_mode`、梯度状态和 hook 生命周期 |
| 目标层解析 | `src/plantdisease/explainability/layers.py`、`tests/explainability/test_layers.py` | 已验证，正式 ResNet50 目标层为最后一个 residual block 输出 `layer4.2` |
| 样本冻结入口 | `src/plantdisease/explainability/predictions.py`、`src/plantdisease/explainability/samples.py`、`src/plantdisease/explainability/workflow.py`、`plant-freeze-samples` | 已验证并用于正式导出 |
| Week 4 冻结样本 | `outputs/plantvillage/week4_explainability/frozen_samples.json`、`reports/week4_frozen_samples.md` | 已按目标层 `layer4.2` 重新生成，四组各 6 个 test index；`predictions.json` 为本地 10MB 逐样本预测证据，不纳入 Git |
| Grad-CAM 图集入口 | `src/plantdisease/explainability/atlas.py`、`src/plantdisease/explainability/visualization.py`、`plant-gradcam-atlas` | 已验证并用于正式导出 |
| Week 4 Grad-CAM 图集 | `outputs/plantvillage/week4_explainability/gradcam_atlas/`、`reports/week4_gradcam_atlas.md` | 已按目标层 `layer4.2` 重新生成，24 张固定样本 original/heatmap/overlay panel；target mode 为 `predicted` |
| 错误分析入口 | `src/plantdisease/explainability/error_analysis.py`、`plant-error-analysis`、`tests/explainability/test_error_analysis.py`、`tests/test_error_analysis_cli.py` | 已验证，输出低 F1 类别、重点混淆对、非归一化/行归一化混淆矩阵和高置信错误 |
| Week 4 错误分析 | `outputs/plantvillage/week4_explainability/error_analysis.json`、`reports/week4_error_analysis.md` | 已生成，测试集错误 `50` 条，高置信错误阈值 `0.8` 下 `2` 条；错误类型统计见 Week 4 关注区域审阅 |
| 关注区域审阅模板 | `src/plantdisease/explainability/attention_review.py`、`plant-attention-review`、`tests/explainability/test_attention_review.py`、`tests/test_attention_review_cli.py` | 已验证，生成 24 个固定样本的可编辑人工审阅 JSON 和 Markdown 摘要；候选提示不等于人工结论 |
| Week 4 关注区域审阅 | `outputs/plantvillage/week4_explainability/attention_review.json`、`reports/week4_attention_review.md` | 已完成 24 个固定样本视觉审阅；关注区域统计：lesion 14、mixed 4、leaf 4、background 2；错误样本主要失败类型为 visual_similarity `8/12` |
| 校准分析入口 | `src/plantdisease/explainability/calibration.py`、`plant-calibration-analysis`、`tests/explainability/test_calibration.py`、`tests/test_calibration_cli.py` | 已验证，输出 top-label ECE/MCE/Brier、reliability bins 和 reliability diagram |
| Week 4 校准分析 | `outputs/plantvillage/week4_explainability/calibration.json`、`reports/week4_calibration.md`、`reports/figures/week4_reliability_diagram.png` | 已生成，Top-label ECE `0.0965`、MCE `0.3348`、Brier `0.0140`；非完整多类别概率校准 |
| Week 4 baseline Grad-CAM 图集 | `outputs/plantvillage/week4_explainability/baseline_gradcam_atlas/`、`reports/week4_baseline_gradcam_atlas.md` | 已生成，使用 Week 3 `00_resnet50_baseline_seed42` checkpoint 与同一冻结样本配置 |
| Week 4 baseline/final 同样本对比 | `outputs/plantvillage/week4_explainability/baseline_vs_final_gradcam.json`、`reports/week4_baseline_vs_final_gradcam.md`、`reports/figures/week4_baseline_vs_final_gradcam.png` | 已生成，12 个最终模型失败样本中 baseline top-1 正确 `4/12`，二者 top-1 相同 `5/12`；该集合不能代表整体测试集 |
| Week 4 Grad-CAM 复现性验证 | `outputs/plantvillage/week4_explainability/gradcam_reproducibility.json`、`outputs/plantvillage/week4_explainability/gradcam_reproducibility_direct.json`、`reports/week4_gradcam_reproducibility.md` | 已验证，24/24 个 direct heatmap 精确一致；atlas PNG 24/24 最大通道差 ≤ `5/255` |
| Week 1–4 阶段报告 | `reports/week4_stage_report.md` | 已生成，论文式结构包含 Abstract、Related Work、Method、Results、Grad-CAM、错误分析、校准、局限和参考文献 |
| Week 4 一致性审计 | `outputs/plantvillage/week4_explainability/consistency_audit.json`、`reports/week4_consistency_audit.md` | 已通过，阶段报告路径、关键指标、实验 ID、图表引用和 Week4 收口证据 `20/20` 一致 |
| Week 1–4 LaTeX 论文草稿 | `paper/zh/main.tex`、`paper/en/main.tex`、`paper/out/plantdisease_ai_zh.pdf`、`paper/out/plantdisease_ai_en.pdf` | 已同步到 Week 4 证据，包含中英文草稿、Grad-CAM、错误分析、校准图、局限和参考文献；结论限定于官方 split 与 seed 42 |
| Week 4 基础验证 | `uv run pytest tests/explainability -q`、`uv run pytest -q`、`uv run ruff check .` | 代码、单元测试与静态检查已通过；人工关注区域/错误类型审阅、baseline 同样本对比、Grad-CAM 复现性和一致性审计均已完成 |

## Week 5

| 证据 | 路径或生成命令 | 状态 |
| --- | --- | --- |
| UI 无关推理服务 | `src/plantdisease/serving/service.py`、`tests/serving/test_service.py` | 已验证，覆盖 Top-5、耗时、Grad-CAM overlay、低置信提示、非法输入和推理异常包装 |
| 疾病知识卡 | `src/plantdisease/serving/knowledge.py`、`tests/serving/test_knowledge.py` | 已验证，覆盖 PlantVillage label 解析、healthy 类和未知类 fallback；不提供处方性处置建议 |
| 服务缓存 | `src/plantdisease/serving/cache.py`、`tests/serving/test_cache.py` | 已验证，同 checkpoint/device/layer 复用服务实例 |
| Streamlit Demo | `app/streamlit_app.py`、`tests/test_streamlit_app.py` | 已验证，模块导入不加载 checkpoint；本地 Streamlit healthcheck 返回 `ok` |
| Demo 截图 | `reports/figures/week5_streamlit_demo.jpg` | 已生成，本地 Streamlit 页面截图 |
| 固定合成样例 | `app/examples/synthetic_leaf.png` | 已生成，仅作为工程 smoke 输入，不代表真实准确率 |
| 本地固定样例端到端 | `scripts/demo_e2e.py`、`tests/test_demo_e2e.py`、`outputs/plantvillage/week5_demo/local_e2e.json` | 已验证，ResNet50 CPU Top-5 + Grad-CAM overlay；输出目录本地生成、Git 忽略 |
| Week 5 证据报告 | `reports/week5_demo_engineering.md` | 已记录本地验证、容器验证、低置信/安全限制和 Apple container troubleshooting |
| Apple container 配置与运行 | `Containerfile`、`.dockerignore`、`tests/test_container_config.py`、`outputs/plantvillage/week5_demo/container_e2e.json` | 已验证 CPU-only `localhost/plantdisease-ai:week5` build/run、Streamlit healthcheck、容器内固定样例 Top-5 + Grad-CAM；镜像约 909 MiB，运行时内存采样 821.67 MiB / 1.00 GiB |
| 公开架构与功能说明 | `docs/project-architecture.md` | 已补充公开可展示的系统架构图、功能范围、证据路径和农业安全边界 |

## Week 6

| 证据 | 路径或生成命令 | 状态 |
| --- | --- | --- |
| VLM 选型记录 | `reports/week6_vlm_selection.md` | 已记录 2026-07-13 本机 Apple M5 / 24 GiB / MPS 可用环境、SmolVLM/Qwen/InternVL 候选、许可证和第一候选选择理由 |
| Week6 设计与实施计划 | `docs/superpowers/specs/2026-07-13-week6-vlm-exploration-design.md`、`docs/superpowers/plans/2026-07-13-week6-vlm-exploration.md` | 已建立，明确 LoRA 未完成、VQA 先行、真实 VLM smoke 后置 |
| VQA schema 与测试 | `src/plantdisease/vlm/schema.py`、`tests/vlm/test_schema.py` | 已验证，覆盖必填字段、split/source/audit_status 校验、JSONL round trip 和实体 split 泄漏检查 |
| VQA seed 数据构建 | `src/plantdisease/vlm/dataset.py`、`scripts/build_vqa_dataset.py`、`tests/vlm/test_dataset.py` | 已验证，从 Week4 冻结样本构建 24 图/72 问 label-grounded seed 数据，不使用模型生成答案 |
| VQA seed 数据卡 | `reports/week6_vqa_datacard.md`、`outputs/plantvillage/week6_vlm/vqa_seed_summary.json` | 已生成，本地输出 Git 忽略；summary 显示 `entity_split_leakage=false` |
| Qwen3-VL baseline scaffold and smoke | `src/plantdisease/vlm/backends.py`、`src/plantdisease/vlm/baseline.py`、`scripts/run_vlm_baseline.py`、`reports/week6_vlm_experiment.md`、`reports/week6_vlm_prompt_compare.md` | 已验证 download-free tests、skip-mode CLI 和真实 `mlx-community/Qwen3-VL-4B-Instruct-4bit` smoke；原始 prompt 0/15，短答案 prompt 10/15，choice 与 few-shot choice 均为 11/15；均为 5 图/15 问小样本 smoke |
| VLM 结果分析与自动质量审计 | `src/plantdisease/vlm/analysis.py`、`scripts/analyze_vlm_results.py`、`tests/vlm/test_analysis.py`、`reports/week6_vlm_result_analysis.md` | 已验证，按题型拆分 exact-match、记录 condition 混淆、风险词标记和 seed 数据自动质量审计；人工审计仍未完成 |
| VQA 人工审计模板 | `src/plantdisease/vlm/audit.py`、`scripts/build_vqa_audit_template.py`、`tests/vlm/test_vlm_audit.py`、`reports/week6_vqa_manual_audit_template.md` | 已生成 72 条待审模板，状态 `pending_human_review`；人工逐条审阅仍未完成 |
| 农业助手安全原型 | `src/plantdisease/vlm/assistant.py`、`scripts/demo_vlm_assistant.py`、`tests/vlm/test_assistant.py`、`tests/vlm/test_assistant_demo.py`、`reports/week6_vlm_assistant.md` | 已验证分类器结构化上下文、教育性摘要、高风险剂量拒答、低置信拒答、非叶片/越界拒答；不是 LoRA 结果或专业诊断系统 |
| Choice / few-shot choice prompt comparison | `src/plantdisease/vlm/baseline.py`、`scripts/run_vlm_baseline.py`、`tests/vlm/test_baseline.py`、`reports/week6_vlm_choice_prompt_scaffold.md`、`reports/week6_vlm_prompt_compare.md` | 已验证闭集选项 prompt、train-only few-shot 示例和选项字母解析；真实 Qwen choice 与 few-shot choice 均为 11/15，condition 仍为 1/5，风险词标记为 0 |

任何简历或公开材料只能引用“已验证”且与真实实验范围一致的条目。

## Week 7

| 证据 | 路径或生成命令 | 状态 |
| --- | --- | --- |
| Week 7 展示材料启动记录 | `reports/week7_showcase_kickoff.md` | 已开始，记录 Week7 范围、顺序和边界 |
| Week 7 Apple 展示设计规范（evidence） | `docs/superpowers/specs/2026-07-13-week7-apple-showcase-design.md` | 已批准，锁定 Apple Hybrid Nature 视觉方向、事实边界与验收条件 |
| Week 7 Apple 实施计划（evidence） | `docs/superpowers/plans/2026-07-13-week7-apple-showcase.md` | 已执行，记录 README、媒体、架构、PPT 与 QA 的分步交付 |
| Week 7 证据映射 | `docs/week7_evidence_map.md` | 已建立，规定 README/博客/PPT 可用事实、证据路径和禁止夸大表述 |
| Week 7 结果快照 | `docs/week7_results_snapshot.md` | 已建立，集中记录 Week 2–6 可公开引用指标、证据路径和限制 |
| Week 7 展示架构图 | `docs/week7_showcase_architecture.md` | 已建立，Mermaid 图展示数据、训练、评估、解释、Demo 和 VLM 依赖关系 |
| Week 7 Apple 架构 PNG（derived media） | `docs/media/week7_apple_architecture.png` | 已生成，分类器为主线、Qwen3-VL 为探索分支 |
| Week 7 Demo/图表素材清单 | `docs/week7_demo_media_inventory.md` | 已建立，列出 README/博客/PPT 可用图表、截图和 caption 边界 |
| Week 7 Apple Demo poster（derived media） | `docs/media/week7_apple_demo_poster.png` | 已生成，来自真实本地 Streamlit 固定合成样例流程 |
| Week 7 Apple Demo GIF（derived media） | `docs/media/week7_apple_demo.gif` | 已生成，展示输入、Top-5、Grad-CAM 与安全边界 |
| Week 7 Apple Demo MP4（derived media） | `docs/media/week7_apple_demo.mp4` | 已生成，展示真实本地 Streamlit 视口序列 |
| README 首屏展示入口 | `README.md` | 已重构首屏：项目定位、结果快照、限制和 Week7 展示材料入口 |
| Week 7 中文技术博客 | `docs/blog/week7_technical_blog_zh.md` | 已完成初稿，覆盖背景、数据、Benchmark、消融、解释、部署、VLM、局限和复现入口 |
| Week 7 PPT 大纲与讲稿 | `docs/presentation/week7_ppt_outline.md` | 已完成 12 页 PPT 大纲、5 分钟讲稿和 10 分钟讲稿 |
| Week 7 Apple 最终演示文稿（presentation） | `docs/presentation/week7_apple_showcase_deck.pptx` | 已生成 12 页 Apple Hybrid Nature 展示稿与讲稿备注 |
| Week 7 Apple 展示 QA 报告（evidence） | `reports/week7_apple_showcase.md` | 已记录演示媒体、架构图、PPT 渲染与逐页 QA 结果及限制 |
| Week 7 公开发布检查 | `reports/week7_public_release_check.md` | 已扫描 tracked 内容中的密钥、个人路径、Notebook 输出、缓存目录、大文件、许可证/模型许可表述和无法核验/夸大声明；需在最终发布准备阶段重新运行扫描 |

## Week 8

| 证据 | 路径或生成命令 | 状态 |
| --- | --- | --- |
| 本地 release candidate manifest | `reports/release/week8_rc1_manifest.json` | `week8-rc1` 的当前源码、环境、锁文件、checkpoint 与 Git 跟踪交付物哈希已记录；运行通道明确为 `not_run`，未创建或发布远程 release |
| Claim 与链接账本 | `configs/week8_claims.yaml`、`reports/release/week8_claim_evidence.json` | 11 个数字/运行主张、4 个边界主张与仓库内链接通过审计 |
| 干净环境复现报告 | `reports/week8_reproducibility.md` | 仓库外锁定环境通过 226 tests、Ruff、ty、claim/link audit、synthetic smoke、package build 与 CLI help |
| 历史冻结本地证据与 Apple container | `reports/week8_reproducibility.md` | 已记录冻结 checkpoint 指标重算、Top-5/MPS Demo/24 样本 Grad-CAM，以及 linux/arm64 image/health probe；当前交付 manifest 不继承这些运行状态 |
| React Liquid Glass Demo 与浏览器 QA | `frontend/`、`reports/figures/week8_react_demo_desktop.png`、`reports/week8_react_demo_qa.md` | 用户图片是 no verified ground truth 的 out-of-domain 田间样例；一次 38 类推理先按作物聚合，再在选中作物内排序条件，避免跨作物同名病害混列。当前源码采用顶部上传摄影卡、分析成功后移动到下方完整 Classifier/Management guidance、无结果卡内部纵向滚动的流程，并以 `scripts/export_logo_paths.py` 将用户 Desmos Bézier 内部路径与叶片融合成项目 Logo。既有 1280×720 与 390×844 QA 仅为历史证据；新布局按用户要求未重跑浏览器 QA，不新增几何通过声明。MPS 结果仅为 prediction |
| React QA 锁定值 | `reports/week8_react_demo_qa.md` | 田间图像 SHA-256 `0364ff44229c70666216343057f9ae77d82438a7f842b30af1ffabb786061a7e`；分类器 prediction `0.870144`；本地运行时 `mlx-community/Qwen3-VL-4B-Instruct-4bit`；图像仍标注 no verified ground truth 与 out-of-domain，模型保持 no automatic download |
| 独立作物层级 Demo | `scripts/train_crop_classifier.py`、`src/plantdisease/training/crop.py`、`reports/week8_hierarchical_crop_qa.md` | 14 类 MobileNetV2 作物头使用按作物均衡抽样与官方 test 子集；本地 test Accuracy `0.977121` / Macro F1 `0.977101`。外部多叶葡萄图未通过作物门控，因此病名、Grad-CAM 与管理建议被拒绝，不将期望标签伪装成模型真值 |
| 最终实验报告 | `reports/final_experiment_report.md` | 汇总 Benchmark、消融、错误与校准、解释、部署、VLM、局限和后续路线 |
| 模型卡与数据卡 | `reports/model_card.md`、`reports/data_card.md` | 预期/排除用途、数据泄漏、偏差、田间泛化与安全边界已记录 |
| 最终双语论文 | `paper/zh/main.tex`、`paper/en/main.tex`、`paper/out/plantdisease_ai_zh.pdf`、`paper/out/plantdisease_ai_en.pdf` | 中英文各 12 页 A4；共享证据宏和 13 节结构审计通过 |
| 双语论文审计 | `reports/release/week8_paper_audit.json` | 中文/英文结构与共享 claim macro 使用通过机器审计 |
| 20 页研究答辩 PPTX | `docs/presentation/plantdisease_ai_week8_research_defense.pptx` | 20 页、20 份讲者备注、8 个 Morph；渲染与溢出测试通过 |
| 原生 Keynote 答辩稿 | `docs/presentation/plantdisease_ai_week8_research_defense.key` | Keynote 只读核验 20 页、8 个点击触发 0.9 秒 Magic Move |
| 答辩动画图与 QA | `docs/presentation/week8_research_defense_animation_map.md`、`reports/week8_presentation_qa.md` | 对象配对、转场、视觉、内容和 PowerPoint 兼容边界已记录 |
| 简历证据映射 | `docs/resume/week8_resume_evidence.md` | 3 条可用 bullet 均链接真实证据并保留 official split / single-seed 限制 |
| 导师沟通摘要 | `docs/mentor/week8_mentor_summary.md` | 研究问题、个人贡献、负结果、局限与下一实验已整理 |
| 发布检查清单 | `docs/release/week8_release_checklist.md` | 本地门禁通过；multi-seed、实体隔离、田间验证、完整人工 VQA 审计等明确未完成 |

## Post-Week 8 experimental research

| 证据 | 路径或生成命令 | 状态 |
| --- | --- | --- |
| OpenPlant-H 研究协议 | `docs/research/open_world_hierarchical_plant_research.md`、`configs/openworld_research.yaml` | 已建立；明确可扩展目录与 unknown 拒识，不声称通用植物识别 |
| 开放世界 manifest | `src/plantdisease/openworld/manifest.py`、`configs/openworld_manifest.example.jsonl` | 已实现；来源/许可/实体分组/OOD split 可审计 |
| 冻结特征与多原型索引 | `src/plantdisease/openworld/encoder.py`、`src/plantdisease/openworld/index.py`、`src/plantdisease/openworld/cli.py` | 合成验证；尚无真实数据指标 |
| 植物优先病害路由 | `src/plantdisease/openworld/condition.py`、`src/plantdisease/openworld/router.py`、`tests/openworld/test_router.py` | 合成验证；未知植物不会调用病害模型 |
| OpenPlant-H 验证记录 | `reports/openworld_research_scaffold.md` | 10 个定向测试与 Ruff 通过；真实数据 pilot 未开始 |
| Pl@ntNet / PlantWild / PlantSeg pilot | 见研究协议的 Milestones | 未开始；没有下载数据或训练结果 |
