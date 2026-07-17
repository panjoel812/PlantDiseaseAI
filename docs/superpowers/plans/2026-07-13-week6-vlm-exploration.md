# Week 6 VLM Exploration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Week 6 VLM foundation: audited model selection, VQA schema/data seed, evaluation scaffolding, and honest docs that do not overclaim LoRA or field diagnosis.

**Architecture:** Add a small `plantdisease.vlm` package with schema, deterministic dataset building, backend isolation, and later evaluation/assistant modules. Unit tests remain download-free. Real execution uses the 3.09 GB MLX 4-bit conversion of Qwen3-VL-4B-Instruct on Apple Silicon.

**Tech Stack:** Python 3.12, dataclasses, JSONL, pytest, MLX-VLM on Apple Silicon, existing PlantDiseaseAI serving knowledge cards, and official/model-card sources for selection evidence.

## Global Constraints

- Do not commit raw PlantVillage images, model checkpoints, Hugging Face caches, or generated large outputs.
- No model-generated answer may become VQA ground truth unless separately audited.
- Split VQA records by `image_id`; every question for one image must stay in one split.
- QLoRA/low-bit training must not be claimed unless it actually runs on the recorded platform.
- Agricultural advice must remain educational, non-prescriptive, and refer high-risk decisions to qualified local experts.
- Apple `container` remains CPU-only for the Week 5 demo; native macOS MLX/Metal is the
  selected Qwen inference path.

---

## File Structure

- Create `src/plantdisease/vlm/__init__.py`: public VLM package exports.
- Create `src/plantdisease/vlm/schema.py`: VQA dataclass, validation, JSONL helpers, split leakage check.
- Create `src/plantdisease/vlm/dataset.py`: deterministic VQA record builders from frozen sample evidence.
- Create `scripts/build_vqa_dataset.py`: CLI for seed JSONL + datacard summary.
- Create `tests/vlm/test_schema.py`: schema and JSONL tests.
- Create `tests/vlm/test_dataset.py`: builder and leakage tests.
- Create `src/plantdisease/vlm/backends.py`: mock and guarded MLX-VLM backends.
- Create `src/plantdisease/vlm/baseline.py`: fixed-set runner and score summary.
- Create `scripts/run_vlm_baseline.py`: explicit real-model baseline CLI.
- Create `tests/vlm/test_backends.py`: backend contract tests.
- Create `tests/vlm/test_baseline.py`: offline baseline/scoring tests.
- Create `reports/week6_vlm_selection.md`: source-backed model selection matrix.
- Create `reports/week6_vqa_datacard.md`: generated seed dataset description.
- Modify `TASKS.md`, `README.md`, `docs/artifact-index.md`: only mark evidence-backed Week 6 items complete.

## Task 1: VQA Schema

**Files:**

- Create: `src/plantdisease/vlm/__init__.py`
- Create: `src/plantdisease/vlm/schema.py`
- Test: `tests/vlm/test_schema.py`

**Interfaces:**

- Produces: `VQASample`, `VQA_SPLITS`, `VQA_AUDIT_STATUSES`, `VQA_SOURCES`,
  `write_jsonl(path, samples)`, `read_jsonl(path)`, `assert_entity_split_integrity(samples)`.

- [ ] **Step 1: Write failing schema tests**

```python
from pathlib import Path

import pytest

from plantdisease.vlm.schema import (
    VQASample,
    assert_entity_split_integrity,
    read_jsonl,
    write_jsonl,
)


def test_vqa_sample_requires_valid_split() -> None:
    with pytest.raises(ValueError, match="split"):
        VQASample(
            sample_id="q1",
            image_id="img-1",
            image_ref="hf-test-1",
            question="Which plant is shown?",
            answer="Apple",
            question_type="plant",
            source="plantvillage_label",
            split="holdout",
            audit_status="pending",
        )


def test_jsonl_roundtrip(tmp_path: Path) -> None:
    sample = VQASample(
        sample_id="q1",
        image_id="img-1",
        image_ref="hf-test-1",
        question="Which plant is shown?",
        answer="Apple",
        question_type="plant",
        source="plantvillage_label",
        split="train",
        audit_status="passed",
        metadata={"class_name": "Apple___healthy"},
    )
    path = tmp_path / "vqa.jsonl"
    write_jsonl(path, [sample])
    assert read_jsonl(path) == [sample]


def test_entity_split_integrity_rejects_leakage() -> None:
    samples = [
        VQASample("q1", "img-1", "hf-test-1", "Q?", "A", "plant", "plantvillage_label", "train", "passed"),
        VQASample("q2", "img-1", "hf-test-1", "Q?", "A", "plant", "plantvillage_label", "test", "passed"),
    ]
    with pytest.raises(ValueError, match="image_id"):
        assert_entity_split_integrity(samples)
```

- [ ] **Step 2: Run tests and confirm failure**

Run: `uv run pytest tests/vlm/test_schema.py -q`

Expected: fails because `plantdisease.vlm.schema` does not exist.

- [ ] **Step 3: Implement schema**

Implement `VQASample` as a frozen dataclass, validate enum fields in `__post_init__`,
serialize with `asdict`, read/write UTF-8 JSONL, and raise `ValueError` if one
`image_id` appears in multiple splits.

- [ ] **Step 4: Verify schema**

Run: `uv run pytest tests/vlm/test_schema.py -q`

Expected: `3 passed`.

- [ ] **Step 5: Commit**

```bash
git add src/plantdisease/vlm tests/vlm/test_schema.py
git commit -m "feat: add week6 vqa schema"
```

## Task 2: Deterministic VQA Seed Builder

**Files:**

- Create: `src/plantdisease/vlm/dataset.py`
- Create: `scripts/build_vqa_dataset.py`
- Test: `tests/vlm/test_dataset.py`

**Interfaces:**

- Consumes: `VQASample`, `assert_entity_split_integrity`.
- Produces:
  - `parse_plantvillage_label(class_name: str) -> tuple[str, str, bool]`
  - `build_samples_from_frozen_groups(frozen: Mapping[str, object]) -> list[VQASample]`
  - `summarize_samples(samples: Sequence[VQASample]) -> dict[str, object]`

- [ ] **Step 1: Write failing builder tests**

Test that `Tomato___Leaf_Mold` parses to plant `Tomato`, condition `Leaf Mold`, diseased;
`Apple___healthy` parses to healthy; and two frozen records produce plant, condition, and
health-status questions with no entity leakage.

- [ ] **Step 2: Run tests and confirm failure**

Run: `uv run pytest tests/vlm/test_dataset.py -q`

Expected: fails because `plantdisease.vlm.dataset` does not exist.

- [ ] **Step 3: Implement builder**

Use only `true_class_name` from frozen samples for answers. Generate sample IDs as
`vqa-<split>-<image_id>-<question_type>`. Assign VQA split deterministically by sorted
unique `sample_id`: first 70% train, next 15% validation, final 15% test, with all
questions for an image sharing the same split.

- [ ] **Step 4: Implement CLI**

CLI arguments:

```text
--frozen-samples outputs/plantvillage/week4_explainability/frozen_samples.json
--output outputs/plantvillage/week6_vlm/vqa_seed.jsonl
--summary outputs/plantvillage/week6_vlm/vqa_seed_summary.json
```

- [ ] **Step 5: Verify builder**

Run:

```bash
uv run pytest tests/vlm/test_dataset.py -q
uv run python scripts/build_vqa_dataset.py \
  --frozen-samples outputs/plantvillage/week4_explainability/frozen_samples.json \
  --output outputs/plantvillage/week6_vlm/vqa_seed.jsonl \
  --summary outputs/plantvillage/week6_vlm/vqa_seed_summary.json
```

Expected: tests pass and summary reports no entity leakage.

- [ ] **Step 6: Commit**

```bash
git add src/plantdisease/vlm/dataset.py scripts/build_vqa_dataset.py tests/vlm/test_dataset.py
git commit -m "feat: build week6 vqa seed dataset"
```

## Task 3: Week 6 Selection and Data Reports

**Files:**

- Create: `reports/week6_vlm_selection.md`
- Create: `reports/week6_vqa_datacard.md`
- Modify: `TASKS.md`
- Modify: `README.md`
- Modify: `docs/artifact-index.md`

**Interfaces:**

- Consumes: `outputs/plantvillage/week6_vlm/vqa_seed_summary.json`
- Produces: auditable Week 6 documentation with current model-card URLs and local hardware.

- [ ] **Step 1: Write report**

Record local hardware, MPS/MLX availability, candidate model matrix, license notes, and
the selected source/runtime pair: `Qwen/Qwen3-VL-4B-Instruct` and
`mlx-community/Qwen3-VL-4B-Instruct-4bit`. Keep Gemma 3 4B and SmolVLM-256M as
comparison/resource-floor candidates.

- [ ] **Step 2: Write VQA datacard**

Document schema version, source files, split policy, counts by split/question type/source,
audit status, limitations, and the fact that the seed is small and label-grounded.

- [ ] **Step 3: Update task state**

Only mark completed:

- model selection record and hardware feasibility conclusion;
- VQA schema;
- seed data construction and entity split leakage check.

Leave zero-shot/few-shot, LoRA, and assistant prototype unchecked until implemented.

- [ ] **Step 4: Verify docs and tests**

Run:

```bash
uv run pytest tests/vlm -q
uv run pytest -q
uv run ruff check .
```

Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add reports/week6_vlm_selection.md reports/week6_vqa_datacard.md TASKS.md README.md docs/artifact-index.md
git commit -m "docs: record week6 vlm selection and vqa seed"
```

## Task 4: Real VLM Smoke Baseline

**Files:**

- Create: `src/plantdisease/vlm/backends.py`
- Create: `src/plantdisease/vlm/baseline.py`
- Create: `scripts/run_vlm_baseline.py`
- Create: `tests/vlm/test_backends.py`
- Create: `tests/vlm/test_baseline.py`
- Modify: `pyproject.toml`
- Modify: `uv.lock`

**Interfaces:**

- Produces a real or explicitly skipped zero-shot/few-shot smoke run.
- Must not run automatically in normal tests because model download is large.

- [ ] **Step 1: Add optional dependency group**

Add a `vlm` dependency group with `mlx-vlm>=0.5,<0.6` on Apple Silicon macOS. Do not
add `flash-attn` or CUDA-only low-bit dependencies.

- [ ] **Step 2: Add backend protocol and mock tests**

Define `VLMBackend.generate(image: object, question: str) -> str`, plus a mock backend for
deterministic tests. The real runner resolves PlantVillage `hf-test-*` references to
in-memory PIL images.

- [ ] **Step 3: Implement real MLX backend guarded by imports**

Lazily import MLX-VLM, load `mlx-community/Qwen3-VL-4B-Instruct-4bit`, apply the model's
chat template, and generate deterministic short answers. If dependencies or model weights
are missing, fail with a clear setup message. Do not download models in unit tests.

- [ ] **Step 4: Implement fixed-set runner and CLI**

Read schema-valid JSONL, select one split, resolve each unique image once, run all selected
questions, compute normalized exact match, and save run metadata plus per-question records.

- [ ] **Step 5: Run real zero-shot smoke after user accepts download**

Run `mlx-community/Qwen3-VL-4B-Instruct-4bit` on the fixed VQA test subset. Record exact
command, backend, platform, runtime, raw outputs, metrics, and failures. Describe this as
a zero-shot smoke baseline until dataset language audit and broader evaluation are done.

## Task 5: Assistant Prototype and Safety Refusal

**Files:**

- Create: `src/plantdisease/vlm/assistant.py`
- Create: `tests/vlm/test_assistant.py`
- Create: `reports/week6_vlm_experiment.md`

**Interfaces:**

- Consumes classifier context from Week 5 service output.
- Produces safe, bounded assistant prompts and refusal messages.

- [ ] **Step 1: Test unsafe requests**

Assert that pesticide dosage, local legal instructions, unknown disease claims, and
low-confidence context produce refusal/redirect language.

- [ ] **Step 2: Implement assistant wrapper**

Format classifier context, VQA answer, source, confidence, and educational disclaimer.

- [ ] **Step 3: Verify and document**

Run targeted assistant tests, then full tests. Update Week 6 report without claiming
agronomic reliability.
