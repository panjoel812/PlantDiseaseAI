# Week 8 Release Checklist — `week8-rc1`

This checklist describes a local release candidate. The proposed tag
`v0.8.0-rc1` **has not been created or published**. Publishing a GitHub branch or
PR is separate from creating a release and does not imply model deployment.

## Source and dependencies

- [x] Candidate source commit and artifact hashes recorded in the
  [release manifest](../../reports/release/week8_rc1_manifest.json).
- [x] Python **3.12.13**, PyTorch **2.13.0**, and lockfile SHA-256 are recorded
  ([release manifest](../../reports/release/week8_rc1_manifest.json)).
- [x] Locked dependency sync completed in a repository-external clean environment
  ([reproducibility report](../../reports/week8_reproducibility.md)).
- [x] Source distribution and wheel built in the historical clean lane
  ([reproducibility report](../../reports/week8_reproducibility.md)); the current
  delivery manifest marks package status `not_run`.

## Clean installation and quality gates

- [x] `uv sync --frozen --all-groups` passed in the isolated environment.
- [x] Full clean-lane suite passed with **226 tests and 7 recorded PyTorch
  deprecation warnings** ([reproducibility report](../../reports/week8_reproducibility.md)).
- [x] `uv run ruff check .` passed.
- [x] `uv run ty check src/plantdisease app scripts` passed.
- [x] Claim, boundary, and local-link audit passed
  ([claim evidence](../../reports/release/week8_claim_evidence.json)).
- [x] Synthetic fixed-seed smoke and CLI help passed.

## Evidence and reproducibility

- [x] Final checkpoint logical path, **94,660,305-byte size**, and SHA-256 recorded
  ([release manifest](../../reports/release/week8_rc1_manifest.json)).
- [x] Frozen official-split metrics were recomputed for equality without
  selecting or tuning the checkpoint ([reproducibility report](../../reports/week8_reproducibility.md)).
- [x] The **0.9953 Accuracy / 0.9941 Macro F1** result is always paired with
  single seed 42, official split, and **227 overlapping `leaf_id` values**
  ([metrics](../../outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/metrics.json),
  [split audit](../../reports/data_audit.md)).
- [x] Historical Week 5 evidence is distinguished from Week 8 recomputation.

## Demo and Apple container

- [x] Top-5 output was verified on the fixed synthetic input.
- [x] MPS Demo E2E completed; the **246.92 ms** value is documented only as one
  fixed synthetic observation, not a benchmark
  ([reproducibility report](../../reports/week8_reproducibility.md)).
- [x] MPS Grad-CAM atlas completed **24/24 fixed samples**
  ([reproducibility report](../../reports/week8_reproducibility.md)).
- [x] Apple `container` Linux ARM64 image built and Streamlit health returned `ok`
  in the recorded runtime audit
  ([reproducibility report](../../reports/week8_reproducibility.md)); the current
  delivery manifest marks the container lane `not_run`.
- [x] Historical **129.8 ms** container timing remains one fixed synthetic CPU
  observation, not a benchmark
  ([container E2E](../../outputs/plantvillage/week5_demo/container_e2e.json)).

## React research interface

- [x] The React/Vite interface uses `liquid-glass-react` and the supplied field
  image, whose SHA-256 is
  `0364ff44229c70666216343057f9ae77d82438a7f842b30af1ffabb786061a7e`.
  This is an **out-of-domain** field example with **no verified ground truth**
  ([browser QA](../../reports/week8_react_demo_qa.md)).
- [x] One representative local MPS request returned the ResNet-50
  `Cercospora leaf spot Gray leaf spot` **prediction** at **0.870144** with
  checkpoint ID `d53c09ab7fd3`; it is not field-accuracy evidence.
- [x] The optional `mlx-community/Qwen3-VL-4B-Instruct-4bit` panel exposes the
  actual local runtime state. Default-cache weights were absent, so
  `ready=false` and the UI unavailable state—not a response—was verified. The
  browser and API perform **no automatic download**.

## Safety and repository hygiene

- [x] UI and documentation state educational use and no professional diagnosis.
- [x] Grad-CAM is described as non-causal relevance visualization.
- [x] No pesticide name, dosage, or prescriptive treatment workflow is claimed.
- [x] Secret-pattern scan, personal-path scan, large-tracked-file review, and
  `git diff --check` are part of the final local gate.
- [x] Raw data, cache, and checkpoint are not tracked; hashes and logical paths
  are tracked instead ([release manifest](../../reports/release/week8_rc1_manifest.json)).

## Claims and application materials

- [x] [Final experiment report](../../reports/final_experiment_report.md) uses
  evidence-linked claims and separates historical from Week 8 results.
- [x] [Model card](../../reports/model_card.md) and
  [data card](../../reports/data_card.md) document intended/excluded use.
- [x] [Resume evidence](../resume/week8_resume_evidence.md) contains only
  traceable candidate wording.
- [x] [Mentor summary](../mentor/week8_mentor_summary.md) includes negative
  results and next experiments.

## Paper and research defense

- [x] Chinese and English research papers each build to a 12-page A4 PDF with
  13 audited sections and no missing shared claim macros
  ([paper audit](../../reports/release/week8_paper_audit.json)).
- [x] Both papers use the audited React Demo screenshot, distinguish local
  candidate provenance from remote publication, and state the official-split,
  single-seed, no-ground-truth field-example, VLM-runtime, and agricultural-safety
  boundaries.
- [x] The final PowerPoint contains 20 slides, 20 speaker-note parts, and eight
  object-level Morph records; canvas overflow and ZIP integrity checks passed
  ([presentation QA](../../reports/week8_presentation_qa.md)).
- [x] The native Keynote file opens as 20 slides and reports eight click-triggered
  Magic Move transitions at 0.9 seconds
  ([animation map](../presentation/week8_research_defense_animation_map.md)).
- [x] All 20 slides were visually audited; Microsoft PowerPoint playback was
  unavailable locally, so cross-version Morph parity remains unclaimed.

## Known incomplete work

- [ ] Multi-seed confirmation.
- [ ] Entity-isolated (`leaf_id`-disjoint) evaluation.
- [ ] External field validation and unknown-class evaluation.
- [ ] Full expert/human VQA audit.
- [ ] LoRA/QLoRA training and fixed-test evaluation.
- [ ] Consistent peak-memory benchmark.
- [ ] Public deployment, user study, publication, or award evidence.

Unchecked items are intentionally not claimed by this candidate.

## Remote authorization

- [ ] Create Git tag `v0.8.0-rc1` — **not authorized; not created**.
- [ ] Push branch or tag — **not authorized; not performed**.
- [ ] Publish release, checkpoint, dataset, container image, paper, or Demo —
  **not authorized; not performed**.
