# OpenLeaf-14 research scaffold evidence

Date: 2026-07-18  
Branch: `codex/open-world-plant-research`  
Status: implementation and synthetic tests complete; real-data pilot not started

## Completed scope

- Auditable JSONL records with plant, condition, taxonomy, source, license, entity,
  site, observer, and known/OOD split fields.
- Frozen MobileNetV2 feature extraction with no gradient training.
- Per-plant multi-prototype cosine index with explicit similarity and Top-1/Top-2
  margin rejection.
- Threshold calibration using separate known and OOD validation embeddings.
- Host-specific prototype condition model and plant-first router.
- A hard routing invariant: a rejected/unknown plant cannot call a condition model.
- OpenCV single-leaf preparation that exports a transparent cutout, neutral-background
  species input, full-resolution mask, scale-independent outline features, lesion
  overlay, and leaf-constrained lesion crops while preserving the original image.
- A strict single-leaf quality gate for small, truncated, fragmented, multi-leaf, and
  non-leaf inputs.
- Protocol documentation for Pl@ntNet-300K, PlantWild v2, PlantSeg, and PlantDoc,
  including open-set metrics, data grouping, licensing boundaries, and compute tiers.

## Validation actually run

```text
.venv/bin/pytest tests/openworld tests/serving/test_lesions.py \
  tests/serving/test_crop_leaf.py tests/serving/test_service.py \
  tests/training/test_crop_leaf_training.py -q
28 passed, 1 non-test-failure joblib CPU-count warning

.venv/bin/ruff check <all OpenLeaf-14 affected source and tests>
All checks passed!

git diff --check
no output (passed)
```

The tests use tiny synthetic vectors and generated images. They validate contracts,
single-leaf gating, output artifacts, leaf-constrained lesion boxes, and routing—not
botanical accuracy, OOD quality, or disease performance.

A read-only smoke on the user-supplied multi-leaf grape image was rejected before
classification because several large green components were present (largest-component
dominance `0.514`). This is expected under the current one-clear-leaf input contract;
it is not a botanical evaluation.

## Results not claimed

- No external dataset was downloaded in this work.
- No Pl@ntNet, PlantWild, PlantSeg, or PlantDoc model was trained or evaluated.
- No AUROC, FPR@95TPR, OSCR, field accuracy, lesion IoU, or end-to-end disease metric
  is available yet.
- MobileNetV2 ImageNet features are a compute baseline, not a selected final encoder.
- “Expandable catalog” does not mean universal plant recognition.

## Next evidence gate

Freeze a pilot containing the 14 configured crop leaves and at least six completely
disjoint unknown leaf species, preserving entity/source/license metadata. First audit
single-leaf acceptance/rejection; then compare at least two encoders under one split
and report open-set, latency, memory, and end-to-end routing results.
