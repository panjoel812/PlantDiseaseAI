# Week 6 VLM Exploration Design

## Goal

Week 6 adds an exploratory visual-language layer without weakening the proven
PlantVillage classifier. The output must be auditable: model selection, VQA schema,
small VQA dataset construction, zero-shot/few-shot evaluation harness, and an assistant
prototype that refuses unsafe or unsupported advice.

This is not a promise of completed LoRA training. Full fine-tuning is only complete if
training and fixed-set evaluation actually run on the recorded hardware.

## Current Context

- Branch: `codex/week6-vlm-exploration`
- Host: Apple Silicon macOS, Apple M5, 24 GiB memory, PyTorch MPS available
- Project baseline: Week 1–5 classification, Grad-CAM, Streamlit, and Apple `container`
  are complete and verified.
- Existing classifier evidence remains the primary project result. Week 6 is an
  exploratory extension.

## Model Selection Strategy

Use a conservative three-tier selection:

1. **Primary model: Qwen3-VL 4B Instruct**
   - Source model: `Qwen/Qwen3-VL-4B-Instruct`, Apache 2.0, image/text input, and
     4B-class weights. The official repository is about 8.9 GB in BF16 shards.
   - Apple runtime: `mlx-community/Qwen3-VL-4B-Instruct-4bit`, an MLX conversion of the
     source model. Its model card reports a 3.09 GB artifact and identifies MLX-VLM 0.3.4
     as the conversion tool.
   - Rationale: stronger visual reasoning and Chinese interaction than the tiny smoke
     candidates while remaining practical on the 24 GiB Apple M5 after 4-bit conversion.
     Apache 2.0 is also suitable for a reproducible portfolio project.

2. **Comparison candidates**
   - `google/gemma-3-4b-it`: same-size image/text comparison with strong multilingual
     support, but it uses the custom Gemma terms rather than Apache 2.0.
   - `HuggingFaceTB/SmolVLM-256M-Instruct`: very small Apache 2.0 resource-floor model;
     retain it only as a lightweight baseline, not the main quality candidate.

3. **Deferred larger candidates**
   - `Qwen/Qwen3-VL-8B-Instruct` and Gemma 4 12B may improve quality, but they increase
     memory and fine-tuning cost. They are out of scope until the 4B fixed-set baseline
     is measured.

The implementation should start with schema, data, and evaluation code that can run
without downloading any VLM. Real execution uses MLX-VLM on Apple Silicon and must remain
an explicit command so ordinary unit tests never download model weights.

## VQA Research Scope

The first Week 6 VQA task is closed, source-grounded PlantVillage question answering:

- identify the labeled plant;
- identify the labeled condition/class;
- classify whether the labeled condition is healthy or diseased;
- answer short symptom/education questions only when the answer comes from the existing
  curated knowledge cards or a cited source.

The VLM is not allowed to invent diagnoses, pesticides, dosages, local regulations, or
field treatment plans. For low-confidence classifier context, non-leaf inputs, unknown
disease requests, or insufficient evidence, the assistant must refuse or redirect to a
qualified plant-health professional.

## VQA Schema

Versioned JSONL records should include at least:

- `schema_version`: integer, starting at `1`
- `sample_id`: stable VQA sample identifier
- `image_id`: stable image/entity identifier
- `image_ref`: dataset-local image reference, not a committed raw image
- `question`: user-facing question
- `answer`: expected answer
- `question_type`: controlled enum such as `plant`, `condition`, `health_status`,
  `symptom`, `safety`
- `source`: controlled enum such as `plantvillage_label`, `knowledge_card`,
  `classifier_context`
- `split`: `train`, `validation`, or `test`
- `audit_status`: `pending`, `passed`, `failed`, or `needs_review`
- `metadata`: optional object for class name, plant, condition, classifier confidence,
  source path, and notes

The split must be entity-based by `image_id`: every question about the same image must
stay in the same split.

## Components

1. `src/plantdisease/vlm/schema.py`
   - Dataclasses and validation for VQA samples.
   - JSONL read/write helpers.
   - Entity-leakage checks.

2. `src/plantdisease/vlm/dataset.py`
   - Deterministic builders that convert existing label/class evidence into VQA records.
   - No model-generated answer is accepted as ground truth.

3. `scripts/build_vqa_dataset.py`
   - CLI entry point to generate a small, versioned VQA seed dataset from frozen Week 4
     samples or later full split metadata.

4. `src/plantdisease/vlm/backends.py`
   - A small backend protocol, deterministic mock, and guarded MLX-VLM adapter.
   - The MLX adapter lazily loads `mlx-community/Qwen3-VL-4B-Instruct-4bit` and accepts
     in-memory PIL images so decoded dataset images do not need temporary files.

5. `src/plantdisease/vlm/baseline.py`
   - Fixed-split zero-shot execution and normalized exact-match scoring.
   - Machine-readable per-question results, timing, model ID, backend, and environment.

6. `src/plantdisease/vlm/evaluation.py`
   - Exact-match and normalized string metrics for closed questions.
   - Refusal/safety checks for assistant outputs.

7. `src/plantdisease/vlm/assistant.py`
   - A classifier-context assistant wrapper that formats prompts and safety disclaimers.
   - It may wrap a real VLM backend later, but must work with a mock backend in tests.

8. Reports and docs
   - `reports/week6_vlm_selection.md`
   - `reports/week6_vqa_datacard.md`
   - `reports/week6_vlm_experiment.md`
   - Updates to `TASKS.md`, `README.md`, and `docs/artifact-index.md` only when evidence
     exists.

## Validation

Minimum validation for the first implementation slice:

- schema rejects missing fields, invalid split, invalid audit status, and invalid source;
- JSONL round trip preserves records;
- entity split checker catches the same `image_id` in more than one split;
- builder creates expected plant/condition/health-status questions from fixed records;
- generated VQA seed data has no entity leakage;
- mock backend and baseline tests run without network or model downloads;
- a real Qwen3-VL 4-bit run records exact model ID, runtime, platform, prompt, raw answer,
  expected answer, and score;
- selection report cites official model-card/license sources and records local hardware;
- `uv run pytest -q` and `uv run ruff check .` pass before any completion claim.

## LoRA Boundary

LoRA/QLoRA is not part of the first slice. It can be attempted only after:

- the selected model loads successfully on this Mac or a recorded external environment;
- dependencies are pinned and tested;
- the fixed VQA train/validation/test split exists;
- a zero-shot baseline exists on the same fixed test set.

If any of those fail, Week 6 should record a pipeline smoke result and resource-limited
status, not a fine-tuning result.

## Sources Checked on 2026-07-13

- Qwen3-VL-4B-Instruct model card:
  https://huggingface.co/Qwen/Qwen3-VL-4B-Instruct
- MLX 4-bit Qwen3-VL-4B conversion:
  https://huggingface.co/mlx-community/Qwen3-VL-4B-Instruct-4bit
- MLX-VLM inference and fine-tuning project:
  https://github.com/Blaizzy/mlx-vlm
- Gemma 3 model card:
  https://ai.google.dev/gemma/docs/core/model_card_3
- Gemma 4 sizing and inference-memory guide:
  https://ai.google.dev/gemma/docs/core
- SmolVLM-256M model card:
  https://huggingface.co/HuggingFaceTB/SmolVLM-256M-Instruct
