"""Build a small Week 6 VQA seed dataset from audited frozen samples."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from plantdisease.vlm.dataset import build_samples_from_frozen_groups, summarize_samples
from plantdisease.vlm.schema import write_jsonl


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--frozen-samples",
        type=Path,
        default=Path("outputs/plantvillage/week4_explainability/frozen_samples.json"),
        help="Week 4 frozen sample JSON path.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("outputs/plantvillage/week6_vlm/vqa_seed.jsonl"),
        help="Output VQA JSONL path.",
    )
    parser.add_argument(
        "--summary",
        type=Path,
        default=Path("outputs/plantvillage/week6_vlm/vqa_seed_summary.json"),
        help="Output summary JSON path.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    frozen = json.loads(args.frozen_samples.read_text(encoding="utf-8"))
    samples = build_samples_from_frozen_groups(frozen)
    summary = summarize_samples(samples)

    write_jsonl(args.output, samples)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": "completed", **summary}, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
