# Week 8 Research Defense Animation Map

The native Keynote deck is the motion reference. Each mapped source slide uses
click-triggered Magic Move with a duration of 0.9 seconds. The PowerPoint copy
contains object-level Morph transition metadata for the same eight source
slides. Stable object names beginning with `!!` identify the intended paired
objects.

| Group | Source -> target | Stable paired objects | Keynote | PowerPoint |
| --- | --- | --- | --- | --- |
| Scope risk | 3 -> 4 | `!!scope-main`, `!!scope-hero`, `!!scope-title` | Magic Move, 0.9 s, click | Morph by object |
| Models | 6 -> 7 | `!!model-0`, `!!model-2` | Magic Move, 0.9 s, click | Morph by object |
| Ablation baseline | 8 -> 9 | `!!ablation-title`, `!!ablation-axis`, `!!ablation-trace`, `!!ablation-main` | Magic Move, 0.9 s, click | Morph by object |
| Ablation result | 9 -> 10 | `!!ablation-title`, `!!ablation-axis`, `!!ablation-trace`, `!!ablation-main` | Magic Move, 0.9 s, click | Morph by object |
| Errors | 11 -> 12 | `!!errors-main` | Magic Move, 0.9 s, click | Morph by object |
| Explainability | 13 -> 14 | `!!explain-frame`, `!!explain-visual` | Magic Move, 0.9 s, click | Morph by object |
| Demo | 15 -> 16 | `!!demo-title`, `!!demo-hero` | Magic Move, 0.9 s, click | Morph by object |
| VLM boundary | 17 -> 18 | `!!vlm-model`, `!!vlm-branch` | Magic Move, 0.9 s, click | Morph by object |

## Verification

- Keynote opened the final `.key` file as a 20-slide document and reported
  `magic move`, duration `0.899999976158`, and `automatic transition=false`
  for source slides 3, 6, 8, 9, 11, 13, 15, and 17.
- The final `.pptx` contains 20 slide parts, 20 speaker-note parts, and eight
  `p159:morph` elements inside click-advanced transition records.
- A rendered keyframe sequence for slides 3 -> 4 was visually inspected and
  showed the 38-class scope composition resolving into the `227` overlap
  warning without an abrupt layout jump.
- Microsoft PowerPoint playback was not available on this machine. The PPTX
  result is therefore structurally verified and fully rendered, but client-
  specific Morph playback remains a compatibility limitation.

## Files

- Native motion reference:
  `docs/presentation/plantdisease_ai_week8_research_defense.key`
- PowerPoint copy:
  `docs/presentation/plantdisease_ai_week8_research_defense.pptx`
- Locked content and notes:
  `docs/presentation/week8_research_defense_content.json`
- Visual and structural QA:
  `reports/week8_presentation_qa.md`
