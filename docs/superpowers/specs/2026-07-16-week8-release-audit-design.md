# Week 8 Local Release Candidate and Evidence Audit Design

**Date:** 2026-07-16

**Status:** Approved design direction

**Branch:** `codex/week8-release-audit`

**Release candidate:** `week8-rc1`

**Suggested future tag:** `v0.8.0-rc1` (not created by this work)

## 1. Objective

Complete Week 8 as a local, evidence-first release-candidate audit. The work
must prove that a third party can install and exercise the repository's core
workflow, reconcile public claims with machine-readable evidence, and produce
honest research and application materials.

Week 8 does not add a new research feature, retrain every formal experiment, or
publish the project. Remote pushes, tags, releases, and hosted deployment remain
outside scope until the user gives separate authorization.

## 2. Selected Approach

The selected approach is a **local evidence-first release candidate**:

- create a clean dependency environment and reproduce installation, tests,
  static checks, synthetic smoke, inference, Grad-CAM, Demo, and Apple
  `container` where the local system permits;
- re-evaluate or recompute affordable core evidence from the frozen final
  checkpoint rather than rerunning every historical training job;
- generate a machine-readable release manifest and claim-to-evidence ledger;
- finalize research, model/data documentation, resume bullets, and mentor
  communication from verified evidence only.

A documentation-only audit is insufficient because it cannot close the clean
environment requirement. A full retraining campaign is rejected because it
would expand Week 8, consume substantial compute, and potentially create a new
model-selection cycle.

## 3. Evidence Locks

The release audit may correct drift but must not silently change these facts:

- the official split has `227` overlapping train/test `leaf_id` values;
- Week 2 ResNet50 reports Accuracy `0.9830` and Macro F1 `0.9743`;
- Week 2 MobileNetV2 reports `2.27M` parameters, `0.31G` FLOPs, and
  `644.3 img/s` batch-32 MPS throughput excluding preprocessing;
- the Week 3 selected ResNet50 combination reports Accuracy `0.9953` and
  Macro F1 `0.9941` for seed 42 under the official split;
- Grad-CAM is a relevance visualization, not a causal explanation;
- the Week 5 `129.8 ms` container result is one CPU-only fixed-example
  observation, not a latency distribution;
- the Qwen3-VL smoke comparison covers 5 images and 15 questions, with choice
  and few-shot choice at `11/15` and condition recognition at `1/5`;
- LoRA/QLoRA, per-entry manual VQA review, field validation, professional
  diagnosis, pesticide guidance, publication, submission, awards, and real
  users remain incomplete or unverified.

Any discrepancy is recorded before correction. Historical raw evidence is not
overwritten to make a public claim pass.

## 4. Reproduction Architecture

Week 8 uses three explicit validation lanes.

### 4.1 Clean-install lane

Create an isolated virtual environment under the runtime temporary directory,
not the repository `.venv`. Use the committed lockfile and run:

- `uv sync --frozen --all-groups`;
- the complete pytest suite;
- Ruff;
- the pinned Python type checker;
- a repository-local Markdown link checker;
- `plant-smoke` with a fixed seed and synthetic data;
- packaging/import and CLI help checks.

This lane must not require the PlantVillage download, the final checkpoint, or
private machine paths. It proves that a clean clone can install and exercise the
minimum supported workflow.

### 4.2 Local-evidence lane

Use the existing ignored data cache and frozen final checkpoint only as local
inputs. Recompute affordable evidence:

- checkpoint load and SHA256;
- final metrics from saved predictions or the fixed evaluation protocol;
- single-image Top-5 inference;
- fixed-sample Grad-CAM;
- Streamlit service and fixed-example end-to-end smoke;
- key figure/table consistency checks.

The manifest stores repository-relative logical paths, checksums, file sizes,
protocol identifiers, seeds, device information, and availability status. It
must not store user-home or volatile temporary paths.

### 4.3 Apple container lane

Run `container system` checks, image build or reuse, healthcheck, and the
fixed-example Top-5 plus Grad-CAM flow with a mounted checkpoint. Record CLI
version, image digest, architecture, device limitation, timestamps, and exact
status.

If Apple `container`, its kernel, Rosetta, registry access, or local resources
block the run, preserve the failure and remediation evidence. A blocked
container step is not rewritten as a successful clean reproduction.

## 5. Release Audit Components

### 5.1 Machine-readable release manifest

Add a small release-audit module under `src/plantdisease/release/` with stable
functions for hashing, environment capture, logical artifact records, and
schema validation. A CLI in `scripts/` generates:

- a tracked release-candidate manifest under `reports/release/`;
- detailed runtime logs and intermediate results under ignored
  `outputs/plantvillage/week8_release/week8-rc1/`.

The tracked manifest contains no secrets, absolute personal paths, raw data, or
large model payloads.

### 5.2 Claim-to-evidence audit

Maintain a machine-readable ledger mapping each public claim to:

- the exact value and unit;
- experiment/run identifier;
- source metric or report;
- public consumers such as README, blog, deck, report, resume, or mentor brief;
- validation status and limitation text.

Automated checks cover locked numeric claims, required boundary wording,
missing evidence paths, contradictory completion status, and local Markdown
links. PPTX facts are checked through its text/notes extraction rather than by
manual recollection.

### 5.3 Final research documents

Produce and cross-link:

- reproducibility and validation report;
- final experiment report;
- final classifier model card;
- PlantVillage project data card;
- release checklist and explicit incomplete-work list;
- final result-to-run-to-artifact map;
- two or three resume bullets with evidence links;
- mentor communication summary and future research questions.

The existing Week 6 VQA data card remains a VQA-specific artifact; it does not
replace the project-level PlantVillage data card.

## 6. Data Flow and State

The release workflow is append-only:

1. read the committed configuration, lockfile, reports, and local ignored
   artifacts;
2. capture environment and availability without changing evidence;
3. run validation commands into a unique timestamped output directory;
4. generate a candidate manifest and claim ledger;
5. compare generated facts with public consumers;
6. correct public drift or record a failure;
7. re-run validation;
8. update `TASKS.md`, README, and the artifact index only for passed items.

The final candidate records both the pre-audit source commit and the final audit
commit. Because a commit cannot contain its own final SHA, the manifest uses an
explicit two-stage model: `source_commit` is generated before document
updates, while `release_commit` is filled by the final verification commit or
recorded in a small follow-up provenance update.

## 7. Error Handling and Integrity Rules

- Every command records `passed`, `failed`, `blocked`, or `not_run`;
  absence is never interpreted as success.
- Failed validation retains command, exit code, relevant stderr summary, and
  remediation status without copying credentials or personal paths.
- Test-set evidence may be recomputed but is not used for new hyperparameter
  selection or checkpoint choice.
- Dataset label corrections, split changes, and protocol changes require a new
  research protocol and are not performed during release audit.
- Missing ignored artifacts receive a documented retrieval instruction and
  checksum expectation; they are not silently embedded in Git.
- No original data, checkpoint, cache, environment directory, or secret enters
  the tracked release candidate.
- Resume and mentor statements distinguish implemented, formally evaluated,
  smoke-tested, blocked, and future work.

## 8. Testing and Verification

Implementation follows test-first development for release helpers and
claim/link checks. Required verification includes:

- unit tests for deterministic hashing, path sanitization, schema validation,
  claim comparison, and Markdown link resolution;
- a clean temporary environment install using the locked dependencies;
- full pytest, Ruff, and a pinned type checker;
- synthetic smoke with fixed seed;
- local final-checkpoint inference, Grad-CAM, and Demo smoke;
- affordable metric/table/figure recomputation;
- Apple `container` validation or an explicit blocked record;
- secret, personal-path, raw-data, cache, and tracked-large-file scans;
- README/blog/PPT/report/resume claim consistency;
- `git diff --check` and an independent final review.

Type checking is introduced as a pinned development dependency and scoped to
project-owned Python code. Any third-party stub limitation or justified
exclusion is listed in the reproducibility report; errors are not hidden by a
blanket ignore.

## 9. Deliverables

Expected tracked deliverables:

- `reports/release/week8_rc1_manifest.json`;
- `reports/release/week8_claim_evidence.json`;
- `reports/week8_reproducibility.md`;
- `reports/final_experiment_report.md`;
- `reports/model_card.md`;
- `reports/data_card.md`;
- `docs/release/week8_release_checklist.md`;
- `docs/resume/week8_resume_evidence.md`;
- `docs/mentor/week8_mentor_summary.md`;
- updated `README.md`, `TASKS.md`, and `docs/artifact-index.md`;
- tested release-audit source and CLI files.

Detailed logs, recomputed metrics, temporary environments, container build
state, and checkpoints remain ignored local outputs.

## 10. Completion Criteria

Week 8 is complete locally when:

- the clean-install lane passes in full; a failed installation, test, static
  check, link check, type check, packaging check, or synthetic smoke keeps
  Week 8 incomplete until fixed and rerun;
- the local-evidence lane proves the frozen checkpoint and core demo artifacts
  are reproducible within the recorded local constraints;
- metrics, plots, tables, README, blog, deck, reports, resume bullets, and mentor
  summary agree with the claim ledger;
- model/data cards and limitations cover intended use, non-intended use,
  controlled-background bias, split overlap, calibration, VLM status, and
  agricultural safety;
- every checked `TASKS.md` item points to evidence;
- no remote push, tag, release, or publication has occurred.

The Apple `container` lane and optional large-data recomputation may be
recorded as `blocked` only when the external local runtime or required ignored
artifact is unavailable and the already verified historical result remains
clearly distinguished from the current Week 8 run. A blocked lane cannot be
described as newly reproduced.

The suggested `v0.8.0-rc1` tag remains a recommendation until the user
separately authorizes creation or publication.
