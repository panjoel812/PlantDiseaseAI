"""Human-review templates for Week 4 Grad-CAM attention analysis."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import cast

ATTENTION_REGION_VALUES = [
    "leaf",
    "lesion",
    "background",
    "shadow",
    "border",
    "mixed",
    "unclear",
]

ERROR_TYPE_VALUES = [
    "visual_similarity",
    "background_bias",
    "low_quality",
    "occlusion",
    "label_question",
    "domain_shift",
    "not_error",
    "unclear",
]


@dataclass(frozen=True)
class AttentionReviewResult:
    """Summary of generated attention-review template artifacts."""

    review_path: Path
    report_path: Path | None
    sample_count: int
    needs_review_count: int
    high_confidence_error_count: int


def _load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(payload: Mapping[str, object], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _atlas_samples(
    atlas_manifest_path: Path,
) -> tuple[Mapping[str, object], list[dict[str, object]]]:
    payload = _load_json(atlas_manifest_path)
    if not isinstance(payload, Mapping):
        raise ValueError("atlas manifest must be a JSON object")
    samples = payload.get("samples")
    if not isinstance(samples, list) or not samples:
        raise ValueError("atlas manifest must contain samples")
    manifest = cast(Mapping[str, object], payload)
    return manifest, [dict(cast(Mapping[str, object], sample)) for sample in samples]


def _index_error_analysis(
    error_analysis_path: Path | None,
) -> tuple[set[int], set[tuple[int, int]], set[int]]:
    if error_analysis_path is None:
        return set(), set(), set()
    payload = _load_json(error_analysis_path)
    if not isinstance(payload, Mapping):
        raise ValueError("error analysis must be a JSON object")
    payload = cast(Mapping[str, object], payload)
    low_f1_classes = {
        int(cast(int | float | str, row["class_index"]))
        for raw_row in cast(Sequence[object], payload.get("low_f1_classes", []))
        if isinstance(raw_row, Mapping)
        for row in [cast(Mapping[str, object], raw_row)]
    }
    confusion_pairs = {
        (
            int(cast(int | float | str, row["true_class_index"])),
            int(cast(int | float | str, row["predicted_class_index"])),
        )
        for raw_row in cast(Sequence[object], payload.get("confusion_pairs", []))
        if isinstance(raw_row, Mapping)
        for row in [cast(Mapping[str, object], raw_row)]
    }
    high_confidence_errors = {
        int(cast(int | float | str, row["test_index"]))
        for raw_row in cast(Sequence[object], payload.get("high_confidence_errors", []))
        if isinstance(raw_row, Mapping)
        for row in [cast(Mapping[str, object], raw_row)]
    }
    return low_f1_classes, confusion_pairs, high_confidence_errors


def _evidence_flags(
    sample: Mapping[str, object],
    *,
    low_f1_classes: set[int],
    confusion_pairs: set[tuple[int, int]],
    high_confidence_errors: set[int],
) -> list[str]:
    flags: list[str] = []
    true_index = int(cast(int | float | str, sample["true_class_index"]))
    predicted_index = int(cast(int | float | str, sample["predicted_class_index"]))
    if int(cast(int | float | str, sample["test_index"])) in high_confidence_errors:
        flags.append("high_confidence_error")
    if (true_index, predicted_index) in confusion_pairs:
        flags.append("frequent_confusion_pair")
    if true_index in low_f1_classes or predicted_index in low_f1_classes:
        flags.append("low_f1_related")
    return flags


def _candidate_error_types(sample: Mapping[str, object], flags: Sequence[str]) -> list[str]:
    if bool(sample["correct"]):
        return ["not_error"]
    candidates: list[str] = []
    if "frequent_confusion_pair" in flags:
        candidates.append("visual_similarity")
    if "high_confidence_error" in flags:
        candidates.extend(["background_bias", "label_question"])
    if not candidates:
        candidates.extend(["visual_similarity", "low_quality"])
    candidates.append("unclear")
    return list(dict.fromkeys(candidates))


def _candidate_attention_regions(sample: Mapping[str, object]) -> list[str]:
    if bool(sample["correct"]):
        return ["leaf", "lesion", "mixed", "unclear"]
    return ["lesion", "background", "shadow", "border", "mixed", "unclear"]


def _review_sample(
    sample: Mapping[str, object],
    *,
    low_f1_classes: set[int],
    confusion_pairs: set[tuple[int, int]],
    high_confidence_errors: set[int],
) -> dict[str, object]:
    flags = _evidence_flags(
        sample,
        low_f1_classes=low_f1_classes,
        confusion_pairs=confusion_pairs,
        high_confidence_errors=high_confidence_errors,
    )
    correct = bool(sample["correct"])
    return {
        "test_index": int(cast(int | float | str, sample["test_index"])),
        "sample_id": str(sample["sample_id"]),
        "group": str(sample["group"]),
        "true_class_index": int(cast(int | float | str, sample["true_class_index"])),
        "true_class_name": str(sample["true_class_name"]),
        "predicted_class_index": int(
            cast(int | float | str, sample["predicted_class_index"])
        ),
        "predicted_class_name": str(sample["predicted_class_name"]),
        "target_class_index": int(
            cast(int | float | str, sample["target_class_index"])
        ),
        "target_class_name": str(sample["target_class_name"]),
        "confidence": float(cast(int | float | str, sample["confidence"])),
        "correct": correct,
        "panel_path": str(sample["panel_path"]),
        "evidence_flags": flags,
        "candidate_attention_regions": _candidate_attention_regions(sample),
        "candidate_error_types": _candidate_error_types(sample, flags),
        "attention_region": None,
        "error_type": "not_error" if correct else None,
        "review_note": "",
    }


def _write_report(payload: Mapping[str, object], report_path: Path) -> None:
    summary = payload["summary"]
    samples = payload["samples"]
    assert isinstance(summary, Mapping)
    assert isinstance(samples, list)
    summary = cast(Mapping[str, object], summary)
    lines = [
        "# Week 4 Attention Review Template",
        "",
        "生成时间：2026-07-13",
        "",
        "## 摘要",
        "",
        f"- 样本数：`{summary['sample_count']}`",
        f"- 需要人工审阅样本数：`{summary['needs_review_count']}`",
        f"- 高置信错误提示数：`{summary['high_confidence_error_count']}`",
        f"- 重点混淆提示样本数：`{summary['frequent_confusion_sample_count']}`",
        f"- 低 F1 相关提示样本数：`{summary['low_f1_related_sample_count']}`",
        "",
        "## 可选标签",
        "",
        f"- attention_region：`{', '.join(ATTENTION_REGION_VALUES)}`",
        f"- error_type：`{', '.join(ERROR_TYPE_VALUES)}`",
        "",
        "## 待人工审阅样本",
        "",
        "| group | test_index | true → pred | confidence | flags | panel |",
        "| --- | ---: | --- | ---: | --- | --- |",
    ]
    for raw_sample in samples:
        if not isinstance(raw_sample, Mapping):
            continue
        sample = cast(Mapping[str, object], raw_sample)
        if bool(sample["correct"]):
            continue
        flags = (
            ", ".join(
                str(flag)
                for flag in cast(Sequence[object], sample["evidence_flags"])
            )
            or "-"
        )
        lines.append(
            f"| `{sample['group']}` | "
            f"`{sample['test_index']}` | "
            f"`{sample['true_class_name']} → {sample['predicted_class_name']}` | "
            f"{float(cast(int | float | str, sample['confidence'])):.4f} | "
            f"`{flags}` | "
            f"`{sample['panel_path']}` |"
        )
    lines.extend(
        [
            "",
            "## 使用说明",
            "",
            (
                "`attention_region` 和错误样本的 `error_type` 需要人工查看 panel 后填写。"
                "本模板中的 flags 和 candidate 字段只表示审阅优先级提示，"
                "不能当作已经验证的错误原因。"
            ),
            "",
            "## 解释边界",
            "",
            (
                "Grad-CAM 只能说明目标类别分数与输入区域之间的相关性。"
                "人工审阅时应区分观察结果、合理假设和已验证解释，"
                "并记录 PlantVillage 受控背景限制。"
            ),
        ]
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def create_attention_review_template(
    *,
    atlas_manifest_path: Path,
    output_path: Path,
    error_analysis_path: Path | None = None,
    report_path: Path | None = None,
) -> AttentionReviewResult:
    """Create an editable human-review template from the fixed Grad-CAM atlas."""
    atlas_manifest, atlas_samples = _atlas_samples(atlas_manifest_path)
    low_f1_classes, confusion_pairs, high_confidence_errors = _index_error_analysis(
        error_analysis_path
    )
    samples = [
        _review_sample(
            sample,
            low_f1_classes=low_f1_classes,
            confusion_pairs=confusion_pairs,
            high_confidence_errors=high_confidence_errors,
        )
        for sample in atlas_samples
    ]
    needs_review_count = sum(1 for sample in samples if not bool(sample["correct"]))
    high_confidence_error_count = sum(
        1
        for sample in samples
        if "high_confidence_error"
        in cast(Sequence[object], sample["evidence_flags"])
    )
    frequent_confusion_sample_count = sum(
        1
        for sample in samples
        if "frequent_confusion_pair"
        in cast(Sequence[object], sample["evidence_flags"])
    )
    low_f1_related_sample_count = sum(
        1
        for sample in samples
        if "low_f1_related" in cast(Sequence[object], sample["evidence_flags"])
    )
    payload: dict[str, object] = {
        "schema_version": 1,
        "inputs": {
            "atlas_manifest_path": str(atlas_manifest_path),
            "error_analysis_path": str(error_analysis_path) if error_analysis_path else None,
        },
        "model": atlas_manifest.get("model", {}),
        "visualization": atlas_manifest.get("visualization", {}),
        "review_schema": {
            "attention_region_allowed_values": ATTENTION_REGION_VALUES,
            "error_type_allowed_values": ERROR_TYPE_VALUES,
            "review_note": "Free-form short human observation.",
        },
        "summary": {
            "sample_count": len(samples),
            "needs_review_count": needs_review_count,
            "high_confidence_error_count": high_confidence_error_count,
            "frequent_confusion_sample_count": frequent_confusion_sample_count,
            "low_f1_related_sample_count": low_f1_related_sample_count,
        },
        "samples": samples,
    }
    _write_json(payload, output_path)
    if report_path is not None:
        _write_report(payload, report_path)
    return AttentionReviewResult(
        review_path=output_path,
        report_path=report_path,
        sample_count=len(samples),
        needs_review_count=needs_review_count,
        high_confidence_error_count=high_confidence_error_count,
    )
