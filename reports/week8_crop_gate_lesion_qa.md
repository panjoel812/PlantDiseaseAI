# Crop-gate and OpenCV lesion QA

> Historical first-stage record. The independent crop checkpoint and second
> disease gate were subsequently added; see
> [week8_hierarchical_crop_qa.md](week8_hierarchical_crop_qa.md).

Date: 2026-07-18

## Scope

This targeted QA covers the new three-stage demo path:

1. OpenCV visible lesion evidence on the original upload resolution.
2. Crop-confidence and crop-margin gate derived from the existing joint checkpoint.
3. Crop-restricted disease ranking only after the crop gate accepts.

The supplied grape-leaf image was used only as a local interactive QA input. It is
not committed. SHA-256:
`efd397fbbb7fa2867ca566b21e10591b4b71ae8632a0b4ef37b2d2195abe62ad`.
Its filename/user description is not treated as independently audited ground truth.

## Observed model failure before the gate

The frozen Week 3 candidate returned these leading joint classes for the supplied
image:

- `Tomato___Late_blight`: `0.3331085`
- `Strawberry___Leaf_scorch`: `0.2954107`
- `Apple___Black_rot`: `0.0698510`
- `Grape___Black_rot`: `0.0127838` (tenth among the requested Top-10)

This confirms that reformatting the old Top-5 could not correct the crop identity.

## New result

The crop aggregation produced Tomato `38.08%` with a `7.19` percentage-point
margin. Both are below the acceptance contract (`60%` probability and `10`
percentage-point margin). The service therefore returned:

- `crop_confident = false`
- `selected_class_name = null`
- zero disease conditions
- no Grad-CAM disease target
- a crop-uncertainty warning
- management guidance disabled in React

The UI labels Tomato only as an unverified candidate and explicitly states that the
disease result is withheld.

## OpenCV visible evidence

The deterministic original-resolution pass (`921 × 638`) reported:

- estimated leaf coverage: `35.90%` of image pixels
- estimated lesion coverage: `10.14%` of the leaf mask
- stable connected regions: `37`
- largest region: `0.84%` of leaf-mask area
- dominant coarse colour: tan (`87.8%` of sampled lesion pixels)
- dominant displayed shape: irregular
- distribution: widely scattered

These values are segmentation estimates, not verified masks or disease features.
They are displayed separately from neural-model probabilities.

## Verification

- Python targeted suite: `51 passed`, one Starlette deprecation warning.
- React targeted suite: `55 passed`.
- React production build: passed.
- Ruff on affected Python files: passed.
- Browser QA: upload, automatic result focus, OpenCV overlay/metrics, uncertain crop,
  disease abstention, compact LiquidGlass layout, and enabled visual-evidence panel
  were observed on the live local app.

## Remaining boundary

The crop gate prevents a low-confidence cascade; it does not identify the supplied
leaf as grape. Reliable correction requires a separately trained and evaluated crop
model (preferably a lightweight 224 px classifier) or another explicitly audited
plant-identification component. OpenCV measurements are not fused into disease
probabilities because no trained, calibrated fusion model currently exists.
