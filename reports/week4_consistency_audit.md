# Week 4 Consistency Audit

生成时间：2026-07-13

## 审计范围

- 阶段报告：`reports/week4_stage_report.md`
- 机器可读指标：Week 3 final `metrics.json`、Week 4 `error_analysis.json`、`calibration.json`、`attention_review.json`、`baseline_vs_final_gradcam.json`、Grad-CAM 复现性 JSON。
- 图表路径：Week 4 reliability diagram 与 baseline/final 同样本对比图。
- 机器可读审计结果：`outputs/plantvillage/week4_explainability/consistency_audit.json`

## 总结

- 检查项：`20/20` 通过。
- 结论：`PASS`

## 检查明细

| check | status | evidence |
| --- | --- | --- |
| Stage report local evidence paths exist | PASS | 15 paths checked; missing=[] |
| Accuracy matches metrics.json | PASS | 0.9953 from metrics.json |
| Macro F1 matches metrics.json | PASS | 0.9941 from metrics.json |
| Sample count matches metrics/error/calibration | PASS | 10709 samples |
| Error count matches error_analysis.json | PASS | 50 errors |
| Top-label ECE matches calibration.json | PASS | 0.0965 from calibration.json |
| Final experiment ID appears in stage report | PASS | 09_combo_candidate_seed42 / 09_combo_candidate |
| Frozen sample checkpoint matches final checkpoint | PASS | outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/checkpoint.pt |
| Atlas checkpoint matches final checkpoint | PASS | outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/checkpoint.pt |
| Attention review checkpoint matches final checkpoint | PASS | outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/checkpoint.pt |
| Baseline comparison references both checkpoints | PASS | {"frozen_samples": "outputs/plantvillage/week4_explainability/frozen_samples.json", "baseline_checkpoint": "outputs/plantvillage/week3_ablation/00_resnet50_baseline_seed42/checkpoint.pt", "final_checkpoint": "outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/checkpoint.pt", "split_manifest": "outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/split.json"} |
| Target layer is consistently layer4.2 | PASS | frozen/atlas/attention target_layer=layer4.2 |
| Attention review sample count recorded | PASS | 24 reviewed samples |
| Attention region counts recorded | PASS | {"lesion": 14, "mixed": 4, "leaf": 4, "background": 2} |
| Primary error type recorded | PASS | {"not_error": 12, "visual_similarity": 8, "label_question": 2, "low_quality": 1, "background_bias": 1} |
| Baseline/final comparison counts recorded | PASS | {"baseline_correct_count": 4, "final_correct_count": 0, "same_top1_count": 5} |
| Grad-CAM direct reproducibility recorded | PASS | {"sample_count": 24, "exact_heatmap_match_count": 24, "max_abs_diff_overall": 0.0} |
| Grad-CAM atlas PNG tolerance recorded | PASS | {"panel_near_identical_atol_5_count": 24, "panel_max_channel_abs_diff_overall": 5} |
| Week4 figure references exist | PASS | reports/figures/week4_reliability_diagram.png, reports/figures/week4_baseline_vs_final_gradcam.png |
| No stale Week4-open wording remains in stage report | PASS | found=[] |

## 结论边界

该审计只检查报告文本、图表路径、实验 ID 和机器可读结果之间的一致性；不重新训练模型，也不扩大 Week 4 的科学结论范围。
