# Week 7 Apple Hybrid Nature Showcase Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a coherent Apple Hybrid Nature Week 7 showcase consisting of a polished Streamlit presentation layer, truthful demo media, a 12-slide PowerPoint deck, an Apple-style architecture visual, and synchronized README/blog/evidence documentation.

**Architecture:** The verified classifier and existing evidence remain the data source. A small Streamlit theme layer supplies real browser states; those states become the poster/GIF/MP4 used by README, blog, and the deck. The PowerPoint is generated from scratch with `@oai/artifact-tool`, exports the shared architecture PNG, and is validated before documentation and `TASKS.md` are synchronized.

**Tech Stack:** Python 3.12, Streamlit, pytest, Ruff, browser control, FFmpeg, JavaScript ES modules, `@oai/artifact-tool`, LibreOffice/Poppler slide rendering helpers.

## Global Constraints

- Work only on `codex/week7-showcase-materials`; do not push, publish, release, or create a remote PR.
- Preserve the existing untracked `docs/presentation/week7_showcase_deck.pptx`, its inspect file, and rendered directory.
- Use the approved Apple Hybrid Nature palette: `#F5F5F7`, `#050608`, `#1D1D1F`, `#6E6E73`, `#0071E3`, `#30D158`, `#FF9F0A`, and `#FF453A`.
- Do not use Apple logos, imitate official Apple ownership, or imply an Apple collaboration.
- Do not change training, evaluation, inference, classifier, or VLM behavior for visual polish.
- Do not change any verified metric or capability status from `docs/week7_results_snapshot.md` and `docs/week7_evidence_map.md`.
- Label the fixed demo input as synthetic engineering smoke evidence.
- Keep Grad-CAM wording at “relevance visualization,” not causal explanation.
- Keep Qwen3-VL wording at a 5-image / 15-question smoke comparison; LoRA/QLoRA and manual VQA review remain incomplete.
- Use `/usr/bin/trash <absolute-path>` for any recoverable removal; never use permanent deletion commands.

---

## File Structure

### Create

- `docs/media/week7_apple_demo_poster.png` — README, blog, and deck demo cover.
- `docs/media/week7_apple_demo.mp4` — 8-second 1440×900 H.264 showcase.
- `docs/media/week7_apple_demo.gif` — README-compatible 1280-wide animated showcase.
- `docs/media/week7_apple_architecture.png` — rendered Apple-style classifier-first architecture.
- `docs/presentation/week7_apple_showcase_deck.pptx` — final 12-slide deck.
- `scripts/build_week7_apple_showcase.mjs` — reproducible artifact-tool deck generator.
- `reports/week7_apple_showcase.md` — build, source, QA, and limitation record.

### Modify

- `app/streamlit_app.py` — add the Apple Hybrid Nature visual layer and clearer safety framing.
- `tests/test_streamlit_app.py` — lock the visual tokens, research-demo copy, and import behavior.
- `README.md` — replace the current first screen with the shared Apple showcase assets and concise evidence hierarchy.
- `docs/blog/week7_technical_blog_zh.md` — add editorial hierarchy and shared evidence images without changing facts.
- `docs/week7_showcase_architecture.md` — embed the rendered architecture while retaining Mermaid as the maintainable source.
- `docs/week7_demo_media_inventory.md` — record final media paths, commands, dimensions, and caption boundaries.
- `docs/presentation/week7_ppt_outline.md` — point to the rendered deck and keep 5/10-minute speaker notes aligned.
- `docs/artifact-index.md` — index all final Week 7 Apple artifacts.
- `reports/week7_public_release_check.md` — add the post-redesign audit result.
- `TASKS.md` — mark only artifacts that pass their stated validation.

### External scratch only

- `$SCRATCH_ROOT/codex-presentations/${CODEX_THREAD_ID:-manual-week7}/week7-apple-showcase/tmp/week7_apple_showcase.mjs` — runnable copy of the artifact-tool deck source.
- `$SCRATCH_ROOT/codex-presentations/${CODEX_THREAD_ID:-manual-week7}/week7-apple-showcase/tmp/qa/` — rendered slide PNGs, montage, layouts, and inspect output.
- `outputs/plantvillage/week7_showcase/apple_demo_frames/` — local browser captures; remains Git-ignored.

---

### Task 1: Apple Hybrid Nature Streamlit Presentation Layer

**Files:**
- Modify: `tests/test_streamlit_app.py`
- Modify: `app/streamlit_app.py`

**Interfaces:**
- Consumes: existing `InferenceServiceResult`, `DEFAULT_CHECKPOINT`, `DEFAULT_EXAMPLE_IMAGE`, and Streamlit controls.
- Produces: `APPLE_THEME_CSS: str`, `RESEARCH_DEMO_COPY: str`, `SAFETY_BOUNDARY_COPY: str`, `_inject_apple_theme() -> None`, and the same `main()` / `_render_result(result)` behavior used by Week 5.

- [ ] **Step 1: Add failing theme and safety-copy tests**

Extend `tests/test_streamlit_app.py` with assertions that the imported module exposes stable visual and safety contracts:

```python
from types import ModuleType


def _load_streamlit_module() -> ModuleType:
    module_path = Path("app/streamlit_app.py")
    spec = importlib.util.spec_from_file_location("streamlit_app_for_test", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_streamlit_app_exposes_apple_showcase_contract() -> None:
    module = _load_streamlit_module()

    assert "#050608" in module.APPLE_THEME_CSS
    assert "#F5F5F7" in module.APPLE_THEME_CSS
    assert "#30D158" in module.APPLE_THEME_CSS
    assert "Research demo" in module.RESEARCH_DEMO_COPY
    assert "not a professional diagnosis" in module.SAFETY_BOUNDARY_COPY
    assert "synthetic" in module.FIXED_EXAMPLE_COPY.lower()
    assert callable(module._inject_apple_theme)
```

Update the existing import test to call `_load_streamlit_module()` and keep its `main` and checkpoint-name assertions.

- [ ] **Step 2: Run the focused test and confirm the new contract fails**

Run:

```bash
uv run pytest tests/test_streamlit_app.py -q
```

Expected: the existing import test passes and `test_streamlit_app_exposes_apple_showcase_contract` fails because `APPLE_THEME_CSS` is not defined.

- [ ] **Step 3: Add the minimal Apple theme contract**

Add constants and a dedicated injection function near the existing path constants in `app/streamlit_app.py`:

```python
RESEARCH_DEMO_COPY = "Research demo · PlantVillage closed set"
FIXED_EXAMPLE_COPY = "Fixed synthetic engineering smoke input"
SAFETY_BOUNDARY_COPY = (
    "Educational use only — not a professional diagnosis. "
    "Unknown diseases and field images may fail; consult a local plant-health expert."
)

APPLE_THEME_CSS = """
<style>
:root {
  --pda-ink: #050608;
  --pda-paper: #F5F5F7;
  --pda-text: #1D1D1F;
  --pda-muted: #6E6E73;
  --pda-blue: #0071E3;
  --pda-green: #30D158;
  --pda-amber: #FF9F0A;
}
.stApp { background: var(--pda-paper); color: var(--pda-text); }
[data-testid="stHeader"] { background: rgba(245, 245, 247, 0.78); }
.pda-hero { background: var(--pda-ink); border-radius: 32px; padding: 48px 52px; color: white; }
.pda-kicker { color: var(--pda-green); font-weight: 700; letter-spacing: .12em; text-transform: uppercase; }
.pda-hero h1 { color: white; font-size: clamp(3rem, 7vw, 6rem); letter-spacing: -.055em; line-height: .94; }
.pda-hero p { color: #C7C7CC; font-size: 1.18rem; max-width: 760px; }
.pda-safety { border-left: 4px solid var(--pda-amber); padding: 16px 20px; background: white; border-radius: 18px; }
[data-testid="stMetric"] { background: white; border: 1px solid rgba(0, 0, 0, .06); border-radius: 20px; padding: 18px; }
</style>
"""

def _inject_apple_theme() -> None:
    st.markdown(APPLE_THEME_CSS, unsafe_allow_html=True)
```

Call `_inject_apple_theme()` immediately after `st.set_page_config(...)`.

- [ ] **Step 4: Recompose the visible hierarchy without changing inference flow**

Replace the current title/caption with a semantic hero, add a visible synthetic-sample caption beside the fixed-example control, preserve the existing sidebar configuration, and end every result with the safety boundary:

```python
st.markdown(
    f"""
    <section class="pda-hero">
      <div class="pda-kicker">{RESEARCH_DEMO_COPY}</div>
      <h1>Evidence before diagnosis.</h1>
      <p>Top-5 classification, Grad-CAM relevance, and explicit limits from one auditable serving layer.</p>
    </section>
    """,
    unsafe_allow_html=True,
)
st.caption(FIXED_EXAMPLE_COPY)
```

In `_render_result`, add a visible status line above predictions and render `SAFETY_BOUNDARY_COPY` in `.pda-safety`. Keep all current metrics, Top-5 values, knowledge text, warnings, images, and checkpoint evidence.

- [ ] **Step 5: Run focused tests and lint**

Run:

```bash
uv run pytest tests/test_streamlit_app.py tests/serving -q
uv run ruff check app/streamlit_app.py tests/test_streamlit_app.py
```

Expected: all focused tests pass and Ruff reports `All checks passed!`.

- [ ] **Step 6: Commit the tested UI layer**

```bash
git add app/streamlit_app.py tests/test_streamlit_app.py
git commit -m "feat: restyle week7 streamlit showcase"
```

---

### Task 2: Real Demo Capture and Media Assembly

**Files:**
- Create: `docs/media/week7_apple_demo_poster.png`
- Create: `docs/media/week7_apple_demo.mp4`
- Create: `docs/media/week7_apple_demo.gif`
- Modify: `docs/week7_demo_media_inventory.md`
- Create: `reports/week7_apple_showcase.md`

**Interfaces:**
- Consumes: the Task 1 Streamlit page, the verified Week 3 checkpoint, `app/examples/synthetic_leaf.png`, and actual serving results.
- Produces: five browser frames in the ignored output directory and three tracked media assets with truthful captions.

- [ ] **Step 1: Start the verified local demo**

Run the server in a persistent terminal session:

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

Expected: Streamlit reports `URL: http://127.0.0.1:8507` and its health endpoint returns `ok`. If MPS fails during actual inference, restart only the capture run with `--device cpu` and record that fallback in `reports/week7_apple_showcase.md`.

- [ ] **Step 2: Capture five real browser states at 1440×900**

Using the Browser plugin, open `http://127.0.0.1:8507`, set a 1440×900 viewport, and save only the app viewport as:

```text
outputs/plantvillage/week7_showcase/apple_demo_frames/01_hero.png
outputs/plantvillage/week7_showcase/apple_demo_frames/02_input.png
outputs/plantvillage/week7_showcase/apple_demo_frames/03_top5.png
outputs/plantvillage/week7_showcase/apple_demo_frames/04_gradcam.png
outputs/plantvillage/week7_showcase/apple_demo_frames/05_safety.png
```

The sequence must show the initial hero, the selected fixed synthetic example, the actual prediction/Top-5 state, the actual Grad-CAM state, and the educational safety statement. No browser chrome, username, personal path, or extension may appear.

- [ ] **Step 3: Inspect every captured frame**

Open all five PNGs at full size. Confirm that the prediction frame contains the actual model name and values, the Grad-CAM frame contains both heatmap and overlay, and the safety frame contains the non-diagnostic statement. Re-capture any frame with clipped content, loading skeletons, or hidden evidence.

- [ ] **Step 4: Assemble the MP4 with restrained crossfades**

Run from the repository root:

```bash
mkdir -p docs/media
ffmpeg -y \
  -loop 1 -t 1.8 -i outputs/plantvillage/week7_showcase/apple_demo_frames/01_hero.png \
  -loop 1 -t 1.8 -i outputs/plantvillage/week7_showcase/apple_demo_frames/02_input.png \
  -loop 1 -t 1.8 -i outputs/plantvillage/week7_showcase/apple_demo_frames/03_top5.png \
  -loop 1 -t 1.8 -i outputs/plantvillage/week7_showcase/apple_demo_frames/04_gradcam.png \
  -loop 1 -t 1.8 -i outputs/plantvillage/week7_showcase/apple_demo_frames/05_safety.png \
  -filter_complex "[0:v]fps=30,format=yuv420p[v0];[1:v]fps=30,format=yuv420p[v1];[2:v]fps=30,format=yuv420p[v2];[3:v]fps=30,format=yuv420p[v3];[4:v]fps=30,format=yuv420p[v4];[v0][v1]xfade=transition=fade:duration=0.25:offset=1.55[x1];[x1][v2]xfade=transition=fade:duration=0.25:offset=3.10[x2];[x2][v3]xfade=transition=fade:duration=0.25:offset=4.65[x3];[x3][v4]xfade=transition=fade:duration=0.25:offset=6.20[out]" \
  -map "[out]" -t 8 -an -c:v libx264 -crf 20 -preset slow -movflags +faststart \
  docs/media/week7_apple_demo.mp4
```

Expected: an 8-second, silent, 1440×900 H.264 video.

- [ ] **Step 5: Create the README GIF and poster**

```bash
ffmpeg -y -i docs/media/week7_apple_demo.mp4 \
  -filter_complex "fps=12,scale=1280:-2:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=128[p];[s1][p]paletteuse=dither=bayer" \
  docs/media/week7_apple_demo.gif

cp outputs/plantvillage/week7_showcase/apple_demo_frames/04_gradcam.png \
  docs/media/week7_apple_demo_poster.png
```

Expected: a readable GIF under 10 MiB and a 1440×900 poster showing real Top-5/Grad-CAM evidence.

- [ ] **Step 6: Validate media metadata and content**

```bash
ffprobe -v error -show_entries stream=codec_name,width,height,r_frame_rate \
  -show_entries format=duration,size -of json docs/media/week7_apple_demo.mp4
ffprobe -v error -show_entries stream=codec_name,width,height,r_frame_rate \
  -show_entries format=duration,size -of json docs/media/week7_apple_demo.gif
du -h docs/media/week7_apple_demo.*
```

Expected: MP4 duration approximately 8 seconds, video 1440×900 at 30 fps, GIF width 1280 at 12 fps, and GIF size below 10 MiB.

- [ ] **Step 7: Record the media evidence**

Update `docs/week7_demo_media_inventory.md` with the three final paths, capture source, actual device, FFmpeg commands, dimensions, duration, and fixed-synthetic-input caption. Start `reports/week7_apple_showcase.md` with a media section that records the same facts and explicitly says the sequence is an engineering demonstration rather than field diagnosis evidence.

- [ ] **Step 8: Commit the validated media set**

```bash
git add docs/media/week7_apple_demo_poster.png \
  docs/media/week7_apple_demo.mp4 \
  docs/media/week7_apple_demo.gif \
  docs/week7_demo_media_inventory.md \
  reports/week7_apple_showcase.md
git commit -m "docs: add week7 apple demo media"
```

---

### Task 3: Apple Hybrid Nature PowerPoint and Architecture Visual

**Files:**
- Create: `docs/presentation/week7_apple_showcase_deck.pptx`
- Create: `docs/media/week7_apple_architecture.png`
- Create: `scripts/build_week7_apple_showcase.mjs`
- Modify: `docs/presentation/week7_ppt_outline.md`
- Modify: `reports/week7_apple_showcase.md`
- External runnable copy: `$SCRATCH_ROOT/codex-presentations/${CODEX_THREAD_ID:-manual-week7}/week7-apple-showcase/tmp/week7_apple_showcase.mjs`

**Interfaces:**
- Consumes: Week 7 evidence map/results snapshot, existing Week 2–5 figures, Task 2 poster, and the approved design specification.
- Produces: an editable 12-slide PPTX, speaker notes on every slide, slide-level PNG/layout QA, and the architecture PNG exported from slide 2.

- [ ] **Step 1: Initialize the artifact-tool workspace**

Use the bundled Node runtime and external scratch location:

```bash
SKILL_DIR="${PRESENTATIONS_SKILL_DIR:?Set PRESENTATIONS_SKILL_DIR to the presentations skill directory}"
NODE="${NODE_BIN:-node}"
PYTHON="${PYTHON_BIN:?Set PYTHON_BIN to a Python runtime with presentation QA dependencies}"
SCRATCH_ROOT="${TMPDIR:-$("$NODE" -p "require('node:os').tmpdir()")}"
WORKSPACE="$SCRATCH_ROOT/codex-presentations/${CODEX_THREAD_ID:-manual-week7}/week7-apple-showcase"
TMP_DIR="$WORKSPACE/tmp"
mkdir -p "$TMP_DIR/qa" "$TMP_DIR/assets"
"$NODE" "$SKILL_DIR/container_tools/setup_artifact_tool_workspace.mjs" --workspace "$TMP_DIR"
```

Expected: `$TMP_DIR/node_modules/@oai/artifact-tool` resolves successfully.

- [ ] **Step 2: Write the plain JavaScript deck module**

Create `scripts/build_week7_apple_showcase.mjs` using `@oai/artifact-tool`, then copy it to `$TMP_DIR/week7_apple_showcase.mjs` before execution so the prepared workspace resolves the package. The module must:

```javascript
import fs from "node:fs/promises";
import path from "node:path";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const repoRoot = process.cwd();
const qaDir = process.env.QA_DIR;
if (!qaDir) throw new Error("QA_DIR is required");
const finalPptx = `${repoRoot}/docs/presentation/week7_apple_showcase_deck.pptx`;
const architectureOutput = `${repoRoot}/docs/media/week7_apple_architecture.png`;

async function writeBlob(filePath, blob) {
  await fs.mkdir(path.dirname(filePath), { recursive: true });
  await fs.writeFile(filePath, new Uint8Array(await blob.arrayBuffer()));
}

const presentation = Presentation.create({
  slideSize: { width: 1280, height: 720 },
});

const COLORS = {
  paper: "#F5F5F7",
  ink: "#050608",
  text: "#1D1D1F",
  muted: "#6E6E73",
  blue: "#0071E3",
  green: "#30D158",
  amber: "#FF9F0A",
  red: "#FF453A",
};

function addNotes(slide, lines) {
  slide.speakerNotes.textFrame.setText(lines);
  slide.speakerNotes.setVisible(true);
}
```

Use helper functions for title, kicker, compact evidence footer, large metric text, image placement, and byte-backed PNG/JPEG loading. Use native PowerPoint shapes only for the simple architecture and status diagrams; create connectors before their nodes.

After saving the canonical script, prepare the runnable copy:

```bash
cp scripts/build_week7_apple_showcase.mjs "$TMP_DIR/week7_apple_showcase.mjs"
```

- [ ] **Step 3: Implement the exact 12-slide narrative**

Build these audience-facing slides with one primary claim each:

1. `Evidence before diagnosis.` — dark hero, synthetic leaf/Grad-CAM crop, research-demo boundary.
2. `The model is only one link in the evidence chain.` — classifier-first six-stage architecture; VLM labeled `Exploratory`.
3. `The official split is useful—and not entity isolated.` — large `227` overlap caveat and safe interpretation.
4. `Accuracy and deployability need different winners.` — large ResNet50 and MobileNetV2 callouts plus readable Pareto evidence.
5. `Controlled ablation selected the final classifier.` — large `0.9953` and `0.9941`, selected curve, and seed/split qualifier.
6. `Grad-CAM shows relevance, not causality.` — large baseline/final comparison, 24 fixed samples, explicit boundary.
7. `High accuracy still needs confidence auditing.` — reliability diagram with ECE `0.0965`, MCE `0.3348`, Brier `0.0140`.
8. `The same serving layer powers the product moment.` — Task 2 poster, Top-5/Grad-CAM features, container `129.8 ms` fixed-example qualifier.
9. `Prompt constraints reduced format risk, not disease ambiguity.` — original `0/15`, short `10/15`, choice `11/15`, few-shot choice `11/15`, condition best `1/5`.
10. `A safe assistant knows when to stop.` — Educational summary, High-risk refusal, Low-confidence refusal, Out-of-scope refusal.
11. `Verified, smoke-tested, and pending are different states.` — three-column evidence ledger with LoRA/manual audit/field validation pending.
12. `Credible AI needs evidence and limits.` — dark closing synthesis and Week 8 handoff.

Each slide uses 54–72 pt titles where the layout permits, 24–30 pt body text, and at least 16 pt evidence footnotes. All evidence paths are relative repository paths. Add complete 5-minute and 10-minute talk-track content to speaker notes without displaying timing scaffolds on slides.

- [ ] **Step 4: Export QA assets, architecture PNG, inspect data, and PPTX**

The module must export:

```javascript
for (const [index, slide] of presentation.slides.items.entries()) {
  const stem = `slide-${String(index + 1).padStart(2, "0")}`;
  await writeBlob(`${qaDir}/${stem}.png`, await presentation.export({ slide, format: "png", scale: 2 }));
  const layout = await slide.export({ format: "layout" });
  await fs.writeFile(`${qaDir}/${stem}.layout.json`, await layout.text());
}
await writeBlob(`${qaDir}/deck-montage.webp`, await presentation.export({ format: "webp", montage: true, scale: 1 }));
await writeBlob(architectureOutput, await presentation.export({ slide: presentation.slides.items[1], format: "png", scale: 2 }));
const inspect = await presentation.inspect({ kind: "slide,textbox,shape,image,notes,layout", maxChars: 50000 });
await fs.writeFile(`${qaDir}/deck.inspect.ndjson`, inspect.ndjson);
const pptx = await PresentationFile.exportPptx(presentation);
await pptx.save(finalPptx);
```

Run the module with the bundled Node executable. Expected: 12 slide PNGs/layout files, one montage, one inspect file, `docs/media/week7_apple_architecture.png`, and `docs/presentation/week7_apple_showcase_deck.pptx`.

- [ ] **Step 5: Run structural slide validation**

```bash
QA_DIR="$TMP_DIR/qa" "$NODE" "$TMP_DIR/week7_apple_showcase.mjs"
"$PYTHON" \
  "$SKILL_DIR/container_tools/slides_test.py" \
  docs/presentation/week7_apple_showcase_deck.pptx
"$PYTHON" \
  "$SKILL_DIR/container_tools/render_slides.py" \
  docs/presentation/week7_apple_showcase_deck.pptx
```

Expected: exactly 12 rendered slides and no out-of-bounds objects. Treat every overlap warning as a defect until full-size inspection proves it intentional.

- [ ] **Step 6: Inspect every slide visually**

Open all 12 slides individually at full size and inspect the montage for sequence consistency. Fix clipped titles, unreadable chart text, accidental overlaps, excessive card repetition, broken words, duplicate footers, weak contrast, or inconsistent margins. Re-run Steps 4–6 until every slide passes.

- [ ] **Step 7: Verify presentation contents and notes**

```bash
rg -n '0\.9953|0\.9941|227|0\.0965|0\.3348|0\.0140|129\.8|11/15|1/5|Exploratory|not caus' \
  "$TMP_DIR/qa/deck.inspect.ndjson"
rg -c '"kind":"slide"' "$TMP_DIR/qa/deck.inspect.ndjson"
rg -c '"kind":"notes"' "$TMP_DIR/qa/deck.inspect.ndjson"
```

Expected: all locked claims are present, slide count is 12, and notes count is 12.

- [ ] **Step 8: Synchronize the outline and showcase report**

Update `docs/presentation/week7_ppt_outline.md` so it identifies `week7_apple_showcase_deck.pptx` as the final rendered deck and uses the same slide titles. Extend `reports/week7_apple_showcase.md` with artifact-tool version/path, input figures, rendered QA paths, slide count, notes count, and any intentional layout decisions.

- [ ] **Step 9: Commit the presentation set**

```bash
git add docs/presentation/week7_apple_showcase_deck.pptx \
  docs/media/week7_apple_architecture.png \
  scripts/build_week7_apple_showcase.mjs \
  docs/presentation/week7_ppt_outline.md \
  reports/week7_apple_showcase.md
git commit -m "docs: add week7 apple showcase deck"
```

---

### Task 4: Apple Editorial README, Blog, and Architecture

**Files:**
- Modify: `README.md`
- Modify: `docs/blog/week7_technical_blog_zh.md`
- Modify: `docs/week7_showcase_architecture.md`
- Modify: `docs/artifact-index.md`

**Interfaces:**
- Consumes: Task 2 demo media, Task 3 architecture visual/deck, and the locked evidence map.
- Produces: a GitHub-native Apple editorial entry point with no external hosting dependency.

- [ ] **Step 1: Rebuild the README first screen**

Replace the current opening and `Verified snapshot` area with GitHub-compatible Markdown/HTML using this content order:

```markdown
<p align="center"><strong>PLANTDISEASEAI · RESEARCH DEMO</strong></p>

# Evidence before diagnosis.

PlantVillage 闭集分类、Grad-CAM 相关性可视化、Streamlit / Apple container 演示，以及明确标注边界的 Qwen3-VL smoke。

![PlantDiseaseAI Apple demo](docs/media/week7_apple_demo_poster.png)

| 0.9953 | 0.9941 | 5 models |
| ---: | ---: | ---: |
| Test Accuracy | Macro F1 | Shared benchmark |

> **Research boundary:** official split 含 227 个 train/test 重叠 `leaf_id`；结果不是田间泛化证明。Grad-CAM 不是因果解释，VLM 不是专业诊断系统。
```

Place direct links to the animated GIF, deck, architecture, blog, results snapshot, evidence map, and artifact index immediately after this section. Preserve the full quick-start and technical documentation below.

- [ ] **Step 2: Apply the same editorial rhythm to the Chinese blog**

Add the demo poster below the blog title, a one-paragraph thesis, large Markdown blockquotes for the final classifier and official-split limitation, and embedded figures at the relevant sections:

```markdown
![Week 3 validation Macro F1](../../reports/figures/week3_validation_macro_f1_curves.png)

> **Evidence** — Test Accuracy `0.9953`，Macro F1 `0.9941`；seed 42、官方 split。
>
> **Limit** — 官方 split 含 `227` 个重叠 `leaf_id`，不是严格实体隔离结果。
```

Embed the architecture PNG, Grad-CAM comparison, reliability diagram, and demo GIF once each. Keep every existing evidence path and remove repetitive prose only when the same fact is already stated in the adjacent evidence block.

- [ ] **Step 3: Upgrade the architecture document**

Add `docs/media/week7_apple_architecture.png` above the existing Mermaid source with a caption that names the classifier as the main line and Qwen3-VL as exploratory. Keep the Mermaid block unchanged as the maintainable, text-readable source.

- [ ] **Step 4: Extend the artifact index**

Add rows for the design specification, implementation plan, demo poster/GIF/MP4, architecture PNG, final PPTX, and Week 7 Apple showcase QA report. Each row must state whether the artifact is evidence, presentation, or derived media.

- [ ] **Step 5: Validate links, locked numbers, and overclaim wording**

```bash
rg -n '0\.9953|0\.9941|227|129\.8|11/15|1/5' \
  README.md docs/blog/week7_technical_blog_zh.md \
  docs/week7_showcase_architecture.md docs/presentation/week7_ppt_outline.md
rg -n 'field-ready|professional diagnosis|causal explanation|LoRA.*complete|QLoRA.*complete' \
  README.md docs/blog/week7_technical_blog_zh.md docs/week7_showcase_architecture.md || true
```

Expected: locked numbers agree with the results snapshot; any matched high-risk phrase appears only in an explicit negation or limitation.

- [ ] **Step 6: Commit the editorial documentation**

```bash
git add README.md \
  docs/blog/week7_technical_blog_zh.md \
  docs/week7_showcase_architecture.md \
  docs/artifact-index.md
git commit -m "docs: apply week7 apple editorial design"
```

---

### Task 5: Week 7 Completion Audit and Task Synchronization

**Files:**
- Modify: `reports/week7_public_release_check.md`
- Modify: `reports/week7_apple_showcase.md`
- Modify: `TASKS.md`

**Interfaces:**
- Consumes: all Task 1–4 artifacts and verification outputs.
- Produces: a clean, evidence-backed Week 7 completion record without changing unverified checklist items.

- [ ] **Step 1: Run focused and full code verification**

```bash
uv run pytest tests/test_streamlit_app.py tests/serving tests/test_demo_e2e.py -q
uv run ruff check .
uv run pytest -q
```

Expected: focused tests pass, Ruff reports `All checks passed!`, and the full suite passes with only already documented PyTorch deprecation warnings.

- [ ] **Step 2: Run final media and presentation verification**

```bash
ffprobe -v error -show_entries format=duration,size -of json docs/media/week7_apple_demo.mp4
ffprobe -v error -show_entries format=duration,size -of json docs/media/week7_apple_demo.gif
SKILL_DIR="${PRESENTATIONS_SKILL_DIR:?Set PRESENTATIONS_SKILL_DIR to the presentations skill directory}"
PYTHON="${PYTHON_BIN:?Set PYTHON_BIN to a Python runtime with presentation QA dependencies}"
"$PYTHON" \
  "$SKILL_DIR/container_tools/slides_test.py" \
  docs/presentation/week7_apple_showcase_deck.pptx
file docs/presentation/week7_apple_showcase_deck.pptx docs/media/week7_apple_demo.*
```

Expected: valid MP4/GIF/PPTX files, GIF below 10 MiB, 12-slide presentation, and no structural slide errors.

- [ ] **Step 3: Re-run the public-release scans**

```bash
git grep -nI -i -E 'api[_-]?key|secret|password|passwd|private[[:space:]_-]?key|-----BEGIN|hf_[A-Za-z0-9]{10,}|sk-[A-Za-z0-9]{10,}|ghp_[A-Za-z0-9]{10,}|github_pat_[A-Za-z0-9_]{10,}|HF_TOKEN|OPENAI_API_KEY' -- . || true
macos_home='/''Users/'
private_var='/private/''var'
user_temp='/var/''folders/'
path_pattern="${macos_home}|${private_var}|${user_temp}"
git grep -nI -E "$path_pattern" -- . || true
git ls-files -z | xargs -0 du -k | sort -n | tail -20
git diff --check
```

Expected: no credential values, no personal absolute paths, no unexpected large model/data files, and no whitespace errors.

- [ ] **Step 4: Update the Week 7 release records**

Append the post-redesign commands and results to `reports/week7_public_release_check.md`. Complete `reports/week7_apple_showcase.md` with:

- actual commit/branch at validation time;
- Streamlit device used for capture;
- media dimensions, duration, and size;
- PPTX slide/notes counts and full-size visual QA result;
- full test and Ruff results;
- known remaining Week 8 work.

- [ ] **Step 5: Synchronize `TASKS.md` conservatively**

Mark these Week 7 items complete only when their evidence exists and the commands above pass:

- short GIF/video covering input, Top-5, heatmap, and safety;
- 10–15 page PPT with speaker notes;
- high-quality README, architecture, result figures, and Demo media;
- README/architecture/Demo evidence bundle;
- blog/PPT/speaker-note evidence bundle;
- figure title/unit/condition validation when every referenced figure has been checked;
- Week 8 handoff requiring no new major showcase feature.

Leave the clean-environment quick-start item unchecked unless it is actually run in a clean environment during this task. Cite `reports/week7_apple_showcase.md`, the final media paths, and the PPTX path beside newly completed items.

- [ ] **Step 6: Review the complete staged change set**

```bash
git status --short
git diff --stat HEAD~4..HEAD
git diff --check
git log --oneline -8
```

Confirm the legacy untracked deck still exists and remains outside every commit. Confirm no ignored checkpoint, data, output frame, cache, or personal path is staged.

- [ ] **Step 7: Commit the completion audit**

```bash
git add TASKS.md reports/week7_public_release_check.md reports/week7_apple_showcase.md
git commit -m "docs: complete week7 apple showcase audit"
```

- [ ] **Step 8: Final handoff commands**

Provide the user with:

```bash
cd "$(git rev-parse --show-toplevel)"
git log --oneline -8
git status --short
open docs/presentation/week7_apple_showcase_deck.pptx
open docs/media/week7_apple_demo.mp4
uv run ruff check .
uv run pytest -q
```

State separately which Week 7 items are complete, which clean-environment check remains for Week 8, and that no remote push or publication was performed.
