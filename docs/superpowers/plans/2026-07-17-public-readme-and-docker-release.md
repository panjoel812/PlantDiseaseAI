# Public README and Cross-Platform Docker Release Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish an English-first teaching README with a compact Chinese entry, verified Linux/macOS Bash and Windows PowerShell Docker instructions, and an audited public GitHub repository at `panjoel812/PlantDiseaseAI`.

**Architecture:** `README.md` becomes the canonical operational guide and `README.zh-CN.md` becomes a concise Chinese navigation layer. A release contract test locks platform, Docker, checkpoint, research-boundary, and safety wording. Documentation changes are committed before the manifest is regenerated from that exact source commit; the final audited tip is then bootstrapped directly to a new public `main` branch because no pre-existing GitHub base branch exists.

**Tech Stack:** Markdown, Python 3.12, pytest, `uv`, Docker/OCI `Containerfile`, Streamlit, React/Vite, Git, GitHub CLI.

## Global Constraints

- `README.md` is English-first and canonical; `README.zh-CN.md` is a compact Chinese entry, not a duplicated command manual.
- Python support remains `>=3.12,<3.13`; no dependency versions change.
- The container remains CPU-only Streamlit and mounts `/models/checkpoint.pt` read-only; it does not include React or Qwen.
- The final checkpoint, PlantVillage data, Qwen weights, `outputs/`, caches, credentials, and personal paths remain outside GitHub.
- Qwen MLX remains optional and Apple-Silicon-only with local-cache weights and no automatic download.
- Accuracy `0.9953` and Macro F1 `0.9941` remain seed-42 official-split observations with 227 overlapping `leaf_id` values and no field-validation claim.
- Grad-CAM remains non-causal; all outputs are educational research material, not professional diagnosis or treatment advice.
- Do not create a Git tag, GitHub Release, hosted deployment, or container-registry image.
- Preserve unrelated untracked presentation decks, inspection sidecars, and LaTeX auxiliary files.
- Never delete files permanently; use `/usr/bin/trash <absolute-path>` only if a removal becomes necessary.

## 2026-07-17 override

The original plan required Docker build and health execution before
publication. The user later chose Apple `container` locally and declined Docker
installation. This 2026-07-17 override supersedes the original Docker publication gate while retaining the runtime steps below as historical plan
context. The revised acceptance boundary requires focused documentation
contracts, static command inspection, and claim/link audits to pass without any
Docker runtime claim. Docker Engine/Desktop runtime remains `not_run`, and Windows PowerShell validation remains static-only. Public history construction
and publication remain later tasks and are not performed by this source-content
update.

---

### Task 1: Lock the public README contract

**Files:**
- Create: `tests/release/test_public_readme_contract.py`
- Reference: `README.md`
- Reference: `README.zh-CN.md`
- Reference: `Containerfile`

**Interfaces:**
- Consumes: the approved design in `docs/superpowers/specs/2026-07-17-public-readme-and-docker-release-design.md`.
- Produces: pytest functions that reject missing language navigation, platform distinctions, Docker commands, checkpoint boundaries, or research/safety qualifiers.

- [ ] **Step 1: Write the failing contract tests**

Create `tests/release/test_public_readme_contract.py` with:

```python
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
README = ROOT / "README.md"
README_ZH = ROOT / "README.zh-CN.md"
CONTAINERFILE = ROOT / "Containerfile"


def test_public_readme_has_layered_teaching_structure() -> None:
    text = README.read_text(encoding="utf-8")
    required = (
        "[English](README.md) | [简体中文](README.zh-CN.md)",
        "## What you can try",
        "## Architecture",
        "## Platform support",
        "## Prerequisites",
        "## Five-minute smoke test",
        "## Train and evaluate on PlantVillage",
        "## React + FastAPI demo",
        "## Streamlit demo",
        "## Docker on Linux, macOS, and Windows",
        "## Reproducibility and evidence",
        "## Known limitations",
        "## Safety",
    )
    for fragment in required:
        assert fragment in text


def test_public_readme_has_copyable_cross_platform_docker_commands() -> None:
    text = README.read_text(encoding="utf-8")
    required = (
        "docker build -f Containerfile -t plantdisease-ai:week8 .",
        'MODEL_DIR="$(pwd)/outputs/plantvillage/week3_ablation/09_combo_candidate_seed42"',
        '--mount "type=bind,src=${MODEL_DIR},dst=/models,readonly"',
        '$ModelDir = (Resolve-Path ".\\outputs\\plantvillage\\week3_ablation\\09_combo_candidate_seed42").Path',
        '--mount "type=bind,source=$ModelDir,target=/models,readonly"',
        "curl --fail http://127.0.0.1:8501/_stcore/health",
        "Invoke-RestMethod http://127.0.0.1:8501/_stcore/health",
        "Docker Desktop with the WSL2 backend",
        "CPU-only Streamlit image",
    )
    for fragment in required:
        assert fragment in text


def test_public_readme_keeps_model_and_research_boundaries() -> None:
    text = README.read_text(encoding="utf-8")
    required = (
        "The final checkpoint is not distributed in this repository",
        "single seed 42",
        "227 overlapping `leaf_id` values",
        "not evidence of field generalization",
        "Grad-CAM is a non-causal relevance visualization",
        "educational and research use only",
        "No automatic download",
        "Apple Silicon",
    )
    for fragment in required:
        assert fragment in text


def test_chinese_entry_is_present_and_links_to_canonical_guide() -> None:
    text = README_ZH.read_text(encoding="utf-8")
    assert "[English](README.md) | [简体中文](README.zh-CN.md)" in text
    assert "完整英文运行指南" in text
    assert "docs/tutorials/README.md" in text
    assert "paper/out/plantdisease_ai_zh.pdf" in text
    assert "不会自动下载" in text
    assert "仅供教育和研究使用" in text


def test_containerfile_matches_documented_runtime_contract() -> None:
    text = CONTAINERFILE.read_text(encoding="utf-8")
    assert "ENV UV_TORCH_BACKEND=cpu" in text
    assert 'EXPOSE 8501' in text
    assert '"--checkpoint", "/models/checkpoint.pt"' in text
    assert "COPY outputs" not in text
    assert "COPY data" not in text
```

- [ ] **Step 2: Run the tests to verify RED**

Run:

```bash
PYTHONPATH=src .venv/bin/pytest tests/release/test_public_readme_contract.py -q
```

Expected: failures because `README.zh-CN.md` does not exist and the current
README lacks the approved English headings and Docker Desktop/PowerShell text.

- [ ] **Step 3: Run Ruff on the new test**

Run:

```bash
.venv/bin/ruff check tests/release/test_public_readme_contract.py
```

Expected: `All checks passed!` even while the behavioral contract is RED.

---

### Task 2: Build the English teaching README and Chinese entry

**Files:**
- Modify: `README.md`
- Create: `README.zh-CN.md`
- Modify: `Containerfile`
- Test: `tests/release/test_public_readme_contract.py`

**Interfaces:**
- Consumes: the exact heading/wording contract from Task 1 and all existing project CLI entry points.
- Produces: canonical English commands, compact Chinese navigation, and matching CPU-only container comments used by readers and release audits.

- [ ] **Step 1: Replace the historical-log README with the approved layered guide**

Write `README.md` with the exact section order below. Use the existing verified
desktop screenshot and evidence links; do not copy estimated metrics.

```markdown
[English](README.md) | [简体中文](README.zh-CN.md)

<p align="center"><strong>PLANTDISEASEAI · AUDITABLE RESEARCH DEMO</strong></p>

# Evidence before diagnosis

PlantDiseaseAI is a reproducible plant-leaf classification research project:
five shared-protocol CNN benchmarks, controlled ablation, error and calibration
analysis, Grad-CAM, a React/FastAPI interface, a Streamlit container interface,
and a deliberately bounded Qwen3-VL smoke branch.

![PlantDiseaseAI React Liquid Glass demo](reports/figures/week8_react_demo_desktop.png)

| Test Accuracy | Macro F1 | Models compared |
| ---: | ---: | ---: |
| 0.9953 | 0.9941 | 5 |

> Result boundary: this is one single seed 42 observation on the PlantVillage
> official split. The audit found 227 overlapping `leaf_id` values between train
> and test. It is not evidence of field generalization or professional diagnosis.

## What you can try

| Path | Needs data | Needs checkpoint | Purpose |
| --- | --- | --- | --- |
| Five-minute smoke | No | No | Validate install, data/model/evaluation wiring |
| Local React or Streamlit demo | No | Yes | Try Top-5 prediction and Grad-CAM |
| Full research reproduction | Yes | Trained locally | Recreate audits, training, evaluation, and analysis |

The final checkpoint is not distributed in this repository. Train it from a
tracked configuration or provide a compatible local checkpoint and verify its
hash against `reports/release/week8_rc1_manifest.json`.

## Table of contents

- [Architecture](#architecture)
- [Platform support](#platform-support)
- [Prerequisites](#prerequisites)
- [Five-minute smoke test](#five-minute-smoke-test)
- [Train and evaluate on PlantVillage](#train-and-evaluate-on-plantvillage)
- [React + FastAPI demo](#react--fastapi-demo)
- [Streamlit demo](#streamlit-demo)
- [Docker on Linux, macOS, and Windows](#docker-on-linux-macos-and-windows)
- [Optional Qwen panel](#optional-qwen-panel)
- [Reproducibility and evidence](#reproducibility-and-evidence)
- [Known limitations](#known-limitations)

## Architecture

Document the flow `image -> deterministic preprocessing -> ResNet50 -> Top-5`
and the separate Grad-CAM relevance path. Explain that FastAPI exposes the
classifier service to React, Streamlit uses the same serving layer, and Qwen is
an optional context branch rather than the classifier truth source. Link
`docs/project-architecture.md` for the complete module map.

## Platform support

Include the exact four-row platform matrix from the approved design. State that
Linux/Windows support describes intended interfaces, while only environments in
`reports/week8_reproducibility.md` are completed audit evidence.

## Prerequisites

List Python 3.12, `uv`, Git, Node.js/npm for React, and Docker Engine/Desktop for
the Streamlit container. State that Windows Python commands are intended for
WSL2 and Docker Desktop must use the WSL2 backend.

## Five-minute smoke test

```bash
git clone https://github.com/panjoel812/PlantDiseaseAI.git
cd PlantDiseaseAI
uv sync --all-groups
uv run plant-smoke --output-dir outputs/smoke/week1 --seed 42 --image-size 32
uv run pytest -q
```

State that synthetic smoke validates plumbing and does not reproduce the
reported PlantVillage metrics.

## Train and evaluate on PlantVillage

Show the existing `download_data.py`, `plant-audit`, 500-sample smoke training,
full `configs/week3_ablation/09_combo_candidate.yaml` training, `plant-evaluate`,
`plant-predict`, `plant-error-analysis`, `plant-calibration-analysis`, and
`plant-gradcam-atlas` commands. Define each output and retain the official-split,
single-seed, and overlap qualifiers.

## React + FastAPI demo

Show two terminals: `scripts/run_demo_api.py` with a local checkpoint and
`npm ci && npm run dev` from `frontend/`. State that the bundled field image has
no verified ground truth and its visible output is a prediction, not accuracy
evidence.

## Streamlit demo

Show `uv run streamlit run app/streamlit_app.py ... --checkpoint ... --device
cpu` and link the service/model card.

## Docker on Linux, macOS, and Windows

State that `Containerfile` builds a CPU-only Streamlit image. It does not contain
the checkpoint, PlantVillage data, React development server, or Qwen runtime.

### Build the image

```bash
docker build -f Containerfile -t plantdisease-ai:week8 .
```

### Linux or macOS with Bash

```bash
MODEL_DIR="$(pwd)/outputs/plantvillage/week3_ablation/09_combo_candidate_seed42"
test -f "${MODEL_DIR}/checkpoint.pt"

docker run -d --rm --name plantdisease-ai \
  -p 8501:8501 \
  --mount "type=bind,src=${MODEL_DIR},dst=/models,readonly" \
  plantdisease-ai:week8

curl --fail http://127.0.0.1:8501/_stcore/health
docker logs plantdisease-ai
docker stop plantdisease-ai
```

### Windows PowerShell with Docker Desktop

Use Docker Desktop with the WSL2 backend. Ensure the repository path is shared
with Docker Desktop.

```powershell
docker build -f Containerfile -t plantdisease-ai:week8 .

$ModelDir = (Resolve-Path ".\outputs\plantvillage\week3_ablation\09_combo_candidate_seed42").Path
if (-not (Test-Path "$ModelDir\checkpoint.pt")) { throw "checkpoint.pt not found" }

docker run -d --rm --name plantdisease-ai `
  -p 8501:8501 `
  --mount "type=bind,source=$ModelDir,target=/models,readonly" `
  plantdisease-ai:week8

Invoke-RestMethod http://127.0.0.1:8501/_stcore/health
docker logs plantdisease-ai
docker stop plantdisease-ai
```

Add the six approved troubleshooting bullets for checkpoint, mount sharing,
port collision, startup health, CPU-only dependencies, and Apple `container`
separation.

## Optional Qwen panel

State **No automatic download**. Explain the Apple Silicon + MLX requirement,
the explicit `uv sync --group vlm` and `hf download` commands, the verified
`ready=false` unavailable state without local weights, and the 5-image/15-question
smoke boundary. Linux/Windows are unsupported by the current MLX implementation.

## Reproducibility and evidence

Link the final report, manifest, claim ledger, model/data cards, bilingual PDFs,
presentation, chart index, and artifact index. Distinguish historical 226-test
runtime evidence from the refreshed manifest’s `not_run` runtime lanes.

## Known limitations

List official-split overlap, single seed, controlled backgrounds, no external
field validation, no entity-isolated final protocol, no calibrated professional
risk threshold, incomplete human VQA audit, and no LoRA/QLoRA.

## Repository map

Explain `configs/`, `src/plantdisease/`, `app/`, `frontend/`, `scripts/`,
`tests/`, `reports/`, `paper/`, and `docs/`.

## Development checks

Show pytest, Ruff, `ty`, React test/lint/build, claim audit, and paper audit.

## Safety

PlantDiseaseAI outputs are for educational and research use only. They are not
professional plant diagnosis, pesticide, dosage, treatment, regulatory, or
insurance advice. Grad-CAM is a non-causal relevance visualization.

## License

[MIT](LICENSE)
```

- [ ] **Step 2: Add the compact Chinese navigation page**

Create `README.zh-CN.md` with the same language switch, result boundary, three
start lanes, Chinese platform matrix, and these exact navigation links:

```markdown
[English](README.md) | [简体中文](README.zh-CN.md)

# PlantDiseaseAI 中文入口

PlantDiseaseAI 是一个强调证据链与能力边界的植物叶片病害分类研究项目。
正式候选的 0.9953 Accuracy / 0.9941 Macro F1 是 official split、single seed
42 的单次结果；train/test 存在 227 个重叠 `leaf_id`，不能当作田间泛化或
专业诊断证据。

## 从哪里开始

- [完整英文运行指南](README.md)：安装、数据、训练、评估、React、Streamlit、
  Linux/Windows Docker 与故障排查。
- [新生代码教程](docs/tutorials/README.md)：Dataset、Transform、Model、Train、
  Metrics 与数学基础。
- [中文论文](paper/out/plantdisease_ai_zh.pdf)
- [双语答辩大纲](docs/presentation/plantdisease_ai_complete_bilingual_outline.md)
- [成果证据索引](docs/artifact-index.md)

## 三条体验路径

1. 合成 smoke：不需要 PlantVillage 或 checkpoint，只验证代码链路。
2. React/Streamlit Demo：需要本地兼容 checkpoint；仓库不提供自动下载。
3. 完整研究复现：需要约 2 GB PlantVillage 数据，并按配置训练与审计。

## 平台说明

分类主线可在 macOS、Linux 以及 Windows 11 的 WSL2 环境运行；Windows 容器
使用 Docker Desktop WSL2 backend。可选 Qwen 面板当前依赖 Apple Silicon
上的 MLX 与已存在的本地权重，Linux/Windows 不支持；浏览器与 API 不会自动下载
Qwen 权重。

## 安全边界

项目输出仅供教育和研究使用，不构成专业植物诊断、农药、剂量或处置建议。
Grad-CAM 是相关性可视化，不是因果解释。田间样例没有已验证真值，页面结果只是
模型 prediction。
```

- [ ] **Step 3: Normalize the Containerfile usage comments**

Change only the trailing comments from the Apple-only `week5` example to:

```dockerfile
# Build with Docker Engine/Desktop:
# docker build -f Containerfile -t plantdisease-ai:week8 .
# Run with a read-only checkpoint directory mounted at /models.
# Apple container uses the same Containerfile with its own build/run syntax.
# Runtime: Streamlit, CPU-only, checkpoint=/models/checkpoint.pt
```

Do not change the executable `CMD`, base image, dependency installation, port,
or health check.

- [ ] **Step 4: Run the contract tests to verify GREEN**

Run:

```bash
PYTHONPATH=src .venv/bin/pytest tests/release/test_public_readme_contract.py -q
```

Expected: `5 passed`.

- [ ] **Step 5: Run documentation checks**

Run:

```bash
.venv/bin/ruff check tests/release/test_public_readme_contract.py
PYTHONPATH=src .venv/bin/python scripts/audit_week8_claims.py \
  --config configs/week8_claims.yaml \
  --output /private/tmp/week8-public-readme-claims.json \
  --check-links
git diff --check
```

Expected: Ruff passes, claim/link audit reports `status=passed`, and Git diff
check exits 0.

- [ ] **Step 6: Commit the teaching documentation**

```bash
git add README.md README.zh-CN.md Containerfile tests/release/test_public_readme_contract.py
git commit -m "docs: add public setup and Docker guide"
```

---

### Task 3: Verify the documented Docker path

**Files:**
- Verify: `Containerfile`
- Verify: `.dockerignore`
- Verify: `README.md`
- Local-only output: `/private/tmp/plantdisease-public-docker-health.txt`

**Interfaces:**
- Consumes: the local checkpoint directory and the `plantdisease-ai:week8` image contract from Task 2.
- Produces: fresh build, launch, health, and log evidence without changing tracked runtime-lane status.

- [ ] **Step 1: Confirm required local inputs and exclusions**

Run:

```bash
test -f outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/checkpoint.pt
test -f Containerfile
test -f .dockerignore
rg -n '^/(data|outputs|paper/out)/$|^\*\.pt$|^\.env' .dockerignore
```

Expected: all files exist and `.dockerignore` excludes data, outputs, paper
build outputs, checkpoints, and environment files.

- [ ] **Step 2: Build the CPU image**

Run:

```bash
docker build -f Containerfile -t plantdisease-ai:week8 .
```

Expected: exit 0; the build uses the current `UV_TORCH_BACKEND=cpu` layer.

- [ ] **Step 3: Launch with the read-only checkpoint mount**

Run:

```bash
MODEL_DIR="$(pwd)/outputs/plantvillage/week3_ablation/09_combo_candidate_seed42"
docker run -d --name plantdisease-ai-readme-qa \
  --rm \
  -p 8505:8501 \
  --mount "type=bind,src=${MODEL_DIR},dst=/models,readonly" \
  plantdisease-ai:week8
```

Expected: prints a container ID and leaves the QA container running.

- [ ] **Step 4: Verify health and runtime logs**

Run:

```bash
curl --retry 20 --retry-delay 2 --retry-connrefused --fail \
  http://127.0.0.1:8505/_stcore/health \
  -o /private/tmp/plantdisease-public-docker-health.txt
docker inspect --format '{{json .Mounts}}' plantdisease-ai-readme-qa
docker logs plantdisease-ai-readme-qa
```

Expected: health body is `ok`; mount JSON reports `/models` with read-only true;
logs contain the Streamlit URL and no missing-checkpoint error.

- [ ] **Step 5: Stop the QA container recoverably**

Run:

```bash
docker stop plantdisease-ai-readme-qa
```

Expected: prints `plantdisease-ai-readme-qa`. Do not use `docker rm`; the
QA container was launched with `--rm`, so Docker removes that generated runtime
resource automatically after it stops. Never delete repository files.

- [ ] **Step 6: Validate PowerShell blocks statically or with `pwsh`**

Run:

```bash
if command -v pwsh >/dev/null 2>&1; then
  pwsh -NoProfile -Command '$text = Get-Content README.md -Raw; if ($text -notmatch "Docker Desktop with the WSL2 backend") { exit 1 }'
else
  rg -n 'Resolve-Path|Test-Path|Docker Desktop with the WSL2 backend|target=/models,readonly|Invoke-RestMethod' README.md
fi
```

Expected: exit 0. Report explicitly whether PowerShell was parsed by `pwsh` or
only checked statically on macOS.

---

### Task 4: Run final verification and refresh the release manifest

**Files:**
- Modify: `reports/release/week8_rc1_manifest.json`
- Verify: `reports/release/week8_claim_evidence.json`
- Verify: all tracked source, docs, frontend, chart, and paper artifacts

**Interfaces:**
- Consumes: the exact documentation source commit from Task 2.
- Produces: a manifest whose `source_commit` equals that commit and whose tracked artifact sizes/SHA-256 values match the working tree.

- [ ] **Step 1: Run the complete Python and static suite**

Run outside the filesystem/process sandbox because the DataLoader test requires
shared memory:

```bash
PYTHONPATH=src .venv/bin/pytest -q
.venv/bin/ruff check .
.venv/bin/ty check src/plantdisease app scripts
uv build
```

Expected: 0 pytest failures, both static tools pass, and wheel/sdist build exits
0. Record the actual test count rather than assuming the previous 288 count.

- [ ] **Step 2: Run React and presentation verification**

Run:

```bash
cd frontend
npm run test:run
npm run lint
npm run build
cd ..
NODE_PATH="$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules" \
  node scripts/validate_presentation_chart_generator.mjs
node scripts/validate_presentation_slide_map.mjs
PYTHONPATH=src .venv/bin/python scripts/audit_week8_paper.py \
  --zh paper/zh/main.tex --en paper/en/main.tex \
  --claims paper/shared/week8_verified_claims.tex \
  --output /private/tmp/week8-public-paper-audit.json
```

Expected: 47 React tests, clean Oxlint/build, 24 validated SVG/PNG chart pairs,
45/45 slide-map entries, and a passed 13-section bilingual paper audit.

- [ ] **Step 3: Capture the exact source commit**

Run:

```bash
SOURCE_COMMIT="$(git rev-parse HEAD)"
git show --no-patch --format='%H %s' "$SOURCE_COMMIT"
```

Expected: the commit is `docs: add public setup and Docker guide` and includes
README, Chinese entry, Containerfile comments, and the contract test.

- [ ] **Step 4: Regenerate the manifest from that commit**

Run in the host environment so Apple MPS availability is recorded accurately:

```bash
PYTHONPATH=src .venv/bin/python scripts/build_release_candidate.py \
  --candidate-id week8-rc1 \
  --source-commit "$SOURCE_COMMIT" \
  --checkpoint outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/checkpoint.pt \
  --output reports/release/week8_rc1_manifest.json \
  --claims-output reports/release/week8_claim_evidence.json
```

Expected: JSON status `passed`; claims/evidence pass; clean/package/local/container
remain `not_run`; no historical `lane_evidence` is inherited.

- [ ] **Step 5: Verify manifest identity and repository hygiene**

Run:

```bash
PYTHONPATH=src .venv/bin/pytest \
  tests/test_week8_release_cli.py::test_checked_in_release_manifest_matches_tracked_artifacts \
  tests/release/test_claims.py::test_tracked_text_does_not_publish_personal_macos_paths \
  -q
git diff --check
git status --short
```

Expected: both tests pass; only the refreshed manifest is an intended tracked
change; unrelated untracked presentation/LaTeX files remain untouched.

- [ ] **Step 6: Commit the refreshed manifest**

```bash
git add reports/release/week8_rc1_manifest.json
git commit -m "chore: refresh public release manifest"
```

---

### Task 5: Bootstrap and verify the public GitHub repository

**Files:**
- External create: `https://github.com/panjoel812/PlantDiseaseAI`
- Local Git metadata: add remote `origin`
- No repository file changes expected

**Interfaces:**
- Consumes: the final audited local tip and authenticated GitHub CLI account `panjoel812`.
- Produces: a public GitHub repository whose default `main` points to the audited tip.

- [ ] **Step 1: Verify publication scope and authentication**

Run in the host environment:

```bash
gh auth status
git status -sb
git log -4 --oneline
git remote -v
gh repo view panjoel812/PlantDiseaseAI --json nameWithOwner,visibility,url
```

Expected: GitHub authentication is active; intended commits are present; no
remote exists; repository lookup still reports not found. Untracked user files
are not staged and will not be published.

- [ ] **Step 2: Scan the exact tracked publication set**

Run:

```bash
PERSONAL_PREFIX="$(printf '/%s/%s' Users panjoel)"
git ls-files -z | xargs -0 rg -n "${PERSONAL_PREFIX}|gho_[A-Za-z0-9_]+|github_pat_[A-Za-z0-9_]+" || true
git ls-files -z | xargs -0 stat -f '%z %N' | sort -nr | head -20
git ls-files | rg '\.(pt|pth|ckpt|onnx)$|(^|/)(data|\.venv|node_modules|dist)/' && exit 1 || true
```

Expected: no personal path/token match, no tracked model checkpoint/raw data/
cache/build directory, and the largest intended tracked files are reviewed.

- [ ] **Step 3: Create the empty public repository**

Run:

```bash
gh repo create panjoel812/PlantDiseaseAI \
  --public \
  --description "Auditable plant-disease classification research pipeline with Grad-CAM, React, Streamlit, and bounded Qwen exploration"
```

Expected: GitHub returns `https://github.com/panjoel812/PlantDiseaseAI` and does
not generate a remote README, license, or `.gitignore`.

- [ ] **Step 4: Add origin and publish the audited tip as main**

Run:

```bash
git remote add origin https://github.com/panjoel812/PlantDiseaseAI.git
git push -u origin HEAD:main
```

Expected: push succeeds and remote `main` points to the local final commit.
Because this is a new repository with no pre-existing base branch, do not create
an empty or zero-diff pull request.

- [ ] **Step 5: Set and verify the default branch and visibility**

Run:

```bash
gh repo edit panjoel812/PlantDiseaseAI --default-branch main
gh repo view panjoel812/PlantDiseaseAI \
  --json nameWithOwner,defaultBranchRef,visibility,url
git ls-remote --heads origin main
gh release list --repo panjoel812/PlantDiseaseAI
```

Expected: `visibility` is `PUBLIC`, default branch is `main`, remote main SHA
matches the local final tip, and no GitHub Release exists.

- [ ] **Step 6: Verify the public README and forbidden paths remotely**

Run:

```bash
gh api repos/panjoel812/PlantDiseaseAI/readme --jq '.html_url'
gh api repos/panjoel812/PlantDiseaseAI/git/trees/main?recursive=1 \
  --jq '.tree[].path' \
  | rg '\.(pt|pth|ckpt|onnx)$|(^|/)(data|\.venv|node_modules)/' \
  && exit 1 || true
```

Expected: README URL is returned and the forbidden-path scan has no matches.

- [ ] **Step 7: Report publication evidence**

Report:

- public repository URL;
- remote/default branch and final commit SHA;
- README and Chinese entry links;
- actual pytest/React/build/Docker verification results;
- Docker verification platform and the fact that Windows PowerShell was static
  unless `pwsh` was available;
- no checkpoint/data/Qwen weights, tag, Release, or hosted deployment.

Keep the local branch/worktree; do not delete or clean it after publication.
