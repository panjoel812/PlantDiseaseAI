# Week 8 React Demo A+ Redesign QA (current)

Date: 2026-07-17 (Asia/Shanghai)

## Compact configurable-demo closeout

Implementation commit: `afca2d5` (published to public `main`).

The delivered follow-up adds bounded morphology-only Qwen prompts, concise structured observation rows with the original model response behind a closed disclosure, temporary OpenAI/Claude/Gemini configuration held only in FastAPI process memory, configure/clear controls directly in the website, compact viewport-derived desktop geometry, and fixed ambient leaf/dew decoration with reduced-motion and reduced-transparency fallbacks. The full English and Chinese public guides are reciprocal and document the local, Apple Container, and Docker paths.

Per the user's explicit final-pass instruction, the API/Vite servers, 1440×900 and 1920×1080 browser geometries, 390×844 mobile geometry, automated suites, and release-manifest generator were **not rerun** during this documentation closeout. No new PASS claim is made for those checks. The QA below is retained as the previously executed baseline for its stated commits and viewports; `reports/release/week8_rc1_manifest.json` likewise remains the historical manifest for its embedded source commit rather than being relabeled without fresh hashes.

Implementation commits: `c1e6b44`, `a51dfbe`, `083603c`, and `331950b`.

Target flow: React page loads the supplied field image → one real MPS classifier pass returns the complete 38-class distribution → the service aggregates crop probabilities → the UI shows only conditions within the selected crop, Grad-CAM, research warnings, and the optional-Qwen panel.

## Previously executed A+ baseline

| Check | Result | Evidence |
|---|---|---|
| Page identity and meaningful render | PASS | URL `http://127.0.0.1:5173/`; title `PlantDiseaseAI Research Demo`; hero, supplied image, classifier, Qwen and research-boundary regions present. |
| Crop-first hierarchy | PASS | Supplied field image rendered `Corn (maize)` crop probability `87.9%`; conditions were restricted to four Corn classes. Python test uses Apple/Grape `Black rot` inputs and proves only the selected crop's conditions survive. |
| One-model semantics | PASS | `single_model_taxonomy_aggregation_v1` consumes the full probability vector from one `predict_topk` call; README explicitly states this is not a second crop detector. |
| No duplicate same-name disease rows | PASS | React fixture contains Apple and Grape `Black rot`; rendered selected-Apple condition list contains one `Black rot` plus Apple healthy only. |
| Real classifier and Grad-CAM interaction | PASS | Clicking **Analyze leaf** changed the action to **Analyze again**, rendered crop and condition results, and produced a non-null Grad-CAM heatmap; final observed total was `27.7 ms`, a functional sample rather than a benchmark. |
| Desktop layout | PASS | `1280 × 720`; `scrollWidth == clientWidth == 1280`; no framework overlay or console warning/error. |
| Mobile geometry | PASS | `390 × 844`; root `scrollWidth == clientWidth == 390`; image/classifier/Qwen stack widths `367.61 px`; no console warning/error. The controller's DPR screenshot crop was not promoted as a current artifact, so the DOM/geometry evidence is the claim. |
| Mouse stability | PASS | Before/after pointer movement across image and classifier, image stage remained `802.47 × 672 px` and classifier remained `391.45 × 426.40 px` at identical coordinates. |
| Light Liquid Glass material | PASS | Three production surfaces still render `liquid-glass-react`; large-card refraction filter resolves to `none`, while bright edges, translucency, blur and highlights remain. |
| Ambient decoration | PASS | Bottom leaf/dew layer is `aria-hidden`, `pointer-events:none`, and CSS-animated; reduced-motion contract disables animation and transforms. |
| Stable states | PASS | Desktop workspace has a fixed height and fixed result-rail rows; classifier/Qwen bodies have dedicated scrollable state containers, preventing layout jumps. |
| Console health | PASS | Browser error/warn log was empty after initial render, classification, pointer movement and responsive resize. |
| Reduced motion browser emulation | NOT AVAILABLE | Browser controller did not expose media-feature emulation; the CSS branch is enforced by the frontend smoke contract. |

Previously executed verification commands:

```bash
cd frontend
npm test -- --run       # 47 passed
npm run lint            # passed
npm run build           # passed
cd ..
.venv/bin/pytest -q tests/serving/test_hierarchy.py tests/serving/test_service.py tests/test_demo_api.py
# 41 passed, one third-party Starlette deprecation warning
```

## Previous concept fidelity ledger

1. Mist-white, pale-blue and tender-green gradient matches the accepted reference palette.
2. Large optical headline and restrained SF-style typography preserve the Apple-like information hierarchy.
3. The supplied photo remains the dominant floating card; no generated substitute is used.
4. Crop-first result hierarchy, bright thin right panels and broad low-opacity shadows match the reference material language.
5. `liquid-glass-react` remains in all three surfaces but is intentionally restrained to non-deforming material/highlight behavior.
6. Existing upload/analyze controls remain over the photo; the concept's invented left-side “Photography tips” rail was intentionally not implemented.
7. Bottom leaf/dew forms are code-native, non-interactive and slower than task motion, with a reduced-motion fallback.
8. The classifier scrolls internally at shorter viewports so the outer image/result geometry remains stable; this is an intentional deviation from the taller static concept.

Previous representative screenshot: `reports/figures/week8_react_demo_desktop.png`.

## Remaining limitations

- The field image is outside the verified PlantVillage distribution and has no validated label.
- Crop-first aggregation is still a closed-set view of one 38-class model, not a separately trained crop detector.
- Native OS file chooser completion remains a manual check; file selection and drag/drop are covered by component tests.
- Qwen full inference was not rerun in this redesign QA because the optional weights were not required for the classifier/UI change.

---

## Historical QA before the A+ redesign (superseded visual evidence)

Date: 2026-07-16–17 (Asia/Shanghai)

Tested implementation commits: `d549540` and QA correction `2f7bfc8`, plus the follow-up safety tests documented in this report.

Target flow: React page loads the supplied field image → real MPS classifier returns Top-5 and Grad-CAM → the UI shows research warnings and the true optional-Qwen runtime state.

## Environment and provenance

- Browser path: Codex in-app Browser controller; final screenshots contain no browser-controller or framework overlay.
- Desktop viewport and representative screenshot: exactly `1280 × 720`.
- Mobile viewport and representative screenshot: exactly `390 × 844`.
- API: FastAPI on `127.0.0.1:8000`; React/Vite on `127.0.0.1:5173`.
- Classifier device: Apple MPS.
- Checkpoint: `outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/checkpoint.pt`.
- Checkpoint ID returned by the API: `d53c09ab7fd3`; model: `resnet50`.
- Supplied/repository image SHA-256: `0364ff44229c70666216343057f9ae77d82438a7f842b30af1ffabb786061a7e`; the audited repository copy is `app/examples/field_corn_leaf.jpeg`.
- The field image has no verified ground truth. All displayed classes are model predictions, not field-accuracy evidence.

## Checks

| Check | Result | Evidence |
|---|---|---|
| Page identity and meaningful first render | PASS | Title `PlantDiseaseAI Research Demo`; hero, supplied image, classifier and Ask Qwen regions present. |
| Real classifier execution | PASS | Top-1 `Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot`, probability `0.870144`; the captured MPS requests rendered `335.5 ms` desktop and `38.9 ms` mobile totals. These individual timings are functional evidence, not a benchmark. |
| Top-5 and Grad-CAM | PASS | Ordered Top-5 progress bars and a non-null Grad-CAM heatmap rendered from the API response. |
| Warning boundary | PASS | Both API warnings render before Top-5, so the agricultural/field-generalization boundary is visible without scrolling the classifier surface. |
| Qwen runtime truthfulness | PASS | `/api/qwen/status`: platform/dependency available, `weights_cached=false`, `ready=false`; the panel disables Ask Qwen, shows the exact cache command and “No automatic download”, and **Check again** successfully re-probes the unchanged state without a console error. Unsupported-platform and missing-dependency branches are covered by component tests. |
| Desktop layout | PASS | `scrollWidth == clientWidth == 1280`; no horizontal overflow, browser-controller/framework overlay or console error. |
| Mobile layout | PASS | `scrollWidth == clientWidth == 390`; single-column stacking, wrapped copy and complete controls; no console error. |
| Keyboard focus | PASS | Keyboard navigation reached an interactive control with `3px` green `focus-visible` outline and `3px` offset. |
| Reduced motion/transparency styles | NOT VERIFIED IN BROWSER | CSS preference branches remain present and are covered by the frontend smoke contract, but this Browser controller does not expose media-feature emulation. No browser-level claim is made. |
| Contrast correction | PASS | Result/Qwen inner panels use an ivory 86% material so dark text stays readable over the real Liquid Glass surface; the style is covered by the frontend smoke contract and final screenshots. |
| Reset interaction | PASS | Reset cancels the current result and returns classifier/Qwen feature state to idle; image selection becomes empty by current product design. |
| Upload interaction in controlled Chrome | PARTIAL | The native chooser opened, but the Browser security layer returned `Not allowed` for Downloads and workspace paths. The follow-up controller session did not expose Chrome file-selection control. File selection and drag/drop are covered by component/hook tests; interactive OS chooser selection remains a manual check. |

Representative API response facts:

```json
{
  "checkpoint_id": "d53c09ab7fd3",
  "top1": {
    "class_name": "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot",
    "probability": 0.8701441287994385
  },
  "gradcam": true,
  "qwen": {
    "model_id": "mlx-community/Qwen3-VL-4B-Instruct-4bit",
    "weights_cached": false,
    "ready": false
  }
}
```

## Qwen local experience boundary

The React panel is wired to the real local `mlx-community/Qwen3-VL-4B-Instruct-4bit` service, not a scripted chat response. It is not directly runnable on this machine at QA time because the approximately 3 GB weights are absent from the default Hugging Face cache. The UI and README give the explicit opt-in path:

```bash
uv sync --group vlm
uv run --group vlm hf download mlx-community/Qwen3-VL-4B-Instruct-4bit
```

After caching, restart the API, then click **Check again** or reload the React page. Browser requests themselves never trigger a model download. The only measured VLM evidence remains the fixed five-image smoke: choice/few-shot `11/15`, fine-grained condition `1/5`; this is not a complete VQA evaluation or professional diagnosis.

## Concept fidelity ledger

1. **Hierarchy retained:** graphite shell, large ivory app field, dominant image workspace, right result rail and bottom research boundary match the accepted analyzed concept.
2. **Real Liquid Glass retained:** image, classifier and Ask Qwen surfaces render `liquid-glass-react`; focused translucency and rounded geometry replace generic card styling.
3. **Source image exactness retained:** the production default uses the byte-identical user-supplied corn-leaf photo rather than a generated substitute.
4. **Data fidelity improved over concept:** concept placeholder probabilities were replaced by the real checkpoint output (`87.0%` Top-1) and actual Grad-CAM.
5. **Qwen readiness intentionally differs:** the concept shows a ready example; the rendered QA evidence truthfully shows the current `ready=false` local state and setup path.
6. **Responsive adaptation is intentional:** desktop remains a two-column research workspace; mobile stacks the same three glass surfaces without horizontal overflow.
7. **Warnings remain evidence-first:** the persistent bottom boundary is visible at both sizes; detailed classifier warnings appear before predictions inside the classifier surface.

## Commands and artifacts

```bash
uv run python scripts/run_demo_api.py \
  --checkpoint outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/checkpoint.pt \
  --device mps --host 127.0.0.1 --port 8000
cd frontend && npm run dev -- --host 127.0.0.1 --port 5173
npm test -- --run
npm run build
npm run lint
uv run pytest tests/integration/test_react_demo_contract.py -q
```

- Desktop screenshot: `reports/figures/week8_react_demo_desktop.png`
- Mobile screenshot: `reports/figures/week8_react_demo_mobile.png`
- Static integration contract: `tests/integration/test_react_demo_contract.py`

## Remaining limitations

- The OS-native file chooser could not be completed through the controlled-browser security boundary; perform one manual upload check before a public live demo.
- Reduced-motion and reduced-transparency media queries passed static tests but were not emulated in the controlled browser.
- Qwen full inference was not rerun because its weights are not in the default local cache. This QA verifies the real unavailable state and opt-in setup, not a generated answer.
- The field image is outside the verified PlantVillage distribution and has no validated label.
