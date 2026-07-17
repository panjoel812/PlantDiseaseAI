"""Build a manual-review template for Week 6 VQA seed samples."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from plantdisease.vlm.audit import build_audit_payload, write_audit_json, write_audit_report
from plantdisease.vlm.schema import read_jsonl


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path("outputs/plantvillage/week6_vlm/vqa_seed.jsonl"),
        help="Input VQA JSONL dataset.",
    )
    parser.add_argument(
        "--analysis",
        type=Path,
        default=Path("outputs/plantvillage/week6_vlm/vlm_result_analysis.json"),
        help="Optional VLM result analysis JSON used for review hints.",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("outputs/plantvillage/week6_vlm/vqa_manual_audit_template.json"),
        help="Output JSON audit template.",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("reports/week6_vqa_manual_audit_template.md"),
        help="Output Markdown audit template.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    samples = read_jsonl(args.dataset)
    analysis = (
        json.loads(args.analysis.read_text(encoding="utf-8")) if args.analysis.exists() else {}
    )
    payload = build_audit_payload(
        samples,
        analysis,
        dataset_path=args.dataset,
        analysis_path=args.analysis if args.analysis.exists() else None,
    )
    write_audit_json(args.output_json, payload)
    write_audit_report(args.report, payload)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "entry_count": payload["entry_count"],
                "output_json": str(args.output_json),
                "report": str(args.report),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
