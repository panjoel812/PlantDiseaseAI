# Week 8 React Demo Browser QA

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
