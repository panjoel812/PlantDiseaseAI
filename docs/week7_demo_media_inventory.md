# Week 7 Demo and Figure Inventory

This inventory separates the new Apple Hybrid Nature demo media from the
existing research figures. It does not create new performance claims.

## Apple showcase demo media

The sequence was captured from the local Streamlit app after a real inference
run with the frozen Week 3 checkpoint and the fixed synthetic engineering smoke
input. The serving device shown and used during capture was `mps`; no CPU
fallback was needed.

Capture inputs:

- checkpoint: `outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/checkpoint.pt`
- example: `app/examples/synthetic_leaf.png`
- viewport: 1440 x 900
- Top-K: 5
- capture directory: `outputs/plantvillage/week7_showcase/apple_demo_frames/`

| Frame | Evidence shown | Full-size visual QA |
| --- | --- | --- |
| `01_hero.png` | Research-demo hero and PlantVillage closed-set boundary | Complete; no loading skeleton or personal path |
| `02_input.png` | Fixed-example control and synthetic-input caption | Complete; fixed synthetic status visible |
| `03_top5.png` | Actual `resnet50` result and sorted Top-5 probabilities | Complete; model, values, low-confidence and closed-set warnings visible |
| `04_gradcam.png` | Grad-CAM heatmap, overlay, checkpoint evidence, and safety statement | Complete; both relevance views visible |
| `05_safety.png` | Educational and non-diagnostic boundary | Complete; warning is unclipped |

| Final asset | Format and measured metadata | Intended use | Caption boundary |
| --- | --- | --- | --- |
| `docs/media/week7_apple_demo.mp4` | H.264, yuv420p, 1440 x 900, 30 fps, 8.00 s, silent | Deck and standalone demo | Fixed synthetic engineering smoke input; engineering demonstration, not field diagnosis evidence. |
| `docs/media/week7_apple_demo.gif` | GIF, 1280 x 800, 12 fps, 8.00 s, 1,957.7 KiB | README-compatible animation | Same boundary as the MP4; do not present as field performance. |
| `docs/media/week7_apple_demo_poster.png` | PNG, 1440 x 900 | README, blog, and deck cover | Actual Top-5/Grad-CAM serving result from the fixed synthetic input. Grad-CAM is relevance visualization, not causal explanation. |

Start command used for the capture session:

```bash
uv run streamlit run app/streamlit_app.py \
  --server.address 127.0.0.1 \
  --server.port 8507 \
  --server.headless true \
  -- \
  --checkpoint outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/checkpoint.pt \
  --device mps \
  --top-k 5
```

Media assembly command. The final range conversion and `-pix_fmt yuv420p`
keep FFmpeg 8 output in broadly compatible 4:2:0 instead of promoting the
crossfade result to 4:4:4.

```bash
ffmpeg -y \
  -loop 1 -t 1.8 -i outputs/plantvillage/week7_showcase/apple_demo_frames/01_hero.png \
  -loop 1 -t 1.8 -i outputs/plantvillage/week7_showcase/apple_demo_frames/02_input.png \
  -loop 1 -t 1.8 -i outputs/plantvillage/week7_showcase/apple_demo_frames/03_top5.png \
  -loop 1 -t 1.8 -i outputs/plantvillage/week7_showcase/apple_demo_frames/04_gradcam.png \
  -loop 1 -t 1.8 -i outputs/plantvillage/week7_showcase/apple_demo_frames/05_safety.png \
  -filter_complex "[0:v]fps=30,format=yuv420p[v0];[1:v]fps=30,format=yuv420p[v1];[2:v]fps=30,format=yuv420p[v2];[3:v]fps=30,format=yuv420p[v3];[4:v]fps=30,format=yuv420p[v4];[v0][v1]xfade=transition=fade:duration=0.25:offset=1.55[x1];[x1][v2]xfade=transition=fade:duration=0.25:offset=3.10[x2];[x2][v3]xfade=transition=fade:duration=0.25:offset=4.65[x3];[x3][v4]xfade=transition=fade:duration=0.25:offset=6.20[xf];[xf]scale=in_range=full:out_range=tv,format=yuv420p[out]" \
  -map "[out]" -t 8 -an -c:v libx264 -crf 20 -preset slow \
  -pix_fmt yuv420p -color_range tv -movflags +faststart \
  docs/media/week7_apple_demo.mp4

ffmpeg -y -i docs/media/week7_apple_demo.mp4 \
  -filter_complex "fps=12,scale=1280:-2:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=128[p];[s1][p]paletteuse=dither=bayer" \
  docs/media/week7_apple_demo.gif

cp outputs/plantvillage/week7_showcase/apple_demo_frames/04_gradcam.png \
  docs/media/week7_apple_demo_poster.png
```

## Existing research figures

| Asset | Path | Suggested use | Caption boundary |
| --- | --- | --- | --- |
| Week 3 validation Macro F1 curves | `reports/figures/week3_validation_macro_f1_curves.png` | Blog/PPT ablation slide | Selected runs only; do not infer multi-seed stability. |
| Week 4 reliability diagram | `reports/figures/week4_reliability_diagram.png` | Calibration slide | Top-label calibration only. |
| Week 4 baseline vs final Grad-CAM comparison | `reports/figures/week4_baseline_vs_final_gradcam.png` | Explainability slide | Qualitative comparison, not causal proof. |
| Week 5 Streamlit screenshot | `reports/figures/week5_streamlit_demo.jpg` | README/PPT demo section | Educational closed-set demo. |
| Week 2 Pareto figure | `outputs/plantvillage/benchmarks/week2_accuracy_efficiency_pareto.png` | Blog/PPT benchmark section | Local output; include hardware/protocol caveat. |
| Week 4 Grad-CAM atlas | `outputs/plantvillage/week4_explainability/gradcam_atlas/` | Demo appendix / slide backup | 24 fixed samples; selected for analysis, not random field data. |
| Week 5 local overlay | `outputs/plantvillage/week5_demo/local_e2e_overlay.png` | Demo appendix | Fixed engineering smoke image only. |
| Week 5 container overlay | `outputs/plantvillage/week5_demo/container_e2e_overlay.png` | Deployment evidence | Fixed engineering smoke image only. |

Do not use these assets to support pesticide advice, unrestricted field
diagnosis, causal Grad-CAM claims, or professional recommendations.
