"""Run or explicitly skip the fixed Week 6 Qwen3-VL zero-shot smoke baseline."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from plantdisease.vlm.backends import QWEN3_VL_MODEL_ID, MLXVLMBackend, VLMSetupError
from plantdisease.vlm.baseline import PROMPT_STYLES, run_baseline, write_skipped_baseline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("outputs/plantvillage/week6_vlm/vqa_seed.jsonl"),
        help="Schema-valid VQA JSONL input.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("outputs/plantvillage/week6_vlm/qwen3_vl_zero_shot_smoke.json"),
        help="Machine-readable smoke result JSON.",
    )
    parser.add_argument("--split", choices=("train", "validation", "test"), default="test")
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=Path("data/huggingface"),
        help="Hugging Face dataset and model cache.",
    )
    parser.add_argument("--model-id", default=QWEN3_VL_MODEL_ID)
    parser.add_argument("--max-tokens", type=int, default=32)
    parser.add_argument(
        "--prompt-style",
        choices=tuple(sorted(PROMPT_STYLES)),
        default="original",
        help="Prompt format used for VQA questions.",
    )
    parser.add_argument(
        "--allow-model-download",
        action="store_true",
        help="Allow MLX-VLM to download model weights; use only after explicit approval.",
    )
    parser.add_argument(
        "--skip-reason",
        help="Record an explicit skipped smoke run without loading data or model weights.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    command = [sys.executable, *sys.argv]
    if args.skip_reason is not None:
        result = write_skipped_baseline(
            args.output,
            args.skip_reason,
            split=args.split,
            backend_name="MLXVLMBackend",
            model_id=args.model_id,
            command=command,
            prompt_style=args.prompt_style,
        )
    else:
        backend = MLXVLMBackend(
            args.model_id,
            allow_model_download=args.allow_model_download,
            max_tokens=args.max_tokens,
        )
        try:
            result = run_baseline(
                args.input,
                args.output,
                backend,
                split=args.split,
                cache_dir=args.cache_dir,
                command=command,
                prompt_style=args.prompt_style,
            )
        except VLMSetupError as exc:
            result = write_skipped_baseline(
                args.output,
                str(exc),
                split=args.split,
                backend_name=type(backend).__name__,
                model_id=backend.model_id,
                command=command,
                prompt_style=args.prompt_style,
            )
    print(json.dumps({"status": result["status"], "output": str(args.output)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
