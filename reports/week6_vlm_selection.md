# Week 6 VLM Selection Record

Selection date: 2026-07-13

## Scope

Week 6 is an exploratory VLM extension. The completed Week 1–5 classifier remains the
verified core result. This record selects a local-first VLM path for small PlantVillage
VQA smoke experiments and explicitly does not claim LoRA training or field diagnosis.

## Local Hardware and Environment

Measured locally:

```text
OS: macOS Darwin 25.5.0 arm64
CPU/SoC: Apple M5
CPU cores: 10
Unified memory: 25,769,803,776 bytes (~24 GiB)
Python: 3.12.13
PyTorch: 2.13.0
torch.backends.mps.is_built(): True
torch.backends.mps.is_available(): True
```

Implication: 4B VLM inference is practical with an Apple-native 4-bit MLX conversion.
Full LoRA training remains unverified on this machine. CUDA/bitsandbytes-style low-bit
training is not assumed to work on Apple MPS.

## Candidate Matrix

| Candidate | Params / size note | License note | Local feasibility | Decision |
| --- | ---: | --- | --- | --- |
| `Qwen/Qwen3-VL-4B-Instruct` | 4B class; BF16 repository about 8.9 GB | Apache 2.0 | Fits 24 GiB but MLX 4-bit is more efficient | Selected source model |
| `mlx-community/Qwen3-VL-4B-Instruct-4bit` | 3.09 GB MLX artifact; converted with MLX-VLM 0.3.4 | Apache 2.0 inherited from source | Best Apple Silicon runtime path | Selected runtime |
| `google/gemma-3-4b-it` | 4B; image/text; 128K context | Gemma terms | Feasible with MLX quantization | Same-size comparison |
| `HuggingFaceTB/SmolVLM-256M-Instruct` | 256M; model card says one-image inference uses under 1 GiB GPU RAM | Apache 2.0 | Very easy to run but materially weaker | Resource-floor baseline |
| Qwen3-VL 8B / Gemma 4 12B | Larger quality candidates | Apache 2.0 / Gemma terms | Quantized inference may fit, training cost is higher | Deferred |

## Decision

Use `Qwen/Qwen3-VL-4B-Instruct` as the primary Week 6 model and
`mlx-community/Qwen3-VL-4B-Instruct-4bit` as the Apple Silicon runtime. This was confirmed
by the user on 2026-07-13 after comparing Qwen and Gemma. Keep Gemma 3 4B as the fairest
same-size comparison and SmolVLM-256M only as a resource-floor baseline.

## Research Question

The first VQA task is closed and source-grounded:

1. identify the labeled plant;
2. identify the labeled PlantVillage condition/class;
3. answer whether the labeled condition is healthy or diseased.

Open agricultural advice is out of scope unless grounded in curated project knowledge
cards or cited sources. The assistant must not provide pesticide names, dosage, local
regulatory instructions, or definitive field diagnoses.

## Current Implementation Status

Completed in this slice:

- `src/plantdisease/vlm/schema.py`: versioned VQA schema and entity leakage check.
- `src/plantdisease/vlm/dataset.py`: deterministic source-grounded seed builder.
- `scripts/build_vqa_dataset.py`: seed generation CLI.
- `outputs/plantvillage/week6_vlm/vqa_seed.jsonl`: generated locally, Git-ignored output.
- `outputs/plantvillage/week6_vlm/vqa_seed_summary.json`: generated locally, Git-ignored output.

Not completed yet:

- real Qwen3-VL download or inference;
- zero-shot/few-shot baseline metrics;
- LoRA training;
- assistant prototype.

## Sources Checked

- Qwen3-VL-4B source model card: https://huggingface.co/Qwen/Qwen3-VL-4B-Instruct
- Qwen3-VL-4B MLX 4-bit model card:
  https://huggingface.co/mlx-community/Qwen3-VL-4B-Instruct-4bit
- MLX-VLM project: https://github.com/Blaizzy/mlx-vlm
- Gemma 3 model card: https://ai.google.dev/gemma/docs/core/model_card_3
- Gemma 4 sizing guide: https://ai.google.dev/gemma/docs/core
- SmolVLM-256M model card: https://huggingface.co/HuggingFaceTB/SmolVLM-256M-Instruct
