# Week 7 Results Snapshot

Use this table for README, blog, and PPT drafts. Every number below must stay
linked to a machine-readable output or checked report.

## Classification and engineering results

| Area | Result | Evidence | Public caveat |
| --- | --- | --- | --- |
| Data audit | PlantVillage loaded and audited; official split has `227` overlapping `leaf_id` values across train/test. | `reports/data_audit.md`, `outputs/plantvillage/audit.json` | Do not claim strict entity-level leakage freedom for official split results. |
| Week 2 best accuracy model | ResNet50 official split: Test Accuracy `0.9830`, Macro F1 `0.9743`. | `reports/week2_benchmark_progress.md`, `outputs/plantvillage/baseline_resnet50_seed42/metrics.json` | Single protocol run on official split. |
| Week 2 lightweight candidate | MobileNetV2: `2.27M` params, `0.31G` FLOPs, `644.3 img/s` batch-32 throughput. | `reports/week2_benchmark_progress.md`, `outputs/plantvillage/benchmarks/mobilenet_v2_seed42.json` | Throughput measured on MPS, excludes preprocessing. |
| Week 3 selected classifier | ResNet50 + Label Smoothing + Cosine Scheduler: Test Accuracy `0.9953`, Macro F1 `0.9941`. | `reports/week3_final_model_decision.md`, `outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/metrics.json` | Seed 42 official split result; not field-generalization evidence. |
| Week 4 calibration | Accuracy `0.9953`, top-label ECE `0.0965`, MCE `0.3348`, Brier `0.0140`. | `reports/week4_calibration.md`, `outputs/plantvillage/week4_explainability/calibration.json` | Top-label calibration only, not full multiclass calibration. |
| Week 4 explainability | 24 fixed Grad-CAM samples, error analysis, attention review, baseline/final comparison, and reproducibility check completed. | `reports/week4_stage_report.md`, `reports/week4_consistency_audit.md` | Grad-CAM is relevance visualization, not causal proof. |
| Week 5 local demo | Fixed example Top-5 + Grad-CAM e2e completed locally. | `reports/week5_demo_engineering.md`, `outputs/plantvillage/week5_demo/local_e2e.json` | Demo is educational and closed-set. |
| Week 5 Apple container | CPU-only Apple `container` demo validated; single-image container e2e total time `129.8 ms`. | `reports/week5_demo_engineering.md`, `outputs/plantvillage/week5_demo/container_e2e.json` | Runtime memory is one sample, not a benchmark distribution. |

## VLM exploratory results

| Prompt style | Overall exact match | Plant | Health status | Condition | Risk flags | Evidence |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `original` | `0/15` | `0/5` | `0/5` | `0/5` | `7` | `reports/week6_vlm_prompt_compare.md` |
| `short` | `10/15` | `5/5` | `5/5` | `0/5` | `2` | `reports/week6_vlm_prompt_compare.md` |
| `choice` | `11/15` | `5/5` | `5/5` | `1/5` | `0` | `reports/week6_vlm_prompt_compare.md` |
| `few_shot_choice` | `11/15` | `5/5` | `5/5` | `1/5` | `0` | `reports/week6_vlm_prompt_compare.md` |

Interpretation: closed choices reduced free-form hallucination and risk-word
flags, but did not solve fine-grained disease-condition recognition. This is a
small smoke comparison, not evidence of completed LoRA or field-ready diagnosis.

## Recommended headline metrics

- Final classifier candidate: Test Accuracy `0.9953`, Macro F1 `0.9941`
  under the official split and seed 42.
- Deployment demo: local Streamlit and Apple `container` flows validated with
  fixed-example Top-5 and Grad-CAM inference.
- VLM extension: Qwen3-VL choice prompts reached `11/15` on a 5-image /
  15-question smoke set, but condition recognition remained `1/5`.
