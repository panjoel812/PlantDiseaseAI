# Week 7 Public Release Check

Date: 2026-07-13
Branch at scan time: `codex/week7-showcase-materials`
Head at scan time: `b60e163`

This check reviews tracked repository content for public-showcase readiness. It
does not inspect local ignored artifacts such as downloaded datasets,
checkpoints, Hugging Face caches, or generated `outputs/` files except where
their paths are referenced by tracked documentation.

## Scope

- README first-screen claims and Week 7 showcase links.
- Week 7 blog draft and PPT outline / speaker notes.
- Tracked reports, docs, source, tests, configuration, and figures.
- Git-tracked file sizes and high-risk path patterns.

## Commands run

```bash
git grep -nI -i -E 'api[_-]?key|secret|password|passwd|private[[:space:]_-]?key|-----BEGIN|hf_[A-Za-z0-9]{10,}|sk-[A-Za-z0-9]{10,}|ghp_[A-Za-z0-9]{10,}|github_pat_[A-Za-z0-9_]{10,}|HF_TOKEN|OPENAI_API_KEY|AWS_ACCESS_KEY_ID|AWS_SECRET_ACCESS_KEY' -- . | cut -d: -f1-2 || true

macos_home='/''Users/'
private_var='/private/''var'
user_temp='/var/''folders/'
generic_tmp='/''tmp/'
path_pattern="${macos_home}|${private_var}|${user_temp}|${generic_tmp}"
git grep -nI -E "$path_pattern" -- . | cut -d: -f1-2 || true

git ls-files -z | xargs -0 du -k | sort -n | tail -20

git ls-files | rg '^(data|outputs|\.venv|\.cache|__pycache__|\.pytest_cache|\.ruff_cache)/' || true

git grep -nI -i -E 'field-ready|field ready|真实田间泛化可靠|专业诊断|农药剂量|pesticide dosage|LoRA/QLoRA 已完成|LoRA 已完成|QLoRA 已完成|无泄漏|万能农作物医生|field diagnosis|diagnosis reliability|causal explanation|因果解释|农业 Agent' -- README.md docs reports TASKS.md app src scripts tests paper 2>/dev/null || true

uv run python - <<'PY'
import json
import subprocess
from pathlib import Path

files = subprocess.check_output(['git', 'ls-files', '*.ipynb'], text=True).splitlines()
if not files:
    print('NO_TRACKED_NOTEBOOKS')
for name in files:
    path = Path(name)
    data = json.loads(path.read_text(encoding='utf-8'))
    code_cells = [cell for cell in data.get('cells', []) if cell.get('cell_type') == 'code']
    output_cells = [cell for cell in code_cells if cell.get('outputs')]
    execution_cells = [cell for cell in code_cells if cell.get('execution_count') is not None]
    print(f'{name}\tcode_cells={len(code_cells)}\toutput_cells={len(output_cells)}\texecution_count_cells={len(execution_cells)}')
PY

rg -n '0\.9953|0\.9941|0\.9830|0\.9743|644\.3|2\.27M|0\.31G|0\.0965|0\.3348|0\.0140|129\.8|11/15|1/5|227' README.md docs/blog/week7_technical_blog_zh.md docs/presentation/week7_ppt_outline.md docs/week7_results_snapshot.md docs/week7_evidence_map.md reports/week2_benchmark_progress.md reports/week3_final_model_decision.md reports/week4_calibration.md reports/week5_demo_engineering.md reports/week6_vlm_prompt_compare.md
```

## Findings

| Area | Result | Notes |
| --- | --- | --- |
| Secrets / credentials | Pass | Grep hits were instructional words such as `secrets` in plans/tests and `.dockerignore` assertions, not credential values. No tracked token-like value was found by the patterns above. |
| Personal absolute paths | Pass | No tracked macOS user-home or per-user temporary-directory paths were found. Hits were generic temporary paths in container/test examples. |
| Notebook outputs | Pass | `NO_TRACKED_NOTEBOOKS`; no tracked `.ipynb` output needs clearing. |
| Raw data / outputs / caches | Pass | No tracked files under `data/`, `outputs/`, `.venv/`, `.cache/`, `__pycache__`, `.pytest_cache`, or `.ruff_cache`. |
| Large tracked files | Pass | Largest tracked artifact is `reports/figures/week4_baseline_vs_final_gradcam.png` at about 2.7 MiB. No raw dataset, checkpoint, or model cache is tracked. |
| License/public wording | Pass with caveat | Project license is MIT. Week 6 model-selection notes record Qwen and SmolVLM candidates as Apache 2.0 and defer Gemma-term usage. This is a project-level release check, not legal advice. |
| Overclaim scan | Pass | Matches are boundary statements such as “not field diagnosis,” “not LoRA,” “not causal explanation,” and “cannot claim leakage-free official split.” No positive public claim of field-ready diagnosis, completed LoRA/QLoRA, pesticide dosage guidance, or causal Grad-CAM explanation was found. |
| Metric consistency | Pass | README, Week 7 blog, PPT outline, results snapshot, and source reports consistently cite the same checked numbers for Week 2 benchmark, Week 3 final classifier, Week 4 calibration, Week 5 container smoke, and Week 6 Qwen smoke. |
| VLM status wording | Pass | Public materials describe Qwen3-VL as a small smoke comparison and safety-bounded prototype, not as a professional agricultural agent or completed fine-tuned model. |

## Public-showcase readiness notes

- The repository is ready for continued Week 7 showcase polishing from a
  tracked-file hygiene perspective.
- The short GIF/video is still pending.
- The rendered `.pptx` is still pending; the current PPT deliverable is an
  outline plus 5-minute and 10-minute speaker notes.
- A full Week 8 release audit should still re-run installation, smoke, lint,
  tests, model/data-card checks, and final resume-claim review before any
  public push or release.

## Post-redesign audit — 2026-07-15

Branch at validation time: `codex/week7-showcase-materials`

Pre-audit HEAD validated: `a614d49`

Post-remediation tracked-content status: **PASS**. The strict personal-path
scan produced no output after the implementation plan was made portable. This
result was obtained with the Task 5 audit draft and path remediation present as
uncommitted working-tree changes against `a614d49`; it is not a clean-
environment reproduction or a publication event.

This audit supersedes the earlier statements that the GIF/video and rendered
PPTX were pending. It validates the final Apple Hybrid Nature showcase
artifacts locally; it does not represent a remote push, publication, clean
environment reproduction, field validation, LoRA/QLoRA training, or completed
manual VQA review.

### Commands run

```bash
uv run pytest tests/test_streamlit_app.py tests/serving tests/test_demo_e2e.py -q
uv run ruff check .
uv run pytest -q

ffprobe -v error \
  -show_entries stream=index,codec_name,codec_type,width,height,pix_fmt,r_frame_rate \
  -show_entries format=duration,size -of json \
  docs/media/week7_apple_demo.mp4
ffprobe -v error \
  -show_entries stream=index,codec_name,codec_type,width,height,r_frame_rate \
  -show_entries format=duration,size -of json \
  docs/media/week7_apple_demo.gif

SKILL_DIR="${PRESENTATIONS_SKILL_DIR:?Set PRESENTATIONS_SKILL_DIR to the presentations skill directory}"
PYTHON="${PYTHON_BIN:-python3}"
"$PYTHON" \
  "$SKILL_DIR/container_tools/slides_test.py" \
  docs/presentation/week7_apple_showcase_deck.pptx
file docs/presentation/week7_apple_showcase_deck.pptx \
  docs/media/week7_apple_demo.mp4 \
  docs/media/week7_apple_demo.gif \
  docs/media/week7_apple_demo_poster.png
unzip -Z1 docs/presentation/week7_apple_showcase_deck.pptx

git grep -nI -i -E \
  'api[_-]?key|secret|password|passwd|private[[:space:]_-]?key|-----BEGIN|hf_[A-Za-z0-9]{10,}|sk-[A-Za-z0-9]{10,}|ghp_[A-Za-z0-9]{10,}|github_pat_[A-Za-z0-9_]{10,}|HF_TOKEN|OPENAI_API_KEY' \
  -- . || true
macos_home='/''Users/'
private_var='/private/''var'
user_temp='/var/''folders/'
path_pattern="${macos_home}|${private_var}|${user_temp}"
git grep -nI -E "$path_pattern" -- . || true
git ls-files -z | xargs -0 du -k | sort -n | tail -20
git diff --check
```

The first sandboxed `uv` attempts could not open the existing user-level uv
cache and exited before test collection. The same three commands were then run
unchanged in an approved context with access to that cache; the results below
are from those completed runs.

### Results

| Area | Fresh result | Disposition |
| --- | --- | --- |
| Focused serving/UI tests | `15 passed in 1.09s` | Pass |
| Ruff | `All checks passed!` | Pass |
| Full test suite | `175 passed, 7 warnings in 15.74s` | Pass; all seven warnings are the already documented PyTorch `torch.jit.script` deprecation warning |
| MP4 | H.264, yuv420p, 1440 × 900, 30 fps, 8.000 s, 469,831 bytes | Pass |
| GIF | GIF89a, 1280 × 800, 12 fps, 8.000 s, 2,004,718 bytes | Pass; below 10 MiB |
| Poster | PNG, 1440 × 900, 347,741 bytes | Pass |
| PPTX structure | Microsoft PowerPoint 2007+, 12 slide XML records, 12 notes-slide records; `slides_test.py` reported `Test passed. No overflow detected.` | Pass |
| Speaker notes | Every slide contains both a `5-minute talk track` and a `10-minute talk track` | Pass, 12/12 for each track |
| Rendered visual QA | The Task 3 full-size review checked all 12 LibreOffice-rendered slides; slides 1, 2, 8, and 12 also received full-size contrast checks. No missing image, clipping, overlap, or broken status encoding was recorded. | Pass; fresh structural inspection also passed |
| Post-review control contrast | Desktop 1440 × 900 and mobile 390 × 844 Browser-plugin passes verified readable upload, fixed-example, and primary controls. The ink/paper primary pair measures 18.62:1; the blue focus ring measures 4.31:1 against both paper and ink. The fixed-example MPS Top-5/Grad-CAM flow completed with no relevant console error; mobile width had no horizontal overflow. | Pass |
| Architecture topology | The regenerated slide 2 ends the verified classifier main line at `Serve` and draws `VLM · Exploratory` as a dashed amber branch from bounded serving context. Full-size render and structural checks found no overlap or clipping. | Pass |
| Secrets / credentials | Hits are the scan expression itself or instructional uses of `secrets`; no token-like credential value was found. | Pass |
| Personal absolute paths | Post-remediation strict scan produced no output across tracked files. The internal implementation plan now uses environment-provided tool locations, repository-relative paths, and a runtime temporary root. | Pass |
| Tracked large files | Largest tracked files are the expected deck (3,680,868 bytes), Grad-CAM comparison figure (about 2.7 MiB), GIF (2,004,718 bytes), and MP4 (469,831 bytes). No checkpoint, raw dataset, generated `outputs/`, venv, or cache is tracked. | Pass for artifact scope |
| Overclaim scan | Hits remain capability-boundary statements: not field diagnosis, not a causal Grad-CAM explanation, and not completed LoRA/QLoRA. | Pass |
| Git whitespace | `git diff --check` produced no output. | Pass |

### Remaining Week 8 release work

- Run the documented quick start from a genuinely clean environment. This was
  intentionally not claimed by the Week 7 audit.
- Freeze a release candidate and re-run installation, smoke, data/model-card,
  link, metric, resume-claim, and final artifact audits before any public push.
- Keep manual VQA review and LoRA/QLoRA work explicitly incomplete unless their
  own fixed-protocol evidence is produced.

The post-remediation scan was run from pre-audit HEAD `a614d49` while the four
tracked audit/remediation files were intentionally dirty; it validates their
current content rather than claiming a clean-environment reproduction. The
legacy untracked `docs/presentation/week7_showcase_deck*` artifacts remain
outside Git. No ignored checkpoint, data, cache, output frame, or personal path
was staged, and no remote push or publication was performed.
