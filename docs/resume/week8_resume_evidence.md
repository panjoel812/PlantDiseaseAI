# Week 8 Resume Evidence

These are candidate bullets, not a claim that the project has been publicly
released. Every number must remain attached to its protocol and limitation.

## Candidate bullet 1 — benchmark and selected model

> Built a reproducible PlantVillage benchmark across MobileNetV2, ResNet18,
> ResNet50, EfficientNet-B0, and EfficientNetV2-S, then selected a ResNet50
> label-smoothing + cosine-schedule candidate that achieved **0.9953 Accuracy /
> 0.9941 Macro F1** on the **seed 42 official split**; explicitly audited and
> disclosed **227 overlapping `leaf_id` values**, so the result is not presented
> as entity-isolated field performance.

| Claim fragment | Direct evidence |
| --- | --- |
| Five-model benchmark | [benchmark report](../../reports/week2_benchmark_progress.md); direct machine evidence is listed below |
| 0.9953 / 0.9941 | [final metrics](../../outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/metrics.json) |
| seed 42 / official split | [run manifest](../../outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/run_manifest.json) |
| 227 overlapping `leaf_id` values | [split audit](../../reports/data_audit.md) |

| Week 2 model | Test metrics | Efficiency benchmark |
| --- | --- | --- |
| MobileNetV2 | [metrics JSON](../../outputs/plantvillage/baseline_mobilenet_v2_best_seed42/metrics.json) | [benchmark JSON](../../outputs/plantvillage/benchmarks/mobilenet_v2_seed42.json) |
| ResNet18 | [metrics JSON](../../outputs/plantvillage/baseline_resnet18_seed42/metrics.json) | [benchmark JSON](../../outputs/plantvillage/benchmarks/resnet18_seed42.json) |
| ResNet50 | [metrics JSON](../../outputs/plantvillage/baseline_resnet50_seed42/metrics.json) | [benchmark JSON](../../outputs/plantvillage/benchmarks/resnet50_seed42.json) |
| EfficientNet-B0 | [metrics JSON](../../outputs/plantvillage/baseline_efficientnet_b0_seed42/metrics.json) | [benchmark JSON](../../outputs/plantvillage/benchmarks/efficientnet_b0_seed42.json) |
| EfficientNetV2-S | [metrics JSON](../../outputs/plantvillage/baseline_efficientnet_v2_s_seed42/metrics.json) | [benchmark JSON](../../outputs/plantvillage/benchmarks/efficientnet_v2_s_seed42.json) |

## Candidate bullet 2 — ablation and failure analysis

> Designed controlled ablations for regularization, loss, scheduling, EMA, and
> mixed-sample augmentation; retained negative results, then audited the selected
> official-split model with **50/10,709 errors**, calibration diagnostics
> (**ECE 0.0965**), and a fixed **24-sample** Grad-CAM atlas, treating Grad-CAM as
> non-causal relevance rather than biological explanation.

| Claim fragment | Direct evidence |
| --- | --- |
| Ablation matrix and negative results | [ablation results](../../reports/week3_ablation_results.md) |
| 50/10,709 errors | [error-analysis JSON](../../outputs/plantvillage/week4_explainability/error_analysis.json) |
| ECE 0.0965 | [calibration JSON](../../outputs/plantvillage/week4_explainability/calibration.json) |
| 24-sample atlas / non-causal boundary | [Week 8 reproducibility report](../../reports/week8_reproducibility.md) and [stage report](../../reports/week4_stage_report.md) |

## Candidate bullet 3 — reproducible serving and bounded VLM exploration

> Engineered Top-5 inference, Grad-CAM, Streamlit, and Apple `container` serving;
> reproduced a clean locked environment with **226 passing tests**, package/CLI
> checks, MPS local evidence, and container health, while bounding a Qwen3-VL
> prompt smoke to **11/15** choice/few-shot exact match and only **1/5** on
> fine-grained condition questions.

| Claim fragment | Direct evidence |
| --- | --- |
| Clean tests/package/CLI | [Week 8 reproducibility report](../../reports/week8_reproducibility.md) |
| Historical MPS and Apple-container health | [Week 8 reproducibility report](../../reports/week8_reproducibility.md) |
| Qwen 11/15 and condition 1/5 | [choice smoke JSON](../../outputs/plantvillage/week6_vlm/qwen3_vl_choice_smoke.json) and [few-shot smoke JSON](../../outputs/plantvillage/week6_vlm/qwen3_vl_few_shot_choice_smoke.json) |

Interface evidence is deliberately kept out of the headline resume metrics. The
React Demo uses the supplied image with SHA-256
`0364ff44229c70666216343057f9ae77d82438a7f842b30af1ffabb786061a7e`, an
**out-of-domain** field example with **no verified ground truth**. Its
`0.870144` top-1 is a classifier **prediction**, not a validated label. The
optional `mlx-community/Qwen3-VL-4B-Instruct-4bit` panel was verified only in
its `ready=false` unavailable state; browser/API requests perform **no automatic download**
([browser QA](../../reports/week8_react_demo_qa.md)).

## Wording guardrails

Do **not** claim any of the following until new evidence exists:

- multi-seed confirmation or statistical significance;
- entity-isolated or leakage-free evaluation;
- real-field robustness, unknown-disease detection, or professional diagnosis;
- completed LoRA/QLoRA fine-tuning or broad VLM reliability;
- public deployment, online users, production traffic, publication, acceptance,
  competition result, patent, or award;
- causal explanation from Grad-CAM;
- the historical **129.8 ms CPU** or Week 8 **246.92 ms MPS** fixed-synthetic
  observation as a latency benchmark
  ([Week 5 E2E](../../outputs/plantvillage/week5_demo/container_e2e.json),
  [Week 8 manifest](../../reports/release/week8_rc1_manifest.json)).
