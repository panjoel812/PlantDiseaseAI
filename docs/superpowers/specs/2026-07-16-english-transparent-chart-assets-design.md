# English Transparent Chart Assets Design

## Goal

Generate a complete, presentation-ready English chart set for PlantDiseaseAI. Every chart must use repository evidence, export as editable SVG and transparent PNG, and borrow the reference images' launch-event visual language without copying their screen-recording chrome.

## Approved Direction

- Transparent background; no canvas fill.
- Editable SVG plus 2× transparent PNG.
- English labels only.
- 16:9 default canvas, with a taller class-distribution asset where necessary.
- Use the approved Imagen style board as the primary visual reference: oversized numeric anchors, thick three-part rings with rounded gaps, short capsule tracks, direct labels, and compact high-contrast data tables.
- Reference palette: cobalt blue, violet, mint cyan, coral, and soft gray; use black only for selected high-contrast comparison assets.
- Prefer one dominant chart grammar per asset. Avoid generic dashboards, dense card grids, glossy pseudo-3D, excessive gridlines, and app/browser chrome.
- Gradients may appear inside data marks, but never behind text. Keep generous whitespace and crisp vector-like geometry.
- Every result includes its protocol or limitation where omission could mislead.

## Chart Set

1. Project evidence snapshot.
2. Dataset composition.
3. Reproducible split and `leaf_id` overlap.
4. Full 38-class distribution.
5. Five-model Accuracy and Macro F1.
6. Model efficiency Pareto chart.
7. Batch-1 model latency.
8. Ten-run ablation Macro F1.
9. Ablation delta from the frozen baseline.
10. Ablation duration and best epoch.
11. Baseline-to-final improvement.
12. Error audit overview.
13. Top confusion pairs.
14. Grad-CAM attention-review distributions.
15. Reliability diagram and calibration metrics.
16. Grad-CAM reproducibility.
17. Fixed-example local/container timing observations.
18. VQA seed composition.
19. Qwen3-VL prompt comparison.
20. Clean reproducibility audit.
21. Eight-week evidence timeline.
22. Apple container engineering facts.
23. Full 38-class per-class F1 chart.
24. Full normalized 38×38 confusion matrix with an English class index.

## Evidence Rules

- Read values from repository JSON whenever available.
- Keep the selected classifier result attached to `seed 42`, `official split`, and `227 overlapping leaf_id values`.
- Mark fixed-example timing as a single engineering observation, never a benchmark.
- Mark VLM values as a 5-image / 15-question smoke study.
- Describe Grad-CAM as non-causal relevance visualization.
- Do not claim entity isolation, field robustness, completed LoRA/QLoRA, public deployment, or professional diagnosis.

## Output

- Directory: `docs/presentation/charts/english-transparent/`
- One `.svg` and one `.png` per chart.
- PNG width: 3200 pixels for 16:9 assets; transparent alpha preserved.
- `README.md` records purpose, evidence sources, and slide suggestions.
- `_qa-contact-sheet.png` is for local review only and is not a presentation asset.

## Validation

- Check every required output exists and is non-empty.
- Parse every SVG as XML-compatible text and reject background rectangles matching the canvas.
- Inspect PNG metadata and confirm alpha is present.
- Render a contact sheet on white solely for visual QA.
- Compare displayed values against source JSON/report values.
