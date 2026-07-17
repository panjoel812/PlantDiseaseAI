# Week 8 Local Release Candidate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a locally reproducible `week8-rc1` candidate with machine-readable provenance, clean-environment validation, audited public claims, final research documentation, and evidence-linked application materials.

**Architecture:** A small `plantdisease.release` package provides deterministic hashing, portable manifest records, command-result capture, claim validation, PPTX text extraction, and Markdown link checking. Three validation lanes—clean install, local evidence, and Apple `container`—write detailed ignored outputs, while compact manifests and final documents are tracked.

**Tech Stack:** Python 3.12, dataclasses, pathlib, hashlib, subprocess, JSON, YAML, zipfile/XML, PyTorch, pytest, Ruff, ty, uv, Streamlit, Apple `container`.

## Global Constraints

- Work only on `codex/week8-release-audit`; do not push, publish, create a tag, release, remote PR, or hosted deployment.
- Candidate ID is `week8-rc1`; suggested future tag is `v0.8.0-rc1`, but this plan does not create it.
- Preserve the official-split `227 leaf_id` overlap boundary and all locked Week 2–6 metrics from the approved spec.
- Do not rerun every formal training experiment or start a new model-selection cycle.
- Use a runtime temporary `UV_PROJECT_ENVIRONMENT`, never the repository `.venv`, for the clean-install lane.
- Do not track raw data, checkpoints, caches, temporary environments, container state, secrets, personal absolute paths, or detailed runtime logs.
- Existing untracked `docs/presentation/week7_showcase_deck*` artifacts and the Apple deck inspect sidecar remain untouched and untracked.
- Every validation command has one of `passed`, `failed`, `blocked`, or `not_run`; absence is never success.
- The clean-install lane must pass in full. Only Apple `container` or optional large-data recomputation may be marked `blocked` with evidence.
- Test-set results are recomputed only to verify frozen evidence; they cannot select a new checkpoint or tune a parameter.
- Use test-first development for every new Python behavior and request independent review after each task.

## File Map

- `src/plantdisease/release/__init__.py` — public release-audit interfaces.
- `src/plantdisease/release/manifest.py` — hashing, portable artifact records, environment records, manifest serialization.
- `src/plantdisease/release/claims.py` — claim schema, source/consumer checks, PPTX text extraction, Markdown link checks.
- `src/plantdisease/release/runner.py` — command execution, status capture, output redaction, JSON result serialization.
- `configs/week8_claims.yaml` — locked claims, sources, consumers, and limitation wording.
- `scripts/build_release_candidate.py` — generate the tracked manifest and claim ledger.
- `scripts/audit_week8_claims.py` — fail when claims, limitations, or links drift.
- `scripts/run_week8_repro.py` — execute the clean-install lane into ignored outputs.
- `tests/release/`, `tests/test_week8_release_cli.py` — release helper and CLI tests.
- `reports/release/`, final reports/cards, release/resume/mentor documents — tracked release evidence.

---

### Task 1: Portable release manifest core

**Files:**
- Create: `src/plantdisease/release/__init__.py`
- Create: `src/plantdisease/release/manifest.py`
- Create: `tests/release/test_manifest.py`

**Interfaces:**
- Consumes: repository files and local ignored artifacts.
- Produces:
  - `sha256_file(path: Path, chunk_size: int = 1_048_576) -> str`
  - `logical_repo_path(path: Path, repo_root: Path) -> str`
  - `ArtifactRecord`, `ReleaseManifest`
  - `write_manifest(manifest: ReleaseManifest, output_path: Path) -> None`

- [ ] **Step 1: Write failing hashing and portable-path tests**

```python
from pathlib import Path

import pytest

from plantdisease.release.manifest import logical_repo_path, sha256_file


def test_sha256_file_is_deterministic(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact.bin"
    artifact.write_bytes(b"PlantDiseaseAI\n")
    first = sha256_file(artifact)
    assert len(first) == 64
    assert first == sha256_file(artifact)


def test_logical_repo_path_rejects_outside(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    inside = repo / "reports" / "metrics.json"
    inside.parent.mkdir(parents=True)
    inside.write_text("{}", encoding="utf-8")
    assert logical_repo_path(inside, repo) == "reports/metrics.json"
    with pytest.raises(ValueError, match="outside repository"):
        logical_repo_path(tmp_path / "private.pt", repo)
```

- [ ] **Step 2: Run the tests and verify RED**

Run `uv run pytest tests/release/test_manifest.py -q`.

Expected: collection fails because `plantdisease.release.manifest` does not exist.

- [ ] **Step 3: Implement hashing, path normalization, records, and deterministic JSON**

```python
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal

ValidationStatus = Literal["passed", "failed", "blocked", "not_run"]


def sha256_file(path: Path, chunk_size: int = 1_048_576) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def logical_repo_path(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError as exc:
        raise ValueError(f"path is outside repository: {path.name}") from exc


@dataclass(frozen=True)
class ArtifactRecord:
    logical_path: str
    status: ValidationStatus
    required: bool
    size_bytes: int | None = None
    sha256: str | None = None
    note: str | None = None


@dataclass(frozen=True)
class ReleaseManifest:
    schema_version: int
    candidate_id: str
    source_commit: str
    release_commit: str | None
    generated_at_utc: str
    environment: dict[str, Any]
    artifacts: list[ArtifactRecord] = field(default_factory=list)
    lanes: dict[str, ValidationStatus] = field(default_factory=dict)


def write_manifest(manifest: ReleaseManifest, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(asdict(manifest), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
```

Export these names from `src/plantdisease/release/__init__.py`.

- [ ] **Step 4: Add round-trip and path-safety coverage**

Create a `ReleaseManifest` with candidate `week8-rc1`, one README artifact,
and clean lane `not_run`; serialize it, load it with `json.loads`, and assert
the candidate, lane, SHA field, sorted newline-terminated JSON, and absence of
the current user-home and runtime-temporary absolute prefixes discovered through
`Path.home()` and `tempfile.gettempdir()`.

- [ ] **Step 5: Verify and commit**

```bash
uv run pytest tests/release/test_manifest.py -q
uv run ruff check src/plantdisease/release tests/release/test_manifest.py
git add src/plantdisease/release tests/release/test_manifest.py
git commit -m "feat: add week8 release manifest core"
```

---

### Task 2: Claim, PPTX, and Markdown-link audit

**Files:**
- Create: `configs/week8_claims.yaml`
- Create: `src/plantdisease/release/claims.py`
- Create: `tests/release/test_claims.py`

**Interfaces:**
- Consumes: claim YAML, Markdown files, PPTX slide/notes XML.
- Produces:
  - `ClaimRecord`, `ClaimAuditResult`
  - `load_claims(path: Path) -> list[ClaimRecord]`
  - `extract_pptx_text(path: Path) -> str`
  - `audit_claims(repo_root: Path, claims: list[ClaimRecord]) -> list[ClaimAuditResult]`
  - `find_broken_markdown_links(repo_root: Path, paths: list[Path]) -> list[str]`

- [ ] **Step 1: Add the locked claim configuration**

The YAML contains schema 1 and these exact value/source pairs:

```yaml
claims:
  - {id: official_split_overlap, value: "227", source: reports/data_audit.md, required_boundary: "field"}
  - {id: final_accuracy, value: "0.9953", source: reports/week3_final_model_decision.md, required_boundary: "official split"}
  - {id: final_macro_f1, value: "0.9941", source: reports/week3_final_model_decision.md, required_boundary: "seed 42"}
  - {id: container_observation_ms, value: "129.8", source: reports/week5_demo_engineering.md, required_boundary: "fixed"}
  - {id: qwen_choice_score, value: "11/15", source: reports/week6_vlm_prompt_compare.md, required_boundary: "smoke"}
  - {id: qwen_condition_score, value: "1/5", source: reports/week6_vlm_prompt_compare.md, required_boundary: "condition"}
```

Each claim lists only consumers that actually publish the value: `README.md`,
`docs/blog/week7_technical_blog_zh.md`, and/or
`docs/presentation/week7_apple_showcase_deck.pptx`. Add boundary records for
Grad-CAM non-causality, LoRA incompleteness, field limits, and no professional
diagnosis.

- [ ] **Step 2: Write failing extraction, audit, and link tests**

```python
def test_extract_pptx_text_reads_slide_and_notes(tmp_path: Path) -> None:
    deck = tmp_path / "deck.pptx"
    with ZipFile(deck, "w") as archive:
        archive.writestr("ppt/slides/slide1.xml", "<a:t>0.9953</a:t>")
        archive.writestr("ppt/notesSlides/notesSlide1.xml", "<a:t>official split</a:t>")
    text = extract_pptx_text(deck)
    assert "0.9953" in text
    assert "official split" in text


def test_claim_audit_reports_missing_value(tmp_path: Path) -> None:
    (tmp_path / "report.md").write_text("official split", encoding="utf-8")
    result = audit_claims(
        tmp_path,
        [ClaimRecord("accuracy", "0.9953", "report.md", ("report.md",), "official split")],
    )[0]
    assert result.status == "failed"
    assert result.missing_value_consumers == ("report.md",)


def test_link_audit_reports_only_missing_local_link(tmp_path: Path) -> None:
    readme = tmp_path / "README.md"
    readme.write_text("[ok](docs/ok.md) [bad](docs/missing.md)", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "ok.md").write_text("ok", encoding="utf-8")
    assert find_broken_markdown_links(tmp_path, [readme]) == ["README.md -> docs/missing.md"]
```

Run `uv run pytest tests/release/test_claims.py -q`; expected RED because the
claims module is absent.

- [ ] **Step 3: Implement typed claim records and PPTX extraction**

Use frozen dataclasses for claim/result fields. `extract_pptx_text` opens the
ZIP, sorts `ppt/slides/slide*.xml` and `ppt/notesSlides/notesSlide*.xml`,
extracts `<a:t>` values, HTML-unescapes them, and joins with newlines.
`audit_claims` reads Markdown or extracted PPTX text case-insensitively and
records missing source/value/boundary lists without raising.

- [ ] **Step 4: Implement safe local-link checking**

Match Markdown targets, skip `http://`, `https://`, `mailto:`, `data:`
and anchor-only targets, strip query/fragment parts, resolve relative to the
containing Markdown file, reject paths outside the repo, and return sorted
`"<consumer> -> <target>"` strings.

- [ ] **Step 5: Verify and commit**

```bash
uv run pytest tests/release/test_claims.py -q
uv run ruff check src/plantdisease/release/claims.py tests/release/test_claims.py
git add configs/week8_claims.yaml src/plantdisease/release/claims.py tests/release/test_claims.py
git commit -m "feat: add week8 claim and link audit"
```

---

### Task 3: Command runner, CLIs, and pinned type checking

**Files:**
- Create: `src/plantdisease/release/runner.py`
- Create: `scripts/build_release_candidate.py`
- Create: `scripts/audit_week8_claims.py`
- Create: `scripts/run_week8_repro.py`
- Create: `tests/release/test_runner.py`
- Create: `tests/test_week8_release_cli.py`
- Modify: `pyproject.toml`
- Modify: `uv.lock`

**Interfaces:**
- Consumes: Task 1 manifest and Task 2 claim APIs.
- Produces `CommandSpec`, `CommandResult`, `run_command(...)`, and three stable CLIs.

- [ ] **Step 1: Write failing runner tests**

```python
import sys


def test_run_command_records_pass_and_redacts_repo_root(tmp_path: Path) -> None:
    result = run_command(
        CommandSpec("probe", (sys.executable, "-c", "import os; print(os.getcwd())"), 10),
        repo_root=tmp_path,
        env={},
    )
    assert result.status == "passed"
    assert result.exit_code == 0
    assert str(tmp_path) not in result.stdout
    assert "<REPO_ROOT>" in result.stdout


def test_run_command_records_nonzero_without_raising(tmp_path: Path) -> None:
    result = run_command(
        CommandSpec("failure", (sys.executable, "-c", "raise SystemExit(7)"), 10),
        repo_root=tmp_path,
        env={},
    )
    assert result.status == "failed"
    assert result.exit_code == 7
```

Run `uv run pytest tests/release/test_runner.py -q`; expected RED because the
runner module is absent.

- [ ] **Step 2: Implement the runner**

```python
@dataclass(frozen=True)
class CommandSpec:
    name: str
    argv: tuple[str, ...]
    timeout_seconds: int


@dataclass(frozen=True)
class CommandResult:
    name: str
    status: str
    exit_code: int | None
    stdout: str
    stderr: str


def run_command(spec: CommandSpec, *, repo_root: Path, env: dict[str, str]) -> CommandResult:
    merged_env = os.environ.copy()
    merged_env.update(env)
    try:
        completed = subprocess.run(
            spec.argv,
            cwd=repo_root,
            env=merged_env,
            capture_output=True,
            text=True,
            timeout=spec.timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return CommandResult(
            spec.name,
            "failed",
            None,
            _redact(exc.stdout or "", repo_root),
            "command timed out",
        )
    return CommandResult(
        spec.name,
        "passed" if completed.returncode == 0 else "failed",
        completed.returncode,
        _redact(completed.stdout, repo_root),
        _redact(completed.stderr, repo_root),
    )
```

`_redact` replaces the resolved repo root, user home, and runtime temporary
root with `<REPO_ROOT>`, `<HOME>`, and `<TMP_ROOT>`.

- [ ] **Step 3: Write failing CLI help tests**

```python
def test_week8_clis_expose_help() -> None:
    for script in (
        "scripts/build_release_candidate.py",
        "scripts/audit_week8_claims.py",
        "scripts/run_week8_repro.py",
    ):
        result = subprocess.run(
            [sys.executable, script, "--help"],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        assert "week8" in result.stdout.casefold()
```

Run `uv run pytest tests/test_week8_release_cli.py -q`; expected RED because
the scripts are absent.

- [ ] **Step 4: Implement `build_release_candidate.py`**

Arguments:

```text
--candidate-id week8-rc1
--source-commit <git-sha>
--release-commit <git-sha-or-omit>
--checkpoint outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/checkpoint.pt
--output reports/release/week8_rc1_manifest.json
--claims-output reports/release/week8_claim_evidence.json
```

Capture Python, PyTorch, OS, machine, MPS availability, `uv.lock` SHA256,
checkpoint availability/hash/size, required evidence artifact hashes, and lane
states. All tracked paths are logical repo-relative strings. Serialize with
sorted JSON and write the claim ledger by calling Task 2.

- [ ] **Step 5: Implement `audit_week8_claims.py`**

Accept `--config`, `--output`, and `--check-links`. Write schema 1 JSON
with claim results, boundary results, broken links, counts, and overall status.
Return exit code 1 when any required check fails.

- [ ] **Step 6: Implement `run_week8_repro.py`**

Accept `--environment`, `--output`, and `--smoke-output`. Set
`UV_PROJECT_ENVIRONMENT` to the supplied temporary path and run exactly:

```python
commands = (
    CommandSpec("sync", ("uv", "sync", "--frozen", "--all-groups"), 1800),
    CommandSpec("pytest", ("uv", "run", "pytest", "-q"), 1800),
    CommandSpec("ruff", ("uv", "run", "ruff", "check", "."), 300),
    CommandSpec(
        "typecheck",
        ("uv", "run", "ty", "check", "src/plantdisease", "app", "scripts"),
        600,
    ),
    CommandSpec(
        "claims",
        (
            "uv", "run", "python", "scripts/audit_week8_claims.py",
            "--config", "configs/week8_claims.yaml",
            "--output", "outputs/plantvillage/week8_release/week8-rc1/claims.json",
            "--check-links",
        ),
        300,
    ),
    CommandSpec(
        "smoke",
        (
            "uv", "run", "plant-smoke",
            "--output-dir", "outputs/plantvillage/week8_release/week8-rc1/clean_smoke",
            "--seed", "42", "--image-size", "32",
        ),
        900,
    ),
    CommandSpec("package", ("uv", "build"), 600),
    CommandSpec("cli_help", ("uv", "run", "plant-smoke", "--help"), 120),
)
```

Stop after a required command fails, write gathered results, and exit 1. JSON
contains no temporary environment or personal path.

- [ ] **Step 7: Add and lock the type checker**

Run `uv add --group dev ty`. The resolver updates `pyproject.toml` and
`uv.lock`; never edit the lockfile manually.

- [ ] **Step 8: Verify and commit**

```bash
uv run pytest tests/release/test_runner.py tests/test_week8_release_cli.py -q
uv run ty check src/plantdisease/release scripts/build_release_candidate.py scripts/audit_week8_claims.py scripts/run_week8_repro.py
uv run ruff check src/plantdisease/release scripts tests/release tests/test_week8_release_cli.py
git add pyproject.toml uv.lock src/plantdisease/release/runner.py scripts/build_release_candidate.py scripts/audit_week8_claims.py scripts/run_week8_repro.py tests/release/test_runner.py tests/test_week8_release_cli.py
git commit -m "feat: add week8 release audit commands"
```

Fix concrete project-owned type diagnostics with annotations or narrow input
validation. Do not add a blanket type ignore.

---

### Task 4: Execute and close the clean-install lane

**Files:**
- Create: `reports/release/week8_rc1_manifest.json`
- Create: `reports/release/week8_claim_evidence.json`
- Create: `reports/week8_reproducibility.md`
- Local ignored output: `outputs/plantvillage/week8_release/week8-rc1/`

**Interfaces:**
- Consumes: Task 3 CLIs and committed lockfile.
- Produces: clean-install evidence and initial tracked candidate records.

- [ ] **Step 1: Capture source commit and choose a runtime temp environment**

```bash
SOURCE_COMMIT=$(git rev-parse HEAD)
ENV_ROOT="$(python3 -c 'import tempfile; print(tempfile.gettempdir())')/plantdisease-week8-rc1-venv"
OUTPUT_ROOT=outputs/plantvillage/week8_release/week8-rc1
```

Do not copy the expanded environment path into tracked artifacts.

- [ ] **Step 2: Run clean reproduction**

```bash
uv run python scripts/run_week8_repro.py \
  --environment "$ENV_ROOT" \
  --output "$OUTPUT_ROOT/clean_repro.json" \
  --smoke-output "$OUTPUT_ROOT/clean_smoke"
```

Expected: all eight required results are `passed`. A failed install, test,
Ruff, ty, claim/link audit, smoke, package build, or CLI help keeps Task 4 open.

- [ ] **Step 3: Generate the initial candidate**

```bash
uv run python scripts/build_release_candidate.py \
  --candidate-id week8-rc1 \
  --source-commit "$SOURCE_COMMIT" \
  --checkpoint outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/checkpoint.pt \
  --output reports/release/week8_rc1_manifest.json \
  --claims-output reports/release/week8_claim_evidence.json
```

Expected: schema 1, checkpoint and lockfile SHA256 present, clean lane
`passed`, local/container lanes `not_run`, no personal path.

- [ ] **Step 4: Write `reports/week8_reproducibility.md`**

Record candidate/source commit, clean environment strategy, Python/OS/hardware,
exact commands/statuses, test/Ruff/ty/link/package/CLI/smoke results, runtime,
ignored output paths, known PyTorch warnings, and a statement that clean install
used neither PlantVillage data nor the final checkpoint.

- [ ] **Step 5: Verify and commit**

```bash
jq '[.commands[] | select(.status != "passed")]' "$OUTPUT_ROOT/clean_repro.json"
home_parent="$(dirname "$HOME")"
runtime_temp="$(python3 -c 'import tempfile; print(tempfile.gettempdir())')"
git grep -nIF "$home_parent/" -- reports/release reports/week8_reproducibility.md || true
git grep -nIF "$runtime_temp/" -- reports/release reports/week8_reproducibility.md || true
git diff --check
git add reports/release/week8_rc1_manifest.json reports/release/week8_claim_evidence.json reports/week8_reproducibility.md
git commit -m "docs: record week8 clean reproduction"
```

Expected: the jq result is `[]`; scans and whitespace pass.

---

### Task 5: Recompute local evidence and audit Apple container

**Files:**
- Modify: `reports/release/week8_rc1_manifest.json`
- Modify: `reports/week8_reproducibility.md`
- Local ignored output: `outputs/plantvillage/week8_release/week8-rc1/local_evidence/`

**Interfaces:**
- Consumes: frozen final checkpoint, Week 4 predictions, fixed sample, local data cache, Containerfile.
- Produces: local-evidence and container statuses with hashes and commands.

- [ ] **Step 1: Recompute metrics-derived evidence**

```bash
mkdir -p outputs/plantvillage/week8_release/week8-rc1/local_evidence
uv run plant-evaluate \
  --metrics outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/metrics.json \
  > outputs/plantvillage/week8_release/week8-rc1/local_evidence/metrics_echo.json
uv run plant-calibration-analysis \
  --predictions outputs/plantvillage/week4_explainability/predictions.json \
  --output outputs/plantvillage/week8_release/week8-rc1/local_evidence/calibration.json \
  --report outputs/plantvillage/week8_release/week8-rc1/local_evidence/calibration.md \
  --figure outputs/plantvillage/week8_release/week8-rc1/local_evidence/reliability.png
uv run plant-error-analysis \
  --metrics outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/metrics.json \
  --predictions outputs/plantvillage/week4_explainability/predictions.json \
  --output outputs/plantvillage/week8_release/week8-rc1/local_evidence/error_analysis.json \
  --report outputs/plantvillage/week8_release/week8-rc1/local_evidence/error_analysis.md
```

Expected: Accuracy `0.9953`, Macro F1 `0.9941`, sample count `10709`,
error count `50`, ECE `0.0965`, MCE `0.3348`, Brier `0.0140`.

- [ ] **Step 2: Run inference, Demo, and 24-sample Grad-CAM**

```bash
uv run plant-predict \
  --checkpoint outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/checkpoint.pt \
  --image app/examples/synthetic_leaf.png --top-k 5 \
  > outputs/plantvillage/week8_release/week8-rc1/local_evidence/top5.json
uv run python scripts/demo_e2e.py \
  --checkpoint outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/checkpoint.pt \
  --image app/examples/synthetic_leaf.png \
  --output outputs/plantvillage/week8_release/week8-rc1/local_evidence/demo_e2e.json \
  --overlay-output outputs/plantvillage/week8_release/week8-rc1/local_evidence/demo_overlay.png \
  --device mps --top-k 5
uv run plant-gradcam-atlas \
  --checkpoint outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/checkpoint.pt \
  --frozen-samples outputs/plantvillage/week4_explainability/frozen_samples.json \
  --output-dir outputs/plantvillage/week8_release/week8-rc1/local_evidence/gradcam_atlas \
  --cache-dir data/huggingface \
  --split-manifest outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/split.json \
  --report outputs/plantvillage/week8_release/week8-rc1/local_evidence/gradcam_atlas.md \
  --device mps --target-layer layer4.2
```

Expected: sorted Top-5 probabilities, MPS Demo completion, and a 24-sample
`layer4.2` atlas.

- [ ] **Step 3: Run Apple container validation**

```bash
container --version
container system status
container build -f Containerfile -t localhost/plantdisease-ai:week8-rc1 .
container run --rm -p 8510:8501 \
  -v "$PWD/outputs/plantvillage/week3_ablation/09_combo_candidate_seed42:/models" \
  localhost/plantdisease-ai:week8-rc1
```

From a second terminal run:

```bash
curl --fail --silent http://127.0.0.1:8510/_stcore/health
```

Stop the foreground container with `Ctrl-C`; do not delete images or state. If
an external runtime dependency blocks the lane, record `blocked`, sanitized
error, CLI version, and historical Week 5 evidence. Do not claim Week 8 success.

- [ ] **Step 4: Update, verify, and commit**

Regenerate the manifest and extend the reproducibility report with checkpoint
hash/size, evidence hashes, recomputed equality, MPS result, Grad-CAM count,
container version/image digest/health or blocked reason, and the distinction
between current Week 8 and historical Week 5.

```bash
uv run pytest tests/serving tests/explainability tests/test_demo_e2e.py -q
uv run ruff check .
git diff --check
git add reports/release/week8_rc1_manifest.json reports/week8_reproducibility.md
git commit -m "docs: record week8 local evidence audit"
```

## Task 6: Write the final research and application materials

**Files:**

- Create: `reports/final_experiment_report.md`
- Create: `reports/model_card.md`
- Create: `reports/data_card.md`
- Create: `docs/release/week8_release_checklist.md`
- Create: `docs/resume/week8_resume_evidence.md`
- Create: `docs/mentor/week8_mentor_summary.md`
- Modify: `reports/release/week8_claim_evidence.json`

- [ ] **Step 1: Write the final experiment report**

Use this exact section structure so every research claim has an obvious home:

```markdown
# PlantDiseaseAI Final Experiment Report
## Abstract
## Research Question and Scope
## Related Methods
## Dataset and Split Audit
## Shared Training and Evaluation Protocol
## Five-Model Benchmark
## Controlled Ablation and Model Selection
## Explainability, Error Analysis, and Calibration
## Serving, Streamlit, and Apple Container
## Qwen3-VL Exploration and Safety Prototype
## Reproducibility Audit
## Limitations and Agricultural Safety
## Ethics, Licenses, and Intended Use
## Future Work
## Evidence Index
```

Link every reported number to its machine-readable source. Keep `0.9953`
accuracy and `0.9941` Macro F1 adjacent to both the single-seed limitation and
the official-split overlap warning. Distinguish historical evidence from results
recomputed during Week 8.

- [ ] **Step 2: Write the model card**

Document architecture, logical checkpoint path and SHA-256, the 38-class
closed set, preprocessing, intended and excluded uses, split overlap,
controlled-background bias, per-class limits, calibration, non-causal
Grad-CAM interpretation, hardware, dependency/license context, and checkpoint
retrieval instructions. Never present the model as a field diagnostic system.

- [ ] **Step 3: Write the data card**

Document the loader revision/cache, sample and class counts, split sizes, label
mapping, deterministic validation/test transforms, train-only augmentation,
the official test set's role, overlap and duplicate risk, controlled
backgrounds, storage/license notes, and the need for future entity-isolated
field evaluation.

- [ ] **Step 4: Write the release checklist**

Group checklist items under source/dependencies, clean installation,
tests/Ruff/type checks/link audit, evidence, Demo/container, safety scans,
claims/application materials, known incomplete work, and remote authorization.
State explicitly that the proposed `v0.8.0-rc1` tag has not been created.

- [ ] **Step 5: Write evidence-backed resume bullets**

Provide two or three candidate bullets with direct evidence tables covering:

1. The five-model benchmark and the final seed-42 official-split result.
2. Ablations, Grad-CAM, errors, and calibration with the split-risk boundary.
3. Serving, Streamlit, container work, and the smoke-only Qwen exploration.

Prohibit claims of multi-seed confirmation, field validation, completed LoRA,
online users, publications, awards, or public deployment.

- [ ] **Step 6: Write the one-page mentor summary**

Summarize the research question, contribution, measured results, negative
results, limitations, and next experiments. Keep it short enough to send to a
mentor without relying on the README for context.

- [ ] **Step 7: Audit and commit the materials**

```bash
uv run python scripts/audit_week8_claims.py \
  --config configs/week8_claims.yaml \
  --output reports/release/week8_claim_evidence.json \
  --check-links
uv run ty check src/plantdisease app scripts
uv run ruff check .
git diff --check
git add reports/final_experiment_report.md reports/model_card.md \
  reports/data_card.md reports/release/week8_claim_evidence.json \
  docs/release/week8_release_checklist.md \
  docs/resume/week8_resume_evidence.md \
  docs/mentor/week8_mentor_summary.md
git commit -m "docs: add week8 final research materials"
```

## Task 7: Synchronize project status and lock release provenance

**Files:**

- Modify: `README.md`
- Modify: `TASKS.md`
- Modify: `docs/artifact-index.md`
- Modify: `reports/release/week8_rc1_manifest.json`
- Modify: `reports/release/week8_claim_evidence.json`
- Modify: `reports/week8_reproducibility.md`
- Modify: `docs/release/week8_release_checklist.md`

- [ ] **Step 1: Synchronize the public entry points**

Update README and the artifact index with the Week 8 status, exact reproduction
commands, evidence links, checkpoint retrieval/hash, known incomplete work, and
the statement that no remote push, tag, PR, or publication was performed.

- [ ] **Step 2: Update `TASKS.md` conservatively**

Mark only items whose acceptance evidence exists. Leave the Apple container
item unchecked when its Week 8 lane is blocked, and describe the blocking
evidence rather than treating historical Week 5 success as a current rerun.

- [ ] **Step 3: Run the full validation matrix**

```bash
uv run python scripts/audit_week8_claims.py \
  --config configs/week8_claims.yaml \
  --output reports/release/week8_claim_evidence.json \
  --check-links
uv run pytest tests/release tests/test_week8_release_cli.py -q
uv run ruff check .
uv run ty check src/plantdisease app scripts
uv run pytest -q
node --check scripts/build_week7_apple_showcase.mjs
```

Validate the Week 7 media and deck separately:

```bash
ffprobe -v error -show_entries format=duration \
  -of default=noprint_wrappers=1:nokey=1 \
  docs/demo/week7_apple_showcase.mp4
ffprobe -v error -show_entries format=duration \
  -of default=noprint_wrappers=1:nokey=1 \
  docs/demo/week7_apple_showcase.gif
unzip -Z1 docs/presentation/week7_apple_showcase_deck.pptx \
  | rg '^ppt/slides/slide[0-9]+\.xml$' | wc -l
unzip -Z1 docs/presentation/week7_apple_showcase_deck.pptx \
  | rg '^ppt/notesSlides/notesSlide[0-9]+\.xml$' | wc -l
```

Expected: both media files are 8 seconds and the deck has 12 slides plus 12
speaker-note files.

- [ ] **Step 4: Run repository safety scans**

Scan tracked files for credential-shaped values, personal absolute paths,
tracked raw data/checkpoints/caches, unexpectedly large files, and whitespace
errors. Review every match; do not automatically remove user files.

```bash
git grep -nEI '(api[_-]?key|secret|token|password)[[:space:]]*[:=]'
home_parent="$(dirname "$HOME")"
runtime_temp="$(python3 -c 'import tempfile; print(tempfile.gettempdir())')"
git grep -nF "$home_parent/"
git grep -nF "$runtime_temp/"
git ls-files | rg '(^data/|checkpoint\.(pt|pth)$|\.cache/|__pycache__)'
git ls-files -z | xargs -0 stat -f '%z %N' | sort -nr | head -20
git diff --check
```

- [ ] **Step 5: Commit the synchronized local release candidate**

```bash
git add README.md TASKS.md docs/artifact-index.md \
  reports/release/week8_rc1_manifest.json \
  reports/release/week8_claim_evidence.json \
  reports/week8_reproducibility.md \
  docs/release/week8_release_checklist.md
git commit -m "docs: finalize week8 local release candidate"
```

- [ ] **Step 6: Record immutable release provenance**

Set `release_commit` in the manifest to the commit created in Step 5, regenerate
the manifest and claim ledger without changing source claims, and make the final
provenance-only commit:

```bash
uv run python scripts/build_week8_release_manifest.py \
  --release-id week8-rc1 \
  --release-commit HEAD \
  --output reports/release/week8_rc1_manifest.json
uv run python scripts/audit_week8_claims.py \
  --config configs/week8_claims.yaml \
  --output reports/release/week8_claim_evidence.json \
  --check-links
git diff --check
git add reports/release/week8_rc1_manifest.json \
  reports/release/week8_claim_evidence.json
git commit -m "docs: record week8 release provenance"
```

- [ ] **Step 7: Request an independent review and resolve findings**

Review the range `830429a..HEAD` for correctness, claim honesty, reproducibility,
portability, and accidental repository pollution. Fix every Critical or
Important finding, rerun the affected verification, and request a second review
before calling the branch complete.

- [ ] **Step 8: Hand off the local candidate**

Report commits, exact validation results, evidence paths, blocked lanes, and
remaining Week 8 items. Do not push, merge, create a tag, publish a release, or
open a PR until the user explicitly authorizes that external action.
