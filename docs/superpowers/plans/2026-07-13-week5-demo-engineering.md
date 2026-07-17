# Week 5 Demo Engineering Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a tested, UI-independent inference service, Streamlit demo, Apple `container` CPU runtime, fixed example flow, and honest Week 5 documentation.

**Architecture:** Add `src/plantdisease/serving/` for inference, safety, knowledge, and cache boundaries. Keep `app/streamlit_app.py` as a thin UI that calls the serving layer. Reuse the existing checkpoint, transform, Top-5, Grad-CAM, and visualization modules.

**Tech Stack:** Python 3.12, PyTorch, torchvision transforms, Pillow, Streamlit, pytest, Apple `container` CPU runtime.

## Global Constraints

- Do not delete files permanently; use `/usr/bin/trash <absolute-path>` for removals.
- Do not commit raw data, generated outputs, checkpoints, secrets, `.venv`, or caches.
- Use TDD: write a failing test, run it, then implement the minimum code.
- Keep labels, preprocessing, and checkpoint config shared with offline evaluation.
- Do not claim Apple `container`, screenshot, performance, or resource evidence unless commands actually ran.
- Safety copy must state the demo is educational and not a professional diagnosis.

---

### Task 1: Serving Core

**Files:**
- Create: `src/plantdisease/serving/__init__.py`
- Create: `src/plantdisease/serving/service.py`
- Test: `tests/serving/test_service.py`

**Interfaces:**
- Produces: `InferenceService.predict(image_bytes: bytes, top_k: int = 5, include_gradcam: bool = True) -> InferenceResult`
- Produces: typed exceptions `InputValidationError` and `InferenceServiceError`

- [ ] Write failing tests for valid prediction metadata, invalid image bytes, oversized files, low-confidence warnings, and Grad-CAM overlay output.
- [ ] Run `uv run pytest tests/serving/test_service.py -q` and confirm the tests fail because `plantdisease.serving` does not exist.
- [ ] Implement dataclasses, validation, canonical preprocessing, Top-5 prediction, optional Grad-CAM, timings, and exception mapping.
- [ ] Run `uv run pytest tests/serving/test_service.py -q` and confirm the service tests pass.

### Task 2: Knowledge And Cache

**Files:**
- Create: `src/plantdisease/serving/knowledge.py`
- Create: `src/plantdisease/serving/cache.py`
- Test: `tests/serving/test_knowledge.py`
- Test: `tests/serving/test_cache.py`

**Interfaces:**
- Produces: `lookup_disease_knowledge(class_name: str) -> DiseaseKnowledge`
- Produces: `get_cached_service(checkpoint_path: Path, device_name: str = "cpu", target_layer: str | None = None) -> InferenceService`

- [ ] Write failing tests for common label parsing, default fallback, cache identity, and cache key separation.
- [ ] Run the new serving tests and confirm expected failures.
- [ ] Implement a small educational knowledge map and `functools.lru_cache` backed service factory.
- [ ] Run `uv run pytest tests/serving -q` and confirm the serving package passes.

### Task 3: Streamlit Demo

**Files:**
- Create: `app/streamlit_app.py`
- Create: `tests/test_streamlit_app.py`
- Modify: `pyproject.toml`
- Modify: `uv.lock` if dependency resolution changes it

**Interfaces:**
- Produces: `streamlit run app/streamlit_app.py -- --checkpoint <checkpoint> --device cpu`

- [ ] Write a failing import/startup smoke test that loads the app module without requiring a checkpoint.
- [ ] Add Streamlit dependency and implement the upload/example/result UI.
- [ ] Run `uv run pytest tests/test_streamlit_app.py tests/serving -q`.

### Task 4: Fixed Example And Local E2E

**Files:**
- Create: `app/examples/synthetic_leaf.png`
- Create: `scripts/demo_e2e.py`
- Create: `tests/test_demo_e2e.py`

**Interfaces:**
- Produces: `uv run python scripts/demo_e2e.py --checkpoint <checkpoint> --image app/examples/synthetic_leaf.png --output outputs/plantvillage/week5_demo/local_e2e.json`

- [ ] Write a failing script test using a tiny injected checkpoint or a skipped real-checkpoint path.
- [ ] Implement the script so it writes JSON metadata and optional Grad-CAM overlay.
- [ ] Run the script against the formal local checkpoint if present and store evidence under ignored `outputs/`.

### Task 5: Apple Container And Docs

**Files:**
- Create: `Containerfile`
- Create: `.dockerignore`
- Modify: `README.md`
- Modify: `docs/artifact-index.md`
- Modify: `TASKS.md`

**Interfaces:**
- Produces: CPU Apple `container` image command and Streamlit healthcheck.

- [ ] Write tests or static checks for `.dockerignore` exclusions.
- [ ] Implement Containerfile with CPU default, Streamlit healthcheck, and no bundled checkpoint.
- [ ] Update README, artifact index, and TASKS with only validated evidence.
- [ ] Run affected tests, `uv run pytest -q`, and `uv run ruff check .`.
- [ ] If Apple `container` is available and initialized, build and smoke-run the container; otherwise document container runtime as not locally verified.
