# OpenPlant-H research scaffold evidence

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
- Protocol documentation for Pl@ntNet-300K, PlantWild v2, PlantSeg, and PlantDoc,
  including open-set metrics, data grouping, licensing boundaries, and compute tiers.

## Validation actually run

```text
.venv/bin/pytest tests/openworld -q
10 passed, 1 non-test-failure joblib CPU-count warning

.venv/bin/ruff check src/plantdisease/openworld tests/openworld
All checks passed!

git diff --check
no output (passed)
```

The tests use tiny synthetic vectors and two generated 8×8 images. They validate
contracts and routing, not botanical accuracy, OOD quality, or disease performance.

## Results not claimed

- No external dataset was downloaded in this work.
- No Pl@ntNet, PlantWild, PlantSeg, or PlantDoc model was trained or evaluated.
- No AUROC, FPR@95TPR, OSCR, field accuracy, lesion IoU, or end-to-end disease metric
  is available yet.
- MobileNetV2 ImageNet features are a compute baseline, not a selected final encoder.
- “Expandable catalog” does not mean universal plant recognition.

## Next evidence gate

Freeze a pilot containing at least 20 known plants and 10 completely disjoint unknown
plants, preserving entity/source/license metadata. Compare at least two encoders under
one split and report open-set, tail, latency, memory, and end-to-end routing results.
