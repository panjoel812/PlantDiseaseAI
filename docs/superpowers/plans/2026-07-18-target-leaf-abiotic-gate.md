# Target Leaf Selection and Abiotic-Stress Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let a user select one target leaf in a cluttered field photograph, reject impure segmentation before classification, and withhold infectious Corn disease claims when visible evidence instead matches a conservative midrib-aligned abiotic/nutrient-stress pattern.

**Architecture:** Extend the existing OpenCV leaf pipeline with normalized target coordinates, click-seeded GrabCut, and auditable mask-purity evidence. Propagate a typed selection-required outcome through FastAPI and React without fabricating a classification result. After an accepted Corn identity, run a separate morphology-only abiotic gate before lesion-focused routing; a positive gate preserves crop identity but clears the selected infectious class, disease knowledge, diagnostic Grad-CAM, and management eligibility. Keep the existing automatic single-leaf and Grape lesion-focus paths unchanged when their gates apply.

**Tech Stack:** Python 3.12, Pillow, NumPy, OpenCV, PyTorch, FastAPI, pytest, React 19, TypeScript, Vite, Vitest, Testing Library, `liquid-glass-react`.

## Global Constraints

- Follow red-green-refactor for every production change: add a focused failing test, run it and observe the expected failure, implement the smallest change, then rerun the focused test.
- Never weaken a threshold merely to make either supplied photograph produce a desired label.
- The OpenCV branch may output only `suspected_abiotic_nutrient_stress` or `unknown_visible_stress`; it must never claim confirmed nitrogen deficiency.
- No fertilizer, pesticide, dose, schedule, or treatment recommendation is unlocked by morphology evidence.
- Automatic isolation requests a click when at least two viable components exist and the selected component represents less than `90%` of viable foreground area.
- Every accepted mask requires coverage in `[3%, 85%]` and border contact at most `0.18`.
- Click mode additionally requires click containment, probable-foreground retention at least `0.60`, and—when PCA aspect ratio is at least `2.0`—axis-band retention at least `0.80`.
- The Corn abiotic positive gate requires abnormal coverage `>= 8%`, central-axis share `>= 55%`, longitudinal continuity `>= 60%`, bilateral similarity `>= 50%`, and off-axis discrete-lesion coverage `< 5%`.
- The target point is normalized to the source image, not the rendered card. Object-fit cropping must be included in coordinate conversion.
- A selection failure returns typed HTTP 409 evidence and performs no crop or disease inference. Incomplete, non-finite, or out-of-range coordinate pairs return HTTP 422.
- Preserve the existing Grape lesion-focus behavior, local/Pl@ntNet crop routes, fixed result layout, reduced-motion support, and bilingual README structure.
- Do not commit user images, API keys, model weights, raw datasets, paper/PPT source files, or unrelated dirty-worktree changes.

---

### Task 1: Add normalized target selection and mask-purity evidence

**Files:**
- Modify: `src/plantdisease/openworld/leaf_pipeline.py`
- Modify: `tests/openworld/test_leaf_pipeline.py`

**Interfaces:**

```python
@dataclass(frozen=True)
class TargetPoint:
    x: float
    y: float


@dataclass(frozen=True)
class LeafPurityEvidence:
    accepted: bool
    coverage_percent: float
    border_touch_ratio: float
    fragment_count: int
    click_contained: bool | None
    probable_foreground_retention: float | None
    principal_axis_aspect_ratio: float
    axis_band_retention: float | None
    coverage_range: tuple[float, float]
    max_border_touch_ratio: float
    min_probable_foreground_retention: float
    min_axis_band_retention: float
    reason: str


@dataclass(frozen=True)
class LeafIsolation:
    method: str
    selection_mode: str
    target_point: TargetPoint | None
    purity: LeafPurityEvidence
    accepted: bool
    reason: str
    image_size: tuple[int, int]
    bounding_box: tuple[int, int, int, int] | None
    shape: LeafShapeFeatures | None
    mask: np.ndarray
    cutout_rgba: Image.Image | None
    species_image: Image.Image | None
```

The exact callable signature is `isolate_leaf(image: Image.Image, *, target_point: TargetPoint | None = None, neutral_rgb: tuple[int, int, int] = (124, 124, 124)) -> LeafIsolation`.

- [ ] **Step 1: Replace the old multi-component expectation with a failing selection-required test**

In `tests/openworld/test_leaf_pipeline.py`, replace `test_best_leaf_is_selected_when_multiple_components_are_visible` with a test that creates two separate green ellipses, calls `isolate_leaf(image)`, and asserts:

```python
assert result.accepted is False
assert result.selection_mode == "automatic"
assert result.target_point is None
assert result.purity.accepted is False
assert result.purity.fragment_count == 2
assert result.shape is not None
assert result.shape.component_dominance < 0.90
assert "select one target leaf" in result.reason.lower()
```

Add unit tests that `TargetPoint(x=-0.01, y=0.5)`, non-finite values, and values above `1.0` are rejected with `ValueError`, while both endpoints `0.0` and `1.0` are valid.

- [ ] **Step 2: Run the leaf-pipeline tests and verify RED**

Run:

```bash
uv run pytest tests/openworld/test_leaf_pipeline.py -q
```

Expected: import/attribute failures for `TargetPoint`, `selection_mode`, and `purity`, plus the old automatic acceptance behavior failing the new assertion.

- [ ] **Step 3: Add immutable target and purity value objects**

Implement `TargetPoint.__post_init__` with `math.isfinite` and inclusive `[0, 1]` validation. Change `LEAF_ISOLATION_METHOD` to `opencv_target_leaf_v2`; keep the checkpoint preprocessing string `opencv_exg_single_leaf_v1` untouched because it describes how the existing crop checkpoint was trained.

Add a private `_assess_purity` function returning `LeafPurityEvidence` that records every threshold in the returned object. The decision order must be deterministic: coverage, border contact, fragment ambiguity, click containment, probable-foreground retention, elongated-axis consistency. The returned `reason` must name the first failed gate.

- [ ] **Step 4: Implement automatic ambiguity rejection**

Keep the current ExG candidate construction and contour measurements. In automatic mode, reject before cutout creation when:

```python
len(viable) >= 2 and shape.component_dominance < 0.90
```

Return the selected contour mask and its shape/purity evidence for auditing, but set both `cutout_rgba` and `species_image` to `None`. Continue accepting uncomplicated single-component images.

- [ ] **Step 5: Run the focused tests and verify GREEN**

Run: `uv run pytest tests/openworld/test_leaf_pipeline.py -q`

Expected: all current single-leaf, non-leaf, and new ambiguous-scene tests pass.

---

### Task 2: Implement click-seeded GrabCut and purity gates

**Files:**
- Modify: `src/plantdisease/openworld/leaf_pipeline.py`
- Modify: `tests/openworld/test_leaf_pipeline.py`

- [ ] **Step 1: Add failing click-selection tests**

Add a synthetic 320×220 scene with a long diagonal target leaf crossing a differently coloured green background leaf. Test a click at the target leaf centre:

```python
result = isolate_leaf(image, target_point=TargetPoint(x=0.38, y=0.52))

assert result.accepted is True
assert result.selection_mode == "click_grabcut"
assert result.target_point == TargetPoint(x=0.38, y=0.52)
assert result.purity.accepted is True
assert result.purity.click_contained is True
assert result.purity.probable_foreground_retention is not None
assert result.purity.probable_foreground_retention >= 0.60
assert result.species_image is not None
```

Add three rejections:

1. a click on the dark background yields `click_contained is False` and no model-ready image;
2. a border-truncated target yields `border_touch_ratio > 0.18`;
3. a deliberately branched/contaminated elongated mask yields `axis_band_retention < 0.80`.

- [ ] **Step 2: Run the new click tests and verify RED**

Run:

```bash
uv run pytest tests/openworld/test_leaf_pipeline.py -q -k "click or truncated or axis"
```

Expected: `isolate_leaf` ignores `target_point` or cannot produce `click_grabcut` evidence.

- [ ] **Step 3: Add mask-initialized GrabCut**

Implement `_click_grabcut_mask(rgb, candidate, point) -> tuple[np.ndarray, float]` using source-pixel coordinates:

```python
pixel_x = min(width - 1, round(point.x * (width - 1)))
pixel_y = min(height - 1, round(point.y * (height - 1)))
```

Initialize OpenCV labels as follows:

- four-pixel image border: `cv2.GC_BGD`;
- non-green interior: `cv2.GC_PR_BGD`;
- ExG candidate pixels: `cv2.GC_PR_FGD`;
- a radius `max(3, round(min(width, height) * 0.025))` around a valid green click: `cv2.GC_FGD`.

If the click is not on probable foreground, return an empty/rejected mask without calling GrabCut. Otherwise call `cv2.grabCut` with the source image, initialized label mask, one-pixel rectangle sentinel, foreground/background models, `iterCount=5`, and `mode=cv2.GC_INIT_WITH_MASK`; convert foreground labels to binary and retain only the connected component containing the clicked pixel.

Compute probable-foreground retention as:

```python
selected_probable_pixels / max(1, probable_pixels_inside_selected_bounding_box)
```

- [ ] **Step 4: Add PCA axis-consistency evidence**

For mask coordinates, use `np.linalg.eigh` on the 2×2 covariance matrix. Define principal-axis aspect ratio as `sqrt(lambda_max / max(lambda_min, 1e-6))`. For aspect ratios `>= 2.0`, calculate cross-axis absolute distances, their median, and the proportion of foreground pixels within `3 * max(median_distance, 1.0)`; record this as `axis_band_retention`. Non-elongated leaves store `None` and do not fail this gate.

- [ ] **Step 5: Reuse one cutout builder for automatic and click modes**

Extract the existing padding/RGBA/neutral-background logic to `_build_cutout`. Only call it after purity acceptance. Ensure `_rejected` now accepts `selection_mode`, `target_point`, and `purity` so every rejection is serializable.

- [ ] **Step 6: Run all leaf-pipeline tests and verify GREEN**

Run: `uv run pytest tests/openworld/test_leaf_pipeline.py -q`

Expected: automatic single-leaf, automatic ambiguity, click acceptance, click-background, truncation, and axis-contamination cases all pass.

---

### Task 3: Propagate target coordinates and typed selection-required errors through the API

**Files:**
- Modify: `src/plantdisease/serving/service.py`
- Modify: `app/api.py`
- Modify: `tests/serving/test_service.py`
- Modify: `tests/test_demo_api.py`

**Interfaces:**

`LeafSelectionRequiredError(RuntimeError)` has the exact constructor `__init__(self, isolation: LeafIsolation) -> None` and exposes the immutable isolation as `.isolation`. `InferenceService.predict` keeps its current arguments and adds the keyword-only argument `target_point: TargetPoint | None = None`, returning `InferenceResult`.

- [ ] **Step 1: Add failing service short-circuit tests**

In `tests/serving/test_service.py`, add a model spy whose `forward` increments a counter. Patch `isolate_leaf` to return an accepted false `LeafIsolation`, then assert:

```python
with pytest.raises(LeafSelectionRequiredError) as error:
    service.predict(image_bytes, target_point=None)

assert error.value.isolation.accepted is False
assert model.forward_calls == 0
```

Add a second test that patches `isolate_leaf`, calls with `TargetPoint(0.25, 0.75)`, and verifies the exact point reaches the leaf pipeline.

- [ ] **Step 2: Add failing API validation and 409 tests**

Update `FakeService.predict` in `tests/test_demo_api.py` to accept and record `target_point`. Add tests for:

- only `target_x` supplied → 422 with `target_x and target_y must be supplied together`;
- `target_x=nan`, either coordinate below zero, or above one → 422;
- valid `target_x=0.25&target_y=0.75` → the fake receives `TargetPoint(0.25, 0.75)`;
- fake raises `LeafSelectionRequiredError` → HTTP 409 body has `detail.code == "leaf_selection_required"`, the normalized target point, purity fields, and no predictions;
- configured Pl@ntNet fallback invokes the second `service.predict` with the identical target point.

- [ ] **Step 3: Run focused backend tests and verify RED**

Run:

```bash
uv run pytest tests/serving/test_service.py tests/test_demo_api.py -q -k "target or selection_required"
```

Expected: missing signature, exception, form fields, and serializer failures.

- [ ] **Step 4: Implement service propagation and short-circuiting**

Import `TargetPoint` at runtime in `service.py`, pass it to `isolate_leaf`, and raise `LeafSelectionRequiredError(isolation)` before `analyze_lesions`, transforms, or model calls whenever isolation is not accepted. Re-raise this exception explicitly before the broad `except Exception` wrapper.

- [ ] **Step 5: Implement FastAPI coordinate validation and reusable isolation serialization**

Add `target_x` and `target_y` optional `Form()` values and change the endpoint return annotation to `dict[str, object] | JSONResponse`. Build a private `_target_point(x, y)` that handles pairing, finiteness, and bounds, translating `ValueError` to HTTP 422. Extract `_serialize_leaf_isolation` from `_serialize_result` so the same schema is used for success and failure.

Catch `LeafSelectionRequiredError` before `InferenceServiceError` and return:

```python
JSONResponse(
    status_code=409,
    content={
        "detail": {
            "code": "leaf_selection_required",
            "message": error.isolation.reason,
            "leaf_isolation": _serialize_leaf_isolation(error.isolation),
        }
    },
)
```

Pass the same `TargetPoint` to initial local inference and the second Pl@ntNet-overridden inference.

- [ ] **Step 6: Run focused and complete API/service tests**

Run:

```bash
uv run pytest tests/serving/test_service.py tests/test_demo_api.py -q
```

Expected: all existing API contracts plus new 409 and coordinate cases pass.

---

### Task 4: Build the Corn morphology-only abiotic evidence module

**Files:**
- Create: `src/plantdisease/serving/abiotic.py`
- Create: `tests/serving/test_abiotic.py`

**Interfaces:**

```python
CORN_ABIOTIC_METHOD = "opencv_corn_midrib_stress_v1"


@dataclass(frozen=True)
class CornAbioticEvidence:
    method: str
    status: str
    suspected: bool
    abnormal_coverage_percent: float
    central_axis_share: float
    longitudinal_continuity: float
    bilateral_similarity: float
    off_axis_lesion_coverage_percent: float
    abnormal_coverage_threshold: float
    central_axis_share_threshold: float
    longitudinal_continuity_threshold: float
    bilateral_similarity_threshold: float
    off_axis_lesion_coverage_threshold: float
    reason: str
    evidence_boundary: str
    overlay: Image.Image
```

The exact callable signature is `analyze_corn_abiotic_pattern(image: Image.Image, leaf_mask: np.ndarray) -> CornAbioticEvidence`.

- [ ] **Step 1: Write failing synthetic morphology tests**

Create deterministic fixtures on a dark background:

- a long green Corn-like leaf mask with a continuous, bilateral yellow-to-brown band following its principal axis;
- the same leaf with six separated off-axis tan rectangles;
- a uniformly green healthy leaf;
- an empty and incorrectly shaped mask.

Assertions:

```python
continuous = analyze_corn_abiotic_pattern(continuous_image, leaf_mask)
assert continuous.status == "suspected_abiotic_nutrient_stress"
assert continuous.suspected is True
assert continuous.abnormal_coverage_percent >= 8.0
assert continuous.central_axis_share >= 0.55
assert continuous.longitudinal_continuity >= 0.60
assert continuous.bilateral_similarity >= 0.50
assert continuous.off_axis_lesion_coverage_percent < 5.0

scattered = analyze_corn_abiotic_pattern(scattered_image, leaf_mask)
assert scattered.suspected is False
assert scattered.status == "unknown_visible_stress"

healthy = analyze_corn_abiotic_pattern(healthy_image, leaf_mask)
assert healthy.suspected is False
assert "abnormal coverage" in healthy.reason.lower()
```

Invalid mask shape raises `ValueError`; an empty mask returns `unknown_visible_stress` with zero measurements and an explicit reason.

- [ ] **Step 2: Run the new module tests and verify RED**

Run: `uv run pytest tests/serving/test_abiotic.py -q`

Expected: module import failure.

- [ ] **Step 3: Implement deterministic abnormal-colour evidence**

Within the accepted leaf mask, calculate HSV and Lab values. Build a morphology mask from the union of:

- yellow/chlorotic pixels: HSV hue `15..38`, saturation `>= 35`, value `>= 70`;
- tan/brown/necrotic pixels: HSV hue `4..30`, saturation `>= 30`, value `35..220`, with Excess Green `< 22`;
- pale desaturated tissue: Lab lightness `>= 135`, saturation `< 70`, and Excess Green `< 18`.

Use a kernel sized from `0.006 * min(width, height)` for one open and one close operation. Intersect every result with the supplied leaf mask. These numeric rules are visible-colour heuristics, not learned probabilities.

- [ ] **Step 4: Implement PCA-axis morphology measurements**

Project leaf and abnormal-pixel coordinates onto the principal and cross axes. Define the central band as the inner `36%` of the robust cross-axis leaf width. Split the occupied longitudinal range into 32 bins:

- `central_axis_share`: abnormal pixels in the central band divided by all abnormal pixels;
- `longitudinal_continuity`: fraction of bins between the first and last abnormal bin that contain central abnormal pixels;
- `bilateral_similarity`: `1 - sum(abs(left_i-right_i)) / max(1, sum(left_i+right_i))`, clamped to `[0,1]`;
- `off_axis_lesion_coverage_percent`: leaf-area share of connected abnormal components whose centroids are outside the central band and whose area is at least `0.15%` of leaf area.

Generate an RGB overlay with the accepted leaf outline in green, the central band in translucent blue, abnormal evidence in amber, and off-axis components in coral.

- [ ] **Step 5: Apply the fixed conjunction and evidence boundary**

Set `suspected=True` only when all five fixed gates pass. The positive reason must say that visible morphology is compatible with an abiotic/nutrient-stress pattern but cannot name a nutrient. The boundary must state that soil/tissue testing and local agronomic context may be required.

- [ ] **Step 6: Run the abiotic tests and verify GREEN**

Run: `uv run pytest tests/serving/test_abiotic.py -q`

Expected: continuous, scattered, healthy, empty, and invalid-mask cases pass.

---

### Task 5: Route accepted Corn leaves through the abiotic gate before disease selection

**Files:**
- Modify: `src/plantdisease/serving/service.py`
- Modify: `tests/serving/test_service.py`
- Modify: `app/api.py`
- Modify: `tests/test_demo_api.py`

- [ ] **Step 1: Add failing positive-route service tests**

Patch `analyze_corn_abiotic_pattern` to return a positive `CornAbioticEvidence` and make the hierarchy identify Corn confidently. Assert:

```python
assert result.hierarchy.selected_crop == "Corn"
assert result.hierarchy.crop_confident is True
assert result.hierarchy.selected_class_name is None
assert result.hierarchy.disease_confident is False
assert result.hierarchy.conditions  # retained only as counterfactual closed-set evidence
assert result.knowledge is None
assert result.gradcam is None
assert result.lesion_focus is None
assert result.abiotic_evidence is positive_evidence
assert "infectious disease label is withheld" in " ".join(result.warnings).lower()
```

Add negative-route tests proving:

- Corn + `unknown_visible_stress` continues through the current confidence gate;
- Grape never invokes the Corn analyzer and preserves lesion-focus routing;
- crop uncertainty never invokes the Corn analyzer;
- a positive abiotic result performs no Grad-CAM call.

- [ ] **Step 2: Add failing API serialization tests**

Extend `FakeService` results with abiotic evidence and assert `_serialize_result` includes every measurement, threshold, reason, boundary, and `overlay_data_url`. Assert `knowledge` and `gradcam` are null and the selected class is null for a positive route.

- [ ] **Step 3: Run focused tests and verify RED**

Run:

```bash
uv run pytest tests/serving/test_service.py tests/test_demo_api.py -q -k "abiotic or nutrient or grape"
```

Expected: `InferenceResult` has no `abiotic_evidence`, analyzer is not routed, and the API does not serialize it.

- [ ] **Step 4: Implement the service branch**

Add `abiotic_evidence: CornAbioticEvidence | None = None` to `InferenceResult`. After the first hierarchy is built and only when leaf isolation/purity and crop identity are accepted, call the analyzer for `selected_crop == "Corn"`.

When `suspected` is true, skip lesion-focus fusion, set:

```python
hierarchy = replace(
    hierarchy,
    selected_class_name=None,
    disease_confident=False,
    disease_decision_reason=(
        "Visible morphology matched the conservative Corn abiotic-stress gate; "
        "PlantVillage infectious-disease labels are counterfactual evidence only."
    ),
)
selected_prediction = None
gradcam_prediction = None
```

Retain `hierarchy.conditions` for transparent closed-set comparison, but never pass them to `lookup_disease_knowledge`. Append a dedicated safety warning. For non-positive or non-Corn paths, leave existing logic unchanged.

- [ ] **Step 5: Serialize abiotic evidence**

Add a private `_serialize_abiotic_evidence` in `app/api.py`, including the PNG overlay. Do not use the `suspected` boolean as a probability and do not add any treatment field.

- [ ] **Step 6: Run complete backend focused suites and verify GREEN**

Run:

```bash
uv run pytest tests/serving/test_abiotic.py tests/serving/test_service.py tests/openworld/test_leaf_pipeline.py tests/test_demo_api.py -q
```

Expected: all target, purity, Grape-regression, Corn-gate, serialization, and existing service/API tests pass.

---

### Task 6: Add typed frontend API support for selection and abiotic evidence

**Files:**
- Modify: `frontend/src/api/types.ts`
- Modify: `frontend/src/api/client.ts`
- Modify: `frontend/src/api/client.test.ts`

**Interfaces:**

```ts
export interface TargetPoint {
  x: number;
  y: number;
}

export interface LeafSelectionRequired {
  code: "leaf_selection_required";
  message: string;
  leaf_isolation: LeafIsolation;
}

export class LeafSelectionRequiredError extends Error {
  readonly detail: LeafSelectionRequired;
}

export interface ClassifyOptions {
  topK: number;
  includeGradcam: boolean;
  device?: "auto" | "cpu" | "cuda" | "mps";
  targetLayer?: string;
  targetPoint?: TargetPoint;
}
```

- [ ] **Step 1: Add failing FormData and 409 parsing tests**

Extend the existing exact-controls test to pass `targetPoint: {x: 0.25, y: 0.75}` and assert `target_x`/`target_y` strings. Keep the optional-controls test and assert both target fields are absent together.

Add a mocked 409 response containing `detail.code`, `message`, and serialized leaf evidence; assert `classifyImage` rejects with `LeafSelectionRequiredError` whose `detail.leaf_isolation.selection_mode` and `purity.reason` are preserved.

- [ ] **Step 2: Run the client tests and verify RED**

Run: `cd frontend && npm test -- --run src/api/client.test.ts`

Expected: target fields are absent and the generic `ApiError` loses structured selection evidence.

- [ ] **Step 3: Extend the response types**

Update `LeafIsolation` to `method: "opencv_target_leaf_v2"`, add `selection_mode`, `target_point`, and the complete `LeafPurityEvidence`. Add `CornAbioticEvidence` to `ClassificationResult` as `abiotic_evidence?: CornAbioticEvidence | null`.

- [ ] **Step 4: Implement exact pair submission and typed 409 parsing**

Append both form fields only when `targetPoint` exists. In `classifyImage`, inspect a 409 response before `requestJson`; validate only the discriminant and object presence needed to construct `LeafSelectionRequiredError`, then throw it. All other failures continue to use `ApiError`.

- [ ] **Step 5: Run the client tests and verify GREEN**

Run: `cd frontend && npm test -- --run src/api/client.test.ts`

Expected: existing API tests and new target/409 cases pass.

---

### Task 7: Map clicks to source-image coordinates and preserve selection state

**Files:**
- Create: `frontend/src/lib/imageCoordinates.ts`
- Create: `frontend/src/lib/imageCoordinates.test.ts`
- Modify: `frontend/src/hooks/useDemo.ts`
- Modify: `frontend/src/hooks/useDemo.test.tsx`

**Interfaces:**

```ts
export function coverPointToNormalizedImage(
  point: { clientX: number; clientY: number },
  rect: Pick<DOMRect, "left" | "top" | "width" | "height">,
  naturalSize: { width: number; height: number },
): TargetPoint | null;
```

`DemoState` gains `targetPoint`, `leafSelection`, `targetSelectionActive`, `setTargetPoint`, `beginTargetSelection`, and `clearTargetPoint`.

- [ ] **Step 1: Add failing coordinate-mapping tests**

Test square source/square card, wide source cropped into a square card, tall source cropped into a wide card, and a click outside the image bounds. For a 400×200 source rendered with `object-fit: cover` in a 200×200 card, the card centre maps to `(0.5, 0.5)` and the left card edge maps to `(0.25, 0.5)`, not `(0, 0.5)`.

- [ ] **Step 2: Run and verify RED**

Run: `cd frontend && npm test -- --run src/lib/imageCoordinates.test.ts`

Expected: module import failure.

- [ ] **Step 3: Implement cover-aware coordinate conversion**

Use `scale = Math.max(rect.width / naturalWidth, rect.height / naturalHeight)`, calculate the hidden horizontal/vertical overflow, translate the pointer into source pixels, and clamp only floating-point edge noise. Return null for non-positive sizes or points outside the rendered element.

- [ ] **Step 4: Add failing hook state tests**

In `useDemo.test.tsx`, simulate a 409 `LeafSelectionRequiredError` and assert:

- classification is not marked successful;
- `leafSelection` is stored and `targetSelectionActive` becomes true;
- setting a target point then classifying resends the same file with that point;
- selecting a different file clears point and selection evidence;
- a successful classification clears `leafSelection`, makes `targetSelectionActive` false, but retains the accepted target crosshair until reset/reselect;
- reset clears all selection state.

- [ ] **Step 5: Run the hook tests and verify RED**

Run: `cd frontend && npm test -- --run src/hooks/useDemo.test.tsx`

Expected: `DemoState` lacks the new selection state and the 409 follows generic error handling.

- [ ] **Step 6: Implement selection state without layout state coupling**

Catch `LeafSelectionRequiredError` before generic errors, set `leafSelection`, activate target selection, and return classification to idle rather than fabricating data. `beginTargetSelection()` activates click handling without discarding the last successful result; selecting another file or reset deactivates it. `classify(options)` must merge `targetPoint` into the request internally so `App` cannot send stale coordinates. Abort behavior remains unchanged.

- [ ] **Step 7: Run coordinate and hook tests and verify GREEN**

Run:

```bash
cd frontend
npm test -- --run src/lib/imageCoordinates.test.ts src/hooks/useDemo.test.tsx
```

Expected: all mapping and lifecycle cases pass.

---

### Task 8: Add one-click target selection and abiotic evidence UI

**Files:**
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/components/ImageWorkspace.tsx`
- Modify: `frontend/src/components/ClassifierPanel.tsx`
- Modify: `frontend/src/components/components.test.tsx`
- Modify: `frontend/src/styles.css`

- [ ] **Step 1: Add failing image-workspace interaction tests**

Render `ImageWorkspace` in selection-required mode. Mock image `naturalWidth`, `naturalHeight`, and `getBoundingClientRect`; click the visible target leaf and assert `onTargetPointChange` receives cover-corrected normalized coordinates. Assert:

- fixed crosshair uses percentage `left`/`top` and does not move on pointer hover;
- `Analyze selected leaf` is disabled until a point exists;
- `Use image centre` sets `(0.5, 0.5)`;
- ArrowRight/Left/Up/Down move the focused crosshair by `0.01` and clamp to `[0,1]`;
- selecting a new file still works.

- [ ] **Step 2: Add failing classifier evidence tests**

Render a positive abiotic result and assert the panel contains:

- `Suspected abiotic / nutrient stress`;
- `Morphology evidence — not a confirmed nitrogen deficiency`;
- all five measurements with units;
- `Closed-set infectious candidates (counterfactual only)` above conditions;
- no disease knowledge or diagnostic Grad-CAM section;
- a `Select another leaf` action.

Render an accepted non-positive result and assert existing disease/Grad-CAM content is unchanged.

- [ ] **Step 3: Run component tests and verify RED**

Run: `cd frontend && npm test -- --run src/components/components.test.tsx`

Expected: missing props, selection controls, abiotic card, and counterfactual copy.

- [ ] **Step 4: Wire App and workspace interaction**

Pass `demo.targetPoint`, `demo.leafSelection`, `demo.targetSelectionActive`, and setters into `ImageWorkspace`. Keep normal click behavior disabled unless selection is required or `Select another leaf` has called `demo.beginTargetSelection()`. Pass `onSelectAnotherLeaf={demo.beginTargetSelection}` into `ClassifierPanel`. The analyze button calls the existing `demo.classify({topK: 5, includeGradcam: true})`; the hook supplies the current point.

After a 409, keep the viewport on the photograph and focus the selection instruction. After a successful classification, preserve the current existing scroll-to-results behavior.

- [ ] **Step 5: Render evidence without unlocking guidance**

In `ClassifierPanel`, show purity mode/reason and the accepted cutout preview. When `abiotic_evidence.suspected` is true, render its overlay and measurements before the closed-set candidates. Continue to label candidates as model evidence, not diagnosis.

`App` already requires `hierarchy.disease_confident !== false` for management guidance; retain that gate and add an explicit `abiotic_evidence?.suspected !== true` condition for audit clarity.

- [ ] **Step 6: Add stable Apple-style selection CSS**

Use a static high-contrast crosshair, a small translucent instruction pill, and the existing mist-white/light-blue/tender-green palette. Do not introduce pointer-follow transforms. Cards remain in normal flow with no nested vertical scrolling. Under `prefers-reduced-motion: reduce`, disable crosshair pulse and use no animated transition.

- [ ] **Step 7: Run component and smoke tests and verify GREEN**

Run:

```bash
cd frontend
npm test -- --run src/components/components.test.tsx src/smoke.test.tsx
```

Expected: target interaction, abiotic copy, management lockout, existing upload/results order, and smoke rendering pass.

---

### Task 9: Record local QA evidence and update the bilingual project entry points

**Files:**
- Create: `scripts/audit_target_leaf_abiotic.py`
- Create (generated): `reports/metrics/target_leaf_abiotic_qa.json`
- Create: `reports/target-leaf-abiotic-qa.md`
- Modify: `README.md`
- Modify: `README.zh-CN.md`
- Modify: `docs/artifact-index.md`
- Modify: `TASKS.md`

- [ ] **Step 1: Add the deterministic local audit script**

The script accepts explicit paths and target coordinates:

```bash
uv run python scripts/audit_target_leaf_abiotic.py \
  --image /Users/panjoel/Downloads/corn-def-nitrogen-2.webp \
  --target-x 0.43 \
  --target-y 0.47 \
  --output reports/metrics/target_leaf_abiotic_qa.json
```

It must write image SHA-256, source dimensions, target point, selection mode, all purity values, all abiotic values/thresholds, status, reason, timestamp, code revision, and whether model inference was withheld. It must not copy the source image into the repository.

- [ ] **Step 2: Run the audit once and inspect the evidence honestly**

Expected acceptable outcomes:

- `suspected_abiotic_nutrient_stress` if and only if all five fixed gates pass; or
- `unknown_visible_stress` / selection rejection with the exact failed gates recorded.

Do not change thresholds to force the first result. If the chosen coordinates fail purity, adjust only the click to a visibly central point on the same foreground leaf and record the final point.

- [ ] **Step 3: Write the QA report from the JSON**

Document the previously observed original-image closed-set Gray leaf spot score (`96.48%`) as historical diagnostic evidence, distinguish it from current gated behavior, and state that the supplied image has no repository ground-truth label. Link the JSON and describe OpenCV evidence as morphology-only.

- [ ] **Step 4: Update both original bilingual README files**

Add matching English and Chinese sections covering:

- automatic isolation versus one-click target selection;
- why overlapping green components request a click;
- the Corn abiotic/nutrient-stress abstention route;
- why this does not confirm nitrogen deficiency;
- the UI workflow and API `target_x`/`target_y` example;
- local run instructions and safety boundary.

Do not replace either README with a shortened surrogate. Preserve all existing installation, Apple Container/Docker, experiment, paper, and citation content.

- [ ] **Step 5: Synchronize artifact and task status only after evidence exists**

Add the design, plan, QA report, and JSON to `docs/artifact-index.md`. Update only the exact `TASKS.md` item whose acceptance criteria are demonstrated; describe the feature as an experimental morphology gate, not a trained deficiency classifier.

---

### Task 10: Full verification and scoped commit

**Files:**
- Review: all files touched in Tasks 1–9
- Do not stage: unrelated pre-existing dirty-worktree files

- [ ] **Step 1: Run backend formatting/static checks for touched Python files**

Run:

```bash
uv run ruff check \
  src/plantdisease/openworld/leaf_pipeline.py \
  src/plantdisease/serving/abiotic.py \
  src/plantdisease/serving/service.py \
  app/api.py \
  scripts/audit_target_leaf_abiotic.py \
  tests/openworld/test_leaf_pipeline.py \
  tests/serving/test_abiotic.py \
  tests/serving/test_service.py \
  tests/test_demo_api.py
```

Expected: no errors.

- [ ] **Step 2: Run backend affected suites**

Run:

```bash
uv run pytest \
  tests/openworld/test_leaf_pipeline.py \
  tests/serving/test_abiotic.py \
  tests/serving/test_service.py \
  tests/test_demo_api.py -q
```

Expected: all pass with no skipped new gate tests.

- [ ] **Step 3: Run frontend affected suites and production build**

Run:

```bash
cd frontend
npm test -- --run \
  src/api/client.test.ts \
  src/lib/imageCoordinates.test.ts \
  src/hooks/useDemo.test.tsx \
  src/components/components.test.tsx \
  src/smoke.test.tsx
npm run build
```

Expected: all tests pass; TypeScript and Vite production build complete without errors.

- [ ] **Step 4: Run the broader repository test suite**

Run: `uv run pytest -q`

Expected: full suite passes. If an unrelated pre-existing failure exists, record the exact failing test and prove all affected suites above are green; do not alter unrelated tests.

- [ ] **Step 5: Inspect final diff and secrets**

Run:

```bash
git status --short
git diff --check
git diff --stat
rg -n "(sk-[A-Za-z0-9]|AIza[0-9A-Za-z_-]|ANTHROPIC_API_KEY=.+|PLANTNET_API_KEY=.+)" \
  README.md README.zh-CN.md app frontend src scripts reports docs TASKS.md
```

Expected: no whitespace errors or committed credentials. Confirm user images, paper/PPT sources, checkpoints, datasets, and unrelated dirty changes are not staged.

- [ ] **Step 6: Commit only the scoped implementation**

Stage exact implementation, test, report, and documentation paths; review `git diff --cached --name-only`; then commit:

```bash
git commit -m "feat: gate corn disease claims with target leaf evidence"
```

Do not push unless the user gives a new explicit push instruction after reviewing the completed local result.
