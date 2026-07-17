# Week 8 Research Defense QA

## Scope

This report audits the 20-slide, Chinese-first research-defense deck for
research-supervisor and research-program review. The narrative moves from the
trustworthiness question through data risk, unified comparison, ablation,
sample-level error and calibration, explainability, engineering evidence, VLM
limits, release reproducibility, and the next research protocol.

## Final artifacts

| Artifact | Size | SHA-256 |
| --- | ---: | --- |
| `docs/presentation/plantdisease_ai_week8_research_defense.pptx` | 1,503,627 bytes | `5cd566918861a70e3c5998ff83ad711b43589eec1097795a2faa4139574f3144` |
| `docs/presentation/plantdisease_ai_week8_research_defense.key` | 1,472,196 bytes | `7f5f2e64b52ad12dc5caeb7e189f3691adf1af1a8c73100111a403eacc9f6dd7` |

## Structural checks

- PowerPoint ZIP integrity: passed; no corrupt entries.
- PowerPoint slide parts: 20.
- PowerPoint speaker-note parts: 20.
- PowerPoint Morph records: eight `p159:morph` elements on source slides 3,
  6, 8, 9, 11, 13, 15, and 17.
- Canvas overflow test: passed with no off-slide content.
- Keynote ZIP integrity: passed; one base slide record plus 19 numbered slide
  IWA records, matching the 20-slide document reported by Keynote.
- Native Keynote inspection: 20 slides; the eight mapped source slides report
  Magic Move, 0.9-second duration, click trigger, and no automatic advance.

## Visual inspection

All 20 PowerPoint slides were rendered and inspected individually at 1600 x
900 pixels. After the final clean-lane count changed to 226, a deterministic
render comparison showed that slides 1--18 and 20 were byte-identical and only
slide 19 changed; the updated slide and a fresh full-deck contact sheet were
inspected again. No title wraps, unresolved placeholders, clipped audience
copy, accidental overlaps, missing images, or off-canvas objects were found.

The black/off-white sequence, blue evidence accent, and amber risk accent are
consistent. Minimum audience-facing text sizes remain legible at full-slide
view. Slides 12 and 14 intentionally crop long machine-generated evidence
headings to emphasize the heatmaps; the audience-facing labels below those
images provide the complete interpretation boundary.

The slide 3 -> 4 keyframe sequence was inspected from start through completion.
The class-scope composition collapses into the `227` risk statement without
flicker or an unrelated intermediate layout. The remaining seven motion pairs
were verified through native transition properties and stable paired-object
names listed in the animation map.

## Content and evidence checks

- The visible and note text contains all locked presentation values: `226`, `227`,
  `0.9830`, `0.9743`, `2.27M`, `0.31G`, `644.3`, `0.9953`, `0.9941`,
  `50/10709`, `0.0965`, `0.3348`, `0.0140`, `129.8`, `11/15`, and `1/5`.
- The final result appears with seed 42, official split, and the 227-overlap
  limitation on slide 10.
- Grad-CAM is labeled non-causal; the target-layer correction is traced to the
  Week 4 reports.
- The `129.8 ms` result is described as a fixed synthetic, single CPU-container
  observation rather than a latency benchmark.
- Qwen3-VL remains a 5-image/15-question smoke exploration; `1/5` condition
  recognition and incomplete LoRA/QLoRA are explicit.
- The Demo is described as educational and not a professional diagnosis.
- The claim and local-link audit passes for the final PPTX and its evidence
  sources.

## Commands and observed results

```text
slides_test.py docs/presentation/plantdisease_ai_week8_research_defense.pptx
=> Test passed. No overflow detected.

unzip -t docs/presentation/plantdisease_ai_week8_research_defense.pptx
=> No errors detected in compressed data.

PowerPoint parts => 20 slides, 20 notes, 8 Morph elements
Keynote inspection => 20 slides, 8 Magic Move transitions at 0.9 s
```

## Compatibility boundary

Keynote 15.3 on this macOS machine is the verified native animation surface.
The PowerPoint file has passed structural, rendering, note, and Morph-metadata
checks, but Microsoft PowerPoint playback was not available locally. This report
does not claim cross-version PowerPoint animation parity.
