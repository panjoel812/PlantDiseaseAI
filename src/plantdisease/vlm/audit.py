"""Manual audit template helpers for Week 6 VQA samples."""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from plantdisease.vlm.schema import VQASample

_DEFAULT_CHECKS = {
    "answer_traceable_to_source": None,
    "answer_unambiguous": None,
    "language_quality_ok": None,
    "question_not_duplicate_problem": None,
}


def build_audit_entries(
    samples: Sequence[VQASample],
    analysis: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Create editable manual-review entries from VQA samples and VLM analysis."""

    analysis = analysis or {}
    risk_markers_by_sample = _risk_markers_by_sample(analysis)
    prediction_hints_by_sample = _prediction_hints_by_sample(analysis)
    entries: list[dict[str, Any]] = []
    for sample in samples:
        entries.append(
            {
                "sample_id": sample.sample_id,
                "image_id": sample.image_id,
                "image_ref": sample.image_ref,
                "split": sample.split,
                "question_type": sample.question_type,
                "question": sample.question,
                "expected_answer": sample.answer,
                "source": sample.source,
                "original_audit_status": sample.audit_status,
                "review_status": "pending_human_review",
                "checks": dict(_DEFAULT_CHECKS),
                "model_risk_markers": risk_markers_by_sample.get(sample.sample_id, []),
                "model_prediction_hint": prediction_hints_by_sample.get(sample.sample_id),
                "human_notes": "",
            }
        )
    return entries


def build_audit_payload(
    samples: Sequence[VQASample],
    analysis: Mapping[str, Any] | None,
    *,
    dataset_path: str | Path,
    analysis_path: str | Path | None = None,
) -> dict[str, Any]:
    """Build a deterministic payload for human VQA quality review."""

    entries = build_audit_entries(samples, analysis)
    return {
        "status": "pending_human_review",
        "dataset": str(dataset_path),
        "analysis": str(analysis_path) if analysis_path is not None else None,
        "entry_count": len(entries),
        "summary": {
            "image_count": len({sample.image_id for sample in samples}),
            "question_type_counts": dict(
                sorted(Counter(sample.question_type for sample in samples).items())
            ),
            "risk_flagged_entry_count": sum(
                1 for entry in entries if entry["model_risk_markers"]
            ),
        },
        "instructions": [
            "Review every entry before changing review_status to passed or failed.",
            "Only mark answer_traceable_to_source as true when the answer follows "
            "from the stored label or curated source.",
            "Do not use model predictions as ground truth.",
            "Record ambiguous wording, duplicate-question problems, or "
            "agricultural-safety concerns in human_notes.",
        ],
        "entries": entries,
    }


def write_audit_json(path: str | Path, payload: Mapping[str, Any]) -> None:
    """Write the manual audit payload as stable UTF-8 JSON."""

    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_audit_markdown(payload: Mapping[str, Any]) -> str:
    """Render a compact Markdown manual-audit template."""

    summary = payload.get("summary", {})
    lines = [
        "# Manual VQA Audit Template",
        "",
        f"- Status: `{payload['status']}`",
        f"- Dataset: `{payload['dataset']}`",
        f"- Analysis: `{payload.get('analysis')}`",
        f"- Entries: {payload['entry_count']}",
        f"- Unique images: {summary.get('image_count', 0)}",
        f"- Risk-flagged entries: {summary.get('risk_flagged_entry_count', 0)}",
        "",
        "## Instructions",
        "",
    ]
    for instruction in payload.get("instructions", []):
        lines.append(f"- {instruction}")
    lines.extend(
        [
            "",
            "## Review entries",
            "",
            "| sample_id | type | question | expected_answer | model_hint | "
            "risk_markers | review_status |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for entry in payload.get("entries", []):
        lines.append(
            "| "
            f"{entry['sample_id']} | "
            f"{entry['question_type']} | "
            f"{_escape_markdown_table(entry['question'])} | "
            f"{_escape_markdown_table(entry['expected_answer'])} | "
            f"{_escape_markdown_table(entry.get('model_prediction_hint') or '')} | "
            f"{', '.join(entry.get('model_risk_markers', []))} | "
            f"{entry['review_status']} |"
        )
    lines.extend(
        [
            "",
            "This file is a template for human review. It is not evidence that the VQA "
            "dataset has passed manual audit until each entry is filled and reviewed.",
            "",
        ]
    )
    return "\n".join(lines)


def write_audit_report(path: str | Path, payload: Mapping[str, Any]) -> None:
    """Write a Markdown manual-audit report."""

    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(write_audit_markdown(payload), encoding="utf-8")


def _risk_markers_by_sample(analysis: Mapping[str, Any]) -> dict[str, list[str]]:
    markers_by_sample: dict[str, list[str]] = {}
    for result_analysis in analysis.get("result_analyses", []):
        for flag in result_analysis.get("risk_flags", []):
            sample_id = str(flag.get("sample_id", ""))
            if not sample_id:
                continue
            current = markers_by_sample.setdefault(sample_id, [])
            for marker in flag.get("markers", []):
                marker_text = str(marker)
                if marker_text not in current:
                    current.append(marker_text)
    return markers_by_sample


def _prediction_hints_by_sample(analysis: Mapping[str, Any]) -> dict[str, str]:
    hints: dict[str, str] = {}
    for result_analysis in analysis.get("result_analyses", []):
        for record in result_analysis.get("error_records", []):
            sample_id = str(record.get("sample_id", ""))
            prediction = record.get("normalized_prediction")
            if sample_id and prediction is not None and sample_id not in hints:
                hints[sample_id] = str(prediction)
    return hints


def _escape_markdown_table(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")
