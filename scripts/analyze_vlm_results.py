"""Analyze Week 6 VLM result JSON files and VQA seed quality."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from plantdisease.vlm.analysis import (
    analyze_result,
    audit_samples,
    load_result,
    write_analysis_json,
    write_report,
)
from plantdisease.vlm.schema import read_jsonl


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path("outputs/plantvillage/week6_vlm/vqa_seed.jsonl"),
        help="VQA JSONL dataset used by the result files.",
    )
    parser.add_argument(
        "--result",
        type=Path,
        action="append",
        required=True,
        help="Machine-readable VLM result JSON. Pass multiple times to compare runs.",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("outputs/plantvillage/week6_vlm/vlm_result_analysis.json"),
        help="Output analysis JSON path.",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("reports/week6_vlm_result_analysis.md"),
        help="Output Markdown report path.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    samples = read_jsonl(args.dataset)
    result_analyses = []
    for result_path in args.result:
        analysis = analyze_result(load_result(result_path))
        analysis["result_path"] = str(result_path)
        result_analyses.append(analysis)

    payload = {
        "dataset": str(args.dataset),
        "dataset_audit": audit_samples(samples),
        "result_analyses": result_analyses,
    }
    write_analysis_json(args.output_json, payload)
    write_report(args.report, payload)
    print(
        json.dumps(
            {
                "status": "completed",
                "output_json": str(args.output_json),
                "report": str(args.report),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
