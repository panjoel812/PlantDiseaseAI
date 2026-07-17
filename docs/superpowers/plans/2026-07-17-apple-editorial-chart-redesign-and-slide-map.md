# Apple Editorial Chart Redesign and Slide Map Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the existing 24-chart kit with semantically correct Apple-editorial visuals and add generated PNG/SVG references to every main-deck and appendix page in the bilingual outline.

**Architecture:** Keep one deterministic Node SVG generator as the evidence-to-visual source of truth. Extend its validator to enforce the new shape, copy, palette, alpha, and data contracts; add a separate idempotent outline-mapping script and validator so chart rendering and deck-document editing remain independently testable.

**Tech Stack:** Node.js ES modules, repository JSON evidence, SVG, bundled `sharp`, macOS `sips`, Markdown.

## Global Constraints

- Task 1 is an explicitly approved acceptance slice: only Chart 11 must satisfy
  the final Apple-editorial visual contract at that checkpoint. Task 2 must bring
  all 24 charts into final compliance before later tasks proceed.
- Follow `docs/superpowers/specs/2026-07-17-apple-editorial-chart-redesign-and-slide-map-design.md` exactly.
- Preserve all 24 existing slugs and output 24 editable SVGs plus 24 transparent 3200-pixel-wide PNGs.
- Remove chart title, subtitle, source line, long protocol copy, donuts, rings, nested rings, and decorative circular halos.
- Allow `<circle>` only in Charts 05, 06, 15, and 23 for quantitative dots or bubbles.
- Use only `#1D1D1F`, `#6E6E73`, `#E8E8ED`, `#0A84FF`, `#32D7C4`, `#7D5FFF`, `#FF6B5E`, `#FFB340`, and transparent/white where required for SVG rasterization.
- Keep chart labels English-only and move sources/limitations into the bilingual outline mapping blocks.
- Add at least one generated PNG and SVG reference to all 33 main slides and 12 appendix slides.
- Do not modify PPT, Keynote, experimental JSON, frozen metrics, model artifacts, or unrelated dirty files.

---

### Task 1: Establish the Apple-editorial contract and redesign Chart 11

**Files:**

- Modify: `scripts/validate_presentation_chart_generator.mjs`
- Modify: `scripts/generate_presentation_charts.mjs`
- Regenerate: `docs/presentation/charts/english-transparent/11-final-improvement.svg`
- Regenerate: `docs/presentation/charts/english-transparent/11-final-improvement.png`
- Regenerate: `docs/presentation/charts/english-transparent/_qa-contact-sheet.png`

**Interfaces:**

- Produces `editorialCanvas(body, width, height)` with no `<title>`, `<desc>`, title text, subtitle text, or source line.
- Produces `metricTransitionRow({ y, label, before, after, delta, color })` for honest before→after comparison.
- Keeps `PRESENTATION_CHARTS_OUT` generation behavior and the final `{"status":"completed","chart_count":24}` response.

- [ ] **Step 1: Add failing Chart 11 semantic and copy checks**

Add exact checks to `scripts/validate_presentation_chart_generator.mjs`:

```js
const finalSvg = fs.readFileSync(path.join(OUT, "11-final-improvement.svg"), "utf8");
assert.doesNotMatch(finalSvg, /<circle\b|<title\b|<desc\b|Source:|Baseline to Final Candidate/);
assert.doesNotMatch(finalSvg, /<path\b[^>]*\bd="[^"]*(?:^|[ ,])A[ ,]/);
for (const token of ["ACCURACY", "98.30%", "99.53%", "+1.23 pp", "MACRO F1", "97.43%", "99.41%", "+1.98 pp"]) {
  assert.match(finalSvg, new RegExp(token.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")));
}
```

- [ ] **Step 2: Run the validator and confirm the old nested-ring chart fails**

Run:

```bash
NODE_PATH="$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules" \
  node scripts/validate_presentation_chart_generator.mjs
```

Expected: non-zero exit caused by Chart 11 containing circles/arcs and old title/source copy.

- [ ] **Step 3: Add editorial primitives without breaking the other 23 charts**

In `scripts/generate_presentation_charts.mjs`, add these concrete interfaces alongside the legacy primitives so Task 1 stays independently runnable:

```js
function editorialCanvas(body, width = 1600, height = 900) {
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">${body}</svg>`;
}

function metricTransitionRow({ y, label, before, after, delta, color }) {
  return [
    svgText(90, y, label, 30, 600, E.secondary),
    svgText(90, y + 116, before, 118, 650, E.ink, "start", 'letter-spacing="-3"'),
    svgText(585, y + 105, "→", 74, 500, E.secondary),
    svgText(745, y + 116, after, 118, 650, E.ink, "start", 'letter-spacing="-3"'),
    roundedRect(1250, y + 40, 260, 92, color, 46),
    svgText(1380, y + 104, delta, 38, 650, "#FFFFFF", "middle"),
    line(90, y + 174, 1510, y + 174, E.track, 2),
  ].join("");
}
```

Add a separate `E` palette with keys `ink`, `secondary`, `track`, `blue`,
`mint`, `violet`, `coral`, and `amber` using the exact global-constraint
values. Keep the legacy `C` palette unchanged in Task 1 so regenerating Chart 11
does not restyle the other 23 charts before their validators and layouts migrate.

- [ ] **Step 4: Replace Chart 11 rings with two transition rows**

Render Chart 11 through `editorialCanvas()` using:

```js
metricTransitionRow({ y: 160, label: "ACCURACY", before: "98.30%", after: "99.53%", delta: "+1.23 pp", color: E.blue })
+ metricTransitionRow({ y: 500, label: "MACRO F1", before: "97.43%", after: "99.41%", delta: "+1.98 pp", color: E.mint })
```

The values must still be computed from the baseline and final JSON metrics; the strings above define formatting and expected output, not hardcoded evidence replacements.

- [ ] **Step 5: Regenerate and verify Chart 11**

Run the generator and validator. Expected: `chart_count:24`, Chart 11 has no circle/arc/title/source, and every PNG remains 3200 pixels wide with alpha.

- [ ] **Step 6: Inspect Chart 11 on white and `#F5F5F7`**

Use bundled `sharp` to composite only `11-final-improvement.png` on both backgrounds in `/private/tmp/plantdisease-chart11-redesign-qa/`. Inspect at original resolution and reject any overlap, clipping, tiny label, or weak contrast.

- [ ] **Step 7: Commit Task 1**

Commit only generator, validator, Chart 11 SVG/PNG, and the regenerated contact sheet.

---

### Task 2: Redesign the remaining 23 charts and enforce the full visual grammar

**Files:**

- Modify: `scripts/generate_presentation_charts.mjs`
- Modify: `scripts/validate_presentation_chart_generator.mjs`
- Regenerate: `docs/presentation/charts/english-transparent/*.svg`
- Regenerate: `docs/presentation/charts/english-transparent/*.png`
- Modify: `docs/presentation/charts/english-transparent/README.md`

**Interfaces:**

- Consumes Task 1 `editorialCanvas()` and Apple-editorial palette.
- Produces all 24 visual forms listed in the design spec with no chart-local titles, subtitles, sources, or long qualifiers.
- Produces README evidence and usage boundaries outside the visual files.

- [ ] **Step 1: Add failing global shape, copy, and palette checks**

In the validator, define:

```js
const circleAllowed = new Set([
  "05-model-accuracy-f1",
  "06-model-efficiency-pareto",
  "15-calibration",
  "23-per-class-f1",
]);
const approvedColors = new Set([
  "#1D1D1F", "#6E6E73", "#E8E8ED", "#0A84FF", "#32D7C4",
  "#7D5FFF", "#FF6B5E", "#FFB340", "#FFFFFF",
]);
```

For every SVG, reject `<title>`, `<desc>`, `Source:`, the old chart title, Chinese text, full-canvas fill rectangles, unapproved hex colors, and circles/arcs outside the allowed set. Also assert the minimum direct-value tokens from the chart-by-chart design table.

- [ ] **Step 2: Run the validator and confirm the legacy 23 charts fail**

Expected: failures for old title/source copy, old rings in Charts 12/16/20/22, the dark card in Chart 10, and old palette values.

- [ ] **Step 3: Replace legacy primitives with editorial primitives**

Keep and use these focused helpers:

```js
function capsuleBar(x, y, width, height, fraction, color) {
  const fillWidth = Math.max(0, Math.min(width, width * fraction));
  return roundedRect(x, y, width, height, E.track, height / 2)
    + roundedRect(x, y, fillWidth, height, color, height / 2);
}

function valueLabel(x, y, value, label, color = E.ink) {
  return svgText(x, y, value, 112, 650, color, "start", 'letter-spacing="-3"')
    + svgText(x, y + 46, label.toUpperCase(), 24, 550, E.secondary);
}

function zeroAxisBar({ x0, y, scale, delta, color }) {
  const width = Math.abs(delta) * scale;
  const x = delta < 0 ? x0 - width : x0;
  return roundedRect(x, y, width, 36, color, 18);
}

function openTableRow({ y, cells, accent }) {
  const xs = [90, 250, 980, 1390];
  return roundedRect(90, y - 30, 10, 54, accent, 5)
    + cells.map((cell, index) => svgText(xs[index], y, cell, index === 1 ? 28 : 24, index === 1 ? 600 : 500, E.ink)).join("")
    + line(90, y + 36, 1510, y + 36, E.track, 2);
}

function segmentBar({ id, x, y, width, height, values, colors }) {
  const total = values.reduce((sum, value) => sum + value, 0);
  let cursor = x;
  const segments = values.map((value, index) => {
    const segmentWidth = width * value / total;
    const rect = `<rect x="${cursor}" y="${y}" width="${segmentWidth + 0.5}" height="${height}" fill="${colors[index]}"/>`;
    cursor += segmentWidth;
    return rect;
  }).join("");
  return `<defs><clipPath id="${id}"><rect x="${x}" y="${y}" width="${width}" height="${height}" rx="${height / 2}"/></clipPath></defs><g clip-path="url(#${id})">${segments}</g>`;
}
```

Remove the legacy `C` palette, `segmentedRing`, ring/arc helpers, dark-panel
fills, pale card/pill backgrounds, and unused gradient definitions after every
chart has migrated to `E`.

- [ ] **Step 4: Implement Charts 01–10 exactly as specified**

Use direct large figures for 01–03, paired dots for 05, quantitative scatter for
06, rounded horizontal bars from a visible zero baseline with no endpoint dots
for 07, ranked/diverging bars for 08–09, and an open ruled table for 10. Preserve
source-derived values and visible axes.

- [ ] **Step 5: Implement Charts 12–24 exactly as specified**

Replace the remaining rings with oversized values and aligned facts; retain only quantitative dots in 15 and 23. Chart 20 must label its 7/4 values as the frozen RC snapshot in README, not inside the image. Chart 24 uses square legend swatches, not circular markers.

- [ ] **Step 6: Regenerate and run the full validator**

Expected:

```text
status=validated
chart_count=24
svg_pairs=24
png_pairs=24
all_width_3200=true
all_alpha=true
```

- [ ] **Step 7: Inspect the 4×6 contact sheet and dense charts**

Composite all PNGs on white and `#F5F5F7` in `/private/tmp`. Inspect the contact sheet plus full-size Charts 04, 05, 06, 10, 15, 23, and 24. Fix every overlap, clipped label, unreadable number, misleading scale, or inconsistent baseline before committing.

- [ ] **Step 8: Commit Task 2**

Commit only generator, validator, README, and the 50 chart-directory outputs.

---

### Task 3: Add an idempotent 45-page generated-chart map to the bilingual outline

**Files:**

- Create: `scripts/update_presentation_chart_map.mjs`
- Create: `scripts/validate_presentation_slide_map.mjs`
- Modify: `docs/presentation/plantdisease_ai_complete_bilingual_outline.md`

**Interfaces:**

- `update_presentation_chart_map.mjs` owns a 45-entry mapping keyed by `Slide 1`…`Slide 33` and `Appendix A1`…`Appendix A12`.
- Each injected block is bounded by `<!-- GENERATED-CHART-REFS:START -->` and `<!-- GENERATED-CHART-REFS:END -->` so rerunning replaces rather than duplicates it.
- `validate_presentation_slide_map.mjs` exits non-zero unless all 45 sections contain valid PNG/SVG pairs and the required context line.

- [ ] **Step 1: Write a failing slide-map validator**

Create `scripts/validate_presentation_slide_map.mjs` with exact expected section IDs:

```js
const expected = [
  ...Array.from({ length: 33 }, (_, index) => `Slide ${index + 1}`),
  ...Array.from({ length: 12 }, (_, index) => `Appendix A${index + 1}`),
];
```

Split the outline by `## Slide N｜` and `## Appendix AN｜`. For every section, assert one marker pair, at least one `charts/english-transparent/*.png` reference, a sibling `.svg` reference for the same slug, and that both referenced files exist. Assert exactly 45 start markers and 45 end markers.

- [ ] **Step 2: Run the validator and confirm the current outline fails**

Run `node scripts/validate_presentation_slide_map.mjs`.

Expected: non-zero exit because slide-level generated-chart blocks do not yet exist.

- [ ] **Step 3: Implement the exact mapping table from the design spec**

In `scripts/update_presentation_chart_map.mjs`, encode entries as:

```js
const mapping = {
  "Slide 1": { charts: ["01-project-evidence-snapshot"], contexts: [] },
  "Slide 2": { charts: ["01-project-evidence-snapshot", "20-clean-reproducibility"], contexts: ["classifier", "clean"] },
  "Slide 3": { charts: ["03-split-and-overlap", "12-error-audit", "15-calibration"], contexts: ["classifier"] },
  "Slide 4": { charts: ["21-eight-week-evidence-timeline", "01-project-evidence-snapshot"], contexts: [] },
  "Slide 5": { charts: ["21-eight-week-evidence-timeline"], contexts: [] },
  "Slide 6": { charts: ["02-dataset-composition", "04-class-distribution"], contexts: [] },
  "Slide 7": { charts: ["04-class-distribution", "02-dataset-composition"], contexts: [] },
  "Slide 8": { charts: ["03-split-and-overlap"], contexts: ["classifier"] },
  "Slide 9": { charts: ["02-dataset-composition", "18-vqa-seed-composition"], contexts: ["vlm"] },
  "Slide 10": { charts: ["20-clean-reproducibility", "03-split-and-overlap"], contexts: ["clean", "classifier"] },
  "Slide 11": { charts: ["05-model-accuracy-f1", "07-model-latency"], contexts: ["classifier", "timing"] },
  "Slide 12": { charts: ["05-model-accuracy-f1"], contexts: ["classifier"] },
  "Slide 13": { charts: ["05-model-accuracy-f1", "06-model-efficiency-pareto", "07-model-latency"], contexts: ["classifier", "timing"] },
  "Slide 14": { charts: ["06-model-efficiency-pareto", "07-model-latency"], contexts: ["classifier", "timing"] },
  "Slide 15": { charts: ["08-ablation-macro-f1", "10-ablation-duration"], contexts: ["classifier"] },
  "Slide 16": { charts: ["09-ablation-delta", "08-ablation-macro-f1"], contexts: ["classifier"] },
  "Slide 17": { charts: ["09-ablation-delta", "10-ablation-duration"], contexts: ["classifier"] },
  "Slide 18": { charts: ["11-final-improvement"], contexts: ["classifier"] },
  "Slide 19": { charts: ["12-error-audit"], contexts: ["classifier"] },
  "Slide 20": { charts: ["13-top-confusions", "24-full-confusion-matrix"], contexts: ["classifier"] },
  "Slide 21": { charts: ["15-calibration"], contexts: ["classifier"] },
  "Slide 22": { charts: ["14-attention-review"], contexts: ["classifier", "gradcam"] },
  "Slide 23": { charts: ["16-gradcam-reproducibility", "14-attention-review"], contexts: ["classifier", "gradcam"] },
  "Slide 24": { charts: ["17-demo-timing-observations", "20-clean-reproducibility"], contexts: ["timing", "clean"] },
  "Slide 25": { charts: ["12-error-audit", "17-demo-timing-observations"], contexts: ["classifier", "timing"] },
  "Slide 26": { charts: ["22-apple-container-facts", "17-demo-timing-observations"], contexts: ["timing"] },
  "Slide 27": { charts: ["18-vqa-seed-composition", "21-eight-week-evidence-timeline"], contexts: ["vlm"] },
  "Slide 28": { charts: ["19-vlm-prompt-comparison"], contexts: ["vlm"] },
  "Slide 29": { charts: ["19-vlm-prompt-comparison"], contexts: ["vlm"] },
  "Slide 30": { charts: ["20-clean-reproducibility"], contexts: ["clean"] },
  "Slide 31": { charts: ["01-project-evidence-snapshot", "20-clean-reproducibility"], contexts: ["clean"] },
  "Slide 32": { charts: ["03-split-and-overlap", "19-vlm-prompt-comparison", "22-apple-container-facts"], contexts: ["classifier", "vlm"] },
  "Slide 33": { charts: ["01-project-evidence-snapshot", "11-final-improvement"], contexts: ["classifier"] },
  "Appendix A1": { charts: ["04-class-distribution", "02-dataset-composition"], contexts: [] },
  "Appendix A2": { charts: ["02-dataset-composition", "03-split-and-overlap", "04-class-distribution"], contexts: ["classifier"] },
  "Appendix A3": { charts: ["11-final-improvement", "10-ablation-duration"], contexts: ["classifier"] },
  "Appendix A4": { charts: ["05-model-accuracy-f1", "06-model-efficiency-pareto", "07-model-latency"], contexts: ["classifier", "timing"] },
  "Appendix A5": { charts: ["06-model-efficiency-pareto", "07-model-latency", "17-demo-timing-observations"], contexts: ["timing"] },
  "Appendix A6": { charts: ["08-ablation-macro-f1", "09-ablation-delta", "10-ablation-duration"], contexts: ["classifier"] },
  "Appendix A7": { charts: ["23-per-class-f1", "13-top-confusions", "24-full-confusion-matrix"], contexts: ["classifier"] },
  "Appendix A8": { charts: ["15-calibration", "14-attention-review", "16-gradcam-reproducibility"], contexts: ["classifier", "gradcam"] },
  "Appendix A9": { charts: ["11-final-improvement", "12-error-audit"], contexts: ["classifier"] },
  "Appendix A10": { charts: ["19-vlm-prompt-comparison", "18-vqa-seed-composition"], contexts: ["vlm"] },
  "Appendix A11": { charts: ["20-clean-reproducibility"], contexts: ["clean"] },
  "Appendix A12": { charts: ["20-clean-reproducibility", "03-split-and-overlap", "19-vlm-prompt-comparison"], contexts: ["clean", "classifier", "vlm"] },
};
```

Do not infer mappings from keywords. Copy all 45 approved mappings exactly so future wording changes cannot silently alter references.

- [ ] **Step 4: Render a stable bilingual block**

For each chart slug, render:

```markdown
<!-- GENERATED-CHART-REFS:START -->
**生成图表参考 / Generated chart reference**

- `01-project-evidence-snapshot`: [PNG](charts/english-transparent/01-project-evidence-snapshot.png) · [SVG](charts/english-transparent/01-project-evidence-snapshot.svg)

**图表限定 / Chart context**

- Seed 42 · official split · 227 overlapping `leaf_id` values.
<!-- GENERATED-CHART-REFS:END -->
```

Include only context lines required by the charts mapped to that page. Insert the block immediately before the section's first evidence heading; if none exists, insert it before the next slide heading.

- [ ] **Step 5: Run the updater twice and prove idempotence**

Run:

```bash
node scripts/update_presentation_chart_map.mjs
shasum -a 256 docs/presentation/plantdisease_ai_complete_bilingual_outline.md
node scripts/update_presentation_chart_map.mjs
shasum -a 256 docs/presentation/plantdisease_ai_complete_bilingual_outline.md
```

Expected: the two hashes are identical.

- [ ] **Step 6: Update the Visual Asset Master Index**

Change the chart-kit coverage to `Slides 1–33; Appendices A1–A12` and keep all existing non-generated assets and their slide suggestions.

- [ ] **Step 7: Run the slide-map validator**

Expected: 45/45 sections mapped, 0 duplicate marker blocks, 0 missing PNG/SVG pairs, 0 broken chart links.

- [ ] **Step 8: Commit Task 3**

Commit only the two mapping scripts and the bilingual outline.

---

### Task 4: Complete visual, factual, and release-boundary QA

**Files:**

- Modify: `reports/week8_chart_asset_qa.md`
- Modify only if defects are found: `scripts/generate_presentation_charts.mjs`
- Modify only if defects are found: `scripts/validate_presentation_chart_generator.mjs`
- Modify only if defects are found: `scripts/update_presentation_chart_map.mjs`
- Regenerate only if defects are found: `docs/presentation/charts/english-transparent/`

**Interfaces:**

- Produces a 24-row visual/evidence QA matrix and a 45-section mapping result.
- Preserves the frozen RC-vs-current-worktree distinction for Chart 20.

- [ ] **Step 1: Run fresh automated validation**

Run the chart generator validator, slide-map validator, Node syntax checks, and `git diff --check`. Require zero failures.

- [ ] **Step 2: Run the Week 8 claim and link audit**

Run:

```bash
PYTHONPATH=src .venv/bin/python scripts/audit_week8_claims.py \
  --config configs/week8_claims.yaml \
  --output /private/tmp/week8-apple-editorial-chart-claims.json \
  --check-links
```

Expected: status `passed`, failed `0`, broken links `0`. Record the current claim/boundary counts without replacing Chart 20's frozen RC values.

- [ ] **Step 3: Inspect every chart at full size on two backgrounds**

Generate temporary white and `#F5F5F7` composites for all 24 PNGs. Open every image at original resolution. Record pass/fail for copy, geometry, color, alpha edge quality, scale, label collision, and five-second comprehension.

- [ ] **Step 4: Inspect the outline mapping**

Read all 45 generated blocks in context. Reject a mapping if the chart does not support the page's primary claim, if a context line is missing, or if a generated block disrupts existing bilingual copy/evidence sections.

- [ ] **Step 5: Update the QA report with exact evidence**

Document:

- 24/24 chart status;
- 45/45 outline-section status;
- Chart 11 no-ring acceptance result;
- PNG width/alpha counts;
- palette and circle-allowlist checks;
- claim/boundary/link-audit counts;
- remaining limitations.

- [ ] **Step 6: Re-run all affected validation after any QA fix**

Do not claim completion from the pre-fix run. Regenerate, rerun both validators, rerun the claim/link audit, and reinspect every changed chart.

- [ ] **Step 7: Commit Task 4**

Commit the QA report and only the minimal defect fixes required by this task. Do not stage PPT, Keynote, frozen evidence, or unrelated dirty files.
