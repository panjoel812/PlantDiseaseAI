# Public README and Cross-Platform Docker Release Design

## Decision

PlantDiseaseAI will use an English-first, layered teaching README for its public
GitHub repository. A compact Chinese navigation page will preserve a clear
Chinese entry without duplicating every command and allowing the two languages
to drift. The public repository will be `panjoel812/PlantDiseaseAI` with public
visibility.

## Goals

- Let a new reader understand the research question, verified result, and
  limitations before running anything.
- Provide a no-dataset smoke path, a trained-checkpoint demo path, and a full
  research reproduction path.
- Teach the project architecture and the relationship between training,
  evaluation, inference, Grad-CAM, Streamlit, React/FastAPI, and optional Qwen.
- Provide copyable Docker Engine/Desktop instructions for Linux, macOS, and
  Windows PowerShell.
- Keep every metric attached to its protocol and evidence source.
- Publish source code and small audited artifacts without publishing raw data,
  checkpoints, caches, credentials, or claiming a hosted deployment.

## Non-goals

- Do not add a new application feature, hosted service, model download, or
  container registry image.
- Do not claim Windows/Linux validation for the Apple-Silicon-only MLX Qwen
  runtime.
- Do not embed the final checkpoint in the container image or Git history.
- Do not create a Git tag, GitHub Release, or public model artifact.
- Do not rewrite historical experiment reports or alter measured results.

## Audience and Language

The primary audience is students, reviewers, and engineers encountering the
repository for the first time. `README.md` is the canonical English operational
guide. `README.zh-CN.md` is a concise Chinese map that explains the project,
states the same research and safety boundaries, and links readers to the
canonical commands plus existing Chinese tutorials, paper, presentation
outline, and reports.

The English README begins with a language switch:

```markdown
[English](README.md) | [简体中文](README.zh-CN.md)
```

## README Information Architecture

`README.md` will use this order:

1. Hero, screenshot, verified result snapshot, and research boundary.
2. “What you can try” with three lanes:
   - five-minute synthetic smoke with no dataset or checkpoint;
   - local UI demo with a user-supplied or locally trained checkpoint;
   - full research reproduction with PlantVillage data.
3. Table of contents.
4. Project capabilities and explicit non-capabilities.
5. Architecture and data flow from image to classifier, Top-5, Grad-CAM, and
   UI, with Qwen shown as an optional bounded branch.
6. Platform and capability matrix.
7. Prerequisites and installation with Python 3.12, `uv`, Node.js for React,
   and Docker only for the Streamlit container lane.
8. Quick smoke tutorial.
9. Dataset download, audit, training, evaluation, prediction, Grad-CAM, and
   calibration tutorial.
10. React/FastAPI demo tutorial, including the supplied image’s no-ground-truth
    boundary and Qwen local-cache behavior.
11. Streamlit tutorial.
12. Cross-platform Docker tutorial.
13. Reproducibility, evidence, results, and known limitations.
14. Repository map, tests, contribution guidance, safety, and license.

Historical week-by-week detail will be summarized rather than occupying the
main learning path. Deep evidence remains linked through `TASKS.md`, reports,
papers, and `docs/artifact-index.md`.

## Teaching Lanes

### Lane 1: Smoke without data

The first runnable path uses `plant-smoke` and synthetic data. It must say that
this validates wiring only and does not reproduce the reported PlantVillage
metrics.

```bash
uv sync --all-groups
uv run plant-smoke --output-dir outputs/smoke/week1 --seed 42 --image-size 32
uv run pytest -q
```

### Lane 2: Demo with a checkpoint

The README must explain that the final checkpoint is intentionally not stored
in GitHub. A reader can either train a checkpoint with a documented config or
provide a compatible local checkpoint and verify its identity. React/FastAPI
and Streamlit commands must fail transparently when `/models/checkpoint.pt` or
the local checkpoint path is absent; the documentation must not imply a public
download exists.

### Lane 3: Research reproduction

The full lane covers the pinned data loader, audit, training configuration,
evaluation, inference, error analysis, calibration, and Grad-CAM. Reported
results remain single-seed official-split observations with 227 overlapping
`leaf_id` values and no field-generalization claim.

## Platform Capability Matrix

The README will distinguish these supported paths:

| Capability | macOS Apple Silicon | Linux | Windows 11 + WSL2/Docker Desktop |
| --- | --- | --- | --- |
| Python smoke/train/evaluate | Yes | Yes, CPU/CUDA depends on local PyTorch | Yes through WSL2; native PowerShell is not the audited Python lane |
| React/FastAPI classifier UI | Yes | Yes with a compatible checkpoint | Yes through WSL2 |
| Streamlit container | Apple `container` or Docker | Docker Engine | Docker Desktop with WSL2 backend |
| Qwen MLX panel | Optional, local weights only | No in the current implementation | No in the current implementation |

“Yes” means the documented interface is intended to work; only the exact
recorded environments in the reproducibility report are evidence of a completed
audit.

## Docker Design

The existing `Containerfile` remains CPU-only and runs the Streamlit interface.
It never copies a checkpoint, raw data, `outputs/`, `.venv`, or secrets into the
image. The final checkpoint directory is mounted read-only at `/models`.

### Common build

All Docker users build from the repository root:

```bash
docker build -f Containerfile -t plantdisease-ai:week8 .
```

The documentation will note that this image provides Streamlit, not the React
development server or MLX Qwen runtime.

### Linux and macOS Bash

```bash
MODEL_DIR="$(pwd)/outputs/plantvillage/week3_ablation/09_combo_candidate_seed42"

docker run -d --rm --name plantdisease-ai \
  -p 8501:8501 \
  --mount "type=bind,src=${MODEL_DIR},dst=/models,readonly" \
  plantdisease-ai:week8

curl --fail http://127.0.0.1:8501/_stcore/health
docker logs plantdisease-ai
docker stop plantdisease-ai
```

The README will require `${MODEL_DIR}/checkpoint.pt` to exist before launch.

### Windows PowerShell

Docker Desktop must use the WSL2 backend and the repository/model path must be
shared with Docker Desktop. Commands are native PowerShell and avoid Bash-only
`$PWD` interpolation:

```powershell
docker build -f Containerfile -t plantdisease-ai:week8 .

$ModelDir = (Resolve-Path ".\outputs\plantvillage\week3_ablation\09_combo_candidate_seed42").Path

docker run -d --rm --name plantdisease-ai `
  -p 8501:8501 `
  --mount "type=bind,source=$ModelDir,target=/models,readonly" `
  plantdisease-ai:week8

Invoke-RestMethod http://127.0.0.1:8501/_stcore/health
docker logs plantdisease-ai
docker stop plantdisease-ai
```

### Container troubleshooting

The README will cover only actionable failures:

- `checkpoint.pt` missing: train/provide the checkpoint and verify the bind
  mount source.
- Docker Desktop “mount denied”: enable file sharing or move the repository
  under the WSL2 filesystem.
- Port 8501 already in use: map another host port such as `-p 8505:8501`.
- Health check is starting: inspect `docker ps` and `docker logs` and allow the
  configured start period.
- Large NVIDIA dependency downloads: rebuild from the current CPU-only
  `Containerfile` and confirm `UV_TORCH_BACKEND=cpu`.
- Apple `container` Rosetta/bootstrap issues remain in a separate macOS note and
  are not presented as Docker requirements.

## Chinese Entry

`README.zh-CN.md` will contain:

- the project summary and verified result boundary;
- three start paths with a link to the canonical English commands;
- a Chinese platform matrix;
- links to `docs/tutorials/README.md`, the Chinese paper, bilingual presentation
  outline, artifact index, and safety statement;
- a warning that the checkpoint and Qwen weights are not automatically
  downloaded or included in the repository.

It will not duplicate the full week-by-week command log.

## Documentation Correctness Controls

A new release test will assert that `README.md` contains:

- the English/Chinese language switch;
- Python 3.12 and `uv` prerequisites;
- the synthetic smoke command;
- Docker build, Bash run, PowerShell run, health, and read-only mount examples;
- a statement that the container is CPU-only Streamlit;
- a statement that the checkpoint is not distributed;
- the 227-overlap, single-seed, no-field-validation, non-causal Grad-CAM, and
  educational-use boundaries;
- Linux, Windows/WSL2, Apple Silicon, and Qwen platform distinctions;
- no duplicated or syntactically truncated command blocks.

Link and claim audits will run after the rewrite. The full Python suite, Ruff,
`ty`, React tests/lint/build, `docker build`, and a container health smoke will
be rerun before publication. If Docker is unavailable, publication stops rather
than claiming cross-platform instructions are verified.

### 2026-07-17 override

After the original gate above was approved, the user chose Apple `container`
locally and declined Docker installation. This 2026-07-17 override supersedes the original Docker publication gate: publication may proceed after the Docker
instructions, links, claims, and shell structure pass static review, provided
the documentation makes no Docker runtime claim. Docker Engine/Desktop runtime remains `not_run`, and Windows PowerShell validation remains static-only. The
original gate remains above as the historical decision; this dated override is
the revised acceptance boundary.

## Release Manifest Sequencing

README and documentation changes alter tracked release artifacts. To preserve
the evidence chain:

1. Commit the approved README, Chinese entry, tests, and any minimal
   `Containerfile` comment/tag normalization.
2. Regenerate `reports/release/week8_rc1_manifest.json` using that exact source
   commit.
3. Verify every manifest artifact hash and runtime-lane status.
4. Commit the refreshed manifest separately.

The refreshed manifest must keep clean/package/local/container lanes
`not_run` unless those exact lanes are actually rerun for the new source
commit. A successful Docker documentation smoke may be reported in the README
verification handoff, but it must not be silently promoted into the historical
release-candidate lane evidence.

## Public GitHub Bootstrap

Because no remote repository exists, publication will bootstrap a new public
repository rather than inventing a PR base:

1. Verify GitHub authentication and confirm `panjoel812/PlantDiseaseAI` is still
   absent.
2. Create it with public visibility, MIT license inherited from the tracked
   repository, and no generated README/license/gitignore from GitHub.
3. Add `origin` and push the audited final tip to remote `main`.
4. Push `codex/week8-release-audit` only if needed for provenance; do not create
   an empty or zero-diff PR.
5. Verify repository visibility, default branch, README rendering, and that no
   forbidden large files, checkpoint, raw data, cache, secret, or personal path
   was published.

This is a source publication, not a model deployment or GitHub Release.

## Acceptance Criteria

- A first-time reader can choose and complete the appropriate start lane without
  reading historical task logs.
- Linux/macOS Bash and Windows PowerShell Docker commands are copyable and use a
  read-only checkpoint mount.
- The README clearly separates Streamlit Docker, React/FastAPI local development,
  and Apple-only Qwen MLX behavior.
- All public metrics and demo screenshots retain their evidence boundaries.
- Documentation contract tests, claim/link audits, full tests, linters, React
  build, Docker build, and container health all pass on the final source.
- The public GitHub repository has `main` as default, contains only intended
  tracked files, and has no tag or Release.

The Docker runtime clause in the original acceptance criteria is superseded by
the 2026-07-17 override: focused documentation contracts and claim/link audits
must pass, Docker Engine/Desktop runtime remains `not_run`, Windows PowerShell
validation remains static-only, and no Docker build or health success may be
claimed.
