# Week 8 Paper and Dual-Native Research Defense Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete evidence-synchronized Chinese/English research papers and a 20-slide Apple-style research defense delivered as native Keynote Magic Move and PowerPoint Morph files.

**Architecture:** A tracked paper audit and a tracked presentation content contract lock every public claim before prose or visuals are generated. The papers consume shared LaTeX claim macros and shared tables; the presentation is built from the JSON contract with `@oai/artifact-tool` in an external scratch workspace, then converted and animated in Keynote 15.3. Final QA checks content, rendering, transitions, notes, bilingual parity, citations, and release evidence.

**Tech Stack:** Python 3.12, pytest, YAML/JSON, XeLaTeX, BibTeX, Poppler, JavaScript ES modules, `@oai/artifact-tool`, AppleScript, Keynote 15.3, OOXML, ffprobe.

## Global Constraints

- Audience is prospective research supervisors and research-program reviewers; target duration is approximately 15 minutes.
- Deliver exactly 20 slides, Chinese-first visible copy, English technical terms, and 20 speaker-note parts.
- Use Apple launch-event visual grammar without copying Apple product images, logos, Bilibili watermarks, or subtitle overlays.
- Keynote is the native motion reference and uses click-triggered Magic Move at `0.8–1.0 s`; PPTX uses paired-object Morph semantics.
- Preserve the locked values `227`, `0.9830`, `0.9743`, `2.27M`, `0.31G`, `644.3`, `0.9953`, `0.9941`, `50/10709`, `0.0965`, `0.3348`, `0.0140`, `129.8`, `11/15`, and `1/5` with their approved boundaries.
- The `0.9953 / 0.9941` result must remain adjacent to seed 42, official split, and the `227 leaf_id` overlap limitation.
- Grad-CAM is non-causal relevance visualization; Qwen3-VL is smoke exploration; the UI is not professional diagnosis.
- LoRA/QLoRA, multi-seed confirmation, entity-isolated evaluation, complete human audit, and field validation remain incomplete.
- `Panjoel` is the paper author; Codex is a disclosed tool, not a co-author.
- Use only repository evidence; never invent citations, metrics, experiments, users, publications, awards, or field performance.
- Use `@oai/artifact-tool` for deck construction; do not use `python-pptx` or Python drawing.
- Keep all presentation build sources and scratch outputs outside the repository; only requested final artifacts, tracked contracts, and QA reports enter Git.
- Existing untracked Week 7 legacy presentation artifacts remain untouched and untracked.
- Do not push, tag, publish, release, open a PR, or upload materials without separate authority.

---

### Task 1: Bilingual paper evidence and parity audit

**Files:**

- Create: `paper/shared/week8_verified_claims.tex`
- Create: `scripts/audit_week8_paper.py`
- Create: `tests/release/test_week8_paper_audit.py`

**Interfaces:**

- Consumes: the two paper entry points and the locked release claims.
- Produces:
  - `parse_claim_macros(path: Path) -> dict[str, str]`
  - `audit_paper_pair(zh_path: Path, en_path: Path, claims_path: Path) -> dict[str, object]`
  - CLI arguments `--zh`, `--en`, `--claims`, and `--output`.

- [ ] **Step 1: Add failing macro and parity tests**

```python
from pathlib import Path

from scripts.audit_week8_paper import audit_paper_pair, parse_claim_macros


def test_parse_claim_macros_reads_locked_values(tmp_path: Path) -> None:
    claims = tmp_path / "claims.tex"
    claims.write_text(
        r"\newcommand{\PDAFinalAccuracy}{0.9953}" + "\n",
        encoding="utf-8",
    )
    assert parse_claim_macros(claims) == {"PDAFinalAccuracy": "0.9953"}


def test_audit_requires_bilingual_sections_and_claim_usage(tmp_path: Path) -> None:
    claims = tmp_path / "claims.tex"
    claims.write_text(
        r"\newcommand{\PDAFinalAccuracy}{0.9953}" + "\n",
        encoding="utf-8",
    )
    zh = tmp_path / "zh.tex"
    en = tmp_path / "en.tex"
    zh.write_text(r"\section{引言}\PDAFinalAccuracy", encoding="utf-8")
    en.write_text(r"\section{Introduction}", encoding="utf-8")
    result = audit_paper_pair(zh, en, claims)
    assert result["status"] == "failed"
    assert result["missing_claims_en"] == ["PDAFinalAccuracy"]
```

- [ ] **Step 2: Verify RED**

Run `uv run pytest tests/release/test_week8_paper_audit.py -q`.

Expected: collection fails because `scripts.audit_week8_paper` does not exist.

- [ ] **Step 3: Implement the audit core**

```python
CLAIM_RE = re.compile(
    r"\\newcommand\{\\(?P<name>PDA[A-Za-z0-9]+)\}\{(?P<value>[^}]*)\}"
)

REQUIRED_SECTION_COUNTS = 13


def parse_claim_macros(path: Path) -> dict[str, str]:
    """Return locked LaTeX command names and values."""

    return {
        match.group("name"): match.group("value")
        for match in CLAIM_RE.finditer(path.read_text(encoding="utf-8"))
    }


def audit_paper_pair(
    zh_path: Path, en_path: Path, claims_path: Path
) -> dict[str, object]:
    """Audit bilingual section count and shared claim-macro usage."""

    claims = parse_claim_macros(claims_path)
    zh_text = zh_path.read_text(encoding="utf-8")
    en_text = en_path.read_text(encoding="utf-8")
    missing_zh = sorted(name for name in claims if f"\\{name}" not in zh_text)
    missing_en = sorted(name for name in claims if f"\\{name}" not in en_text)
    zh_sections = len(re.findall(r"\\section\{", zh_text))
    en_sections = len(re.findall(r"\\section\{", en_text))
    passed = (
        not missing_zh
        and not missing_en
        and zh_sections == REQUIRED_SECTION_COUNTS
        and en_sections == REQUIRED_SECTION_COUNTS
    )
    return {
        "schema_version": 1,
        "status": "passed" if passed else "failed",
        "section_count_zh": zh_sections,
        "section_count_en": en_sections,
        "missing_claims_zh": missing_zh,
        "missing_claims_en": missing_en,
    }
```

Add an argparse `main()` that writes sorted, newline-terminated JSON and exits
1 when the status is failed. All public functions receive type annotations and
short docstrings.

- [ ] **Step 4: Add the complete claim macro file**

```tex
\newcommand{\PDAOfficialOverlap}{227}
\newcommand{\PDAWeekTwoAccuracy}{0.9830}
\newcommand{\PDAWeekTwoMacroFOne}{0.9743}
\newcommand{\PDAMobileParams}{2.27M}
\newcommand{\PDAMobileFlops}{0.31G}
\newcommand{\PDAMobileThroughput}{644.3}
\newcommand{\PDAFinalAccuracy}{0.9953}
\newcommand{\PDAFinalMacroFOne}{0.9941}
\newcommand{\PDAErrorCount}{50}
\newcommand{\PDATestCount}{10709}
\newcommand{\PDAECE}{0.0965}
\newcommand{\PDAMCE}{0.3348}
\newcommand{\PDABrier}{0.0140}
\newcommand{\PDADemoLatency}{129.8}
\newcommand{\PDAVLMChoice}{11/15}
\newcommand{\PDAVLMCondition}{1/5}
```

- [ ] **Step 5: Verify and commit**

```bash
uv run pytest tests/release/test_week8_paper_audit.py -q
uv run ruff check scripts/audit_week8_paper.py tests/release/test_week8_paper_audit.py
uv run ty check scripts/audit_week8_paper.py
git diff --check
git add paper/shared/week8_verified_claims.tex scripts/audit_week8_paper.py tests/release/test_week8_paper_audit.py
git commit -m "feat: add week8 bilingual paper audit"
```

---

### Task 2: Complete and build the Chinese and English papers

**Files:**

- Modify: `paper/zh/main.tex`
- Modify: `paper/en/main.tex`
- Modify: `paper/references.bib`
- Modify: `paper/README.md`
- Create: `paper/tables/week4_analysis_zh.tex`
- Create: `paper/tables/week4_analysis_en.tex`
- Create: `paper/tables/week6_vlm_zh.tex`
- Create: `paper/tables/week6_vlm_en.tex`
- Create: `paper/tables/week8_repro_zh.tex`
- Create: `paper/tables/week8_repro_en.tex`
- Modify: `paper/out/plantdisease_ai_zh.pdf`
- Modify: `paper/out/plantdisease_ai_en.pdf`
- Create: `reports/release/week8_paper_audit.json`

**Interfaces:**

- Consumes: Task 1 macros/audit and tracked Week 1–8 reports.
- Produces: synchronized 13-section TeX sources, tables, references, PDFs, and
  machine-readable parity evidence.

- [ ] **Step 1: Update both preambles and authorship**

Both files input `../shared/week8_verified_claims.tex`, set the date to
`2026-07-16`, use `Panjoel` as the sole author, and add packages `microtype`,
`xcolor`, `longtable`, and `placeins`. Replace the inline bibliography with:

```tex
\bibliographystyle{plain}
\bibliography{../references}
```

- [ ] **Step 2: Replace both bodies with the approved 13-section structure**

The exact English headings are:

```tex
\section{Introduction}
\section{Related Work}
\section{Dataset, Task, and Split Audit}
\section{Unified Training and Evaluation Protocol}
\section{Five-Model Benchmark}
\section{Controlled Ablation and Model Selection}
\section{Explainability, Error Analysis, and Calibration}
\section{Demo, MPS Serving, and Apple Container}
\section{Qwen3-VL Exploration and Safety}
\section{Week 8 Reproducibility Audit}
\section{Discussion and Negative Results}
\section{Limitations, Ethics, and Intended Use}
\section{Conclusion and Future Work}
```

The Chinese file uses the direct Chinese equivalents from the approved design.
Use every Task 1 macro in both papers. Place the final metric macros in a
sentence that also contains seed 42, official split, and
`\PDAOfficialOverlap`.

- [ ] **Step 3: Add synchronized tables and figures**

Create bilingual tables for:

- Week 4: `50/10709`, two high-confidence errors, ECE/MCE/Brier.
- Week 6: short free-form `10/15`, choice/few-shot `11/15`, and condition
  `1/5`, all labeled smoke exploration.
- Week 8: clean lane, local evidence lane, and Apple container lane with only
  real statuses from the release manifest.

Retain the benchmark/ablation tables and the two verified Week 3/4 figures.
Add the Week 5 Streamlit screenshot only when the file exists and its caption
states that it is one fixed Demo input.

- [ ] **Step 4: Extend the bibliography from verified primary sources**

Keep the existing PlantVillage, model, training, Grad-CAM, and calibration
entries. Add the Qwen3-VL paper/model-card citation already recorded by the
Week 6 selection report and cite it only in the exploratory section. Do not add
uncited references.

- [ ] **Step 5: Run the bilingual audit**

```bash
uv run python scripts/audit_week8_paper.py \
  --zh paper/zh/main.tex \
  --en paper/en/main.tex \
  --claims paper/shared/week8_verified_claims.tex \
  --output reports/release/week8_paper_audit.json
```

Expected: status `passed`, 13 sections in each language, and no missing macros.

- [ ] **Step 6: Build both papers with citations**

```bash
cd paper/zh
xelatex -interaction=nonstopmode -halt-on-error -jobname=plantdisease_ai_zh -output-directory=../out main.tex
cd ../out
bibtex plantdisease_ai_zh
cd ../zh
xelatex -interaction=nonstopmode -halt-on-error -jobname=plantdisease_ai_zh -output-directory=../out main.tex
xelatex -interaction=nonstopmode -halt-on-error -jobname=plantdisease_ai_zh -output-directory=../out main.tex
cd ../en
xelatex -interaction=nonstopmode -halt-on-error -jobname=plantdisease_ai_en -output-directory=../out main.tex
cd ../out
bibtex plantdisease_ai_en
cd ../en
xelatex -interaction=nonstopmode -halt-on-error -jobname=plantdisease_ai_en -output-directory=../out main.tex
xelatex -interaction=nonstopmode -halt-on-error -jobname=plantdisease_ai_en -output-directory=../out main.tex
```

- [ ] **Step 7: Render and visually inspect every PDF page**

Use the PDF skill's Poppler workflow. Confirm no missing figures, table
overflow, broken glyphs, blank pages, unresolved `??`, or clipping. Search the
logs for `Undefined`, `Citation`, `Reference`, `Overfull`, and `Underfull`;
resolve every undefined citation/reference and every material overflow.

- [ ] **Step 8: Verify and commit**

```bash
uv run pytest tests/release/test_week8_paper_audit.py -q
uv run ruff check scripts/audit_week8_paper.py tests/release/test_week8_paper_audit.py
rg -n 'Undefined|Citation.*undefined|Reference.*undefined|Overfull \\hbox' paper/out/*.log
git diff --check
git add paper reports/release/week8_paper_audit.json
git commit -m "docs: complete week8 bilingual research paper"
```

---

### Task 3: Lock the 20-slide research-defense content contract

**Files:**

- Create: `docs/presentation/week8_research_defense_content.json`
- Create: `tests/release/test_week8_presentation_contract.py`

**Interfaces:**

- Consumes: tracked release claim sources and the approved narrative.
- Produces: schema-1 JSON with exactly 20 ordered slide records; each record has
  `number`, `id`, `title`, `claim`, `visual`, `notes`, `theme`,
  `transition_group`, and `required_boundary`.

- [ ] **Step 1: Write the failing contract test**

```python
import json
from pathlib import Path


def test_week8_research_defense_contract_is_complete() -> None:
    payload = json.loads(
        Path("docs/presentation/week8_research_defense_content.json").read_text(
            encoding="utf-8"
        )
    )
    slides = payload["slides"]
    assert payload["schema_version"] == 1
    assert len(slides) == 20
    assert [slide["number"] for slide in slides] == list(range(1, 21))
    assert all(slide["notes"].strip() for slide in slides)
    assert {slide["transition_group"] for slide in slides if slide["transition_group"]} == {
        "scope-risk", "models", "ablation", "errors", "explainability",
        "demo", "vlm"
    }
```

Add assertions that the serialized contract includes every locked value and
the phrases `seed 42`, `official split`, `非因果`, `smoke`, and `非专业诊断`.

- [ ] **Step 2: Verify RED**

Run `uv run pytest tests/release/test_week8_presentation_contract.py -q`.

Expected: `FileNotFoundError` because the content contract is absent.

- [ ] **Step 3: Create the exact 20-slide contract**

Use the ordered IDs below. Titles are audience-facing; notes contain evidence
paths and the transition cue.

```json
[
  [1, "title", "PlantDiseaseAI", "从高分模型到可审计研究系统", "black"],
  [2, "question", "高准确率，等于可信诊断吗？", "研究问题与判断标准", "white"],
  [3, "scope", "38 类受控图像分类", "PlantVillage 定义了任务，也限制了结论", "white"],
  [4, "overlap", "227", "official split 并非实体隔离", "black"],
  [5, "loop", "证据必须形成闭环", "数据、训练、评估、解释与服务", "white"],
  [6, "models", "五个模型，同一协议", "比较架构，而不是比较训练条件", "white"],
  [7, "tradeoff", "一个追求精度，一个追求效率", "ResNet50 与 MobileNetV2", "white"],
  [8, "baseline", "先冻结基线", "ResNet50: 0.9830 / 0.9743", "black"],
  [9, "single", "最强单变量改变优化路径", "Cosine Scheduler: 0.9898", "black"],
  [10, "final", "0.9953 / 0.9941", "seed 42 · official split · 227 overlap", "black"],
  [11, "errors", "50 / 10709", "高分仍需要逐样本错误审计", "white"],
  [12, "confusions", "错误集中在视觉相似病害", "三组主要混淆对", "white"],
  [13, "calibration", "准确率不等于置信度质量", "ECE 0.0965 · MCE 0.3348 · Brier 0.0140", "white"],
  [14, "gradcam", "解释目标层会改变观察结果", "Grad-CAM 是相关性，不是因果", "black"],
  [15, "demo", "把研究接口变成可演示系统", "Top-5 · Grad-CAM · 安全边界", "black"],
  [16, "serving", "工程证据也必须注明条件", "MPS · Apple container · fixed-example latency", "black"],
  [17, "vlm", "VLM 是探索分支，不是主线替代", "Qwen3-VL smoke exploration", "white"],
  [18, "vlm_boundary", "11/15 与 1/5", "结构化选择提升输出，细粒度病害仍弱", "black"],
  [19, "release", "结果必须能被重新检查", "week8-rc1 · manifest · claim ledger", "white"],
  [20, "future", "下一步不是再堆功能", "实体隔离 · 多 seed · 田间数据 · 人工审计", "black"]
]
```

Populate all required fields, evidence paths, complete Chinese speaker notes,
and transition groups: 3–4 `scope-risk`, 6–7 `models`, 8–10 `ablation`,
11–12 `errors`, 13–14 `explainability`, 15–16 `demo`, and 17–18 `vlm`.

- [ ] **Step 4: Verify and commit**

```bash
uv run pytest tests/release/test_week8_presentation_contract.py -q
uv run ruff check tests/release/test_week8_presentation_contract.py
git diff --check
git add docs/presentation/week8_research_defense_content.json tests/release/test_week8_presentation_contract.py
git commit -m "docs: lock week8 research defense content"
```

---

### Task 4: Build and verify the dual-native animated presentation

**Files:**

- Create: `docs/presentation/plantdisease_ai_week8_research_defense.pptx`
- Create: `docs/presentation/plantdisease_ai_week8_research_defense.key`
- Create: `docs/presentation/week8_research_defense_animation_map.md`
- Create: `reports/week8_presentation_qa.md`
- External scratch only: artifact-tool `.mjs`, source notes, assets, previews,
  render outputs, AppleScript, OOXML inspection, and motion-preview files.

**Interfaces:**

- Consumes: Task 3 JSON contract and verified project images/reports.
- Produces: 20-slide PPTX, native Keynote, animation map, and QA report.

- [ ] **Step 1: Initialize the required external presentation workspace**

```bash
SKILL_DIR="$HOME/.codex/plugins/cache/openai-primary-runtime/presentations/26.709.11516/skills/presentations"
SCRATCH_ROOT="$(node -p "require('node:os').tmpdir()")"
THREAD_ID="${CODEX_THREAD_ID:-manual-week8-research-defense}"
WORKSPACE="$SCRATCH_ROOT/codex-presentations/$THREAD_ID/week8-research-defense"
TMP_DIR="$WORKSPACE/tmp"
mkdir -p "$TMP_DIR" "$TMP_DIR/assets" "$TMP_DIR/preview" "$TMP_DIR/layout" "$TMP_DIR/qa"
node "$SKILL_DIR/container_tools/setup_artifact_tool_workspace.mjs" --workspace "$TMP_DIR"
```

Do not copy scratch files into Git.

- [ ] **Step 2: Read the artifact-tool API before authoring**

Read completely:

- `artifact_tool/API_QUICK_START.md`
- `artifact_tool/api/API_DOCS.md`
- `artifact_tool/api/references/slide.spec.md`
- `artifact_tool/api/references/speaker-notes.spec.md`

This is explicit custom formatting based on user screenshots, so do not use
Codex Grid or template-following mode.

- [ ] **Step 3: Build the artifact-tool PPTX from the locked contract**

Create `$TMP_DIR/build-week8-defense.mjs` as a plain ES module. Use one
composition per slide, `slide.compose(...)`, SF Pro/PingFang typography, the
approved black/off-white/blue/amber palette, and raster project evidence.
Speaker notes use:

```javascript
slide.speakerNotes.textFrame.setText(contractSlide.notes);
slide.speakerNotes.setVisible(true);
```

Use stable semantic names for every paired hero, title, metric, and evidence
image. Connectors are created before nodes. The only card grid is slide 5.
Export directly to
`docs/presentation/plantdisease_ai_week8_research_defense.pptx`.

- [ ] **Step 4: Render and inspect the static PPTX**

```bash
python "$SKILL_DIR/container_tools/slides_test.py" docs/presentation/plantdisease_ai_week8_research_defense.pptx
python "$SKILL_DIR/container_tools/render_slides.py" docs/presentation/plantdisease_ai_week8_research_defense.pptx
python "$SKILL_DIR/container_tools/create_montage.py" \
  --input_dir docs/presentation/plantdisease_ai_week8_research_defense \
  --output_file "$TMP_DIR/qa/contact-sheet.png"
```

Inspect all 20 slides individually at full size. Fix every unintended overlap,
clip, wrap, placeholder, low-contrast item, and evidence mismatch; rebuild and
repeat until clean.

- [ ] **Step 5: Create the native Keynote and apply Magic Move**

Create `$TMP_DIR/apply-magic-move.applescript` with the following transition
map: source slides `3, 6, 8, 9, 11, 13, 15, 17` transition to their following
paired slide. Use Keynote bundle id `com.apple.Keynote`, duration `0.9`, delay
`0`, and click-triggered transitions.

```applescript
on run argv
  set sourcePath to POSIX file (item 1 of argv)
  set keyPath to POSIX file (item 2 of argv)
  tell application id "com.apple.Keynote"
    activate
    set deckDocument to open sourcePath
    repeat with slideNumber in {3, 6, 8, 9, 11, 13, 15, 17}
      set transition properties of slide slideNumber of deckDocument to ¬
        {transition effect:magic move, transition duration:0.9, ¬
         transition delay:0, automatic transition:false}
    end repeat
    save deckDocument in keyPath
    close deckDocument saving no
  end tell
end run
```

Run it with the resolved repository PPTX and Keynote output paths as the two
arguments. Running Keynote requires the normal GUI approval path.

- [ ] **Step 6: Export a PowerPoint copy from the animated Keynote**

Reopen the `.key` and export it as Microsoft PowerPoint to a scratch PPTX.
Inspect the scratch export for Morph transition data. Use the Keynote-exported
copy as final only if it preserves all 20 slides, notes, and mapped motion;
otherwise retain the artifact-tool PPTX and inject Morph metadata in the eight
source-slide XML parts with an external scratch Python script that uses only
the standard-library `zipfile` module, not `python-pptx`. Insert this exact
transition immediately after `</p:cSld>` in source slides 3, 6, 8, 9, 11, 13,
15, and 17:

```xml
<p:transition advClick="1">
  <p:extLst>
    <p:ext uri="{C676402C-5697-4E1C-873F-D02D1690AC5C}">
      <p159:morph xmlns:p159="http://schemas.microsoft.com/office/powerpoint/2015/09/main" option="byObject"/>
    </p:ext>
  </p:extLst>
</p:transition>
```

Write a new scratch PPTX, validate its ZIP integrity and rendering, then copy
it over the final PPTX only after all checks pass. Record whether the final
transition came from Keynote export or the audited OOXML fallback.

- [ ] **Step 7: Validate the two presentation forms**

Required checks:

```bash
unzip -Z1 docs/presentation/plantdisease_ai_week8_research_defense.pptx | rg '^ppt/slides/slide[0-9]+\.xml$' | wc -l
unzip -Z1 docs/presentation/plantdisease_ai_week8_research_defense.pptx | rg '^ppt/notesSlides/notesSlide[0-9]+\.xml$' | wc -l
unzip -p docs/presentation/plantdisease_ai_week8_research_defense.pptx 'ppt/slides/slide*.xml' | rg -c 'morph|transition'
file docs/presentation/plantdisease_ai_week8_research_defense.key
```

Expected: 20 slides, 20 notes, transition evidence for every mapped group, and
a Keynote document recognized by macOS. Reopen the `.key` in Keynote and play
all mapped transitions. Export a scratch movie and inspect its frames/duration;
the movie is QA evidence and remains outside Git.

- [ ] **Step 8: Write animation and QA evidence**

The animation map lists each group, source/target slides, stable objects,
duration, trigger, Keynote result, PPTX structural result, and the explicit
PowerPoint-client playback limitation. The QA report records artifact hashes,
sizes, slide/note counts, render commands, per-slide inspection, motion preview,
claim checks, and any compatibility limitation.

- [ ] **Step 9: Verify and commit**

```bash
uv run pytest tests/release/test_week8_presentation_contract.py -q
uv run python scripts/audit_week8_claims.py \
  --config configs/week8_claims.yaml \
  --output reports/release/week8_claim_evidence.json \
  --check-links
git diff --check
git add docs/presentation/plantdisease_ai_week8_research_defense.pptx \
  docs/presentation/plantdisease_ai_week8_research_defense.key \
  docs/presentation/week8_research_defense_animation_map.md \
  reports/week8_presentation_qa.md reports/release/week8_claim_evidence.json
git commit -m "docs: add week8 dual-native research defense"
```

---

### Task 5: Integrate paper and presentation into the release evidence

**Files:**

- Modify: `configs/week8_claims.yaml`
- Modify: `README.md`
- Modify: `TASKS.md`
- Modify: `docs/artifact-index.md`
- Modify: `docs/release/week8_release_checklist.md`
- Modify: `reports/release/week8_rc1_manifest.json`
- Modify: `reports/release/week8_claim_evidence.json`

**Interfaces:**

- Consumes: approved outputs from Tasks 1–4 and the main Week 8 release audit.
- Produces: final evidence links and claim coverage for paper/deck artifacts.

- [ ] **Step 1: Extend claim consumers**

Add both paper entry points and the final PPTX only to claims they actually
publish. Do not audit `.key` text independently; record that it is generated
from the same locked contract and verify parity through the QA report.

- [ ] **Step 2: Synchronize project entry points**

Link both presentation formats, both PDFs, TeX sources, animation map, and QA
evidence from README and the artifact index. Update `TASKS.md` only for checks
whose acceptance evidence exists.

- [ ] **Step 3: Regenerate release evidence**

Rebuild the claim ledger and manifest so they include hashes and sizes for the
PPTX, Keynote, TeX entry points, and two PDFs. Preserve logical repository paths
and never record personal or scratch absolute paths.

- [ ] **Step 4: Run final extension validation**

```bash
uv run python scripts/audit_week8_paper.py \
  --zh paper/zh/main.tex --en paper/en/main.tex \
  --claims paper/shared/week8_verified_claims.tex \
  --output reports/release/week8_paper_audit.json
uv run pytest tests/release/test_week8_paper_audit.py tests/release/test_week8_presentation_contract.py -q
uv run python scripts/audit_week8_claims.py \
  --config configs/week8_claims.yaml \
  --output reports/release/week8_claim_evidence.json --check-links
uv run ruff check .
uv run ty check src/plantdisease app scripts
uv run pytest -q
git diff --check
```

- [ ] **Step 5: Commit**

```bash
git add configs/week8_claims.yaml README.md TASKS.md docs/artifact-index.md \
  docs/release/week8_release_checklist.md reports/release/week8_rc1_manifest.json \
  reports/release/week8_claim_evidence.json reports/release/week8_paper_audit.json
git commit -m "docs: integrate week8 paper and defense evidence"
```

Request an independent whole-extension review over the range beginning at the
Task 1 base. Fix every Critical or Important finding, rerun affected checks,
and re-review before the main Week 8 final provenance commit.
