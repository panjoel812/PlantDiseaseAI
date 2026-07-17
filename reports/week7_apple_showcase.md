# Week 7 Apple Showcase Build Report

## PowerPoint artifact and reproducibility

The final editable presentation is
`docs/presentation/week7_apple_showcase_deck.pptx`. It contains 12 slides and
speaker notes on all 12 slides. The notes include both 5-minute and 10-minute
talk-track content; timing scaffolds are not visible on the slide canvases.

The canonical builder is `scripts/build_week7_apple_showcase.mjs`. It uses the
bundled `@oai/artifact-tool` version `2.8.22` from an environment-temporary
presentation workspace; the package is not vendored into this repository. The
same build exports slide 2 as the standalone architecture visual
`docs/media/week7_apple_architecture.png`.

### Build inputs

- `docs/media/week7_apple_demo_poster.png` — verified synthetic-input Top-5 and
  Grad-CAM poster used on slides 1 and 8
- `outputs/plantvillage/benchmarks/week2_accuracy_efficiency_pareto.png` — Week
  2 model trade-off figure used on slide 4
- `reports/figures/week3_validation_macro_f1_curves.png` — Week 3 ablation curve
  used on slide 5
- `reports/figures/week4_baseline_vs_final_gradcam.png` — fixed-sample comparison
  used on slide 6
- `reports/figures/week4_reliability_diagram.png` — calibration evidence used on
  slide 7

All evidence footers in the deck use repository-relative paths. The build does
not embed a personal absolute path in audience-facing content.

### Structural and rendered QA

The environment-temporary QA workspace retains the following evidence relative
to its presentation `tmp/` directory:

- `qa/slide-01.png` through `qa/slide-12.png`
- `qa/slide-01.layout.json` through `qa/slide-12.layout.json`
- `qa/deck.inspect.ndjson`
- `qa/deck-montage.webp`
- `qa/contact.png`
- `week7_apple_showcase_deck/slide-1.png` through
  `week7_apple_showcase_deck/slide-12.png` from LibreOffice rendering

Fresh structural inspection of the final PPTX reports no slide-canvas overflow.
Artifact-tool inspection reports 12 slide records and 12 notes records and
contains every locked claim: `227`, `0.9953`, `0.9941`, `0.0965`, `0.3348`,
`0.0140`, `129.8`, `11/15`, `1/5`, `Exploratory`, and the non-causal Grad-CAM
boundary. LibreOffice rendered exactly 12 slide PNGs.

The canonical builder also passes an exact native-color audit: extracting and
sorting every six-digit hexadecimal token returns only the approved eight-color
system (`#F5F5F7`, `#050608`, `#1D1D1F`, `#6E6E73`, `#0071E3`, `#30D158`,
`#FF9F0A`, and `#FF453A`). Embedded source figures retain their original image
colors and are outside this native PowerPoint token check.

The artifact-tool API call
`presentation.export({ montage: true })` produced only one 1280 x 720 frame in
`qa/deck-montage.webp` in this runtime. This is retained as a tool limitation,
not treated as a complete overview. The bundled `create_montage.py` was applied
to the 12 per-slide PNGs to produce the verified full contact sheet
`qa/contact.png`.

### Final per-slide repair and QA summary

| Slide | Final repair or QA disposition |
| --- | --- |
| 1 | Repaired the hero poster treatment and confirmed readable dark-theme contrast and the closed-set boundary. |
| 2 | Repaired architecture labels; connectors remain behind nodes and `Exploratory` is visible on the VLM stage. |
| 3 | Confirmed the `227` caveat, safe interpretation, and field-generalization boundary remain visually separated. |
| 4 | Confirmed the ResNet50/MobileNetV2 callouts and Pareto figure are readable at full size. |
| 5 | Corrected the Week 3 evidence footer and confirmed both selected-model metrics remain unobstructed. |
| 6 | Repaired the Grad-CAM comparison crop/readability and kept the 24-sample, relevance-not-causality boundary prominent. |
| 7 | Removed metric/layout overlap and confirmed the reliability figure plus ECE/MCE/Brier labels remain readable. |
| 8 | Confirmed the product poster crop, Top-5/Grad-CAM labels, and one-sample `129.8 ms` qualifier on the dark canvas. |
| 9 | Confirmed all four prompt results and the condition-best `1/5` callout without label collisions. |
| 10 | Confirmed the four assistant actions, refusal tags, and safety wording align without overlap. |
| 11 | Confirmed verified, smoke-tested, and pending columns remain distinct and include the unfinished items. |
| 12 | Confirmed the closing hierarchy, Week 8 handoff, and evidence footer at full size. |

The intentional visual decisions are a dark hero/product/closing sequence,
flat evidence-led compositions on the light slides, native PowerPoint shapes
only for the simple architecture/status visuals, and source figures kept as
evidence rather than redrawn. Speaker-note timing guidance is deliberately kept
off the audience-facing slide canvases.

## Media capture and assembly

The Week 7 showcase sequence is complete. It is an engineering demonstration
of the existing classifier-first serving layer, not field diagnosis evidence.
It does not change inference behavior or add a performance claim.

### Provenance

- app: `app/streamlit_app.py`
- checkpoint: `outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/checkpoint.pt`
- input: `app/examples/synthetic_leaf.png`, labeled in the UI as a fixed
  synthetic engineering smoke input
- actual capture device: `mps`; no CPU fallback was used
- capture viewport: 1440 x 900
- ignored source frames:
  `outputs/plantvillage/week7_showcase/apple_demo_frames/01_hero.png` through
  `05_safety.png`

The five source frames were opened at full size. The hero and input states are
complete; the prediction state shows the actual `resnet50` model and sorted
Top-5 values; the Grad-CAM state shows both heatmap and overlay; and the final
state shows the educational, non-diagnostic safety statement. No loading
skeleton, browser chrome, username, extension, or personal absolute path is
visible.

### Validated outputs

| Asset | Measured result |
| --- | --- |
| `docs/media/week7_apple_demo.mp4` | H.264, yuv420p, 1440 x 900, 30 fps, 8.000 s, silent, 469,831 bytes |
| `docs/media/week7_apple_demo.gif` | GIF, 1280 x 800, 12 fps, 8.000 s, 2,004,718 bytes; below 10 MiB |
| `docs/media/week7_apple_demo_poster.png` | PNG, 1440 x 900; actual Top-5/Grad-CAM serving evidence |

The exact capture, FFmpeg assembly, GIF, and poster commands are recorded in
`docs/week7_demo_media_inventory.md`. The MP4 uses restrained 0.25-second
crossfades and an explicit full-to-TV range conversion so the FFmpeg 8 build
remains H.264 4:2:0. The GIF is derived from that MP4. The poster is an exact
copy of the verified `04_gradcam.png` state.

### Caption and safety boundary

Approved caption:

> Fixed synthetic engineering smoke input. Real local Top-5 and Grad-CAM
> relevance output from the frozen PlantVillage closed-set classifier.

This sequence must not be described as real-field validation, professional
crop diagnosis, or evidence of performance on unknown diseases. Grad-CAM is a
relevance visualization, not a causal explanation. PlantVillage's controlled
background and the documented official-split overlap risk remain applicable.

### QA limitations

- The input is synthetic smoke evidence, not a field photograph.
- The displayed prediction is low confidence and the UI says not to treat it
  as a definitive diagnosis.
- The capture validates one local MPS serving path and does not establish
  cross-device latency or field generalization.
- LoRA/QLoRA and manual VQA review are outside this media task and remain
  incomplete as recorded in the Week 7 evidence map.

## Final Week 7 audit

Validation date: 2026-07-15

Branch: `codex/week7-showcase-materials`

Pre-audit HEAD: `a614d49`

Post-remediation tracked-content status: **PASS**

### Fresh verification summary

- Focused Streamlit/serving/E2E suite: `15 passed in 1.09s`.
- Ruff: `All checks passed!`.
- Full suite: `175 passed, 7 warnings in 15.74s`; all seven warnings are the
  previously documented PyTorch `torch.jit.script` deprecation warning.
- MP4: H.264, yuv420p, 1440 × 900, 30 fps, 8.000 seconds, 469,831 bytes.
- GIF: GIF89a, 1280 × 800, 12 fps, 8.000 seconds, 2,004,718 bytes, below 10 MiB.
- Poster: PNG, 1440 × 900, 347,741 bytes.
- PPTX: 12 slide records and 12 notes-slide records; all 12 slides contain both
  5-minute and 10-minute talk tracks. Fresh `slides_test.py` execution reported
  no overflow.
- Visual QA: the prior Task 3 final pass visually inspected all 12 full-size
  LibreOffice renders, with additional full-size contrast checks on slides 1,
  2, 8, and 12. It recorded no missing image, unintended overlap, clipping, or
  broken status encoding.
- Capture device: Apple Silicon `mps`, with no CPU fallback, as recorded during
  the real local Streamlit capture.
- Post-review UI QA: the main-area upload, fixed-example, and primary controls
  now have explicit high-contrast desktop/mobile styles. The ink/paper primary
  button pair measures 18.62:1; the blue keyboard focus ring measures 4.31:1
  against both paper and ink. A 1440 × 900 and 390 × 844 Browser-plugin pass
  found no relevant console error or horizontal mobile overflow; fixed-example
  MPS inference, Top-5, and Grad-CAM completed.
- Post-review architecture QA: the classifier main line now ends at `Serve`;
  the amber `VLM · Exploratory` node is a dashed secondary branch from bounded
  serving context. The regenerated slide 2 and architecture PNG passed
  full-size visual and structural checks.
- Tracked-path hygiene: the internal implementation plan now uses portable
  environment variables, repository-relative paths, and a runtime temporary
  root. The strict tracked-file scan produced no output.

The detailed commands and tracked-content scans are in
`reports/week7_public_release_check.md`.

### Week 8 handoff and limits

The Week 7 presentation layer, real local MPS demo media, editable 12-slide
deck, speaker notes, architecture visual, README, blog, artifact index, and QA
records now exist. Week 8 does not require a new major showcase feature.

Week 8 must still run the quick start from a genuinely clean environment,
freeze and reproduce a release candidate, audit data/model cards and resume
claims, and complete final release review before a public push. The path
remediation and scans were performed from pre-audit HEAD `a614d49` with the
audit draft intentionally dirty; they are not a clean-environment validation.
This local audit did not publish anything and does not establish field
reliability, unknown-disease coverage, completed manual VQA review, or
LoRA/QLoRA results.
