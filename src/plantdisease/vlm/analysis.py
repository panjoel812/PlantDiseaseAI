"""Analysis helpers for Week 6 VLM smoke results and VQA seed quality."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from plantdisease.vlm.schema import VQASample

RISK_MARKERS = (
    "virus",
    "fungus",
    "fungal",
    "bacterial",
    "pseudomonas",
    "tolcv",
    "colletotrichum",
    "spray",
    "dosage",
)


def analyze_result(result: Mapping[str, Any]) -> dict[str, Any]:
    """Summarize one machine-readable VLM result JSON."""

    records = _records(result)
    by_type: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    confusions: Counter[tuple[str, str, str]] = Counter()
    risk_flags: list[dict[str, Any]] = []
    error_records: list[dict[str, Any]] = []

    for record in records:
        question_type = str(record["question_type"])
        by_type[question_type].append(record)
        is_match = bool(record.get("normalized_exact_match"))
        if not is_match:
            expected = str(record.get("expected_answer", ""))
            prediction = str(record.get("normalized_answer") or "")
            confusions[(question_type, expected, prediction)] += 1
            error_records.append(_error_record(record))

        markers = _risk_markers(record)
        if markers:
            risk_flags.append(
                {
                    "markers": markers,
                    "raw_answer": record.get("raw_answer"),
                    "sample_id": record.get("sample_id"),
                }
            )

    question_type_metrics = {
        question_type: _metrics_for_records(type_records)
        for question_type, type_records in sorted(by_type.items())
    }
    return {
        "status": result.get("status"),
        "model_id": result.get("model_id"),
        "prompt_style": result.get("prompt_style", "original"),
        "question_count": len(records),
        "question_type_metrics": question_type_metrics,
        "confusions": [
            {
                "count": count,
                "expected_answer": expected,
                "normalized_prediction": prediction,
                "question_type": question_type,
            }
            for (question_type, expected, prediction), count in sorted(confusions.items())
        ],
        "risk_flags": risk_flags,
        "error_records": error_records,
    }


def audit_samples(samples: Sequence[VQASample]) -> dict[str, Any]:
    """Run automated VQA seed quality checks that complement human audit."""

    question_counts = Counter(sample.question for sample in samples)
    repeated_questions = [
        {"count": count, "question": question}
        for question, count in sorted(question_counts.items())
        if count > 1
    ]
    return {
        "sample_count": len(samples),
        "image_count": len({sample.image_id for sample in samples}),
        "question_type_counts": dict(
            sorted(Counter(sample.question_type for sample in samples).items())
        ),
        "source_counts": dict(sorted(Counter(sample.source for sample in samples).items())),
        "audit_status_counts": dict(
            sorted(Counter(sample.audit_status for sample in samples).items())
        ),
        "repeated_question_count": len(repeated_questions),
        "repeated_questions": repeated_questions,
        "empty_answer_count": sum(1 for sample in samples if not sample.answer.strip()),
        "automated_quality_status": "needs_human_audit",
    }


def write_analysis_report(payload: Mapping[str, Any]) -> str:
    """Render a compact Markdown report for VLM result analysis."""

    lines = [
        "# Week 6 VLM Result Analysis",
        "",
        "## Dataset Audit",
        "",
    ]
    dataset_audit = payload["dataset_audit"]
    lines.extend(
        [
            f"- Samples: {dataset_audit['sample_count']}",
            f"- Images: {dataset_audit['image_count']}",
            f"- Automated quality status: `{dataset_audit['automated_quality_status']}`",
            f"- Repeated question templates: {dataset_audit['repeated_question_count']}",
            f"- Empty answers: {dataset_audit['empty_answer_count']}",
            "",
            "## Result Analyses",
            "",
        ]
    )

    for analysis in payload["result_analyses"]:
        lines.extend(
            [
                f"### {analysis['result_path']}",
                "",
                f"- Status: `{analysis['status']}`",
                f"- Model: `{analysis['model_id']}`",
                f"- Prompt style: `{analysis['prompt_style']}`",
                f"- Questions: {analysis['question_count']}",
                "",
                "| question_type | correct | total | exact_match |",
                "| --- | ---: | ---: | ---: |",
            ]
        )
        for question_type, metrics in analysis["question_type_metrics"].items():
            lines.append(
                "| "
                f"{question_type} | "
                f"{metrics['correct_count']} | "
                f"{metrics['question_count']} | "
                f"{metrics['exact_match']:.4f} |"
            )
        lines.extend(["", "Top confusions:", ""])
        if analysis["confusions"]:
            for confusion in analysis["confusions"]:
                lines.append(
                    "- "
                    f"{confusion['question_type']}: expected "
                    f"`{confusion['expected_answer']}`, got "
                    f"`{confusion['normalized_prediction']}` "
                    f"({confusion['count']}x)"
                )
        else:
            lines.append("- None")
        lines.extend(["", "Potential hallucination / safety flags:", ""])
        if analysis["risk_flags"]:
            for flag in analysis["risk_flags"]:
                markers = ", ".join(flag["markers"])
                lines.append(
                    f"- {flag['sample_id']}: markers `{markers}` in answer "
                    f"`{flag['raw_answer']}`"
                )
        else:
            lines.append("- None")
        lines.append("")

    lines.extend(
        [
            "## Interpretation",
            "",
            "This analysis is for a small Week 6 smoke baseline. It separates exact-match "
            "errors, condition-label confusions, and risky explanatory terms from the "
            "verified classifier results. It is not evidence of LoRA training or field "
            "diagnosis reliability.",
            "",
        ]
    )
    return "\n".join(lines)


def load_result(path: str | Path) -> dict[str, Any]:
    """Load one result JSON file."""

    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_analysis_json(path: str | Path, payload: Mapping[str, Any]) -> None:
    """Write analysis payload as stable UTF-8 JSON."""

    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_report(path: str | Path, payload: Mapping[str, Any]) -> None:
    """Write analysis payload as Markdown."""

    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(write_analysis_report(payload), encoding="utf-8")


def _records(result: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    records = result.get("records", [])
    if not isinstance(records, list):
        raise ValueError("result JSON must contain a records list")
    return records


def _metrics_for_records(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    total = len(records)
    correct = sum(1 for record in records if bool(record.get("normalized_exact_match")))
    return {
        "correct_count": correct,
        "exact_match": correct / total if total else 0.0,
        "question_count": total,
    }


def _error_record(record: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "expected_answer": record.get("expected_answer"),
        "image_id": record.get("image_id"),
        "normalized_prediction": record.get("normalized_answer"),
        "question_type": record.get("question_type"),
        "raw_answer": record.get("raw_answer"),
        "sample_id": record.get("sample_id"),
    }


def _risk_markers(record: Mapping[str, Any]) -> list[str]:
    if bool(record.get("normalized_exact_match")):
        return []
    text = str(record.get("raw_answer") or "").casefold()
    expected = str(record.get("expected_answer") or "").casefold()
    return [marker for marker in RISK_MARKERS if marker in text and marker not in expected]
