# Week 6 Choice-Constrained VLM Prompt Comparison

## Why this was added

The short-prompt Qwen3-VL smoke run answered `plant` and `health_status`
questions correctly, but still missed every `condition` question. The next
controlled experiment is to separate two causes:

1. the model cannot visually identify the disease condition; or
2. the open-ended prompt lets the model drift into unsupported disease names.

This scaffold adds closed-choice prompts before any LoRA claim. It is still a
baseline/evaluation tool, not fine-tuning.

## Implemented prompt styles

- `choice`: asks the model to choose exactly one answer from the known closed
  label options for the current question type.
- `few_shot_choice`: adds deterministic train-split text examples from other
  images, then asks the model to choose from the same closed options.

The few-shot examples use only `train` split samples with a different
`image_id`; validation/test samples are not used as examples.

## Evaluation behavior

Option-style answers are normalized before exact-match scoring. The evaluator
can map answers like `B. Tomato`, `option B`, or `Tomato` back to the canonical
choice text before comparing with the expected label.

Code and tests:

- Prompt/evaluation implementation: `src/plantdisease/vlm/baseline.py`
- CLI: `scripts/run_vlm_baseline.py`
- Tests: `tests/vlm/test_baseline.py`

## Local scaffold evidence

These two commands were run in skip mode to verify CLI wiring without loading
Qwen weights:

```bash
uv run python scripts/run_vlm_baseline.py \
  --output outputs/plantvillage/week6_vlm/qwen3_vl_choice_smoke_skipped.json \
  --prompt-style choice \
  --skip-reason "choice prompt scaffold added; real Qwen run not executed in this commit"

uv run python scripts/run_vlm_baseline.py \
  --output outputs/plantvillage/week6_vlm/qwen3_vl_few_shot_choice_smoke_skipped.json \
  --prompt-style few_shot_choice \
  --skip-reason "few-shot choice prompt scaffold added; real Qwen run not executed in this commit"
```

Initial scaffold status:

- `choice`: CLI scaffold verified in skip mode.
- `few_shot_choice`: CLI scaffold verified in skip mode.

## Real Qwen prompt comparison

The real Qwen3-VL runs completed on 2026-07-13 with
`mlx-community/Qwen3-VL-4B-Instruct-4bit`, 5 test images, 15 questions, and
zero generation failures.

| prompt_style | total correct | plant | health_status | condition | risk flags |
| --- | ---: | ---: | ---: | ---: | ---: |
| `original` | 0/15 | 0/5 | 0/5 | 0/5 | 7 |
| `short` | 10/15 | 5/5 | 5/5 | 0/5 | 2 |
| `choice` | 11/15 | 5/5 | 5/5 | 1/5 | 0 |
| `few_shot_choice` | 11/15 | 5/5 | 5/5 | 1/5 | 0 |

Machine-readable local outputs:

- `outputs/plantvillage/week6_vlm/qwen3_vl_choice_smoke.json`
- `outputs/plantvillage/week6_vlm/qwen3_vl_few_shot_choice_smoke.json`
- `outputs/plantvillage/week6_vlm/vlm_result_analysis_prompt_compare.json`

Rendered comparison report:

- `reports/week6_vlm_prompt_compare.md`

## Interpretation

The choice-constrained prompts improved total exact match from `10/15` to
`11/15`, removed automatic risk-word flags, and prevented unsupported free-form
disease explanations. However, condition recognition remained weak at only
`1/5`, even with closed choices and train-only few-shot text examples. This
suggests the failure is not only prompt drift; the VLM also struggles with the
fine-grained disease-condition visual task on this small smoke set.

This is not evidence of LoRA training, field diagnosis reliability, or a
deployable agronomic assistant.

## Reproduction commands

If the model is already downloaded, omit `--allow-model-download`.

```bash
uv run --group vlm python scripts/run_vlm_baseline.py \
  --input outputs/plantvillage/week6_vlm/vqa_seed.jsonl \
  --output outputs/plantvillage/week6_vlm/qwen3_vl_choice_smoke.json \
  --split test \
  --cache-dir data/huggingface \
  --prompt-style choice \
  --allow-model-download \
  --max-tokens 16

uv run --group vlm python scripts/run_vlm_baseline.py \
  --input outputs/plantvillage/week6_vlm/vqa_seed.jsonl \
  --output outputs/plantvillage/week6_vlm/qwen3_vl_few_shot_choice_smoke.json \
  --split test \
  --cache-dir data/huggingface \
  --prompt-style few_shot_choice \
  --allow-model-download \
  --max-tokens 16
```

Then compare all prompt styles:

```bash
uv run python scripts/analyze_vlm_results.py \
  --dataset outputs/plantvillage/week6_vlm/vqa_seed.jsonl \
  --result outputs/plantvillage/week6_vlm/qwen3_vl_zero_shot_smoke.json \
  --result outputs/plantvillage/week6_vlm/qwen3_vl_zero_shot_smoke_short.json \
  --result outputs/plantvillage/week6_vlm/qwen3_vl_choice_smoke.json \
  --result outputs/plantvillage/week6_vlm/qwen3_vl_few_shot_choice_smoke.json \
  --output-json outputs/plantvillage/week6_vlm/vlm_result_analysis_prompt_compare.json \
  --report reports/week6_vlm_prompt_compare.md
```

Only report these metrics as a 5-image / 15-question Week 6 smoke comparison.
