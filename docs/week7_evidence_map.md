# Week 7 Evidence Map

This map is the source of truth for README, blog, PPT, demo captions, and future
resume wording. Use only claims with direct evidence paths. Do not copy numbers
from screenshots or memory.

## Core verified claims

| Claim area | Safe wording | Evidence |
| --- | --- | --- |
| Project scope | PlantDiseaseAI is a reproducible PlantVillage image-classification research and demo project with explainability, deployment, and exploratory VLM extensions. | `README.md`, `TASKS.md`, `docs/artifact-index.md` |
| Data audit | PlantVillage was loaded from Hugging Face and audited; official split results must mention the known `227` overlapping `leaf_id` risk. | `reports/data_audit.md`, `outputs/plantvillage/audit.json` |
| Week 2 benchmark | Under the shared official split protocol, ResNet50 was the best accuracy candidate and MobileNetV2 was the default lightweight deployment candidate. | `reports/week2_benchmark_progress.md`, `docs/artifact-index.md` |
| Week 3 final candidate | The Week 3 selected classifier is ResNet50 with Label Smoothing + Cosine Scheduler, seed 42, official split; Test Accuracy `0.9953`, Macro F1 `0.9941`. | `reports/week3_final_model_decision.md`, `reports/week3_ablation_results.md`, `outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/metrics.json` |
| Week 4 explainability | Grad-CAM, error analysis, calibration, attention review, baseline/final comparison, and reproducibility checks were completed; Grad-CAM is correlation evidence, not causal proof. | `reports/week4_stage_report.md`, `reports/week4_consistency_audit.md`, `reports/week4_gradcam_atlas.md`, `reports/week4_error_analysis.md` |
| Week 5 demo | Local Streamlit and Apple container demo flows can run fixed-example Top-5 and Grad-CAM inference. | `reports/week5_demo_engineering.md`, `outputs/plantvillage/week5_demo/local_e2e.json`, `outputs/plantvillage/week5_demo/container_e2e.json` |
| Week 6 VQA | VQA seed data has 24 images / 72 questions, entity split integrity verified, but manual per-entry audit remains pending. | `reports/week6_vqa_datacard.md`, `reports/week6_vqa_manual_audit_template.md` |
| Week 6 Qwen smoke | Qwen3-VL MLX 4-bit smoke comparison used 5 test images / 15 questions: original `0/15`, short `10/15`, choice `11/15`, few-shot choice `11/15`; condition remained `1/5` at best. | `reports/week6_vlm_prompt_compare.md`, `outputs/plantvillage/week6_vlm/vlm_result_analysis_prompt_compare.json` |
| Week 6 assistant | The assistant is a safety-bounded prototype that uses classifier context, source provenance, and refusal rules. | `reports/week6_vlm_assistant.md`, `src/plantdisease/vlm/assistant.py`, `outputs/plantvillage/week6_vlm/vlm_assistant_demo.json` |

## Claims to avoid

- Do not say the official split is strictly leakage-free.
- Do not claim real-field disease diagnosis reliability.
- Do not say Grad-CAM proves causal model reasoning.
- Do not claim LoRA/QLoRA fine-tuning was completed.
- Do not claim VQA manual audit is complete.
- Do not describe the VLM assistant as a professional agricultural agent.
- Do not provide pesticide dosage, chemical treatment, or regulatory advice.

## Recommended public wording

- “Official split results are strong but must be read with the documented
  `leaf_id` overlap limitation.”
- “Grad-CAM is used as a qualitative localization aid, not causal explanation.”
- “The VLM extension is exploratory: closed-choice prompts reduce hallucinated
  disease names, but fine-grained condition recognition remains weak on the
  small smoke set.”
- “The demo is educational and does not replace local plant-health experts.”

## Week 7 content priorities

1. README first screen: problem, verified results, demo, limits.
2. Architecture diagram: data → train/eval → explainability → demo → VLM.
3. Results table: Week 2–6 metrics with evidence links.
4. Demo media inventory: screenshot/GIF/video paths and captions.
5. Chinese blog draft.
6. 10–15 slide PPT outline and speaker notes.
