# English Transparent Presentation Charts

All assets use English labels, transparent backgrounds, editable SVG, and 2× PNG raster exports. Values are read from PlantDiseaseAI evidence files by `scripts/generate_presentation_charts.mjs`.

## Usage boundaries

- Final classifier results are seed-42 official-split observations with 227 overlapping `leaf_id` values.
- Timing figures are fixed synthetic-input engineering observations, not general benchmarks.
- VLM figures are a 5-image / 15-question smoke study; LoRA/QLoRA was not completed.
- Grad-CAM is non-causal relevance visualization.
- Chart 20 records the frozen Week 8 RC snapshot: 7 numerical claims and 4 boundary claims; the current worktree may contain later claims.

| File | Chart | SVG | PNG | Evidence | Slide use |
| --- | --- | --- | --- | --- | --- |
| 01-project-evidence-snapshot | Project Evidence Snapshot | [SVG](./01-project-evidence-snapshot.svg) | [PNG](./01-project-evidence-snapshot.png) | Sources: final metrics, Week 4 analysis, Week 8 reproducibility audit | Open with the audited evidence footprint. |
| 02-dataset-composition | Dataset Composition | [SVG](./02-dataset-composition.svg) | [PNG](./02-dataset-composition.png) | Source: outputs/plantvillage/audit.json and final split manifest | Introduce dataset scale and label space. |
| 03-split-and-overlap | Reproducible Split, Known Entity Overlap | [SVG](./03-split-and-overlap.svg) | [PNG](./03-split-and-overlap.png) | Sources: final split manifest and reports/data_audit.md | Explain the official split and overlap limitation. |
| 04-class-distribution | Full 38-Class Development Distribution | [SVG](./04-class-distribution.svg) | [PNG](./04-class-distribution.png) | Source: outputs/plantvillage/audit.json | Appendix view of class balance. |
| 05-model-accuracy-f1 | Five-Model Accuracy and Macro F1 | [SVG](./05-model-accuracy-f1.svg) | [PNG](./05-model-accuracy-f1.png) | Source: reports/week2_benchmark_progress.md and model metrics JSON | Compare predictive quality across backbones. |
| 06-model-efficiency-pareto | Model Efficiency Pareto | [SVG](./06-model-efficiency-pareto.svg) | [PNG](./06-model-efficiency-pareto.png) | Source: Week 2 benchmark JSON; MPS, float32, batch-32 throughput | Discuss compute and throughput trade-offs. |
| 07-model-latency | Batch-1 Model Latency | [SVG](./07-model-latency.svg) | [PNG](./07-model-latency.png) | Source: Week 2 benchmark JSON; 10 warm-ups and 50 measured iterations | Report batch-1 engineering latency. |
| 08-ablation-macro-f1 | Controlled Ablation: Test Macro F1 | [SVG](./08-ablation-macro-f1.svg) | [PNG](./08-ablation-macro-f1.png) | Source: Week 3 ablation metrics JSON · seed 42 · official split · 227 overlapping leaf_id values | Show the controlled ablation ranking. |
| 09-ablation-delta | Ablation Delta from Frozen Baseline | [SVG](./09-ablation-delta.svg) | [PNG](./09-ablation-delta.png) | Source: Week 3 ablation metrics JSON · seed 42 · official split · 227 overlapping leaf_id values | Highlight gains and regressions from baseline. |
| 10-ablation-duration | Ablation Runtime and Best Epoch | [SVG](./10-ablation-duration.svg) | [PNG](./10-ablation-duration.png) | Source: Week 3 run manifests | Compare ablation cost and selection epoch. |
| 11-final-improvement | Baseline to Final Candidate | [SVG](./11-final-improvement.svg) | [PNG](./11-final-improvement.png) | Source: Week 3 baseline and final metrics JSON | Present baseline-to-final improvement. |
| 12-error-audit | Test Error Audit | [SVG](./12-error-audit.svg) | [PNG](./12-error-audit.png) | Source: outputs/plantvillage/week4_explainability/error_analysis.json · seed 42 · official split · 227 overlapping leaf_id values | Quantify the final model's residual errors. |
| 13-top-confusions | Top Confusion Pairs | [SVG](./13-top-confusions.svg) | [PNG](./13-top-confusions.png) | Source: Week 4 error-analysis JSON · seed 42 · official split · 227 overlapping leaf_id values | Explain the most frequent confusion pairs. |
| 14-attention-review | Grad-CAM Attention Review | [SVG](./14-attention-review.svg) | [PNG](./14-attention-review.png) | Source: outputs/plantvillage/week4_explainability/attention_review.json · seed 42 · official split · 227 overlapping leaf_id values | Summarize the manual Grad-CAM review. |
| 15-calibration | Confidence Calibration | [SVG](./15-calibration.svg) | [PNG](./15-calibration.png) | Source: outputs/plantvillage/week4_explainability/calibration.json · seed 42 · official split · 227 overlapping leaf_id values | Discuss confidence calibration and uncertainty. |
| 16-gradcam-reproducibility | Grad-CAM Reproducibility | [SVG](./16-gradcam-reproducibility.svg) | [PNG](./16-gradcam-reproducibility.png) | Source: direct heatmap reproducibility JSON and atlas report · seed 42 · official split · 227 overlapping leaf_id values | Document explainability reproducibility. |
| 17-demo-timing-observations | Fixed-Example Timing Observations | [SVG](./17-demo-timing-observations.svg) | [PNG](./17-demo-timing-observations.png) | Sources: Week 5 local and Apple-container E2E JSON | Show bounded local/container observations. |
| 18-vqa-seed-composition | VQA Seed Composition | [SVG](./18-vqa-seed-composition.svg) | [PNG](./18-vqa-seed-composition.png) | Source: outputs/plantvillage/week6_vlm/vqa_seed_summary.json | Introduce the small VQA seed dataset. |
| 19-vlm-prompt-comparison | Qwen3-VL Prompt Comparison | [SVG](./19-vlm-prompt-comparison.svg) | [PNG](./19-vlm-prompt-comparison.png) | Source: Week 6 Qwen3-VL smoke JSON | Compare bounded VLM smoke prompts. |
| 20-clean-reproducibility | Clean Reproducibility Audit | [SVG](./20-clean-reproducibility.svg) | [PNG](./20-clean-reproducibility.png) | Sources: Week 8 clean-repro and claim-evidence JSON | Summarize clean-environment release checks. |
| 21-eight-week-evidence-timeline | Eight-Week Evidence Timeline | [SVG](./21-eight-week-evidence-timeline.svg) | [PNG](./21-eight-week-evidence-timeline.png) | Source: TASKS.md and docs/artifact-index.md | Close with the staged evidence journey. |
| 22-apple-container-facts | Apple Container Engineering Facts | [SVG](./22-apple-container-facts.svg) | [PNG](./22-apple-container-facts.png) | Sources: Week 5 engineering report and Week 8 reproducibility report | Present container engineering facts. |
| 23-per-class-f1 | Per-Class F1 — All 38 Classes | [SVG](./23-per-class-f1.svg) | [PNG](./23-per-class-f1.png) | Source: final selected run metrics.json · seed 42 · official split · 227 overlapping leaf_id values | Appendix view of every class F1 score. |
| 24-full-confusion-matrix | Normalized Confusion Matrix — All 38 Classes | [SVG](./24-full-confusion-matrix.svg) | [PNG](./24-full-confusion-matrix.png) | Source: Week 4 error-analysis JSON · final selected classifier · seed 42 · official split · 227 overlapping leaf_id values | Appendix view of all normalized confusions. |
