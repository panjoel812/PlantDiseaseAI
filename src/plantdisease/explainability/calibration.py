"""Top-label calibration analysis for Week 4 prediction records."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import cast


@dataclass(frozen=True)
class CalibrationResult:
    """Summary of generated calibration artifacts."""

    calibration_path: Path
    report_path: Path | None
    figure_path: Path | None
    sample_count: int
    top_label_ece: float
    top_label_mce: float


def _load_prediction_records(path: Path) -> list[dict[str, object]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list) or not payload:
        raise ValueError("predictions must be a non-empty JSON list")
    return [dict(cast(Mapping[str, object], record)) for record in payload]


def _write_json(payload: Mapping[str, object], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _confidence(record: Mapping[str, object]) -> float:
    value = float(cast(int | float | str, record["confidence"]))
    if not 0.0 <= value <= 1.0:
        raise ValueError("confidence values must be in [0, 1]")
    return value


def _bin_index(confidence: float, num_bins: int) -> int:
    if confidence == 1.0:
        return num_bins - 1
    return int(confidence * num_bins)


def _calibration_bins(
    records: Sequence[Mapping[str, object]], num_bins: int
) -> tuple[list[dict[str, object]], dict[str, float]]:
    if num_bins <= 0:
        raise ValueError("num_bins must be positive")
    buckets: list[list[tuple[float, float]]] = [[] for _ in range(num_bins)]
    confidences: list[float] = []
    outcomes: list[float] = []
    for record in records:
        confidence = _confidence(record)
        outcome = 1.0 if bool(record["correct"]) else 0.0
        buckets[_bin_index(confidence, num_bins)].append((confidence, outcome))
        confidences.append(confidence)
        outcomes.append(outcome)

    sample_count = len(records)
    bins: list[dict[str, object]] = []
    ece = 0.0
    mce = 0.0
    for index, bucket in enumerate(buckets):
        lower = index / num_bins
        upper = (index + 1) / num_bins
        if not bucket:
            bins.append(
                {
                    "bin_index": index,
                    "lower": lower,
                    "upper": upper,
                    "count": 0,
                    "accuracy": None,
                    "avg_confidence": None,
                    "gap": None,
                }
            )
            continue
        count = len(bucket)
        avg_confidence = sum(confidence for confidence, _outcome in bucket) / count
        accuracy = sum(outcome for _confidence_value, outcome in bucket) / count
        gap = abs(accuracy - avg_confidence)
        ece += count / sample_count * gap
        mce = max(mce, gap)
        bins.append(
            {
                "bin_index": index,
                "lower": lower,
                "upper": upper,
                "count": count,
                "accuracy": accuracy,
                "avg_confidence": avg_confidence,
                "gap": gap,
            }
        )
    accuracy = sum(outcomes) / sample_count
    mean_confidence = sum(confidences) / sample_count
    top_label_brier = sum(
        (confidence - outcome) ** 2
        for confidence, outcome in zip(confidences, outcomes, strict=True)
    ) / sample_count
    return bins, {
        "accuracy": accuracy,
        "mean_confidence": mean_confidence,
        "top_label_ece": ece,
        "top_label_mce": mce,
        "top_label_brier": top_label_brier,
    }


def _write_reliability_diagram(
    bins: Sequence[Mapping[str, object]], figure_path: Path, num_bins: int
) -> None:
    import matplotlib.pyplot as plt

    centers = [
        float(cast(int | float | str, row["lower"])) + 0.5 / num_bins for row in bins
    ]
    accuracies = [
        float(cast(int | float | str, row["accuracy"]))
        if row["accuracy"] is not None
        else 0.0
        for row in bins
    ]
    avg_confidences = [
        float(cast(int | float | str, row["avg_confidence"]))
        if row["avg_confidence"] is not None
        else 0.0
        for row in bins
    ]
    width = 0.8 / num_bins
    figure_path.parent.mkdir(parents=True, exist_ok=True)
    fig, axis = plt.subplots(figsize=(6, 5))
    axis.bar(centers, accuracies, width=width, alpha=0.75, label="bin accuracy")
    axis.plot([0, 1], [0, 1], linestyle="--", color="black", linewidth=1, label="ideal")
    axis.scatter(centers, avg_confidences, color="tab:orange", label="avg confidence", zorder=3)
    axis.set_xlim(0, 1)
    axis.set_ylim(0, 1)
    axis.set_xlabel("Confidence")
    axis.set_ylabel("Accuracy")
    axis.set_title("Week 4 reliability diagram")
    axis.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(figure_path, dpi=160)
    plt.close(fig)


def _write_report(payload: Mapping[str, object], report_path: Path) -> None:
    summary = payload["summary"]
    bins = payload["bins"]
    assert isinstance(summary, Mapping)
    assert isinstance(bins, list)
    summary = cast(Mapping[str, object], summary)
    lines = [
        "# Week 4 Calibration Analysis",
        "",
        "生成时间：2026-07-13",
        "",
        "## 摘要",
        "",
        f"- 样本数：`{summary['sample_count']}`",
        f"- Accuracy：`{float(cast(int | float | str, summary['accuracy'])):.4f}`",
        f"- 平均置信度：`{float(cast(int | float | str, summary['mean_confidence'])):.4f}`",
        f"- Top-label ECE：`{float(cast(int | float | str, summary['top_label_ece'])):.4f}`",
        f"- Top-label MCE：`{float(cast(int | float | str, summary['top_label_mce'])):.4f}`",
        f"- Top-label Brier：`{float(cast(int | float | str, summary['top_label_brier'])):.4f}`",
        f"- reliability diagram：`{summary['figure_path']}`",
        "",
        "## Reliability bins",
        "",
        "| bin | range | count | accuracy | avg confidence | gap |",
        "| ---: | --- | ---: | ---: | ---: | ---: |",
    ]
    for raw_row in bins:
        row = cast(Mapping[str, object], raw_row)
        accuracy = (
            "-"
            if row["accuracy"] is None
            else f"{float(cast(int | float | str, row['accuracy'])):.4f}"
        )
        confidence = (
            "-"
            if row["avg_confidence"] is None
            else f"{float(cast(int | float | str, row['avg_confidence'])):.4f}"
        )
        gap = (
            "-"
            if row["gap"] is None
            else f"{float(cast(int | float | str, row['gap'])):.4f}"
        )
        lines.append(
            f"| {int(cast(int | float | str, row['bin_index']))} | "
            f"[{float(cast(int | float | str, row['lower'])):.2f}, "
            f"{float(cast(int | float | str, row['upper'])):.2f}] | "
            f"{int(cast(int | float | str, row['count']))} | "
            f"{accuracy} | {confidence} | {gap} |"
        )
    lines.extend(
        [
            "",
            "## 解释边界",
            "",
            (
                "本报告使用 top-label confidence 评估校准，只衡量模型预测类别置信度"
                "与正确率之间的关系；它不是完整多类别概率校准评估。"
                "PlantVillage 背景受控，校准结果不能直接外推到真实田间场景。"
            ),
        ]
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def analyze_calibration(
    *,
    predictions_path: Path,
    output_path: Path,
    report_path: Path | None = None,
    figure_path: Path | None = None,
    num_bins: int = 10,
) -> CalibrationResult:
    """Generate top-label calibration metrics and an optional reliability diagram."""
    records = _load_prediction_records(predictions_path)
    bins, summary_values = _calibration_bins(records, num_bins)
    payload: dict[str, object] = {
        "schema_version": 1,
        "inputs": {"predictions_path": str(predictions_path)},
        "summary": {
            "sample_count": len(records),
            "num_bins": num_bins,
            "accuracy": summary_values["accuracy"],
            "mean_confidence": summary_values["mean_confidence"],
            "top_label_ece": summary_values["top_label_ece"],
            "top_label_mce": summary_values["top_label_mce"],
            "top_label_brier": summary_values["top_label_brier"],
            "figure_path": str(figure_path) if figure_path else None,
        },
        "bins": bins,
    }
    _write_json(payload, output_path)
    if figure_path is not None:
        _write_reliability_diagram(bins, figure_path, num_bins)
    if report_path is not None:
        _write_report(payload, report_path)
    return CalibrationResult(
        calibration_path=output_path,
        report_path=report_path,
        figure_path=figure_path,
        sample_count=len(records),
        top_label_ece=summary_values["top_label_ece"],
        top_label_mce=summary_values["top_label_mce"],
    )
