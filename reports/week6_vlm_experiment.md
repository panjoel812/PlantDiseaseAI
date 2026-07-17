# Week 6 VLM Experiment Record

Date: 2026-07-13

## Scope

This is a Week 6 exploratory record. It does not replace the verified Week 1-5 image
classifier, and it is not evidence of LoRA fine-tuning or real field diagnosis.

## Selected model path

- Source model: `Qwen/Qwen3-VL-4B-Instruct`
- Local Apple Silicon runtime: `mlx-community/Qwen3-VL-4B-Instruct-4bit`
- Backend: `MLXVLMBackend`
- Baseline scope: zero-shot smoke on the fixed `test` split of the seed VQA JSONL
- Dataset: `outputs/plantvillage/week6_vlm/vqa_seed.jsonl`

Official source notes checked on 2026-07-13:

- The Qwen source model card lists license `apache-2.0`.
- The MLX 4-bit model card provides the command shape
  `python -m mlx_vlm.generate --model ... --image <path_to_image>` and reports a 3.09 GB
  MLX artifact.
- The MLX-VLM README shows the Python API used by the project backend:
  `load`, `generate`, and `apply_chat_template` with PIL images accepted as inputs.

## Implemented baseline scaffold

The repository now contains a guarded baseline runner:

- `src/plantdisease/vlm/backends.py`: backend protocol, deterministic mock backend, and
  lazy MLX-VLM adapter for Qwen3-VL.
- `src/plantdisease/vlm/baseline.py`: split selection, in-memory `hf-test-*` image
  resolution, normalized exact-match scoring, failure capture, and machine-readable output.
- `scripts/run_vlm_baseline.py`: explicit CLI for either real Qwen inference or a recorded
  skip result.
- `tests/vlm/test_backends.py` and `tests/vlm/test_baseline.py`: download-free tests for
  dependency isolation, backend behavior, image resolution, scoring, and skip-mode CLI.

## Verification completed

Commands run:

```bash
uv run pytest tests/vlm -q
uv run ruff check .
uv run pytest -q
uv run python scripts/run_vlm_baseline.py \
  --output outputs/plantvillage/week6_vlm/qwen3_vl_zero_shot_smoke_skipped.json \
  --skip-reason "Qwen3-VL model download not run in automated verification"
```

Results:

- `tests/vlm`: 21 passed.
- `ruff`: all checks passed.
- Full test suite: 156 passed, 7 existing Torch JIT deprecation warnings.
- Skip-mode output: `outputs/plantvillage/week6_vlm/qwen3_vl_zero_shot_smoke_skipped.json`
  with `status="skipped"`, backend `MLXVLMBackend`, and model
  `mlx-community/Qwen3-VL-4B-Instruct-4bit`.

## Real Qwen smoke result

The real Qwen3-VL zero-shot smoke run was executed on 2026-07-13 after installing the
`vlm` dependency group and allowing the MLX model download. The terminal reported a
2.98 GB download and 3.11 GB reconstruction.

```bash
uv sync --group vlm
uv run --group vlm python scripts/run_vlm_baseline.py \
  --input outputs/plantvillage/week6_vlm/vqa_seed.jsonl \
  --output outputs/plantvillage/week6_vlm/qwen3_vl_zero_shot_smoke.json \
  --split test \
  --cache-dir data/huggingface \
  --allow-model-download \
  --max-tokens 32
```

Machine-readable output:
`outputs/plantvillage/week6_vlm/qwen3_vl_zero_shot_smoke.json`

Measured result:

- Status: `completed`
- Run ID: `20260713-114833-vlm-zero-shot-smoke`
- Backend: `MLXVLMBackend`
- Model: `mlx-community/Qwen3-VL-4B-Instruct-4bit`
- Split: `test`
- Selected questions: 15
- Unique images: 5
- Failures: 0
- Duration recorded by the runner: 464.1 seconds
- Normalized exact match: 0/15 = 0.0

Interpretation:

The first real baseline was operational evidence, not a quality win. Qwen3-VL produced
long explanatory answers for closed label questions. For example, several tomato plant
questions included the word "Tomato" in the raw answer, but normalized exact match still
scored them false because the prediction was a full sentence rather than exactly
`Tomato`.

## Short-answer prompt result

A second zero-shot smoke run used the same fixed test split and the same downloaded
Qwen3-VL MLX model, but changed only the prompt style to `short`. The prompt asks for one
label and no explanation.

```bash
uv run --group vlm python scripts/run_vlm_baseline.py \
  --input outputs/plantvillage/week6_vlm/vqa_seed.jsonl \
  --output outputs/plantvillage/week6_vlm/qwen3_vl_zero_shot_smoke_short.json \
  --split test \
  --cache-dir data/huggingface \
  --prompt-style short \
  --allow-model-download \
  --max-tokens 8
```

Machine-readable output:
`outputs/plantvillage/week6_vlm/qwen3_vl_zero_shot_smoke_short.json`

Measured result:

- Status: `completed`
- Run ID: `20260713-120718-vlm-zero-shot-smoke`
- Backend: `MLXVLMBackend`
- Model: `mlx-community/Qwen3-VL-4B-Instruct-4bit`
- Split: `test`
- Prompt style: `short`
- Selected questions: 15
- Unique images: 5
- Failures: 0
- Duration recorded by the runner: 7.9 seconds
- Normalized exact match: 10/15 = 0.6667

The short prompt improved exact-match because plant questions and health-status questions
mostly became label-only outputs. The remaining errors are all condition-label mistakes:
the model predicted labels such as `Leaf spot disease`, `Tomato leaf curl virus`, or
`Tomato leaf spot disease` where the PlantVillage label was `Leaf Mold`.

## Result analysis

The follow-up analysis is recorded in `reports/week6_vlm_result_analysis.md` and
`outputs/plantvillage/week6_vlm/vlm_result_analysis.json`. It confirms that the short
prompt achieved 5/5 plant exact-match and 5/5 health-status exact-match, while condition
questions remained 0/5. It also flags risky explanatory terms such as `virus`,
`pseudomonas`, `fungal`, and `colletotrichum` in non-matching answers.

## Limitations

- No few-shot prompting result is recorded yet.
- No LoRA or QLoRA training has been run.
- The current metric is strict exact match; it undercounts answers that mention the target
  label inside a longer explanation, and it does not replace human scoring.
- The improved short-prompt result is still a 15-question smoke baseline, not a full
  PlantVillageVQA evaluation.
- Seed VQA answers are label-grounded and suitable for pipeline smoke tests; the dataset
  still needs human quality audit before broader claims.
- This is educational research tooling only, not professional crop diagnosis advice.
