# React Liquid Glass + Qwen Demo Design

Date: 2026-07-16
Status: approved architecture, pending written-spec review

## Goal

Replace the primary Streamlit showcase with a polished React demo that uses
`liquid-glass-react`, follows the Apple Design guidance installed from
`emilkowalski/skills`, accepts a real uploaded field image, exposes the existing
classifier/Grad-CAM pipeline, and offers an optional local Qwen3-VL question panel.
The existing Streamlit app remains a compatibility entry point.

The supplied `KT-2019090405.jpeg` becomes the default field example and the source
for new demo screenshots. It has no project-verified ground-truth label and must be
described as an out-of-domain field example, never as evidence that a prediction is
correct.

## Chosen architecture

Use a Vite + React + TypeScript frontend and a small FastAPI adapter around the
existing Python services.

```text
React/Vite UI
  ├── image upload / supplied field example
  ├── classifier result, Top-5, timing, warnings
  ├── Grad-CAM heatmap and overlay
  └── optional Ask Qwen panel
             │ JSON + multipart HTTP
             ▼
FastAPI adapter
  ├── plantdisease.serving inference service
  ├── cached classifier/checkpoint lifecycle
  ├── cached MLXVLMBackend lifecycle
  └── agricultural safety and capability boundaries
```

This preserves the tested Python model path and avoids duplicating preprocessing,
class labels, checkpoint loading, or Grad-CAM logic in JavaScript.

## Frontend

Create a new `frontend/` Vite application using React and TypeScript. Install and
use `liquid-glass-react` in actual rendered components; it is not sufficient to add
the dependency without using it. The Apple Design skill is installed with the
user-specified `npx skills@latest add emilkowalski/skills` command before visual
implementation, and its relevant design rules are read and applied.

The interface has four visual regions:

1. A restrained hero with project identity, research status, and a concise domain
   warning.
2. A glass image workspace with drag-and-drop upload, the supplied field example,
   preview, reset, and explicit source badge.
3. A result workspace with Top-5, timing, model/checkpoint identity, warnings, and
   side-by-side Grad-CAM views.
4. An optional Ask Qwen drawer or panel bound to the currently selected image.

Glass is used for hierarchy and focus, not as a full-page blur effect. Text contrast,
keyboard focus, reduced motion, loading states, and mobile behavior are required.
The design uses Apple-like spacing, typography, material depth, and transitions
without claiming Apple affiliation or copying proprietary product assets.

## Classifier API

Add a FastAPI application under `app/api.py` or an equivalently focused module.
The API wraps `plantdisease.serving.service` and exposes:

- `GET /api/health`: process and feature availability;
- `POST /api/classify`: image, Top-K, device, target layer, and Grad-CAM toggle;
- static access to the supplied default example and generated visualization data.

The response contains structured predictions, timings, warnings, knowledge-card
content, checkpoint identity, image size, target layer, and optional encoded or
URL-addressable Grad-CAM images. Input limits and existing validation errors are
translated into stable HTTP error responses.

The API does not silently fall back to fabricated model results when a checkpoint is
missing. The UI displays a clear unavailable state and the documented local setup.

## Ask Qwen

The Ask Qwen panel performs real local inference through
`mlx-community/Qwen3-VL-4B-Instruct-4bit` and `MLXVLMBackend`; it is not a scripted
chat mock. It is optional because the runtime is Apple Silicon-specific and the
weights are approximately 3 GB.

Expose:

- `GET /api/qwen/status`: supported platform, dependency state, local-cache state,
  model ID, and readiness;
- `POST /api/qwen/ask`: current image plus one bounded question;
- a token limit, deterministic generation, serialized model access, and cached model
  lifecycle so the model is not loaded for every request.

The service must not automatically download model weights. If the model is absent,
the panel explains how to run `uv sync --group vlm` and explicitly enable the first
download. A local launch command may opt into download, but the browser request cannot.

The panel labels the feature as an exploratory smoke capability. It includes the
measured boundary that choice/few-shot choice reached 11/15 while fine-grained
condition recognition reached 1/5 on the fixed five-image smoke set. It refuses or
redirects pesticide, dosage, regulatory, definitive-diagnosis, and other high-risk
questions using the existing assistant safety policy. Generated answers are not
stored as ground truth.

## Supplied image and media

Copy the supplied field image into a repository-safe example
location with a neutral name such as `app/examples/field_corn_leaf.jpeg`. Preserve
the original bytes unless an additional derived thumbnail is needed. Document it as
user supplied, with no verified class label and no claim of PlantVillage membership.

Use this image for the React default example, end-to-end demo verification, and new
README/demo screenshots. Existing synthetic evidence remains available only where it
is required to reproduce historical Week 1/5 results; historical reports are not
rewritten as if the field image had been used in those runs.

## Existing Streamlit compatibility

Keep `app/streamlit_app.py` functional and tested. Its default example may be changed
to the supplied image only if historical tests and captions are updated without
rewriting prior experiment facts. README should identify the React app as the primary
experience and Streamlit as a compatibility/research entry point.

## Local launch and packaging

Provide one documented local development command for the Python API and one for the
React frontend, plus a production build command. Prefer a small orchestration script
only if it improves repeatability without hiding the individual commands.

The existing Apple `container` evidence remains historical unless the container is
explicitly updated and revalidated for the React build. Do not claim that the new
React/Qwen interface is container-verified when Qwen depends on host MLX/Metal.

## Error and state design

- Invalid, corrupt, empty, oversized, or unsupported images produce actionable UI
  errors and no model call.
- Missing checkpoint and unavailable Qwen are feature-unavailable states, not fake
  successes.
- Classification and Qwen loading have independent progress and cancellation-safe UI
  state.
- A Qwen failure does not erase a successful classifier result.
- Low-confidence and out-of-domain warnings remain visible beside the answer and
  cannot be dismissed as decorative copy.
- Network/API failures have retry actions and preserve the selected image.

## Verification

Backend tests cover health, upload validation, successful classifier serialization,
missing checkpoint, Grad-CAM payloads, Qwen status, cached backend reuse, safe refusal,
and Qwen-unavailable behavior without downloading weights.

Frontend tests cover the supplied example, upload replacement, classify flow, Top-5,
Grad-CAM, warnings, Qwen ready/unavailable/error states, accessible controls, and
responsive layout. The production React build must pass.

Browser QA covers desktop and mobile widths, loading/error states, keyboard focus,
reduced motion, real `liquid-glass-react` rendering, the supplied image, and a local
classifier run. A real Qwen browser interaction is verified when cached weights are
available; otherwise only the explicitly unavailable path may be claimed.

The final repository gate reruns Python tests, Ruff, ty, claim/link audit, frontend
tests/build, and the affected Week 8 release checks. New screenshots, manifests, and
documentation are regenerated from the final implementation.

## GitHub publication

Preserve unrelated untracked Week 7 presentation intermediates and generated LaTeX
auxiliary files. Stage only the final Week 8 and React/Qwen deliverables. Commit with a
clear scope, push `codex/week8-release-audit`, and open a draft pull request.

The local checkout currently has no configured Git remote. Before publishing, resolve
the target repository, add the remote only with the user's authority, verify `gh` in
the same execution environment, and never expose authentication material. No tag or
GitHub Release is created unless separately requested.

## Explicit non-goals

- No cloud-hosted Qwen or paid inference API.
- No automatic multi-gigabyte model download from a browser request.
- No LoRA/QLoRA or new performance claim.
- No claim that the supplied field image has a verified diagnosis.
- No removal of Streamlit or historical synthetic evidence.
- No public deployment, Git tag, or GitHub Release in this scope.
