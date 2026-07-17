# Week 8 Reproducibility Audit

## Historical runtime-lane identity

- Candidate: `week8-rc1`
- Source commit: `08c57f63d09cc776826aefaed93b903a82637971`
- Current delivery manifest: `reports/release/week8_rc1_manifest.json`
- Claim ledger: `reports/release/week8_claim_evidence.json`
- Lockfile SHA-256: `e6942836c633b79aac224b786fa66f1cbc9812289f79f769f1bce843feb1003d`
- Final checkpoint SHA-256: `d53c09ab7fd3e0d1e93fdfbbcac307ebde2d2ee40adfa66440068486374486cf`
- Final checkpoint size: `94,660,305` bytes

This document records the clean-install, frozen local-evidence, and Apple
`container` lanes. The clean lane was created from source commit
`08c57f63d09cc776826aefaed93b903a82637971`; the local and container audit was
executed from `1193726be7764f3a6232bffb9241d11757cbf0ca` without selecting or
tuning a checkpoint from the official test set.

The identities above belong to those historical runtime executions. The current
delivery manifest records its own refreshed source commit, environment,
lock-file hash, checkpoint identity, claim audit, and tracked release-artifact
hashes. Because clean, package, local-evidence, and container lanes were not
rerun for that refreshed source commit, the manifest marks each of those lanes
as `not_run` and does not inherit historical lane evidence.

## Clean-environment strategy

The reproduction runner created a repository-external virtual environment
under the operating system's runtime temporary directory and set
`UV_PROJECT_ENVIRONMENT` for every locked command. The repository `.venv` was
not used by any clean-lane subprocess. `uv sync --frozen --all-groups` consumed
the committed lockfile. The runtime environment and detailed logs remain in
ignored local output; neither a volatile temporary path nor a personal home
path is stored in tracked evidence.

The clean-install lane used synthetic data only. It did **not** read or download
PlantVillage data, and it did **not** load the final Week 3 checkpoint. The
checkpoint was hashed only after the clean lane, while constructing the compact
candidate manifest.

## Environment

| Item | Recorded value |
| --- | --- |
| Python | 3.12.13 |
| PyTorch | 2.13.0 |
| Operating system | Darwin 25.5.0, arm64 |
| Hardware | MacBook Pro (Mac17,2), Apple M5, 10 cores, 24 GB memory |
| MPS available to manifest builder | true |
| Smoke device | CPU |

MPS availability is an environment fact, not evidence that the clean synthetic
smoke used MPS.

## Command and result ledger

The exact entry command was:

```bash
uv run python scripts/run_week8_repro.py \
  --environment <RUNTIME_TEMP>/plantdisease-week8-rc1-venv-20260716T-clean \
  --output outputs/plantvillage/week8_release/week8-rc1/clean_repro.json \
  --smoke-output outputs/plantvillage/week8_release/week8-rc1/clean_smoke/run_manifest.json
```

The runner records status and exit code for each bounded command; it does not
independently time each command or the full lane. Command-local timings emitted
by the tools are preserved below instead of reusing a prior run's wall time.

| Check | Locked command | Status | Exit | Fresh evidence |
| --- | --- | --- | ---: | --- |
| Dependency sync | `uv sync --frozen --all-groups` | passed | 0 | Created the temporary environment; 126 packages installed; installer reported 394 ms |
| Full tests | `uv run pytest -q` | passed | 0 | 226 passed, 7 warnings in 62.12 s |
| Ruff | `uv run ruff check .` | passed | 0 | `All checks passed!` |
| Type check | `uv run ty check src/plantdisease app scripts` | passed | 0 | `All checks passed!` |
| Claims and links | `uv run python scripts/audit_week8_claims.py --config configs/week8_claims.yaml --output outputs/plantvillage/week8_release/week8-rc1/claims.json --check-links` | passed | 0 | Initial frozen clean-lane result: 7 claims and 4 publication boundaries passed; 0 broken links |
| Synthetic smoke | `uv run plant-smoke --output-dir outputs/plantvillage/week8_release/week8-rc1/clean_smoke --seed 42 --image-size 32` | passed | 0 | `smoke_passed`, run `week1-synthetic-mobilenet_v2-seed42` |
| Package build | `uv build` | passed | 0 | Built source distribution and wheel for version 0.1.0 |
| CLI help | `uv run plant-smoke --help` | passed | 0 | Help text returned successfully |

Detailed sanitized command results are stored locally at
`outputs/plantvillage/week8_release/week8-rc1/clean_repro.json`. The fixed-seed
smoke artifacts are stored under
`outputs/plantvillage/week8_release/week8-rc1/clean_smoke/`. Both locations are
ignored by Git.

## Candidate generation

After the clean lane passed, the initial candidate was generated with:

```bash
uv run python scripts/build_release_candidate.py \
  --candidate-id week8-rc1 \
  --source-commit 08c57f63d09cc776826aefaed93b903a82637971 \
  --checkpoint outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/checkpoint.pt \
  --output reports/release/week8_rc1_manifest.json \
  --claims-output reports/release/week8_claim_evidence.json
```

The compact manifest records repository-relative logical paths, SHA-256
digests, sizes, environment facts, and lane status. All required artifacts,
including the final bilingual papers and 20-slide PPTX/Keynote defense files,
were present and hashed. At that initial clean-lane point, the claim ledger
contained 7 numerical claims and 4 publication boundaries. The current delivery
ledger at `reports/release/week8_claim_evidence.json` was regenerated after the
React evidence integration and contains 11 numerical claims plus the same 4
boundaries; all 15 checks pass with no broken local Markdown links. The initial
7-claim output remains historical clean-lane evidence under the ignored
`outputs/plantvillage/week8_release/week8-rc1/` directory.

## Frozen local-evidence audit

The local lane used only the previously selected Week 3 seed-42 checkpoint,
whose SHA-256 is
`d53c09ab7fd3e0d1e93fdfbbcac307ebde2d2ee40adfa66440068486374486cf`
and whose size is `94,660,305` bytes. The official test outputs were recomputed
for audit equality only; they were not used for checkpoint selection, tuning,
or early stopping.

The following commands completed successfully on 2026-07-16:

```bash
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

The recomputed results exactly matched the frozen machine-readable evidence:

| Measure | Recomputed value | Rounded locked value |
| --- | ---: | ---: |
| Accuracy | 0.9953310299747875 | 0.9953 |
| Macro F1 | 0.9940967816954187 | 0.9941 |
| Test samples | 10,709 | 10,709 |
| Errors | 50 | 50 |
| Top-label ECE | 0.09646972457571558 | 0.0965 |
| Top-label MCE | 0.3347918465733528 | 0.3348 |
| Top-label Brier | 0.013993920203081545 | 0.0140 |

Top-5 prediction, MPS Demo E2E, and the fixed Grad-CAM atlas were then run:

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

The Top-5 output contained exactly five entries in descending probability
order. The MPS Demo completed with checkpoint ID `d53c09ab7fd3`, five
predictions, a `layer4.2` overlay, and a single observed total time of
`246.92 ms`; this one synthetic-image timing is not a throughput benchmark.
The MPS Grad-CAM atlas completed all 24 frozen samples with no sample failure:
six samples in each of correct/high-confidence, correct/low-confidence,
error/high-confidence, and error/low-confidence. Grad-CAM is a correlation
visualization, not a causal explanation.

The ignored local evidence files and their SHA-256 hashes were recorded during
the historical local audit. The current delivery manifest does not carry those
runtime hashes forward. The detailed files remain outside Git because they
include generated figures and per-sample evidence; this report preserves the
audited summary and qualifications.

## Apple container audit

Apple `container` CLI `1.1.0` (release commit `5973b9c`) initially reported
that its API server was not running. The lane explicitly started the service
and verified API server `1.1.0`, full commit
`5973b9cc626a3e7a499bb316a958237ebe14e2ed`:

```bash
container system start --enable-kernel-install --timeout 300
container system status
container build --progress plain -f Containerfile \
  -t localhost/plantdisease-ai:week8-rc1 .
container run --rm -p 8510:8501 \
  -v "$PWD/outputs/plantvillage/week3_ablation/09_combo_candidate_seed42:/models" \
  localhost/plantdisease-ai:week8-rc1
curl --fail --silent --show-error http://127.0.0.1:8510/_stcore/health
```

The ARM64 build completed with CPU-only `torch==2.13.0+cpu` and
`torchvision==0.28.0+cpu`; no NVIDIA or CUDA packages were installed. The
resulting image is `localhost/plantdisease-ai:week8-rc1` with manifest-list
digest
`sha256:ec4f25dc57a7fdc853355ad0e0dc3cc36032ed593e291e383cb357debd48ef4d`.
The Streamlit health endpoint returned `ok` with exit code 0.

Forwarding Ctrl-C through the interactive Apple CLI session returned
`invalidArgument: missing signal in xpc message`. This occurred after the
health check and does not change the serving result. The validation container
was stopped non-destructively with `container stop <validation-container-id>`;
the foreground command then exited 0. No image, builder state, or user data was
deleted. This current Week 8 container result is independent of the historical
Week 5 fixed observation.

## Known warnings and scope limits

- The full suite emits 7 identical PyTorch deprecation warnings because
  `torch.jit.script` is deprecated in favor of newer compilation/export APIs.
  They do not change the successful test exit status.
- `uv` warned that the launcher had an active repository `.venv`; it explicitly
  ignored that environment because `UV_PROJECT_ENVIRONMENT` pointed to the
  clean runtime-temporary environment. The sync log confirms creation of the
  separate environment.
- The clean lane validates installation, tests, static checks, links, packaging,
  CLI wiring, and a synthetic CPU smoke. It does not establish PlantVillage
  metric reproduction, MPS inference, field generalization, or container health.
- The Week 3 classifier metrics were reproduced from frozen artifacts in the
  local lane. The Week 5 `129.8 ms` container observation remains historical
  and was not substituted for the current Week 8 health result.

## Current lane status

| Lane | Status |
| --- | --- |
| Claims | passed |
| Required artifact presence and hashes | passed |
| Clean reproduction | passed |
| Package build | passed |
| Local evidence | passed |
| Apple `container` | passed |
