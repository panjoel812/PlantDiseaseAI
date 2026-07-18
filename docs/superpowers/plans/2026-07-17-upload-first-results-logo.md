# Upload-First Results and Fused Logo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Put the upload/photo card above complete classifier and management results, move the viewport to those results after analysis, and replace the generic leaf with a fused Desmos/leaf Apple-minimal vector logo.

**Architecture:** Keep inference and provider services unchanged. Refactor only React presentation: `App` owns the vertical flow and results navigation, `AssistantPanel` derives its selected mode from classification readiness, result glass surfaces participate in normal document flow, and a focused `ProjectLogo` component owns the repository-native fused vector mark.

**Tech Stack:** React 19, TypeScript, Vite, Vitest, Testing Library, `liquid-glass-react`, CSS media/accessibility queries, inline SVG.

## Global Constraints

- The external SVG at `$HOME/Documents/Project/DesmosBezierRenderer/exports/desmos_remaining_functions.svg` is read-only reference material and must not be modified.
- Omit source paths `expr-003` through `expr-018` so the white background and rounded-square frame never enter the project logo.
- Reuse source paths `expr-019` through `expr-054` as the Bézier gesture inside the new leaf mark.
- The upload/photo card appears before all generated results in DOM and visual order.
- Successful analysis moves to the results region; failed analysis does not.
- Management guidance becomes the default assistant mode after each successful analysis; Visual evidence remains selectable.
- Classifier and assistant result content use normal document flow with no nested vertical scroll container.
- Large cards retain `liquid-glass-react` with `elasticity={0}` and fixed pointer-independent geometry.
- Mobile order is upload, classifier, assistant, safety boundary.
- Reduced-motion users receive instant navigation and no ambient looping motion.
- Classifier, Qwen, cloud-provider, API-key, Grad-CAM, and safety semantics remain unchanged.

---

### Task 1: Create the fused Desmos/leaf project logo

**Files:**
- Create: `scripts/export_logo_paths.py`
- Create (generated): `frontend/src/assets/desmosInnerPaths.ts`
- Create: `frontend/src/components/ProjectLogo.tsx`
- Modify: `frontend/src/components/Hero.tsx`
- Modify: `frontend/src/styles.css`
- Test: `frontend/src/components/components.test.tsx`

**Interfaces:**
- Consumes: exact Bézier `d` values from source paths `expr-019`–`expr-054` and the existing `BrandLeafIcon` silhouette direction.
- Produces: `ProjectLogo({ className?, labelled? }: ProjectLogoProps): JSX.Element`.

- [ ] **Step 1: Write the failing logo component test**

Add this test to `frontend/src/components/components.test.tsx`:

```tsx
it("renders the fused project mark without the source frame", () => {
  render(<ProjectLogo labelled />);
  const logo = screen.getByRole("img", { name: "PlantDiseaseAI" });
  expect(logo).toHaveAttribute("viewBox", "0 0 480 480");
  expect(logo.querySelector('[data-logo-layer="leaf"]')).toBeInTheDocument();
  expect(logo.querySelector('[data-logo-layer="desmos-gesture"]')).toBeInTheDocument();
  expect(logo.querySelector("rect")).not.toBeInTheDocument();
  expect(logo.querySelector('[data-source-path="expr-003"]')).not.toBeInTheDocument();
  expect(logo.querySelector('[data-source-path="expr-019"]')).toBeInTheDocument();
  expect(logo.querySelector('[data-source-path="expr-054"]')).toBeInTheDocument();
});
```

Import `ProjectLogo` directly from `./ProjectLogo`.

- [ ] **Step 2: Run the focused test and verify RED**

Run:

```bash
cd frontend
npm test -- --run src/components/components.test.tsx
```

Expected: import failure because `ProjectLogo.tsx` does not exist.

- [ ] **Step 3: Add the deterministic inner-path exporter**

Create `scripts/export_logo_paths.py`:

```python
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

PATH_PATTERN = re.compile(r'<path id="(expr-(\d{3}))" d="([^"]+)"\s*/>')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = args.input.read_text(encoding="utf-8")
    paths = [
        (path_id, data)
        for path_id, number, data in PATH_PATTERN.findall(source)
        if 19 <= int(number) <= 54
    ]
    expected_ids = [f"expr-{number:03d}" for number in range(19, 55)]
    if [path_id for path_id, _ in paths] != expected_ids:
        raise SystemExit("Expected contiguous source paths expr-019 through expr-054")
    payload = json.dumps(paths, ensure_ascii=False, indent=2)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        "// Generated from the supplied Desmos SVG; do not edit by hand.\n"
        f"export const DESMOS_INNER_PATHS = {payload} as const;\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
```

Generate the repository-native data file without modifying the source:

```bash
uv run python scripts/export_logo_paths.py \
  --input "$HOME/Documents/Project/DesmosBezierRenderer/exports/desmos_remaining_functions.svg" \
  --output frontend/src/assets/desmosInnerPaths.ts
```

Expected: the output exports exactly 36 ordered path tuples, beginning with
`expr-019` and ending with `expr-054`.

- [ ] **Step 4: Implement the focused SVG component**

Create `frontend/src/components/ProjectLogo.tsx` with this structure:

```tsx
import { DESMOS_INNER_PATHS } from "../assets/desmosInnerPaths";

interface ProjectLogoProps {
  className?: string;
  labelled?: boolean;
}

export function ProjectLogo({ className, labelled = false }: ProjectLogoProps) {
  return (
    <svg
      className={className}
      viewBox="0 0 480 480"
      role={labelled ? "img" : undefined}
      aria-label={labelled ? "PlantDiseaseAI" : undefined}
      aria-hidden={labelled ? undefined : "true"}
    >
      <defs>
        <linearGradient id="plant-logo-fill" x1="84" y1="72" x2="392" y2="408">
          <stop offset="0" stopColor="#bfe8ff" />
          <stop offset="0.48" stopColor="#aee8c7" />
          <stop offset="1" stopColor="#48a879" />
        </linearGradient>
        <linearGradient id="plant-logo-line" x1="112" y1="132" x2="372" y2="332">
          <stop offset="0" stopColor="#ffffff" stopOpacity="0.96" />
          <stop offset="1" stopColor="#1f7652" stopOpacity="0.88" />
        </linearGradient>
      </defs>
      <path
        data-logo-layer="leaf"
        d="M404 58C225 65 113 153 124 326c78 52 199 25 250-74 29-57 35-126 30-194Z"
        fill="url(#plant-logo-fill)"
        stroke="#247653"
        strokeWidth="8"
        strokeLinejoin="round"
      />
      <path
        d="M102 398C171 291 245 218 350 145"
        fill="none"
        stroke="#ffffff"
        strokeOpacity="0.72"
        strokeWidth="11"
        strokeLinecap="round"
      />
      <g
        data-logo-layer="desmos-gesture"
        fill="none"
        stroke="url(#plant-logo-line)"
        strokeWidth="8"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        {DESMOS_INNER_PATHS.map(([id, d]) => (
          <path key={id} data-source-path={id} d={d} />
        ))}
      </g>
    </svg>
  );
}
```

In `Hero.tsx`, remove `BrandLeafIcon`, import `ProjectLogo`, and render:

```tsx
<span className="brand">
  <ProjectLogo className="brand-logo" />
  <span>PlantDiseaseAI</span>
</span>
```

Add CSS:

```css
.brand-logo {
  width: 2rem;
  height: 2rem;
  flex: 0 0 2rem;
  overflow: visible;
  filter: drop-shadow(0 0.45rem 0.85rem rgb(43 127 87 / 16%));
}

@media (prefers-reduced-transparency: reduce) {
  .brand-logo { filter: none; }
}
```

- [ ] **Step 5: Run the focused test and verify GREEN**

Run: `cd frontend && npm test -- --run src/components/components.test.tsx`

Expected: logo test passes and existing component tests remain green.

- [ ] **Step 6: Commit Task 1**

```bash
git add scripts/export_logo_paths.py frontend/src/assets/desmosInnerPaths.ts \
  frontend/src/components/ProjectLogo.tsx \
  frontend/src/components/Hero.tsx frontend/src/styles.css \
  frontend/src/components/components.test.tsx
git commit -m "feat: add fused plant project logo"
```

---

### Task 2: Rebuild the page as upload-first vertical flow

**Files:**
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/styles.css`
- Modify: `frontend/src/smoke.test.tsx`

**Interfaces:**
- Consumes: `demo.classification.status`, `ImageWorkspace`, `ClassifierPanel`, `AssistantPanel`, and `SafetyNotice`.
- Produces: `resultsRef: RefObject<HTMLElement | null>` and DOM regions `.upload-section`, `.results-section`, `.results-grid`.

- [ ] **Step 1: Write the failing layout contract test**

Add to `frontend/src/smoke.test.tsx` after rendering `<App />`:

```tsx
const upload = screen.getByRole("region", { name: "Upload and analyze" });
const results = screen.getByRole("region", { name: "Analysis results" });
expect(upload.compareDocumentPosition(results)).toBe(Node.DOCUMENT_POSITION_FOLLOWING);
expect(results).toHaveAttribute("tabindex", "-1");
expect(results.querySelector('[data-testid="classifier-glass"]')).toBeInTheDocument();
expect(results.querySelector('[data-testid="assistant-glass"]')).toBeInTheDocument();
```

- [ ] **Step 2: Run the smoke test and verify RED**

Run: `cd frontend && npm test -- --run src/smoke.test.tsx`

Expected: missing named upload and result regions.

- [ ] **Step 3: Implement the vertical DOM order**

Refactor `App.tsx` to import `useEffect`, `useRef`, and render:

```tsx
const resultsRef = useRef<HTMLElement>(null);
const previousClassificationStatus = useRef(demo.classification.status);

useEffect(() => {
  const previous = previousClassificationStatus.current;
  const current = demo.classification.status;
  previousClassificationStatus.current = current;
  if (previous !== "loading" || current !== "success") return;
  const results = resultsRef.current;
  if (!results) return;
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  results.scrollIntoView({ behavior: reducedMotion ? "auto" : "smooth", block: "start" });
  results.focus({ preventScroll: true });
}, [demo.classification.status]);
```

Replace `.workspace-grid`/`.result-rail` markup with:

```tsx
<section className="upload-section" aria-label="Upload and analyze">
  <ImageWorkspace
    previewUrl={demo.previewUrl}
    selectedFileName={demo.selectedFile?.name ?? null}
    hasImage={demo.selectedFile !== null}
    classificationStatus={demo.classification.status}
    onSelectFile={demo.selectFile}
    onAnalyze={() => void demo.classify({ topK: 5, includeGradcam: true })}
  />
</section>
<section
  ref={resultsRef}
  className="results-section"
  aria-labelledby="analysis-results-title"
  tabIndex={-1}
>
  <div className="results-heading">
    <h2 id="analysis-results-title">Analysis results</h2>
    <p>Classifier evidence and optional management guidance.</p>
  </div>
  <div className="results-grid">
    <ClassifierPanel state={demo.classification} />
    <AssistantPanel
      classificationReady={demo.classification.status === "success"}
      qwenEnabled={
        demo.classification.status === "success" &&
        demo.qwenRuntime.status === "success" &&
        demo.qwenRuntime.data.ready
      }
      qwenRuntime={demo.qwenRuntime}
      qwenState={demo.qwen}
      providers={demo.adviceProviders}
      adviceState={demo.advice}
      onAskQwen={(question) => void demo.ask(question)}
      onRetryQwenRuntime={() => void demo.refreshQwenRuntime()}
      onAskAdvice={(provider, question) => void demo.askAdvice(provider, question)}
      onConfigureProvider={demo.configureProvider}
      onClearProvider={demo.clearProvider}
    />
  </div>
</section>
<SafetyNotice />
```

- [ ] **Step 4: Implement the vertical layout CSS**

Replace the fixed-shell desktop geometry with:

```css
body { overflow-x: hidden; overflow-y: auto; }
#root { min-height: 100%; height: auto; }
.page-shell { height: auto; min-height: 100dvh; overflow: visible; }
.app-field { display: block; min-height: 0; }

.upload-section {
  min-height: clamp(30rem, 68dvh, 49rem);
}

.upload-section .image-workspace-stage { height: 100%; min-height: inherit; }

.results-section {
  scroll-margin-top: 0.75rem;
  margin-top: clamp(1.25rem, 2.5vw, 2.2rem);
  outline: none;
}

.results-heading { margin: 0 0 0.8rem; padding-inline: 0.4rem; }
.results-heading h2 { margin: 0; font-size: clamp(1.55rem, 2.4vw, 2.2rem); }
.results-heading p { margin: 0.2rem 0 0; }

.results-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  align-items: start;
  gap: clamp(0.9rem, 1.5vw, 1.35rem);
}

@media (max-width: 760px) {
  .upload-section { min-height: min(42rem, 125vw); }
  .results-grid { grid-template-columns: minmax(0, 1fr); }
}
```

Delete obsolete `.workspace-grid`, `.result-rail`, and desktop `body { overflow:
hidden; }` rules rather than leaving conflicting declarations.

- [ ] **Step 5: Run layout tests and verify GREEN**

Run:

```bash
cd frontend
npm test -- --run src/smoke.test.tsx
npm run lint
```

Expected: smoke contract and lint pass.

- [ ] **Step 6: Commit Task 2**

```bash
git add frontend/src/App.tsx frontend/src/styles.css frontend/src/smoke.test.tsx
git commit -m "refactor: move analysis results below upload"
```

---

### Task 3: Default to management and remove nested result scrolling

**Files:**
- Modify: `frontend/src/components/AssistantPanel.tsx`
- Modify: `frontend/src/components/ClassifierPanel.tsx`
- Modify: `frontend/src/components/QwenPanel.tsx`
- Modify: `frontend/src/components/AdvicePanel.tsx`
- Modify: `frontend/src/styles.css`
- Modify: `frontend/src/components/components.test.tsx`

**Interfaces:**
- Consumes: `AssistantPanelProps.classificationReady`.
- Produces: assistant mode derived on readiness transition and result glass surfaces that size from their content.

- [ ] **Step 1: Write failing assistant and scroll-contract tests**

Add to `components.test.tsx`:

```tsx
it("opens management guidance when classification becomes ready", () => {
  const props = {
    qwenEnabled: false,
    qwenRuntime: readyQwenRuntime(),
    qwenState: idle<QwenAnswer>(),
    providers: idle<AdviceProvidersResponse>(),
    adviceState: idle<ManagementAdvice>(),
    onAskQwen: vi.fn(),
    onRetryQwenRuntime: vi.fn(),
    onAskAdvice: vi.fn(),
    onConfigureProvider: vi.fn().mockResolvedValue(undefined),
    onClearProvider: vi.fn().mockResolvedValue(undefined),
  };
  const { rerender } = render(
    <AssistantPanel {...props} classificationReady={false} />,
  );
  expect(screen.getByRole("tab", { name: /visual evidence/i })).toHaveAttribute("aria-selected", "true");
  rerender(<AssistantPanel {...props} classificationReady />);
  expect(screen.getByRole("tab", { name: /management guidance/i })).toHaveAttribute("aria-selected", "true");
});
```

Extend the CSS contract assertion:

```tsx
expect(styles).toMatch(/\.results-grid[\s\S]*?align-items:\s*start/);
expect(styles).toMatch(/\.results-grid[\s\S]*?\.panel-state-body[\s\S]*?overflow:\s*visible/);
```

- [ ] **Step 2: Run component tests and verify RED**

Run: `cd frontend && npm test -- --run src/components/components.test.tsx`

Expected: Management guidance remains unselected after readiness changes.

- [ ] **Step 3: Derive the assistant mode from analysis readiness**

In `AssistantPanel.tsx`, import `useEffect` and add:

```tsx
useEffect(() => {
  setMode(classificationReady ? "guidance" : "visual");
}, [classificationReady]);
```

User tab selections remain manual after the effect; the effect only runs when
classification readiness changes.

- [ ] **Step 4: Make result Liquid Glass participate in document flow**

For `ClassifierPanel`, `QwenPanel`, and `AdvicePanel`, change the result
`LiquidGlass` inline style from the centered absolute value to:

```tsx
style={{ position: "relative", width: "100%" }}
```

Do not change `ImageWorkspace`; the photo glass remains a fixed-size stage.

Add result-only CSS:

```css
.results-grid .glass-stage { overflow: visible; }
.results-grid .glass-stage > .glass-surface { height: auto; min-height: 100%; }
.results-grid .glass-surface .glass,
.results-grid .glass-surface .glass > .transition-all { height: auto; min-height: 100%; }
.results-grid .side-panel { height: auto; min-height: 100%; overflow: visible; }
.results-grid .panel-state-body { overflow: visible; scrollbar-gutter: auto; }
.results-grid .assistant-tab-panel,
.results-grid .assistant-tab-panel > .glass-stage { height: auto; overflow: visible; }
.results-grid .raw-response p { max-height: none; overflow: visible; }
```

Remove fixed `.classifier-stage`, `.qwen-stage`, and result-row height overrides
from desktop and mobile media queries. Keep horizontal clipping only where
needed for rounded media, never on the results cards.

- [ ] **Step 5: Run frontend verification and verify GREEN**

Run:

```bash
cd frontend
npm test -- --run
npm run lint
npm run build
```

Expected: all React tests pass, lint is clean, and Vite build succeeds.

- [ ] **Step 6: Commit Task 3**

```bash
git add frontend/src/components/AssistantPanel.tsx \
  frontend/src/components/ClassifierPanel.tsx \
  frontend/src/components/QwenPanel.tsx \
  frontend/src/components/AdvicePanel.tsx \
  frontend/src/components/components.test.tsx frontend/src/styles.css
git commit -m "feat: expand complete analysis results"
```

---

### Task 4: Update public behavior documentation and publish

**Files:**
- Modify: `README.md`
- Modify: `README.zh-CN.md`
- Modify: `reports/week8_react_demo_qa.md`
- Modify: `docs/artifact-index.md`

**Interfaces:**
- Consumes: final DOM behavior and fused logo from Tasks 1–3.
- Produces: accurate public descriptions without new research claims.

- [ ] **Step 1: Update English and Chinese demo descriptions**

Add matching statements to both READMEs:

```text
The React demo uses an upload-first flow. After analysis succeeds, it moves to
fully expanded classifier and management panels below the photograph; result
cards do not hide evidence inside nested vertical scrolling.
```

```text
React Demo 采用“先上传、后查看结果”的纵向流程。分析成功后，页面会移动到
照片下方完整展开的分类器与管理建议面板；结果卡不会通过嵌套纵向滚动隐藏证据。
```

Document that the header logo fuses the supplied Desmos Bézier gesture with the
PlantDiseaseAI leaf and that the external source file is not bundled or edited.

- [ ] **Step 2: Update evidence indexes without inventing browser QA**

Record implementation paths and mark browser geometry as `not_run` unless it is
actually inspected. Do not reuse previous 1280×720 evidence for the new layout.

- [ ] **Step 3: Run scoped documentation verification**

Run:

```bash
uv run pytest -q tests/release/test_public_readme_contract.py
git diff --check
```

Expected: README contract passes and no whitespace errors are reported.

- [ ] **Step 4: Commit and push public main**

```bash
git add README.md README.zh-CN.md reports/week8_react_demo_qa.md docs/artifact-index.md
git commit -m "docs: describe upload-first research demo"
git push origin main
```

Expected: public `main` advances to the final implementation commit. No paper,
PPTX, Keynote, checkpoint, dataset, API key, or unrelated artifact is staged.
