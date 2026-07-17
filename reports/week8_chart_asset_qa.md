# Week 8 English Transparent Chart Asset QA

## Outcome

The Apple-editorial chart kit passes final visual, factual, and mapping QA:

- 24/24 SVG and 24/24 transparent PNG assets pass generator validation and full-size visual inspection on white and `#F5F5F7`.
- 45/45 outline sections contain the approved generated-chart references; all 88 PNG references have sibling SVG links and resolve locally.
- Chart 11 contains no circles, arcs, rings, old chart-local title, subtitle, or source line.
- The current-worktree Week 8 audit passes 15/15 checks: 11 numerical claims, 4 boundary claims, 0 failed claims, and 0 broken links.

One visual defect was found during the final full-size inspection. In Chart 20, `226` pytest results and `0` broken links read as the combined value `2260` because the two metric columns were too close. The generator now uses a 500-unit column gap, and the validator requires at least 480 units. Chart 20 and the contact sheet were regenerated and re-inspected on both backgrounds.

No PPT or Keynote file was modified by this QA task.

## Inspection method

- Ran Node syntax checks for the generator, both validators, and the outline updater.
- Ran the deterministic generator validator in a fresh temporary directory.
- Ran the 45-section slide-map validator and `git diff --check`.
- Ran the Week 8 claim and local-link audit to `/private/tmp/week8-apple-editorial-chart-claims.json`.
- Flattened all 24 transparent PNGs onto white and `#F5F5F7`, producing 48 temporary composites.
- Opened every composite at original resolution and checked copy, geometry, color, alpha edges, scale, collisions, and five-second comprehension.
- Read all 45 generated outline blocks with the surrounding bilingual copy and evidence headings.

Temporary composites:

- `/private/tmp/week8-apple-editorial-chart-qa-white/`
- `/private/tmp/week8-apple-editorial-chart-qa-f5f5f7/`

## Asset inspection matrix

| # | Asset | Visual | Evidence | QA note |
| --- | --- | --- | --- | --- |
| 01 | Project evidence snapshot | Pass | Pass | Five independent numeric anchors remain legible and bounded; `226` is clearly labeled as tests. |
| 02 | Dataset composition | Pass | Pass | 54,305 total = 43,596 development + 10,709 test; 38 classes and 14 duplicate groups are directly labeled. |
| 03 | Split and overlap | Pass | Pass | 37,058 / 6,538 / 10,709 split, seed 42, 227 overlapping `leaf_id` values, and 0 overlapping paths are distinct. |
| 04 | Class distribution | Pass | Pass | All 38 development-set counts are readable in two aligned columns; the displayed total is 43,596. |
| 05 | Five-model Accuracy and Macro F1 | Pass | Pass | Ten fixed-size quantitative dots and direct values share a visible 94%–100% scale. |
| 06 | Model efficiency Pareto | Pass | Pass | FLOPs, throughput, and parameter-sized bubbles are readable; 5M and 25M legend bubbles use the same radius function as plotted models. |
| 07 | Batch-1 model latency | Pass | Pass | Zero-baseline rounded bars and external values avoid endpoint circles and label collisions. |
| 08 | Ablation Macro F1 | Pass | Pass | All ten seed-42 results are ordered, directly labeled, and share the stated 0.9500–1.0000 scale. |
| 09 | Ablation delta | Pass | Pass | Nine changes are computed from the frozen baseline; coral negatives and mint positives diverge from a visible zero line. |
| 10 | Ablation duration | Pass | Pass | Open ruled comparison table shows ten run IDs, names, durations, and best epochs without card framing. |
| 11 | Baseline to final | Pass | Pass | Accuracy 98.30% → 99.53% (+1.23 pp) and Macro F1 97.43% → 99.41% (+1.98 pp); no rings or circles. |
| 12 | Error audit | Pass | Pass | 10,709 samples, 50 errors, 99.53% accuracy, 2 high-confidence errors, 0.80 threshold, and 0.47% error rate are separated. |
| 13 | Top confusion pairs | Pass | Pass | Eight ordered true → predicted pairs and counts use a zero-baseline comparison grammar. |
| 14 | Grad-CAM attention review | Pass | Pass | Both 24-sample distributions use justified categorical colors plus a neutral remainder; labels do not collide. |
| 15 | Calibration | Pass | Pass | Fixed-size reliability dots, identity line, and 0.0965 ECE / 0.3348 MCE / 0.0140 Brier values remain distinct. |
| 16 | Grad-CAM reproducibility | Pass | Pass | 24/24 exact direct heatmaps, `layer4.2`, predicted target, max absolute difference 0.0, and atlas tolerance ≤ 5/255 are direct labels. |
| 17 | Fixed-example timing | Pass | Pass | Local 41.3 ms and container 129.8 ms totals are separated from their stacked components; the chart is not presented as a benchmark. |
| 18 | VQA seed composition | Pass | Pass | 24 images, 72 questions, 48/9/15 split, three 24-question types, and leakage flag `false` are derived and readable. |
| 19 | Qwen3-VL prompt comparison | Pass | Pass | Four smoke conditions show 0/15, 10/15, 11/15, and 11/15 with condition results 0/5, 0/5, 1/5, and 1/5. |
| 20 | Clean reproducibility | Pass after fix | Pass | Frozen RC values remain 8/8, 226, 0, 7, and 4; increased column spacing prevents `226` and `0` from reading as `2260`. |
| 21 | Eight-week timeline | Pass | Pass | One connected W1→W8 path with restrained ticks replaces card-like stage nodes; all stage labels are readable. |
| 22 | Apple container facts | Pass | Pass | 821.67 MiB / 1 GiB, 80.2%, ~909 MiB, 4 CPUs, and health `OK` remain visually distinct. |
| 23 | Per-class F1 | Pass | Pass | All 38 fixed-size quantitative dots and support values use a shared 0.95–1.00 scale; support sums to 10,709. |
| 24 | Full normalized confusion matrix | Pass | Pass | Complete 38 × 38 matrix, true/predicted axes, 0–37 class index, and correct/error semantics are readable at original size. |

## Editorial grammar and asset checks

The validator confirms the approved Apple-editorial grammar:

- approved colors only: ink, secondary gray, track gray, blue, mint, violet, coral, amber, and white;
- no chart uses more than three accents, and a third accent is allowed only for an explicit categorical reason;
- circles occur only in the quantitative allowlist: Chart 05 (12), Chart 06 (7), Chart 15 (9), and Chart 23 (38);
- all allowed circles are classified as quantitative dots, bubbles, or legends;
- no other chart contains circles, circle-equivalent rounded squares, or SVG arc commands;
- all charts use the SF Pro-first editorial font stack;
- no chart contains the old chart-local title, a source line, a `<title>`, or a `<desc>` block;
- all required direct labels and boundary tokens are present.

Direct asset metadata:

```text
PNG assets=24; SVG assets=24
PNG width=3200 for 24/24
PNG alpha=yes for 24/24
PNG heights: 1800 (21), 1984 (2), 2176 (1)
```

Chart 11 acceptance slice:

```text
circles=0; arcs=0; old title present=false
```

## Outline mapping inspection

All 45 generated blocks were read in context: Slides 1–33 and Appendices A1–A12. Results:

- 45/45 sections mapped;
- 45 start markers and 45 end markers;
- 88 PNG chart references and 88 sibling SVG references;
- 0 duplicate marker blocks;
- 0 missing asset pairs;
- 0 broken chart links;
- generated blocks sit before the first evidence section when one exists and do not interrupt bilingual copy;
- 56 limitation lines are present; an independent chart-to-context registry verifies every minimum required boundary.

Four sections use only descriptive, dataset-composition, or timeline assets and therefore intentionally have no result qualifier: Slides 5, 6, 7, and Appendix A1. Their bilingual `Chart context` heading remains present, matching the approved 45-entry mapping. Chart 01 references now carry the classifier boundary because the snapshot contains Macro F1 and error results. Every mapped classifier, timing, VLM, Grad-CAM, and frozen-clean result carries its required boundary line.

## Verification commands and results

```bash
node --check scripts/generate_presentation_charts.mjs
node --check scripts/validate_presentation_chart_generator.mjs
node --check scripts/update_presentation_chart_map.mjs
node --check scripts/validate_presentation_slide_map.mjs
# all exit 0

NODE_PATH="$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules" \
  node scripts/validate_presentation_chart_generator.mjs
# status=validated; chart_count=24; svg_pairs=24; png_pairs=24;
# all_width_3200=true; all_alpha=true

node scripts/validate_presentation_slide_map.mjs
# 45/45 sections mapped; 0 duplicate marker blocks;
# 0 missing PNG/SVG pairs; 0 broken chart links

PYTHONPATH=src .venv/bin/python scripts/audit_week8_claims.py \
  --config configs/week8_claims.yaml \
  --output /private/tmp/week8-apple-editorial-chart-claims.json \
  --check-links
# status=passed; claims=11; boundaries=4; passed=15; failed=0; broken_links=0

git diff --check
# exit 0
```

The Chart 20 regression guard was verified red/green: it failed with the former 390-unit column gap and passes with the corrected 500-unit gap.

## Frozen RC distinction and limitations

- Chart 20 intentionally visualizes the locked Week 8 RC evidence: 8/8 checks, 226 pytest cases, 0 broken links, 7 numerical claims, and 4 boundary claims. The current dirty worktree contains four later React-demo claims, so the fresh audit reports 11 numerical claims and 4 boundary claims. Chart 20 is a frozen release snapshot, not a live counter.
- Timing charts are fixed synthetic-input engineering observations, not latency distributions or cross-device benchmarks.
- Classifier results use one seed and the official split with 227 overlapping `leaf_id` values; they are not entity-isolated or field-performance evidence.
- VLM results remain a 5-image / 15-question smoke study; they do not establish completed LoRA/QLoRA or professional diagnostic ability.
- Grad-CAM assets visualize non-causal relevance, not biological causality.
- The chart blocks are references for manual presentation assembly; this task did not edit PPT or Keynote files.
