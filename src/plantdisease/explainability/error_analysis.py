"""Week 4 error-analysis summaries from metrics and prediction records."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import cast


@dataclass(frozen=True)
class ErrorAnalysisResult:
    """Summary of generated error-analysis artifacts."""

    error_analysis_path: Path
    report_path: Path | None
    class_count: int
    sample_count: int
    error_count: int
    high_confidence_error_count: int


def _load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(payload: Mapping[str, object], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _class_names(metrics: Mapping[str, object]) -> list[str]:
    per_class = metrics.get("per_class")
    if not isinstance(per_class, Mapping) or not per_class:
        raise ValueError("metrics must contain a non-empty per_class mapping")
    return [str(name) for name in per_class]


def _confusion_matrix(metrics: Mapping[str, object], class_count: int) -> list[list[int]]:
    matrix = metrics.get("confusion_matrix")
    if not isinstance(matrix, list) or len(matrix) != class_count:
        raise ValueError("metrics confusion_matrix shape does not match per_class")
    parsed: list[list[int]] = []
    for row in matrix:
        if not isinstance(row, list) or len(row) != class_count:
            raise ValueError("metrics confusion_matrix shape does not match per_class")
        parsed_row = [int(cast(int | float | str, value)) for value in row]
        if any(value < 0 for value in parsed_row):
            raise ValueError("metrics confusion_matrix must not contain negative values")
        parsed.append(parsed_row)
    return parsed


def _normalized_confusion_matrix(matrix: Sequence[Sequence[int]]) -> list[list[float]]:
    normalized: list[list[float]] = []
    for row in matrix:
        total = sum(row)
        if total == 0:
            normalized.append([0.0 for _ in row])
        else:
            normalized.append([float(value / total) for value in row])
    return normalized


def _low_f1_classes(
    metrics: Mapping[str, object], class_names: Sequence[str], count: int
) -> list[dict[str, object]]:
    per_class = cast(Mapping[str, object], metrics["per_class"])
    assert isinstance(per_class, Mapping)
    rows: list[dict[str, object]] = []
    for index, class_name in enumerate(class_names):
        values = per_class[class_name]
        if not isinstance(values, Mapping):
            raise ValueError("metrics per_class entries must be mappings")
        class_metrics = cast(Mapping[str, object], values)
        rows.append(
            {
                "class_index": index,
                "class_name": class_name,
                "precision": float(
                    cast(int | float | str, class_metrics["precision"])
                ),
                "recall": float(cast(int | float | str, class_metrics["recall"])),
                "f1": float(cast(int | float | str, class_metrics["f1"])),
                "support": int(cast(int | float | str, class_metrics["support"])),
            }
        )
    rows.sort(
        key=lambda row: (
            float(cast(int | float | str, row["f1"])),
            str(row["class_name"]),
        )
    )
    return rows[:count]


def _confusion_pairs(
    matrix: Sequence[Sequence[int]], class_names: Sequence[str], count: int
) -> list[dict[str, object]]:
    pairs: list[dict[str, object]] = []
    for true_index, row in enumerate(matrix):
        row_total = sum(row)
        for predicted_index, value in enumerate(row):
            if true_index == predicted_index or value == 0:
                continue
            pairs.append(
                {
                    "true_class_index": true_index,
                    "true_class_name": class_names[true_index],
                    "predicted_class_index": predicted_index,
                    "predicted_class_name": class_names[predicted_index],
                    "count": int(value),
                    "true_class_error_rate": float(value / row_total) if row_total else 0.0,
                }
            )
    pairs.sort(
        key=lambda row: (
            -int(cast(int | float | str, row["count"])),
            -float(cast(int | float | str, row["true_class_error_rate"])),
            str(row["true_class_name"]),
            str(row["predicted_class_name"]),
        )
    )
    return pairs[:count]


def _prediction_records(path: Path) -> list[dict[str, object]]:
    payload = _load_json(path)
    if not isinstance(payload, list):
        raise ValueError("predictions must be a JSON list")
    return [dict(cast(Mapping[str, object], record)) for record in payload]


def _validate_prediction_classes(
    records: Sequence[Mapping[str, object]], class_names: Sequence[str]
) -> None:
    for record in records:
        true_index = int(cast(int | float | str, record["true_class_index"]))
        predicted_index = int(cast(int | float | str, record["predicted_class_index"]))
        if (
            true_index < 0
            or true_index >= len(class_names)
            or predicted_index < 0
            or predicted_index >= len(class_names)
        ):
            raise ValueError("prediction class indices are outside metrics class range")
        if (
            str(record["true_class_name"]) != class_names[true_index]
            or str(record["predicted_class_name"]) != class_names[predicted_index]
        ):
            raise ValueError("prediction class names do not match metrics")


def _high_confidence_errors(
    records: Sequence[Mapping[str, object]], threshold: float, count: int
) -> list[dict[str, object]]:
    errors: list[dict[str, object]] = [
        {
            "test_index": int(cast(int | float | str, record["test_index"])),
            "sample_id": str(record["sample_id"]),
            "true_class_index": int(
                cast(int | float | str, record["true_class_index"])
            ),
            "true_class_name": str(record["true_class_name"]),
            "predicted_class_index": int(
                cast(int | float | str, record["predicted_class_index"])
            ),
            "predicted_class_name": str(record["predicted_class_name"]),
            "confidence": float(cast(int | float | str, record["confidence"])),
        }
        for record in records
        if not bool(record["correct"])
        and float(cast(int | float | str, record["confidence"])) >= threshold
    ]
    errors.sort(
        key=lambda row: (
            -float(cast(int | float | str, row["confidence"])),
            int(cast(int | float | str, row["test_index"])),
        )
    )
    return errors[:count]


def _write_report(payload: Mapping[str, object], report_path: Path) -> None:
    summary = payload["summary"]
    low_f1_classes = payload["low_f1_classes"]
    confusion_pairs = payload["confusion_pairs"]
    high_confidence_errors = payload["high_confidence_errors"]
    assert isinstance(summary, Mapping)
    assert isinstance(low_f1_classes, list)
    assert isinstance(confusion_pairs, list)
    assert isinstance(high_confidence_errors, list)
    summary = cast(Mapping[str, object], summary)
    lines = [
        "# Week 4 Error Analysis",
        "",
        "生成时间：2026-07-13",
        "",
        "## 摘要",
        "",
        f"- 样本数：`{summary['sample_count']}`",
        f"- 类别数：`{summary['class_count']}`",
        f"- Accuracy：`{float(cast(int | float | str, summary['accuracy'])):.4f}`",
        f"- Macro F1：`{float(cast(int | float | str, summary['macro_f1'])):.4f}`",
        f"- 错误样本数：`{summary['error_count']}`",
        (
            "- 高置信错误阈值：`"
            f"{float(cast(int | float | str, summary['high_confidence_threshold'])):.2f}`"
        ),
        f"- 高置信错误数：`{summary['high_confidence_error_count']}`",
        "",
        "## 低 F1 类别",
        "",
        "| class | precision | recall | f1 | support |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for raw_row in low_f1_classes:
        row = cast(Mapping[str, object], raw_row)
        lines.append(
            f"| `{row['class_name']}` | "
            f"{float(cast(int | float | str, row['precision'])):.4f} | "
            f"{float(cast(int | float | str, row['recall'])):.4f} | "
            f"{float(cast(int | float | str, row['f1'])):.4f} | "
            f"{int(cast(int | float | str, row['support']))} |"
        )
    lines.extend(
        [
            "",
            "## 重点混淆对",
            "",
            "| true → predicted | count | true-class share |",
            "| --- | ---: | ---: |",
        ]
    )
    for raw_row in confusion_pairs:
        row = cast(Mapping[str, object], raw_row)
        lines.append(
            f"| `{row['true_class_name']} → {row['predicted_class_name']}` | "
            f"{int(cast(int | float | str, row['count']))} | "
            f"{float(cast(int | float | str, row['true_class_error_rate'])):.4f} |"
        )
    lines.extend(
        [
            "",
            "## 高置信错误样本",
            "",
            "| test_index | true | predicted | confidence |",
            "| ---: | --- | --- | ---: |",
        ]
    )
    for raw_row in high_confidence_errors:
        row = cast(Mapping[str, object], raw_row)
        lines.append(
            f"| `{row['test_index']}` | "
            f"`{row['true_class_name']}` | "
            f"`{row['predicted_class_name']}` | "
            f"{float(cast(int | float | str, row['confidence'])):.4f} |"
        )
    lines.extend(
        [
            "",
            "## 解释边界",
            "",
            (
                "本报告从固定测试集指标和逐样本预测中总结错误模式。"
                "混淆对和高置信错误是后续人工审阅与 Grad-CAM 对照的入口，"
                "不能单独证明因果机制或真实田间泛化能力。"
            ),
        ]
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def analyze_error_patterns(
    *,
    metrics_path: Path,
    predictions_path: Path,
    output_path: Path,
    report_path: Path | None = None,
    low_f1_count: int = 8,
    confusion_pair_count: int = 10,
    high_confidence_threshold: float = 0.8,
    high_confidence_error_count: int = 20,
) -> ErrorAnalysisResult:
    """Write Week 4 error-analysis JSON and an optional Markdown report."""
    if low_f1_count <= 0:
        raise ValueError("low_f1_count must be positive")
    if confusion_pair_count <= 0:
        raise ValueError("confusion_pair_count must be positive")
    if not 0.0 <= high_confidence_threshold <= 1.0:
        raise ValueError("high_confidence_threshold must be in [0, 1]")
    if high_confidence_error_count <= 0:
        raise ValueError("high_confidence_error_count must be positive")

    metrics_payload = _load_json(metrics_path)
    if not isinstance(metrics_payload, Mapping):
        raise ValueError("metrics must be a JSON object")
    metrics_payload = cast(Mapping[str, object], metrics_payload)
    class_names = _class_names(metrics_payload)
    matrix = _confusion_matrix(metrics_payload, len(class_names))
    records = _prediction_records(predictions_path)
    _validate_prediction_classes(records, class_names)
    error_count = sum(1 for record in records if not bool(record["correct"]))
    high_confidence_errors = _high_confidence_errors(
        records, high_confidence_threshold, high_confidence_error_count
    )
    payload: dict[str, object] = {
        "schema_version": 1,
        "inputs": {
            "metrics_path": str(metrics_path),
            "predictions_path": str(predictions_path),
        },
        "summary": {
            "sample_count": int(
                cast(int | float | str, metrics_payload["sample_count"])
            ),
            "prediction_count": len(records),
            "class_count": len(class_names),
            "accuracy": float(cast(int | float | str, metrics_payload["accuracy"])),
            "macro_precision": float(
                cast(int | float | str, metrics_payload["macro_precision"])
            ),
            "macro_recall": float(
                cast(int | float | str, metrics_payload["macro_recall"])
            ),
            "macro_f1": float(cast(int | float | str, metrics_payload["macro_f1"])),
            "error_count": error_count,
            "high_confidence_threshold": high_confidence_threshold,
            "high_confidence_error_count": len(high_confidence_errors),
        },
        "class_names": list(class_names),
        "confusion_matrix": matrix,
        "normalized_confusion_matrix": _normalized_confusion_matrix(matrix),
        "low_f1_classes": _low_f1_classes(metrics_payload, class_names, low_f1_count),
        "confusion_pairs": _confusion_pairs(matrix, class_names, confusion_pair_count),
        "high_confidence_errors": high_confidence_errors,
    }
    _write_json(payload, output_path)
    if report_path is not None:
        _write_report(payload, report_path)
    return ErrorAnalysisResult(
        error_analysis_path=output_path,
        report_path=report_path,
        class_count=len(class_names),
        sample_count=int(cast(int | float | str, metrics_payload["sample_count"])),
        error_count=error_count,
        high_confidence_error_count=len(high_confidence_errors),
    )
