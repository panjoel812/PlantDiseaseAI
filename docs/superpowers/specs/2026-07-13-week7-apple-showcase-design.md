# Week 7 Apple Hybrid Nature Showcase Design

**Date:** 2026-07-13

**Status:** Approved design direction

**Audience:** GitHub visitors, research mentors, reviewers, and technical interviewers

**Scope:** Week 7 public-facing showcase materials only; experimental facts and model behavior remain unchanged.

## 1. Objective

Rebuild the Week 7 presentation layer as a coherent, premium, Apple-inspired showcase while preserving the project's research integrity. The result should feel like a polished Keynote narrative rather than a dashboard or consulting report, yet every public metric, limitation, and capability claim must remain traceable to existing evidence.

The project is presented as an auditable PlantVillage classification and demo workflow. It is not presented as an Apple product, an official Apple collaboration, a field-ready crop doctor, or a completed VLM fine-tuning project.

## 2. Approved Visual Direction

The selected direction is **Apple Hybrid Nature**:

- Alternate cinematic near-black hero moments with warm-white evidence slides.
- Use large typography, disciplined whitespace, photographic or evidence-led compositions, and one conclusion per screen.
- Combine restrained Apple blue with a botanical green accent.
- Use translucent or soft-surface cards only for essential callouts, never as the dominant layout system.
- Keep charts and screenshots large enough to read during projection.
- Avoid Apple logos, product names, proprietary marketing language, or any implication of affiliation.

### Design tokens

| Role | Value | Intended use |
| --- | --- | --- |
| Warm white | `#F5F5F7` | Evidence slides and editorial surfaces |
| Near black | `#050608` | Hero and transition slides |
| Graphite | `#1D1D1F` | Primary text on light surfaces |
| Secondary gray | `#6E6E73` | Supporting copy and captions |
| Apple blue | `#0071E3` | Links, selected results, and technical emphasis |
| Botanical green | `#30D158` | Model success and plant-domain emphasis |
| Amber | `#FF9F0A` | Limitations and caution statements |
| System red | `#FF453A` | High-risk or prohibited claims only |

Typography should use the macOS system stack where available, with cross-platform fallbacks. Presentation titles use a display weight and approximately 54–72 pt; slide body text uses 24–30 pt where practical, with 16 pt as the absolute minimum for evidence footnotes.

## 3. Deliverable System

### 3.1 README showcase layer

`README.md` will receive a new first-screen experience while retaining the complete reproducibility content below it:

1. A dark hero with the project name, concise positioning, and an explicit research-demo badge.
2. Three headline proof points: final classifier accuracy, Macro F1, and five-model benchmark scope.
3. A prominent demo poster or GIF linked to the Streamlit and Apple container evidence.
4. A compact evidence-and-limits strip that immediately exposes the official split overlap, Grad-CAM boundary, and exploratory VLM status.
5. Clear paths to architecture, results, blog, deck, and artifact index.

The README must remain readable without animation or external hosting.

### 3.2 Architecture visual

The existing architecture document remains the maintainable source. A new Apple-style presentation asset will depict:

`Data audit -> shared training/evaluation core -> explainability -> serving/demo`

The VLM branch is visually secondary and labeled `Exploratory`. The classifier stays on the primary path so the visual cannot imply that Week 6 is required for the Week 1–5 system.

Target assets:

- `docs/media/week7_apple_architecture.png`
- updated `docs/week7_showcase_architecture.md`

### 3.3 Chinese technical blog

`docs/blog/week7_technical_blog_zh.md` retains its facts and evidence paths but adopts an Apple editorial rhythm:

- a concise cover section and thesis;
- short section leads before technical detail;
- large result callouts;
- evidence and limitation blocks;
- embedded benchmark, ablation, calibration, Grad-CAM, and demo visuals;
- a closing section that separates verified work, pending work, and future research.

The article remains Markdown-first and readable on GitHub.

### 3.4 PowerPoint deck

Create a distinct final deck at:

`docs/presentation/week7_apple_showcase_deck.pptx`

The existing untracked `week7_showcase_deck.pptx` and its renders remain untouched. The new deck contains 12 slides:

1. **Hero — Evidence before diagnosis.** Minimal title, leaf/Grad-CAM visual, and research-demo boundary.
2. **The problem — A demo is easy; an evidence chain is hard.** Show the six-stage workflow.
3. **Data — Strong dataset, documented split risk.** Make the `227 leaf_id` overlap caveat visually unavoidable.
4. **Benchmark — Accuracy and deployability are different objectives.** Show ResNet50 and MobileNetV2 as two defensible choices.
5. **Ablation — The selected classifier won through controlled evidence.** Focus on the final `0.9953` / `0.9941` result and negative-result discipline.
6. **Explainability — Relevance, not causality.** Use the largest practical Grad-CAM comparison.
7. **Calibration — High accuracy still needs confidence auditing.** Feature the reliability diagram and calibration metrics.
8. **Product moment — From image to Top-5 to Grad-CAM.** Use the real demo poster or browser capture and container result.
9. **VLM exploration — Prompt constraints reduced risk, not disease ambiguity.** Compare prompt styles while emphasizing condition `1/5`.
10. **Safety — The assistant knows when to stop.** Use human-readable actions and a restrained refusal narrative.
11. **Evidence ledger — Verified, smoke-tested, and pending.** Make status distinctions explicit.
12. **Closing — Credible AI needs evidence and limits.** Finish with the contribution and Week 8 handoff.

Every slide has speaker notes. Evidence paths belong in notes or compact footnotes. The deck must have no accidental overlap, clipped text, broken words, duplicated footers, or unreadable chart labels.

### 3.5 Demo media

Create a truthful 8–9 second showcase sequence from the real local Streamlit flow:

1. Apple-style research-demo hero.
2. Fixed synthetic smoke input selected.
3. Real inference result and Top-5 list.
4. Original image and Grad-CAM overlay.
5. Educational-use and non-diagnostic safety statement.

Target assets:

- `docs/media/week7_apple_demo.mp4`
- `docs/media/week7_apple_demo.gif`
- `docs/media/week7_apple_demo_poster.png`

Only the browser viewport may appear. The media must not contain usernames, local absolute paths, browser extensions, credentials, or fabricated inference values. The synthetic sample must be labeled as such.

## 4. Evidence and Wording Locks

The redesign may improve visual hierarchy but may not change these facts:

- Week 2 ResNet50: Test Accuracy `0.9830`, Macro F1 `0.9743` under the shared official-split protocol.
- Week 2 MobileNetV2: `2.27M` parameters, `0.31G` FLOPs, `644.3 img/s` batch-32 MPS throughput excluding preprocessing.
- Week 3 selected classifier: ResNet50 + Label Smoothing + Cosine Scheduler, seed 42 official split, Test Accuracy `0.9953`, Macro F1 `0.9941`.
- The official split has `227` overlapping `leaf_id` values across train and test.
- Week 4 uses 24 fixed Grad-CAM samples. Grad-CAM is a relevance visualization, not causal proof.
- Week 5 Apple container `129.8 ms` is a CPU-only, fixed single-example end-to-end observation, not a latency distribution benchmark.
- Week 6 Qwen3-VL comparison uses 5 images and 15 questions. Choice and few-shot choice score `11/15`; condition recognition remains `1/5`.
- LoRA/QLoRA, full manual VQA audit, professional diagnosis, pesticide guidance, and field validation remain incomplete or out of scope.

Any number not present in the evidence map or results snapshot must be verified against a direct report before inclusion. The prior deck's `50 test errors analyzed` claim is excluded unless direct evidence is confirmed during implementation.

## 5. Implementation Boundaries

- Do not change training, evaluation, inference, or VLM behavior merely to improve the showcase.
- A limited Streamlit visual restyle is allowed only when it preserves tested controls, serving behavior, accessibility, and safety copy.
- Reuse existing evidence figures where they remain legible. Reformat or crop them for presentation, but do not edit plotted values.
- Generated decorative imagery must not resemble evidence or imply real field validation.
- Existing untracked deck artifacts are preserved; the new deck uses a distinct filename.
- No external publishing, push, release, or hosted deployment is part of Week 7 completion.

## 6. Validation and Failure Handling

### Content validation

- Cross-check all public numbers against `docs/week7_results_snapshot.md` and direct evidence paths.
- Search final public materials for prohibited or overstated claims.
- Confirm README, blog, architecture, deck, and media captions use the same capability status.

### Presentation validation

- Build the PPTX using the required artifact-tool workflow.
- Render every slide to PNG.
- Inspect every slide at full size, plus a montage for narrative consistency.
- Run slide overflow and overlap checks; fix every unintended issue.
- Confirm speaker notes and evidence paths exist on all evidence-bearing slides.

### Demo validation

- Run the real Streamlit app with the verified checkpoint and fixed example.
- Capture only actual UI states.
- Verify MP4, GIF, and poster dimensions, duration, file size, and playback.
- Confirm the media includes Top-5, Grad-CAM, and the safety boundary.

### Repository validation

- Run affected tests first, followed by `uv run ruff check .` and `uv run pytest -q`.
- Run `git diff --check` and the Week 7 public-release scans.
- Update `TASKS.md`, `README.md`, and `docs/artifact-index.md` only after the corresponding artifacts pass validation.

If the real Streamlit capture cannot be completed locally, the media task remains pending and no synthetic interaction is substituted. If a chart cannot be made projection-readable without altering its meaning, the slide uses a simplified evidence callout and links to the original figure instead.

## 7. Completion Criteria

Week 7 can be marked complete only when:

- the Apple-style README, architecture visual, blog, 12-slide PPTX, speaker notes, GIF/MP4/poster, and artifact index exist;
- the presentation and media pass visual and technical QA;
- all metrics and capability statements remain evidence-traceable;
- the clean-environment quick-start and remaining Week 7 validation items are either verified or explicitly left unchecked with reasons;
- Week 8 can proceed as reproduction, audit, correction, and release preparation without adding another major showcase feature.
