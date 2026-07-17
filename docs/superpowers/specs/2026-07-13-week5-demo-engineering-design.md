# Week 5 Demo Engineering Design

## Context

Week 5 turns the frozen classification and explainability work into a runnable demo. The
current production candidate is
`outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/checkpoint.pt`, using
ResNet50, `image_size=224`, official PlantVillage split, and Grad-CAM target layer
`layer4.2`. All claims remain limited by the known official split `leaf_id` overlap and
PlantVillage's controlled-background domain.

## Scope

This design covers the full Week 5 engineering closure:

- UI-independent serving layer for checkpoint loading, preprocessing, Top-5 prediction,
  Grad-CAM overlays, timing, warnings, and stable exceptions.
- Streamlit demo that delegates inference to the serving layer.
- Model cache so repeated UI interactions do not reload the checkpoint.
- Disease knowledge mapping with educational, non-prescriptive text.
- Fixed example image and local end-to-end command.
- Apple `container` CPU runtime, healthcheck, and exclusion of raw data, caches,
  checkpoints, and generated outputs from the build context.
- README, artifact index, and TASKS updates only for items actually validated.

## Architecture

Create `src/plantdisease/serving/` as the only new runtime boundary. It reuses the
existing project primitives: `load_checkpoint`, `build_eval_transform`, `predict_topk`,
`resolve_target_layer`, `GradCAM`, and `overlay_heatmap`.

The central API is `InferenceService`. It can be constructed from a real checkpoint or
from injected test dependencies. It exposes one `predict()` method that accepts image
bytes, validates and decodes the input, runs canonical preprocessing, returns Top-5
predictions, optionally creates a Grad-CAM heatmap and overlay, and attaches timing,
model metadata, disease knowledge, and safety warnings.

The Streamlit app lives in `app/streamlit_app.py`. It owns only UI concerns: sidebar
configuration, file upload, example selection, calling cached service construction, and
rendering results or clear error messages. It must not duplicate label mapping,
preprocessing, Top-5 sorting, or Grad-CAM logic.

## Data Flow

1. Image bytes are validated before decoding. Empty files, files over 10 MiB, corrupt
   image bytes, and images outside sane dimensions are rejected with typed validation
   errors.
2. Valid input is converted to RGB and transformed by `build_eval_transform(image_size)`
   from the loaded checkpoint config.
3. `predict_topk` produces closed-set probabilities. The highest-probability class is
   used as the default Grad-CAM target.
4. If Grad-CAM is enabled, the service resolves the target layer, creates a short-lived
   `GradCAM` context, generates a normalized heatmap, and blends it over the input image.
5. The service returns structured metadata: model name, checkpoint path, checkpoint
   identifier, image size, target layer, timings, predictions, disease knowledge, and
   safety warnings.

## Error Handling And Safety

The service defines stable exceptions for input validation and inference failures. The UI
maps these to Chinese messages without exposing stack traces.

The classifier remains a closed-set PlantVillage model. It does not detect unknown
diseases, non-leaf images, or field deployment safety. Every successful result includes
an educational-use warning. If the top confidence is below `0.80`, the result also
includes a low-confidence warning. The disease knowledge text must avoid pesticide names,
dosages, regulatory instructions, or definitive treatment claims.

## Testing And Evidence

Use TDD for new behavior. The minimum Week 5 validation set is:

- Service unit tests for image byte validation, Top-5 metadata, low-confidence warnings,
  Grad-CAM overlay output, model cache identity, and exception boundaries.
- Disease knowledge tests for common PlantVillage label parsing and default fallback.
- Streamlit startup/import smoke test that proves the app module can be loaded without
  constructing a real model.
- CLI-style local end-to-end script against a fixed example image and checkpoint when
  the local checkpoint is present.
- `Containerfile` and `.dockerignore` checks that build context excludes data, outputs,
  local caches, secrets, and checkpoint weights.
- README and artifact index updates that cite only commands actually run.

If Apple `container` cannot run because the local container system or kernel is not ready,
record that the container files are present and the local validations passed, but do not
mark container runtime validation complete.

## Completion Criteria

Week 5 can be marked complete only when local service tests, Streamlit smoke, lint, and a
fixed example inference command pass. Apple `container` runtime, screenshot/GIF, and
resource metrics are marked complete only after real local evidence exists.
