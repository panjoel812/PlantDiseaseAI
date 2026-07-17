# English Transparent Chart Assets Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce the approved 24-chart English SVG/transparent-PNG asset set from repository evidence.

**Architecture:** A single Node.js generator reads frozen JSON evidence, builds SVG strings through reusable chart primitives, writes editable SVG files, and uses bundled `sharp` to rasterize 2× transparent PNGs. The same generator writes an evidence manifest and a white-background QA contact sheet.

**Tech Stack:** Node.js ES modules, repository JSON evidence, SVG, bundled `sharp`.

## Global Constraints

- Preserve transparent output backgrounds.
- Use English labels only.
- Match the approved Imagen style board: oversized numbers, thick rounded segmented rings, short capsule tracks, cobalt/violet/mint/coral accents, and selective black comparison tables.
- Keep gradients inside data marks and never behind text; exclude app/browser chrome, pseudo-3D, dense dashboard cards, and excessive gridlines.
- Keep all result qualifiers visible.
- Do not modify experimental evidence.
- Do not claim timings as benchmarks.

---

### Task 1: Build the chart generator

**Files:**

- Create: `scripts/generate_presentation_charts.mjs`

- [ ] Read the audited dataset, benchmark, ablation, explainability, demo, VLM, and Week 8 JSON files.
- [ ] Add reusable SVG primitives for titles, pills, rounded bars, segmented bars, rings, scatter plots, legends, and footnotes.
- [ ] Implement the 24 chart compositions from the approved design.
- [ ] Write SVG and 2× transparent PNG outputs.
- [ ] Run `node scripts/generate_presentation_charts.mjs`; expect JSON containing `"status":"completed"` and `"chart_count":24`.

### Task 2: Generate assets and evidence manifest

**Files:**

- Create: `docs/presentation/charts/english-transparent/*.svg`
- Create: `docs/presentation/charts/english-transparent/*.png`
- Create: `docs/presentation/charts/english-transparent/README.md`

- [ ] Run the generator with the bundled Node runtime and `sharp` module path.
- [ ] Confirm every expected pair is present.
- [ ] Confirm PNG alpha channels are preserved.
- [ ] Run the metadata verifier and expect 24 SVG/PNG pairs, every PNG `hasAlpha: true`, and width `3200` except intentionally taller assets.

### Task 3: Visual and factual QA

**Files:**

- Verify: `docs/presentation/charts/english-transparent/_qa-contact-sheet.png`
- Create: `reports/week8_chart_asset_qa.md`

- [ ] Inspect the contact sheet and selected full-size charts.
- [ ] Fix clipping, overlap, illegible labels, or misleading scales.
- [ ] Compare chart values to source JSON and reports.
- [ ] Record the asset index, full-size inspection coverage, and evidence checks in the QA report; do not modify PPT, Keynote, or presentation-outline files.
- [ ] Run link and repository claim audits.
- [ ] Inspect `_qa-contact-sheet.png` and each full-size PNG; reject clipped text, malformed English, misleading scales, low contrast, or departure from the approved Imagen style board.
