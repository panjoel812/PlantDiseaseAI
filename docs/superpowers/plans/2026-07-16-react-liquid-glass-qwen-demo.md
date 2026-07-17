# React Liquid Glass + Qwen Demo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a primary React/Vite Apple-style demo using `liquid-glass-react`, the user-supplied field image, the existing classifier/Grad-CAM service, and an optional real local Qwen3-VL panel, then audit and publish the completed Week 8 branch to GitHub.

**Architecture:** A Vite + React + TypeScript frontend calls a FastAPI adapter that wraps the existing cached classifier and a new cached interactive MLX Qwen service. The supplied field image is a clearly labeled no-ground-truth, out-of-domain example; Streamlit remains compatible, while React becomes the documented showcase.

**Tech Stack:** Python 3.12, FastAPI, PyTorch, MLX-VLM, React, TypeScript, Vite, Vitest, Testing Library, `liquid-glass-react`, Playwright/browser QA, uv, npm, GitHub CLI.

## Global Constraints

- Install and read the user-requested Apple Design skill with `npx skills@latest add emilkowalski/skills` before visual implementation.
- Install and render `liquid-glass-react` in production UI components; dependency-only installation does not satisfy the requirement.
- Use the supplied field image as the default example, preserving the original bytes and labeling it as user supplied with no verified ground truth.
- Never rewrite historical synthetic-smoke evidence as if the field image had been used in prior experiments.
- Qwen uses `mlx-community/Qwen3-VL-4B-Instruct-4bit`, never downloads weights from a browser request, and remains labeled exploratory.
- Preserve pesticide/dosage/regulatory refusal, low-confidence refusal, domain warnings, and the non-professional-diagnosis statement.
- Keep `app/streamlit_app.py` functional and tested.
- Do not claim new React or Qwen container validation unless it is actually run.
- Preserve unrelated untracked Week 7 deck intermediates and LaTeX auxiliary files.
- Use TDD for Python and React behavior; run browser QA after implementation.
- No Git tag, GitHub Release, public deployment, paid API, LoRA/QLoRA, or fabricated field-image label.

---

### Task 1: Install Apple Design Guidance and Establish the React Toolchain

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/package-lock.json`
- Create: `frontend/tsconfig.json`
- Create: `frontend/tsconfig.app.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/index.html`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/test/setup.ts`
- Create: `frontend/src/smoke.test.tsx`
- Create: `docs/ui/apple-design-implementation.md`
- Modify: `.gitignore`

**Interfaces:**
- Consumes: the approved design spec at `docs/superpowers/specs/2026-07-16-react-liquid-glass-qwen-demo-design.md`.
- Produces: npm scripts `dev`, `build`, `test`, and `test:run`; a tested React root; recorded Apple Design rules used by Tasks 5–7.

- [ ] **Step 1: Install the requested design skill and inspect its instructions**

Run:

```bash
npx skills@latest add emilkowalski/skills
rg --files . ~/.codex ~/.agents | rg 'emilkowalski|apple.*design|SKILL.md' | sort
```

Expected: the installer exits 0 and reports at least one installed skill. Read every installed `SKILL.md` relevant to Apple interface design before continuing. Record only the rules actually applicable to this project in `docs/ui/apple-design-implementation.md`; do not copy copyrighted prose wholesale.

- [ ] **Step 2: Scaffold Vite in a temporary directory and copy only the required files**

Run:

```bash
npm create vite@latest /private/tmp/plantdisease-react-demo -- --template react-ts
cp /private/tmp/plantdisease-react-demo/package.json frontend/package.json
cp /private/tmp/plantdisease-react-demo/tsconfig.json frontend/tsconfig.json
cp /private/tmp/plantdisease-react-demo/tsconfig.app.json frontend/tsconfig.app.json
cp /private/tmp/plantdisease-react-demo/tsconfig.node.json frontend/tsconfig.node.json
cp /private/tmp/plantdisease-react-demo/vite.config.ts frontend/vite.config.ts
cp /private/tmp/plantdisease-react-demo/index.html frontend/index.html
```

Expected: `frontend/` contains configuration only; no unused Vite sample images or styles are copied.

- [ ] **Step 3: Install runtime and test dependencies**

Run:

```bash
cd frontend
npm install liquid-glass-react
npm install --save-dev vitest jsdom @testing-library/react @testing-library/jest-dom @testing-library/user-event
```

Expected: `package-lock.json` is created and `npm ls liquid-glass-react` exits 0.

- [ ] **Step 4: Write the failing React smoke test**

Create `frontend/src/smoke.test.tsx`:

```tsx
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { App } from "./App";

describe("App", () => {
  it("identifies the research demo and its safety boundary", () => {
    render(<App />);
    expect(screen.getByRole("heading", { name: /evidence before diagnosis/i })).toBeVisible();
    expect(screen.getByText(/not a professional diagnosis/i)).toBeVisible();
  });
});
```

Add `frontend/src/test/setup.ts`:

```ts
import "@testing-library/jest-dom/vitest";
```

Configure `vite.config.ts` with `environment: "jsdom"`, `setupFiles: "./src/test/setup.ts"`, and scripts:

```json
{
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "test": "vitest",
    "test:run": "vitest run"
  }
}
```

- [ ] **Step 5: Run the smoke test to verify it fails**

Run: `cd frontend && npm run test:run -- src/smoke.test.tsx`

Expected: FAIL because `src/App.tsx` does not exist.

- [ ] **Step 6: Add the minimal accessible application shell**

Create `frontend/src/App.tsx`:

```tsx
export function App() {
  return (
    <main>
      <h1>Evidence before diagnosis.</h1>
      <p>Educational research demo — not a professional diagnosis.</p>
    </main>
  );
}
```

Create `frontend/src/main.tsx`:

```tsx
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import "./styles.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode><App /></StrictMode>,
);
```

- [ ] **Step 7: Verify the toolchain**

Run:

```bash
cd frontend
npm run test:run
npm run build
npm ls liquid-glass-react
```

Expected: tests and production build pass; the dependency tree contains `liquid-glass-react`.

- [ ] **Step 8: Commit the toolchain slice**

```bash
git add frontend .gitignore docs/ui/apple-design-implementation.md
git commit -m "feat: establish liquid glass react demo"
```

---

### Task 2: Add the Field Example and Shared Image Validation

**Files:**
- Create: `app/examples/field_corn_leaf.jpeg`
- Create: `src/plantdisease/serving/images.py`
- Create: `tests/serving/test_images.py`
- Modify: `src/plantdisease/serving/service.py`
- Modify: `app/streamlit_app.py`
- Modify: `tests/serving/test_service.py`
- Modify: `tests/test_streamlit_app.py`

**Interfaces:**
- Produces: `decode_rgb_image(image_bytes: bytes, *, max_upload_bytes: int, max_pixels: int) -> PIL.Image.Image`; repository asset `app/examples/field_corn_leaf.jpeg`.
- Consumes: `DEFAULT_MAX_UPLOAD_BYTES` and `DEFAULT_MAX_PIXELS` values currently defined by the serving layer.

- [ ] **Step 1: Copy and hash the supplied image**

Run:

```bash
cp <SUPPLIED_FIELD_IMAGE> app/examples/field_corn_leaf.jpeg
shasum -a 256 <SUPPLIED_FIELD_IMAGE> app/examples/field_corn_leaf.jpeg
```

Expected: both SHA-256 values are identical; `sips` reports 1024 × 768 JPEG.

- [ ] **Step 2: Write failing shared-decoder tests**

Create `tests/serving/test_images.py` with tests asserting:

```python
def test_decode_rgb_image_accepts_field_jpeg() -> None:
    image = decode_rgb_image(Path("app/examples/field_corn_leaf.jpeg").read_bytes())
    assert image.mode == "RGB"
    assert image.size == (1024, 768)


@pytest.mark.parametrize("payload, message", [(b"", "empty"), (b"bad", "decode")])
def test_decode_rgb_image_rejects_invalid_payload(payload: bytes, message: str) -> None:
    with pytest.raises(InputValidationError, match=message):
        decode_rgb_image(payload)
```

- [ ] **Step 3: Run the decoder test to verify it fails**

Run: `uv run pytest tests/serving/test_images.py -q`

Expected: collection fails because `plantdisease.serving.images` does not exist.

- [ ] **Step 4: Implement and reuse the shared decoder**

Move the byte-size, decode, positive-dimension, pixel-count, and RGB conversion logic from `InferenceService._decode_image` into:

```python
def decode_rgb_image(
    image_bytes: bytes,
    *,
    max_upload_bytes: int = DEFAULT_MAX_UPLOAD_BYTES,
    max_pixels: int = DEFAULT_MAX_PIXELS,
) -> Image.Image:
    """Validate uploaded bytes and return a fully decoded RGB image."""
```

Keep `InputValidationError` in `service.py` or move both the exception and constants into `images.py`, but expose a single canonical import path and update all callers/tests together. `InferenceService.predict` must call the shared helper.

- [ ] **Step 5: Update Streamlit's default example and copy**

Set:

```python
DEFAULT_EXAMPLE_IMAGE = Path("app/examples/field_corn_leaf.jpeg")
FIXED_EXAMPLE_COPY = (
    "User-supplied field corn leaf · no verified ground truth · out-of-domain example"
)
```

Update the Streamlit contract test to require `field`, `no verified ground truth`, and the new filename while retaining the safety copy.

- [ ] **Step 6: Verify image and Streamlit behavior**

Run:

```bash
uv run pytest tests/serving/test_images.py tests/serving/test_service.py tests/test_streamlit_app.py -q
uv run ruff check src/plantdisease/serving app tests/serving tests/test_streamlit_app.py
```

Expected: all affected tests and Ruff pass.

- [ ] **Step 7: Commit the image slice**

```bash
git add app/examples/field_corn_leaf.jpeg app/streamlit_app.py src/plantdisease/serving tests/serving tests/test_streamlit_app.py
git commit -m "feat: use supplied field leaf example"
```

---

### Task 3: Expose Classifier and Grad-CAM Through FastAPI

**Files:**
- Create: `app/api.py`
- Create: `scripts/run_demo_api.py`
- Create: `tests/test_demo_api.py`
- Modify: `pyproject.toml`
- Modify: `uv.lock`

**Interfaces:**
- Produces: `create_app(settings: DemoSettings, service_provider: ServiceProvider = get_cached_service) -> FastAPI`; endpoints `GET /api/health`, `GET /api/example`, and `POST /api/classify`. Task 4 extends the same app with Qwen status.
- Consumes: `decode_rgb_image`, `get_cached_service`, `InferenceResult`, and `app/examples/field_corn_leaf.jpeg`.

- [ ] **Step 1: Add explicit web-service dependencies**

Add to `[project].dependencies`:

```toml
"fastapi>=0.139,<1",
"python-multipart>=0.0.20,<1",
"uvicorn>=0.40,<1",
```

Run: `uv lock && uv sync --frozen --all-groups`

Expected: lock and sync succeed without changing the Python 3.12 target.

- [ ] **Step 2: Write failing API tests with an injected fake service**

Create `tests/test_demo_api.py` using `fastapi.testclient.TestClient`. Define a fake provider returning a fake object whose `predict` returns a complete `InferenceResult`. Assert:

```python
def test_health_reports_classifier_readiness(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["classifier"]["ready"] is True


def test_classify_serializes_top5_gradcam_and_boundaries(client: TestClient) -> None:
    response = client.post(
        "/api/classify",
        files={"image": ("leaf.jpeg", FIELD_BYTES, "image/jpeg")},
        data={"top_k": "5", "include_gradcam": "true", "device": "cpu"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["predictions"]) == 5
    assert payload["gradcam"]["overlay_data_url"].startswith("data:image/png;base64,")
    assert any("field images" in item for item in payload["warnings"])
```

Also cover corrupt upload → 422, missing checkpoint → health `ready=false`, and `GET /api/example` returning JPEG bytes plus `X-Example-Ground-Truth: unavailable`.

- [ ] **Step 3: Run the API tests to verify they fail**

Run: `uv run pytest tests/test_demo_api.py -q`

Expected: FAIL because `app.api` does not exist.

- [ ] **Step 4: Implement API settings, serialization, and routes**

Use:

```python
@dataclass(frozen=True)
class DemoSettings:
    checkpoint: Path = DEFAULT_CHECKPOINT
    default_device: str = "mps"
    example_image: Path = Path("app/examples/field_corn_leaf.jpeg")
    target_layer: str | None = None


def create_app(
    settings: DemoSettings | None = None,
    *,
    service_provider: ServiceProvider = get_cached_service,
) -> FastAPI:
    resolved = settings or DemoSettings()
    app = FastAPI(title="PlantDiseaseAI Demo API", version="1")
    app.state.settings = resolved
    app.state.service_provider = service_provider
    _register_routes(app)
    return app
```

`_register_routes(app)` defines exactly the three routes in this task and delegates
only to `_health_payload`, `_serialize_result`, and `_png_data_url`, all implemented
in the same module with typed parameters and return values.

Serialize dataclasses explicitly. Convert PIL Grad-CAM images with a helper:

```python
def _png_data_url(image: Image.Image) -> str:
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"
```

Mount CORS only for configurable local development origins (`127.0.0.1` and `localhost` Vite ports); do not use wildcard origins with credentials.

- [ ] **Step 5: Add the launch script**

`scripts/run_demo_api.py` parses checkpoint/device/host/port and runs:

```python
uvicorn.run(create_app(settings), host=args.host, port=args.port)
```

Default host is `127.0.0.1`, port `8000`, device `mps` when available through `auto` rather than a hard failure.

- [ ] **Step 6: Verify API behavior and types**

Run:

```bash
uv run pytest tests/test_demo_api.py tests/serving -q
uv run ruff check app/api.py scripts/run_demo_api.py tests/test_demo_api.py
uv run ty check app/api.py scripts/run_demo_api.py src/plantdisease/serving
```

Expected: all commands pass.

- [ ] **Step 7: Commit the classifier API slice**

```bash
git add app/api.py scripts/run_demo_api.py tests/test_demo_api.py pyproject.toml uv.lock
git commit -m "feat: expose classifier demo api"
```

---

### Task 4: Add the Real Optional Ask Qwen Service

**Files:**
- Create: `src/plantdisease/vlm/interactive.py`
- Create: `tests/vlm/test_interactive.py`
- Modify: `app/api.py`
- Modify: `tests/test_demo_api.py`

**Interfaces:**
- Produces: `QwenRuntimeStatus`, `InteractiveQwenResult`, `InteractiveQwenService.ask(image_bytes: bytes, question: str, classifier_context: ClassifierContext | None) -> InteractiveQwenResult`, `get_qwen_service() -> InteractiveQwenService`.
- Consumes: `MLXVLMBackend.generate`, `decode_rgb_image`, `build_assistant_response`, and the classifier context posted by the frontend.

- [ ] **Step 1: Write failing interactive Qwen tests**

Test with an injected `MockVLMBackend`:

```python
def test_interactive_qwen_uses_real_backend_answer_and_preserves_scope() -> None:
    service = InteractiveQwenService(
        backend=MockVLMBackend({"Is this leaf healthy?": "diseased"}),
        model_id=QWEN3_VL_MODEL_ID,
    )
    result = service.ask(
        FIELD_BYTES,
        "Is this leaf healthy?",
        classifier_context=ClassifierContext(
            top_class_name="Corn_(maize)___Northern_Leaf_Blight",
            confidence=0.91,
            warnings=[DOMAIN_WARNING],
        ),
    )
    assert result.raw_answer == "diseased"
    assert result.model_id == QWEN3_VL_MODEL_ID
    assert result.scope == "exploratory_smoke"
```

Add tests for blank question, >500 characters, pesticide/dosage refusal without backend invocation, unsupported platform status, missing dependency/cache status, and an MLX setup error translated to `ready=false` rather than a fabricated answer.

- [ ] **Step 2: Run Qwen tests to verify they fail**

Run: `uv run pytest tests/vlm/test_interactive.py -q`

Expected: collection fails because `plantdisease.vlm.interactive` does not exist.

- [ ] **Step 3: Implement status probing and cached service**

Define:

```python
@dataclass(frozen=True)
class QwenRuntimeStatus:
    supported_platform: bool
    dependency_available: bool
    weights_cached: bool
    ready: bool
    model_id: str
    detail: str


@lru_cache(maxsize=1)
def get_qwen_service() -> InteractiveQwenService:
    return InteractiveQwenService(
        backend=MLXVLMBackend(allow_model_download=False, max_tokens=96),
        model_id=QWEN3_VL_MODEL_ID,
    )
```

Probe the local Hugging Face cache with
`snapshot_download(repo_id=QWEN3_VL_MODEL_ID, local_files_only=True)` and never set
`allow_model_download=True` from API state. Protect generation with a
`threading.Lock` because a single MLX model instance is shared.

- [ ] **Step 4: Apply the safety policy before and after generation**

High-risk, low-confidence, and out-of-domain refusal is determined by `build_assistant_response`. For an allowed question, call Qwen and return both `raw_answer` and a bounded educational wrapper with sources. The result must include:

```python
scope="exploratory_smoke"
evidence_boundary=(
    "Fixed smoke: choice/few-shot 11/15; fine-grained condition 1/5; "
    "not a professional diagnosis."
)
```

- [ ] **Step 5: Add Qwen API routes**

Extend `create_app` with
`qwen_provider: QwenProvider = get_qwen_service`. Add Qwen readiness under
`GET /api/health`, plus `GET /api/qwen/status` and multipart
`POST /api/qwen/ask` accepting `image`, `question`, and optional classifier fields.
Return 503 with the status payload when Qwen is unavailable, 422 for invalid input,
and 200 for refusals or generated answers.

- [ ] **Step 6: Verify Qwen/API behavior without a model download**

Run:

```bash
uv run pytest tests/vlm/test_interactive.py tests/test_demo_api.py -q
uv run ruff check src/plantdisease/vlm/interactive.py app/api.py tests/vlm/test_interactive.py tests/test_demo_api.py
uv run ty check src/plantdisease/vlm/interactive.py app/api.py
```

Expected: all tests pass without network or model download.

- [ ] **Step 7: Commit the Qwen slice**

```bash
git add src/plantdisease/vlm/interactive.py tests/vlm/test_interactive.py app/api.py tests/test_demo_api.py
git commit -m "feat: add optional local qwen panel api"
```

---

### Task 5: Build the Typed React Data Layer and State Machine

**Files:**
- Create: `frontend/src/api/types.ts`
- Create: `frontend/src/api/client.ts`
- Create: `frontend/src/api/client.test.ts`
- Create: `frontend/src/hooks/useDemo.ts`
- Create: `frontend/src/hooks/useDemo.test.tsx`
- Modify: `frontend/vite.config.ts`

**Interfaces:**
- Produces: `classifyImage`, `fetchHealth`, `fetchQwenStatus`, `askQwen`; hook
  `useDemo(): { classification: FeatureState<ClassificationResult>; qwen:
  FeatureState<QwenAnswer>; selectedFile: File | null; previewUrl: string | null;
  selectFile(file: File): void; classify(options: ClassifyOptions): Promise<void>;
  ask(question: string): Promise<void>; reset(): void }`.
- Consumes: Task 3/4 endpoint schemas.

- [ ] **Step 1: Define exact TypeScript contracts**

Create types for `Prediction`, `TimingBreakdown`, `GradCamPayload`, `ClassificationResult`, `QwenStatus`, `QwenAnswer`, `FeatureState<T>`, and `DemoHealth`. Match Python JSON names exactly; do not use `any`.

- [ ] **Step 2: Write failing client and hook tests**

Mock `fetch` and assert:

```ts
it("sends the selected image and gradcam controls", async () => {
  await classifyImage(file, { topK: 5, includeGradcam: true, device: "mps" });
  const [, init] = vi.mocked(fetch).mock.calls[0];
  const body = init?.body as FormData;
  expect(body.get("image")).toBe(file);
  expect(body.get("top_k")).toBe("5");
});

it("keeps a successful classification when qwen fails", async () => {
  vi.mocked(classifyImage).mockResolvedValue({ warnings: [] } as ClassificationResult);
  vi.mocked(askQwen).mockRejectedValue(new ApiError(503, "Qwen unavailable"));
  const file = new File(["leaf"], "leaf.jpeg", { type: "image/jpeg" });
  const { result } = renderHook(() => useDemo());
  act(() => result.current.selectFile(file));
  await act(async () => result.current.classify({
    topK: 5,
    includeGradcam: true,
    device: "mps",
  }));
  await act(async () => result.current.ask("What visual symptoms are visible?"));
  expect(result.current.classification.status).toBe("success");
  expect(result.current.qwen.status).toBe("error");
});
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd frontend && npm run test:run -- src/api/client.test.ts src/hooks/useDemo.test.tsx`

Expected: FAIL because the modules do not exist.

- [ ] **Step 4: Implement the client and state reducer**

Use `FormData`, an `ApiError` carrying status/detail, and `AbortController` per feature. `useDemo` owns selected file/preview URL, default example loading, classification state, Qwen state, and cleanup of object URLs. Classifier success must survive Qwen status/error transitions.

- [ ] **Step 5: Configure the Vite development proxy**

Proxy `/api` to `http://127.0.0.1:8000` so the browser uses same-origin relative paths in development and production builds.

- [ ] **Step 6: Verify the data layer**

Run:

```bash
cd frontend
npm run test:run
npm run build
```

Expected: all tests and TypeScript build pass.

- [ ] **Step 7: Commit the data layer**

```bash
git add frontend/src/api frontend/src/hooks frontend/vite.config.ts
git commit -m "feat: add typed demo state and api client"
```

---

### Task 6: Implement the Apple Liquid Glass Interface

**Files:**
- Create: `frontend/src/components/Hero.tsx`
- Create: `frontend/src/components/ImageWorkspace.tsx`
- Create: `frontend/src/components/ClassifierPanel.tsx`
- Create: `frontend/src/components/QwenPanel.tsx`
- Create: `frontend/src/components/SafetyNotice.tsx`
- Create: `frontend/src/components/components.test.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/styles.css`
- Modify: `frontend/src/smoke.test.tsx`

**Interfaces:**
- Produces: complete accessible UI rendering real `LiquidGlass` components and binding to `useDemo`.
- Consumes: Task 1 Apple Design notes and `liquid-glass-react`; Task 5 hook/types.

- [ ] **Step 1: Write failing component contract tests**

Tests must assert:

```tsx
expect(screen.getByText(/user-supplied field corn leaf/i)).toBeVisible();
expect(screen.getByText(/no verified ground truth/i)).toBeVisible();
expect(screen.getByRole("button", { name: /analyze leaf/i })).toBeEnabled();
expect(screen.getByRole("button", { name: /ask qwen/i })).toBeDisabled();
expect(screen.getByText(/choice.*11\/15/i)).toBeVisible();
expect(screen.getByText(/condition.*1\/5/i)).toBeVisible();
```

Add an assertion that at least the image workspace, classifier result, and Qwen panel import and render the library's `LiquidGlass` component. Mock the package only to stabilize JSDOM, not to replace it in production code.

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd frontend && npm run test:run -- src/components/components.test.tsx src/smoke.test.tsx`

Expected: FAIL because the components do not exist.

- [ ] **Step 3: Implement the visual hierarchy**

Apply the installed Apple Design guidance recorded in `docs/ui/apple-design-implementation.md`. Use a neutral graphite/ivory base, image-derived green accent, one amber risk accent, large typographic hierarchy, 20–32 px radii, restrained blur, and clear solid fallbacks. Use `LiquidGlass` around focused panels rather than every element.

The primary path is:

```text
Select field example or upload → Analyze leaf → inspect Top-5 / Grad-CAM
→ optionally open Ask Qwen → ask bounded question
```

- [ ] **Step 4: Implement accessibility and responsive behavior**

Use semantic headings, explicit labels, visible focus, `aria-live` for progress/errors, keyboard-accessible upload, 44 px minimum targets, readable contrast, and:

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    scroll-behavior: auto !important;
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

At ≤760 px, panels stack, results remain in reading order, and the Qwen composer stays within the viewport.

- [ ] **Step 5: Verify components and build**

Run:

```bash
cd frontend
npm run test:run
npm run build
```

Expected: tests and build pass with no unresolved assets or type errors.

- [ ] **Step 6: Commit the interface**

```bash
git add frontend/src
git commit -m "feat: build apple liquid glass demo"
```

---

### Task 7: Run Real Local Integration and Browser QA

**Files:**
- Create: `tests/integration/test_react_demo_contract.py`
- Create: `reports/figures/week8_react_demo_desktop.png`
- Create: `reports/figures/week8_react_demo_mobile.png`
- Create: `reports/week8_react_demo_qa.md`
- Modify: `README.md`

**Interfaces:**
- Produces: browser-verified screenshots and QA evidence; a documented local experience.
- Consumes: final checkpoint, supplied image, FastAPI app, React production/dev build, cached Qwen weights when available.

- [ ] **Step 1: Write the static integration contract**

Add a Python test that parses `frontend/package.json` and source files, asserting:

- `liquid-glass-react` is a runtime dependency;
- production source imports it;
- default example is `field_corn_leaf.jpeg`;
- README launch commands reference both API and React;
- Qwen boundary text includes `11/15`, `1/5`, and no automatic download.

- [ ] **Step 2: Run the contract test to verify it fails**

Run: `uv run pytest tests/integration/test_react_demo_contract.py -q`

Expected: FAIL until README and final UI copy are complete.

- [ ] **Step 3: Launch the API and frontend**

Run in separate persistent sessions:

```bash
uv run python scripts/run_demo_api.py \
  --checkpoint outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/checkpoint.pt \
  --device mps --host 127.0.0.1 --port 8000
```

```bash
cd frontend && npm run dev -- --host 127.0.0.1 --port 5173
```

Expected: health endpoints respond and the browser loads without console errors.

- [ ] **Step 4: Use the Browser skill for desktop and mobile QA**

Verify at 1440 × 1000 and 390 × 844:

- supplied image loads and is visibly labeled without ground truth;
- upload replacement and reset work;
- real classifier request returns Top-5 and Grad-CAM;
- warnings remain visible;
- Qwen panel reports true runtime state;
- if cached, ask “What visual symptoms can you describe?” and record the real answer;
- if not cached, verify the exact local setup instructions and make no Qwen success claim;
- no horizontal overflow, clipped controls, illegible glass text, or console errors;
- keyboard focus and reduced-motion mode are usable.

- [ ] **Step 5: Capture final screenshots and QA report**

Save desktop and mobile PNGs through browser screenshots. `reports/week8_react_demo_qa.md` records viewport, commit, image SHA-256, checkpoint ID, browser state, Qwen readiness, commands, results, and limitations.

- [ ] **Step 6: Update README and pass the integration contract**

README must lead with the React Demo, show the new desktop screenshot, include API/frontend launch commands, explain optional Qwen cache requirements, retain Streamlit compatibility instructions, and label the field image correctly.

Run:

```bash
uv run pytest tests/integration/test_react_demo_contract.py -q
cd frontend && npm run test:run && npm run build
```

Expected: all commands pass.

- [ ] **Step 7: Commit browser-verified demo evidence**

```bash
git add README.md tests/integration/test_react_demo_contract.py reports/figures/week8_react_demo_desktop.png reports/figures/week8_react_demo_mobile.png reports/week8_react_demo_qa.md
git commit -m "docs: publish react demo evidence"
```

---

### Task 8: Synchronize Week 8 Research and Release Evidence

**Files:**
- Modify: `TASKS.md`
- Modify: `docs/artifact-index.md`
- Modify: `docs/release/week8_release_checklist.md`
- Modify: `docs/resume/week8_resume_evidence.md`
- Modify: `docs/mentor/week8_mentor_summary.md`
- Modify: `reports/final_experiment_report.md`
- Modify: `reports/model_card.md`
- Modify: `reports/data_card.md`
- Modify: `configs/week8_claims.yaml`
- Modify: `reports/release/week8_claim_evidence.json`
- Modify: `reports/release/week8_rc1_manifest.json`
- Modify: `reports/week8_reproducibility.md`
- Modify: `docs/presentation/week8_research_defense_content.json`
- Modify: `docs/presentation/plantdisease_ai_week8_research_defense.pptx`
- Modify: `docs/presentation/plantdisease_ai_week8_research_defense.key`
- Modify: `reports/week8_presentation_qa.md`
- Modify: `paper/zh/main.tex`
- Modify: `paper/en/main.tex`
- Modify: `paper/out/plantdisease_ai_zh.pdf`
- Modify: `paper/out/plantdisease_ai_en.pdf`

**Interfaces:**
- Produces: synchronized public claims, final artifacts, and manifest hashes.
- Consumes: verified API/frontend/browser results only; no planned result may be written as completed.

- [ ] **Step 1: Extend claim-audit consumers and assertions**

Add the React Demo, field-image boundary, and optional-Qwen boundary to `configs/week8_claims.yaml`. Tests must fail if public materials omit “no verified ground truth”, “field/out-of-domain”, `11/15`, `1/5`, or “no automatic model download”.

- [ ] **Step 2: Run claim tests to verify the new contract fails**

Run: `uv run pytest tests/release/test_claims.py tests/integration/test_react_demo_contract.py -q`

Expected: FAIL until every declared consumer is updated.

- [ ] **Step 3: Update evidence documents without rewriting history**

Record the React Demo as a new Week 8 interface. Keep Week 5 Streamlit/container values historical. State the actual Qwen browser result: real response only if verified; otherwise “UI unavailable state verified”. Do not modify classifier accuracy or field-generalization claims.

- [ ] **Step 4: Update paper and defense only where materially required**

Replace unattractive current-Demo screenshots with the audited React screenshot, captioning the field image as no-ground-truth and out-of-domain. Rebuild both 12-page PDFs; if pagination changes, render and inspect every page. Rebuild the 20-slide PPTX/Keynote and rerun overflow, Morph, Magic Move, notes, and visual QA.

- [ ] **Step 5: Regenerate claim ledger and release manifest**

Run:

```bash
uv run python scripts/audit_week8_claims.py \
  --config configs/week8_claims.yaml \
  --output reports/release/week8_claim_evidence.json \
  --check-links
uv run python scripts/build_release_candidate.py \
  --candidate-id week8-rc1 \
  --source-commit 08c57f63d09cc776826aefaed93b903a82637971 \
  --checkpoint outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/checkpoint.pt \
  --output reports/release/week8_rc1_manifest.json \
  --claims-output reports/release/week8_claim_evidence.json
```

Expected: claims, boundaries, links, and all required artifacts pass.

- [ ] **Step 6: Verify all affected artifact formats**

Run paper audit, PDF page/size/log checks, `slides_test.py`, PPTX/Keynote ZIP integrity, native Keynote transition inspection, and browser screenshot inspection. Record exact hashes in QA reports.

- [ ] **Step 7: Commit synchronized research artifacts**

Stage only the explicit files listed in this task and commit:

```bash
git commit -m "docs: synchronize react demo release evidence"
```

---

### Task 9: Run the Final Reproduction and Quality Gate

**Files:**
- Modify: `reports/week8_reproducibility.md`
- Modify: `reports/release/week8_rc1_manifest.json`
- Modify: `reports/release/week8_claim_evidence.json`
- Modify: any claim consumer whose final test count changes.

**Interfaces:**
- Produces: fresh final verification evidence for the exact publish commit candidate.
- Consumes: all implementation and documentation tasks.

- [ ] **Step 1: Run frontend and Python local gates**

```bash
cd frontend && npm run test:run && npm run build
cd ..
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv run ty check src/plantdisease app scripts
git diff --check
```

Expected: every command exits 0. Record the exact pytest count and warnings.

- [ ] **Step 2: Run the repository-external clean lane**

Use a new child of Python's runtime `tempfile.gettempdir()`:

```bash
uv run python scripts/run_week8_repro.py \
  --environment /var/folders/vf/5kqtfx6s0x99mh3nkcrp5f380000gn/T/plantdisease-week8-react-final-20260716 \
  --output outputs/plantvillage/week8_release/week8-rc1/clean_repro.json \
  --smoke-output outputs/plantvillage/week8_release/week8-rc1/clean_smoke/run_manifest.json
```

Expected: all eight Python commands pass. Frontend gates remain separately recorded because `run_week8_repro.py` is the locked Python lane.

- [ ] **Step 3: Scan tracked publication state**

Run checks for secret patterns, personal absolute paths, tracked data/weights/caches,
oversized tracked files, broken links, and unexpected generated intermediates. The
supplied image is allowed and documented; the source path
The original local source path must not appear in public documents or
manifests.

- [ ] **Step 4: Refresh final counts and hashes, then rerun affected gates**

Update only actual final results. Rebuild paper/PPT if their claim text changes, regenerate manifest/ledger, then rerun the full local gate once more. No code or test may be added after this final clean count without repeating the lane.

- [ ] **Step 5: Commit the final candidate content**

```bash
git add -u
git add frontend app/api.py app/examples/field_corn_leaf.jpeg scripts/run_demo_api.py \
  src/plantdisease/serving/images.py src/plantdisease/vlm/interactive.py \
  tests/serving/test_images.py tests/vlm/test_interactive.py tests/test_demo_api.py \
  tests/integration/test_react_demo_contract.py docs/ui/apple-design-implementation.md \
  reports/figures/week8_react_demo_desktop.png \
  reports/figures/week8_react_demo_mobile.png reports/week8_react_demo_qa.md
git commit -m "feat: complete week8 react qwen release candidate"
```

Expected: unrelated Week 7 render directories, inspect NDJSON, and LaTeX `.bbl/.blg` files remain unstaged.

- [ ] **Step 6: Record immutable release provenance**

Regenerate the manifest with the exact Step 5 commit, preserving verified runtime
lanes:

```bash
RELEASE_COMMIT=$(git rev-parse HEAD)
uv run python scripts/build_release_candidate.py \
  --candidate-id week8-rc1 \
  --source-commit 08c57f63d09cc776826aefaed93b903a82637971 \
  --release-commit "$RELEASE_COMMIT" \
  --checkpoint outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/checkpoint.pt \
  --output reports/release/week8_rc1_manifest.json \
  --claims-output reports/release/week8_claim_evidence.json
git add reports/release/week8_rc1_manifest.json reports/release/week8_claim_evidence.json
git commit -m "docs: record week8 react release provenance"
```

- [ ] **Step 7: Verify the committed tree**

Run the full Python/frontend gates against `HEAD`, inspect `git status -sb`, and confirm only known unrelated untracked artifacts remain.

---

### Task 10: Publish the Branch to GitHub as a Draft PR

**Files:**
- No repository file changes unless a Git remote configuration is needed locally.

**Interfaces:**
- Produces: configured GitHub remote, pushed `codex/week8-release-audit` branch, and draft pull request.
- Consumes: verified commits from Task 9 and authenticated GitHub CLI.

- [ ] **Step 1: Confirm GitHub authentication outside the restricted sandbox**

Run:

```bash
gh auth status
gh api user --jq .login
```

Expected: both commands exit 0 and print `panjoel812`. If the keyring times out, stop and report the exact blocker; never copy a token into project files or command output.

- [ ] **Step 2: Resolve the repository target**

Because no remote is currently configured, first check whether `panjoel812/PlantDiseaseAI` exists:

```bash
gh repo view panjoel812/PlantDiseaseAI --json nameWithOwner,visibility,defaultBranchRef
```

If it exists, confirm it is the intended target and add `origin` using its HTTPS URL. If it does not exist, request the user's visibility choice before running `gh repo create`; repository creation is an external state change not implied by merely naming the project.

- [ ] **Step 3: Confirm publish scope**

Run:

```bash
git status -sb
BASE_BRANCH=$(gh repo view panjoel812/PlantDiseaseAI --json defaultBranchRef --jq .defaultBranchRef.name)
git fetch origin "$BASE_BRANCH"
git diff --stat "origin/$BASE_BRANCH"...HEAD
git log --oneline "origin/$BASE_BRANCH"..HEAD
```

Expected: only intentional Week 8 and React/Qwen commits are included. Do not stage or publish unrelated untracked render/intermediate files.

- [ ] **Step 4: Push the current branch**

Run:

```bash
git push -u origin codex/week8-release-audit
```

Expected: branch tracking is configured and the remote reports success.

- [ ] **Step 5: Open a draft pull request**

Create `/private/tmp/plantdisease-week8-pr-body.md` with `apply_patch`. Its Markdown
body describes the Week 8 release audit, React Liquid Glass UI, supplied field example,
optional local Qwen, validations, and limitations. Run:

```bash
gh pr create --draft --fill --head codex/week8-release-audit \
  --body-file /private/tmp/plantdisease-week8-pr-body.md
```

Expected: a GitHub pull-request URL is returned.

- [ ] **Step 6: Verify remote state and report**

Run:

```bash
gh pr view --json url,isDraft,headRefName,baseRefName,statusCheckRollup
```

Report branch, final commits, PR URL, exact validation results, Qwen runtime status, and any remaining remote checks. Do not create a tag or GitHub Release.
