# Apple Editorial Chart Redesign and Slide Mapping

## Goal

Replace the current 24-chart set with a restrained Apple-editorial visual system,
then map one or more generated charts to every slide in
`docs/presentation/plantdisease_ai_complete_bilingual_outline.md`.

The redesign must correct the current semantic and typographic failures rather
than merely recolor the existing SVGs. In particular, the near-complete nested
rings in Chart 11 are removed because they make a before/after comparison harder
to read and create decorative gaps that look like broken circles.

## Scope

- Redesign all 24 existing chart slugs in place.
- Preserve editable SVG and 3200-pixel-wide transparent PNG output.
- Keep the evidence values and chart filenames stable unless a factual correction
  is required.
- Add generated-chart references to all 33 main slides and all 12 appendix slides.
- Do not modify PPT, Keynote, experimental JSON, model artifacts, or frozen metrics.

## Visual Direction: Apple Editorial

The charts are visual components for an already-titled bilingual slide, not
self-contained report pages.

### Typography

- Use `SF Pro Display, SF Pro Text, Helvetica Neue, Arial, sans-serif` fallbacks.
- Display numbers: 96–160 px at the 1600×900 SVG design size, weight 600–700,
  negative optical tracking.
- Primary data labels: 28–36 px, weight 550–650.
- Secondary labels and units: 20–26 px, weight 450–550.
- Remove chart title, subtitle, source line, and long protocol disclaimer from the
  SVG/PNG. Those belong in the slide outline next to the visual.
- Keep only English text that is required to interpret the marks: model names,
  category names, units, axis labels, direct values, and concise legends.

### Color and materials

- Primary ink: `#1D1D1F`; secondary ink: `#6E6E73`; track: `#E8E8ED`.
- Accent blue: `#0A84FF`; mint: `#32D7C4`; violet: `#7D5FFF`;
  coral: `#FF6B5E`; amber: `#FFB340`.
- Use no more than two semantic accent colors in an ordinary chart. A third color
  is allowed only for a real third category.
- Prefer solid fills. Gradients are optional only inside a continuous quantitative
  mark and must never sit behind text.
- Keep the SVG canvas transparent. Do not add cards, dashboard frames, browser
  chrome, glossy effects, shadows, or pseudo-3D.

### Shape rules

- Ban donut charts, progress rings, nested rings, and decorative circular halos
  from the 24-chart set.
- A circle is allowed only as a scatter-plot bubble, a dot-plot endpoint, or a
  legend marker tied to a quantitative axis.
- Use direct labels, aligned baselines, capsule bars, thin rules, and restrained
  arrows.
- Every visual encoding must have a defensible denominator, axis, or category.
  No decorative shape may look like data.
- Do not truncate a quantitative axis unless the visible scale and baseline are
  explicitly marked.

### Composition

- One primary comparison or claim per chart.
- Maintain generous whitespace and a strong left-to-right reading order.
- Use large values before explanatory labels.
- Dense charts 04, 23, and 24 may use 2000-pixel-wide SVG view boxes while still
  exporting to 3200-pixel-wide PNGs.
- All text and marks must remain readable when placed on a white or `#F5F5F7`
  slide background.

## Chart-by-Chart Redesign

| ID | Slug | New visual form | Required on-chart text |
| --- | --- | --- | --- |
| 01 | `project-evidence-snapshot` | Five large figures on one shared baseline; no pills | `5 Models`, `10 Ablations`, `0.9941 Macro F1`, `50 / 10,709 Errors`, `226 Tests` |
| 02 | `dataset-composition` | One large total plus a two-part horizontal composition bar | `54,305 Images`, `43,596 Development`, `10,709 Test`, `38 Classes`, `14 Duplicate Groups` |
| 03 | `split-and-overlap` | Three-part split bar plus a separate coral warning number | Train/validation/test counts, `Seed 42`, `227 Overlapping leaf_id`, `0 Overlapping paths` |
| 04 | `class-distribution` | Two-column aligned dot/bar list | All 38 development counts and concise crop-condition names |
| 05 | `model-accuracy-f1` | Five-row paired dot plot on a visible 94–100% axis | Model names, Accuracy, Macro F1, direct percentages |
| 06 | `model-efficiency-pareto` | Clean bubble scatter with sparse grid and direct labels | FLOPs, throughput, model names; bubble-size legend for parameters |
| 07 | `model-latency` | Five rounded horizontal bars from a visible zero baseline; no endpoint dots | Model names and batch-1 mean milliseconds |
| 08 | `ablation-macro-f1` | Ranked horizontal bars with the final candidate highlighted | Ten ablation names and four-decimal Macro F1 values |
| 09 | `ablation-delta` | Diverging bars centered on a visible zero line | Nine changes in percentage points |
| 10 | `ablation-duration` | Open editorial table with thin rules, no dark card | Run, ablation, duration, best epoch |
| 11 | `final-improvement` | Two before→after comparison rows; no circles | Accuracy `98.30% → 99.53%`, `+1.23 pp`; Macro F1 `97.43% → 99.41%`, `+1.98 pp` |
| 12 | `error-audit` | Oversized `50` plus four aligned supporting metrics | Errors, test images, accuracy, high-confidence errors, threshold, error rate |
| 13 | `top-confusions` | Eight ranked zero-baseline capsule bars | True→predicted class pair and count |
| 14 | `attention-review` | Two segmented horizontal bars with direct category labels | Attention-region and failed-sample error-type counts |
| 15 | `calibration` | Reliability line with identity line and three large side metrics | Confidence, empirical accuracy, ECE, MCE, Brier |
| 16 | `gradcam-reproducibility` | Oversized `24 / 24` with four aligned metadata rows | Exact matches, target layer/mode, max difference, atlas tolerance |
| 17 | `demo-timing-observations` | Two stacked timing bars with totals outside marks | Local CPU and Apple-container CPU components and totals |
| 18 | `vqa-seed-composition` | Four large values plus split and question-type bars | 24 images, 72 questions, three types, leakage flag, 48/9/15 and 24/24/24 |
| 19 | `vlm-prompt-comparison` | Four direct horizontal comparison bars | Prompt name, exact-match count, condition count |
| 20 | `clean-reproducibility` | Oversized `8 / 8` plus a two-column audit checklist | 226 tests, 0 broken links, frozen 7 numerical and 4 boundary claims |
| 21 | `eight-week-evidence-timeline` | One connected W1→W8 path with eight restrained nodes | One action phrase per week |
| 22 | `apple-container-facts` | Horizontal memory gauge plus three large engineering facts | 821.67 MiB / 1 GiB, 80.2%, ~909 MiB image, 4 CPUs, health `OK` |
| 23 | `per-class-f1` | Two-column dot plot on a visible 0.95–1.00 axis | All 38 class F1/support pairs |
| 24 | `full-confusion-matrix` | Square heatmap with compact numbered class key | True/predicted axes, 38 labels, blue diagonal and coral error legend |

## Wording and Evidence Placement

The chart file contains only the minimum English needed to decode the marks.
Every slide reference added to the bilingual outline must also include a short
`Chart context / 图表限定` line when the chart contains any of these results:

- classifier metrics: `Seed 42 · official split · 227 overlapping leaf_id values`;
- timing: `Fixed-example engineering observation; not a latency benchmark`;
- VLM: `5 images / 15 questions smoke study; no completed LoRA/QLoRA`;
- Grad-CAM: `Non-causal relevance visualization`;
- clean audit: `Frozen RC snapshot; the current worktree audit may contain later claims`.

The outline remains bilingual; the generated chart labels remain English only.

## Slide-to-Chart Mapping

Each slide receives a `Generated chart reference / 生成图表参考` block containing
clickable PNG and SVG links. Reuse is intentional when one evidence artifact
supports more than one narrative slide.

### Main deck

| Slide | Primary chart | Secondary chart when useful |
| --- | --- | --- |
| 1 | 01 Project evidence snapshot | — |
| 2 | 01 Project evidence snapshot | 20 Clean reproducibility |
| 3 | 03 Split and overlap | 12 Error audit; 15 Calibration |
| 4 | 21 Eight-week evidence timeline | 01 Project evidence snapshot |
| 5 | 21 Eight-week evidence timeline | — |
| 6 | 02 Dataset composition | 04 Class distribution |
| 7 | 04 Class distribution | 02 Dataset composition |
| 8 | 03 Split and overlap | — |
| 9 | 02 Dataset composition | 18 VQA seed composition |
| 10 | 20 Clean reproducibility | 03 Split and overlap |
| 11 | 05 Model Accuracy and Macro F1 | 07 Model latency |
| 12 | 05 Model Accuracy and Macro F1 | — |
| 13 | 05 Model Accuracy and Macro F1 | 06 Efficiency scatter; 07 Latency |
| 14 | 06 Efficiency scatter | 07 Model latency |
| 15 | 08 Ablation Macro F1 | 10 Ablation runtime |
| 16 | 09 Ablation delta | 08 Ablation Macro F1 |
| 17 | 09 Ablation delta | 10 Ablation runtime |
| 18 | 11 Final improvement | — |
| 19 | 12 Error audit | — |
| 20 | 13 Top confusion pairs | 24 Full confusion matrix |
| 21 | 15 Calibration | — |
| 22 | 14 Attention review | — |
| 23 | 16 Grad-CAM reproducibility | 14 Attention review |
| 24 | 17 Demo timing observations | 20 Clean reproducibility |
| 25 | 12 Error audit | 17 Demo timing observations |
| 26 | 22 Apple container facts | 17 Demo timing observations |
| 27 | 18 VQA seed composition | 21 Eight-week evidence timeline |
| 28 | 19 VLM prompt comparison | — |
| 29 | 19 VLM prompt comparison | — |
| 30 | 20 Clean reproducibility | — |
| 31 | 01 Project evidence snapshot | 20 Clean reproducibility |
| 32 | 03 Split and overlap | 19 VLM prompt comparison; 22 Container facts |
| 33 | 01 Project evidence snapshot | 11 Final improvement |

### Backup appendix

| Appendix | Primary chart | Secondary chart when useful |
| --- | --- | --- |
| A1 | 04 Class distribution | 02 Dataset composition |
| A2 | 02 Dataset composition | 03 Split and overlap; 04 Class distribution |
| A3 | 11 Final improvement | 10 Ablation runtime |
| A4 | 05 Model Accuracy and Macro F1 | 06 Efficiency scatter; 07 Latency |
| A5 | 06 Efficiency scatter | 07 Model latency; 17 Timing observations |
| A6 | 08 Ablation Macro F1 | 09 Delta; 10 Runtime |
| A7 | 23 Per-class F1 | 13 Top confusions; 24 Full matrix |
| A8 | 15 Calibration | 14 Attention review; 16 Reproducibility |
| A9 | 11 Final improvement | 12 Error audit |
| A10 | 19 VLM prompt comparison | 18 VQA seed composition |
| A11 | 20 Clean reproducibility | — |
| A12 | 20 Clean reproducibility | 03 Split and overlap; 19 VLM prompt comparison |

## Outline Editing Contract

- Insert the chart-reference block before each slide's evidence section or before
  the closing divider when the slide has no explicit evidence heading.
- Use repository-relative links from the outline:
  `charts/english-transparent/<slug>.png` and `.svg`.
- Do not remove existing sample images, Grad-CAM images, UI screenshots, videos,
  evidence links, or slide copy. Generated charts supplement those references.
- Update `Visual Asset Master Index` so the redesigned chart pack is listed as
  covering Slides 1–33 and Appendices A1–A12.

## Validation

### Automated

- Generate exactly 24 SVG/PNG pairs.
- Parse every SVG as XML and reject canvas background rectangles.
- Assert no `<circle>`, ring `<path>`, or arc command exists except in Charts 05,
  06, 15, and 23, where dots/bubbles are semantically required.
- Assert Chart 11 contains no circle or arc and includes both before→after values
  and both percentage-point deltas.
- Assert every PNG is 3200 pixels wide and has alpha.
- Reject Chinese characters, missing required direct values, malformed labels,
  text outside the view box, and colors outside the approved palette.
- Assert all 45 outline sections contain at least one generated PNG reference and
  that every referenced PNG/SVG pair exists.
- Run the Week 8 claim/link audit and require zero failures and zero broken links.

### Visual

- Composite every PNG on white and `#F5F5F7` backgrounds.
- Inspect all 24 images at original resolution and in a 4×6 contact sheet.
- Reject overlapping text, clipped labels, repeated chart titles, tiny source text,
  low contrast, decorative circles, misleading scales, dense dashboard layouts,
  or any chart that cannot be understood in five seconds.
- Inspect Chart 11 first as the redesign acceptance sample before accepting the
  rest of the set.

## Deliverables

- Updated `scripts/generate_presentation_charts.mjs`.
- Updated `scripts/validate_presentation_chart_generator.mjs`.
- Replaced 24 SVGs, 24 transparent PNGs, README, and contact sheet under
  `docs/presentation/charts/english-transparent/`.
- Updated `docs/presentation/plantdisease_ai_complete_bilingual_outline.md` with
  45 slide-to-chart reference blocks.
- Updated `reports/week8_chart_asset_qa.md` with the new visual and mapping audit.
