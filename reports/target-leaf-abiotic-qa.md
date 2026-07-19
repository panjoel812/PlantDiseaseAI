# Target-leaf and Corn abiotic-gate QA

Date: 2026-07-18

## Scope and evidence boundary

This QA covers the experimental `opencv_target_leaf_v2` selection path and the
Corn morphology abstention route. It does not establish field accuracy, confirm
nitrogen deficiency, or provide fertilizer or pesticide guidance.

The originally supplied local path
`$HOME/Downloads/corn-def-nitrogen-2.webp` was no longer present when the
audit was run. It was therefore not silently replaced or represented as tested.
For a deterministic local safety-path audit, a public Bayer Figure 1 image was
downloaded to `/tmp` only and was not copied into the repository. It is a
different pixel source from the missing user attachment. Source page:
<https://www.cropscience.bayer.us/articles/bayer/nutrient-deficiency-symptoms-in-corn>.

Machine-readable evidence:
[`reports/metrics/target_leaf_abiotic_qa.json`](metrics/target_leaf_abiotic_qa.json).

## Observed result

| Field | Result |
| --- | --- |
| Source dimensions | 640 × 480 |
| SHA-256 | `14abb00d5ab0d223611094178a2d6d10cfbc4ed2a034423db40f523578382bed` |
| Target point | `(0.58, 0.45)` in source-image coordinates |
| Selection mode | `click_grabcut` |
| Probable-foreground retention | `0.70595` (passes `0.60`) |
| Axis-band retention | `1.0` (passes `0.80`) |
| Border contact | `0.21519` (fails maximum `0.18`) |
| Decision | selection rejected; all model inference withheld |

The selected leaf is visibly truncated by the frame, so rejection is the
intended outcome. No abiotic score was manufactured after the purity gate
failed. The positive Corn route is covered by deterministic tests for all five
fixed gates: abnormal coverage, central-axis share, longitudinal continuity,
bilateral similarity, and off-axis discrete-lesion coverage. The only positive
label emitted by this route is `suspected_abiotic_nutrient_stress`.

## Historical failure and current behavior

Before this gate, the supplied Corn photograph produced a closed-set Gray leaf
spot score of `96.48%`. That is a historical model output reported during the
interactive diagnosis, not a ground-truth annotation. The current service first
requires one pure target leaf. After Corn identity is accepted, a positive
midrib-aligned morphology gate clears the selected infectious class, disease
knowledge, diagnostic Grad-CAM, and management eligibility. Closed-set disease
candidates may remain visible only as counterfactual model evidence.

The React workflow uses a fixed crosshair and source-image coordinates; it does
not follow pointer movement. An HTTP `409 leaf_selection_required` activates the
one-click prompt. Invalid or incomplete coordinate pairs return HTTP 422 before
model inference.

## Reproduction

```bash
uv run python scripts/audit_target_leaf_abiotic.py \
  --image /path/to/a/local/corn-leaf-image \
  --target-x 0.43 --target-y 0.47 \
  --output reports/metrics/target_leaf_abiotic_qa.json
```

Reattach the missing user image and rerun the command to create evidence for
those exact pixels. Do not reuse the current JSON for that claim.
