# Target Leaf Selection and Abiotic-Stress Gate Design

## Context

The supplied `corn-def-nitrogen-2.webp` reproduces two distinct failure modes:

1. Sending the original field image directly to the closed-set ResNet50 produces a
   Corn conditional score of `96.48%` for Gray leaf spot.
2. The current Excess-Green connected-component isolation lowers Gray leaf spot to
   `37.67%` and causes the disease gate to abstain, but its selected mask still
   contains background leaves and stems because touching green plants form one
   connected component.

The PlantVillage label space has no nutrient deficiency, senescence, chemical injury,
mechanical damage, drought, or general abiotic-stress class. OpenCV evidence alone
cannot establish nitrogen deficiency. The system therefore needs a target-selection
and rejection layer before any infectious-disease claim.

## Goals

- Let the user identify one target leaf in an overlapping field image with one click.
- Use the click to initialize a deterministic GrabCut-based target-leaf mask.
- Measure mask purity and refuse disease inference when the selected leaf remains
  contaminated, truncated, too small, or incoherent.
- Detect a conservative Corn-specific pattern of continuous midrib-aligned chlorosis
  and necrosis that conflicts with discrete infectious lesions.
- Route matching evidence to `suspected abiotic / nutrient stress` and withhold the
  PlantVillage infectious-disease label, Grad-CAM diagnosis, knowledge card, and
  management guidance.
- Preserve the current automatic single-leaf path for uncomplicated images and the
  existing Grape lesion-focus evidence path.

## Non-goals

- Do not claim that OpenCV diagnoses nitrogen deficiency.
- Do not add a trained nitrogen-deficiency class from one user image.
- Do not recommend fertilizer type, amount, timing, or treatment.
- Do not silently lower crop or disease confidence thresholds.
- Do not treat a click as ground-truth segmentation.
- Do not enable the abiotic gate for non-Corn plants without separate calibration.

## Approaches Considered

### A. Click-seeded GrabCut plus conservative abiotic gate — selected

The user clicks the target leaf. The backend combines that seed with colour evidence,
image borders, and GrabCut to isolate the component containing the click. A purity
gate accepts or rejects the mask. Only an accepted Corn leaf is evaluated for
midrib-aligned, V-shaped chlorosis evidence. This is transparent, low-compute, and
does not require a new model or network service.

### B. Fully automatic OpenCV target selection

This avoids interaction but cannot reliably separate similarly coloured, touching
leaves. The supplied image already demonstrates that connected-component ranking can
select a large yet contaminated foreground. This remains a fallback for uncomplicated
images, not the primary path for overlapping scenes.

### C. Train a multiclass abiotic-stress model immediately

This is the long-term direction, but it requires licensed, independently split field
data for nutrient deficiencies and confounders. Training from the supplied image
would be scientifically invalid and would not test generalization.

## Data Flow

```text
uploaded image
  -> automatic OpenCV isolation
  -> purity accepted? ------------------------------ yes -> existing pipeline
         |
         no
         -> API returns selection_required evidence
         -> user clicks target leaf
         -> normalized target_x / target_y
         -> click-seeded GrabCut mask
         -> mask purity gate
              | rejected -> withhold all plant/disease claims; request another click/photo
              | accepted
              -> plant identity gate
              -> if accepted plant is Corn:
                   midrib/long-axis chlorosis evidence
                   -> suspected abiotic pattern?
                        | yes -> withhold infectious disease and management
                        | no  -> existing Corn disease model and reliability gate
              -> non-Corn -> existing host-specific path
```

## Backend Interfaces

### Target selection

`POST /api/classify` gains optional form fields:

- `target_x: float | None`, normalized to `[0, 1]` from the displayed image's left.
- `target_y: float | None`, normalized to `[0, 1]` from the displayed image's top.

Both must be supplied together. Out-of-range, incomplete, or non-finite coordinates
return HTTP 422. The frontend never sends pixel coordinates, so resizing does not
change the selected source location.

`InferenceService.predict(...)` gains an optional immutable `TargetPoint` value. The
service passes it to the leaf-preparation layer; model code never reads UI state.

### Leaf isolation result

`LeafIsolation` is extended with:

- `selection_mode`: `automatic` or `click_grabcut`.
- `target_point`: normalized point or `None`.
- `purity`: a `LeafPurityEvidence` object.

`LeafPurityEvidence` reports mask coverage, border contact, connected-fragment count,
click containment, dominant-axis consistency for elongated leaves, and a final
`accepted` decision with a human-readable reason. A low-purity mask never reaches the
crop or disease model.

The first auditable gate uses these fixed limits:

- automatic mode requests a click when two or more viable green components exist and
  the selected component contains less than `90%` of their combined contour area;
- all masks require coverage in `[3%, 85%]` and border-touch ratio at most `0.18`;
- click mode requires the selected component to contain the click and to retain at
  least `60%` of the probable-foreground pixels inside its GrabCut initialization;
- an elongated mask with PCA aspect ratio at least `2.0` requires at least `80%` of
  foreground pixels to remain inside three median cross-axis widths of its principal
  axis; otherwise it is treated as branch/background leakage.

These are segmentation-safety thresholds, not botanical confidence scores.

### Abiotic evidence

A new focused module, `src/plantdisease/serving/abiotic.py`, owns:

- `CornAbioticEvidence`
- `analyze_corn_abiotic_pattern(image, leaf_mask) -> CornAbioticEvidence`
- the conservative gate thresholds and their evidence boundary

The module measures visible morphology only:

- principal leaf axis and estimated midrib band;
- yellow/tan/brown coverage inside the leaf;
- longitudinal continuity along the axis;
- bilateral similarity across the axis;
- tip-to-base gradient compatible with a V-shaped pattern;
- discrete off-axis lesion component count and coverage.

The initial conservative positive gate requires all of the following: abnormal
yellow/tan/brown coverage at least `8%`, central-axis abnormal share at least `55%`,
longitudinal continuity at least `60%`, bilateral similarity at least `50%`, and
off-axis discrete-lesion coverage below `5%`. The values are recorded with every
result. If the supplied local QA image does not satisfy the gate after a valid target
selection, the system must return `unknown visible stress` rather than weakening a
threshold to force the expected answer.

The only positive route is `suspected_abiotic_nutrient_stress`. It must not output
`nitrogen deficiency` as a confirmed class. The result includes the measured features,
thresholds, reason, and the limitation that laboratory/soil/tissue confirmation may be
required.

## Hierarchy and Safety Behavior

The hierarchy keeps plant identity independent from stress identity. When Corn is
accepted and the abiotic gate is positive:

- `crop_confident` remains true;
- `conditions` may be returned as closed-set counterfactual evidence, but
  `disease_confident` is forced false;
- `selected_class_name`, disease knowledge, and management context are cleared;
- infectious-disease Grad-CAM is not presented as a diagnosis;
- the UI displays `Suspected abiotic / nutrient stress` above the closed-set candidates;
- copy states that the current dataset cannot name a specific nutrient deficiency.

The UI and API must not convert the abiotic evidence score into a probability of
nitrogen deficiency.

## React Interaction

The upload photograph becomes click-selectable only when the API reports that target
selection is required, or when the user explicitly chooses `Select another leaf`.
Clicking records normalized coordinates and shows a fixed crosshair. `Analyze selected
leaf` resubmits the same file with the coordinates. Keyboard users can activate a
button that places the target at the image centre, then adjust using arrow keys in
one-percent increments.

The result panel displays:

- selection mode and purity status;
- the isolated-leaf preview;
- abiotic evidence measurements and limitation text;
- infectious-disease candidates labelled `closed-set counterfactual evidence` when
  the abiotic gate fires.

The image and result cards remain fixed; pointer movement must not deform them.

## Error Handling

- Missing one coordinate: HTTP 422 with `target_x and target_y must be supplied together`.
- Point outside `[0, 1]`: HTTP 422.
- Point on non-leaf/background: structured selection rejection; no model inference.
- GrabCut failure or empty mask: structured selection rejection; no model inference.
- Mask purity failure: return the preview/evidence and request a different click or
  clearer photograph.
- Corn abiotic analysis unavailable: keep the existing disease gate; do not assume the
  image is infectious.
- Non-Corn image: do not run the Corn abiotic gate.

## Testing Strategy

Implementation follows red-green-refactor cycles.

1. Synthetic overlapping-leaf tests prove that automatic connected components fail
   purity while a click-seeded mask selects the intended diagonal leaf.
2. Coordinate-validation API tests cover missing pairs, bounds, and normalized mapping.
3. Synthetic Corn-pattern tests distinguish one continuous midrib-aligned V-shaped
   chlorosis band from multiple off-axis rectangular lesions.
4. Service tests prove that positive abiotic evidence clears the infectious diagnosis,
   knowledge, Grad-CAM diagnosis, and management context without changing crop identity.
5. React tests prove click normalization, crosshair stability, selection resubmission,
   and evidence copy.
6. The user-supplied image is a local QA case, not committed training data. The audit
   records the original-image Gray leaf spot `96.48%`, the current isolated-image
   abstention, mask purity, abiotic evidence, and final rejection behavior.
7. Existing Grape lesion-focus, classifier, Qwen, provider, and production-build tests
   remain green.

## Acceptance Criteria

- The supplied Corn image cannot produce an accepted Gray leaf spot diagnosis.
- An ambiguous automatic mask requests target selection instead of silently using
  background-contaminated pixels.
- A valid click produces a target-leaf preview or an explicit selection rejection.
- A positive Corn abiotic pattern is labelled only as suspected abiotic/nutrient stress.
- No fertilizer or treatment advice is generated from the gate.
- Plant identity remains Corn and is not inferred from the abiotic features.
- API, Python tests, React tests, Ruff, TypeScript, and production build pass.
- README, TASKS, artifact index, and a machine-readable QA record describe actual
  behavior and limitations without claiming field diagnostic accuracy.
