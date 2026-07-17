"""Command-line entry points."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path
from typing import cast

import torch
from PIL import Image

from plantdisease.data.audit import audit_records, save_audit_report
from plantdisease.data.huggingface import load_plantvillage
from plantdisease.data.transforms import build_eval_transform
from plantdisease.evaluation.benchmark import run_checkpoint_benchmark
from plantdisease.explainability.atlas import generate_gradcam_atlas
from plantdisease.explainability.attention_review import create_attention_review_template
from plantdisease.explainability.calibration import analyze_calibration
from plantdisease.explainability.error_analysis import analyze_error_patterns
from plantdisease.explainability.workflow import freeze_explainability_samples
from plantdisease.inference import predict_topk
from plantdisease.models.checkpoint import load_checkpoint
from plantdisease.smoke import run_smoke
from plantdisease.training.baseline import run_baseline_training


def smoke_main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run the offline Week 1 smoke pipeline")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--image-size", type=int, default=32)
    args = parser.parse_args(argv)
    result = run_smoke(args.output_dir, seed=args.seed, image_size=args.image_size)
    print(json.dumps({"status": result.status, "run_id": result.run_id}))


def audit_main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Audit the Hugging Face PlantVillage dataset")
    parser.add_argument("--cache-dir", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-samples", type=int)
    args = parser.parse_args(argv)
    records, class_names = load_plantvillage(args.cache_dir, max_samples=args.max_samples)
    report = audit_records(records, class_names)
    save_audit_report(report, args.output)
    print(json.dumps({"sample_count": report.sample_count, "output": str(args.output)}))


def predict_main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Predict one image with a project checkpoint")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args(argv)
    device = torch.device("cpu")
    model, class_names, config = load_checkpoint(args.checkpoint, device)
    image = Image.open(args.image).convert("RGB")
    tensor = build_eval_transform(int(cast(int | float | str, config["image_size"])))(image)
    predictions = predict_topk(model, tensor, class_names, args.top_k)
    print(json.dumps([asdict(item) for item in predictions], ensure_ascii=False, indent=2))


def train_main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Train a PlantVillage classification baseline")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--cache-dir", type=Path, default=Path("data/huggingface"))
    parser.add_argument("--output-dir", type=Path, required=True)
    sample_group = parser.add_mutually_exclusive_group()
    sample_group.add_argument("--max-samples", type=int)
    sample_group.add_argument("--samples-per-class", type=int)
    parser.add_argument("--log-every", type=int, default=20)
    args = parser.parse_args(argv)
    result = run_baseline_training(
        config_path=args.config,
        cache_dir=args.cache_dir,
        output_dir=args.output_dir,
        max_samples_per_split=args.max_samples,
        samples_per_class=args.samples_per_class,
        log_every=args.log_every,
    )
    print(json.dumps({"status": result.status, "run_id": result.run_id}))


def evaluate_main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Inspect metrics produced by a verified run")
    parser.add_argument("--metrics", type=Path, required=True)
    args = parser.parse_args(argv)
    payload = json.loads(args.metrics.read_text(encoding="utf-8"))
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def benchmark_main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Benchmark a project checkpoint for efficiency")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda", "mps"], default="auto")
    parser.add_argument("--warmup", type=int, default=10)
    parser.add_argument("--iterations", type=int, default=50)
    parser.add_argument("--throughput-batch-size", type=int, default=32)
    args = parser.parse_args(argv)
    report = run_checkpoint_benchmark(
        checkpoint_path=args.checkpoint,
        output_path=args.output,
        device_name=args.device,
        warmup_iterations=args.warmup,
        measured_iterations=args.iterations,
        throughput_batch_size=args.throughput_batch_size,
    )
    print(
        json.dumps(
            {
                "status": "completed",
                "model_name": cast(dict[str, object], report["checkpoint"])["model_name"],
                "output": str(args.output),
            },
            ensure_ascii=False,
        )
    )


def freeze_samples_main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Freeze Week 4 explainability sample indices from a checkpoint"
    )
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--split-manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--cache-dir", type=Path, default=Path("data/huggingface"))
    parser.add_argument("--samples-per-group", type=int, default=6)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--num-workers", type=int, default=0)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda", "mps"], default="auto")
    parser.add_argument("--target-layer")
    parser.add_argument("--progress-every", type=int, default=10)
    args = parser.parse_args(argv)
    result = freeze_explainability_samples(
        checkpoint_path=args.checkpoint,
        split_manifest_path=args.split_manifest,
        output_dir=args.output_dir,
        cache_dir=args.cache_dir,
        samples_per_group=args.samples_per_group,
        top_k=args.top_k,
        batch_size=args.batch_size,
        num_workers=args.num_workers,
        device_name=args.device,
        target_layer=args.target_layer,
        logger=lambda message: print(message, file=sys.stderr, flush=True),
        progress_log_every=args.progress_every,
    )
    print(
        json.dumps(
            {
                "status": "completed",
                "prediction_count": result.prediction_count,
                "target_layer": result.target_layer,
                "predictions": str(result.prediction_path),
                "frozen_samples": str(result.frozen_samples_path),
            },
            ensure_ascii=False,
        )
    )


def gradcam_atlas_main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Generate Grad-CAM panels for frozen Week 4 explainability samples"
    )
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--frozen-samples", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--cache-dir", type=Path, default=Path("data/huggingface"))
    parser.add_argument("--split-manifest", type=Path)
    parser.add_argument("--report", type=Path, default=Path("reports/week4_gradcam_atlas.md"))
    parser.add_argument("--device", choices=["auto", "cpu", "cuda", "mps"], default="auto")
    parser.add_argument("--target-layer")
    parser.add_argument("--target-mode", choices=["predicted", "true"], default="predicted")
    parser.add_argument("--alpha", type=float, default=0.45)
    parser.add_argument("--colormap", default="turbo")
    args = parser.parse_args(argv)
    result = generate_gradcam_atlas(
        checkpoint_path=args.checkpoint,
        frozen_samples_path=args.frozen_samples,
        output_dir=args.output_dir,
        cache_dir=args.cache_dir,
        split_manifest_path=args.split_manifest,
        report_path=args.report,
        device_name=args.device,
        target_layer=args.target_layer,
        target_mode=args.target_mode,
        alpha=args.alpha,
        colormap=args.colormap,
        logger=lambda message: print(message, file=sys.stderr, flush=True),
    )
    print(
        json.dumps(
            {
                "status": "completed",
                "sample_count": result.sample_count,
                "target_layer": result.target_layer,
                "target_mode": result.target_mode,
                "manifest": str(result.manifest_path),
                "report": str(result.report_path) if result.report_path is not None else None,
            },
            ensure_ascii=False,
        )
    )


def error_analysis_main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Summarize Week 4 low-F1 classes, confusion pairs, and confident errors"
    )
    parser.add_argument("--metrics", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, default=Path("reports/week4_error_analysis.md"))
    parser.add_argument("--low-f1-count", type=int, default=8)
    parser.add_argument("--confusion-pair-count", type=int, default=10)
    parser.add_argument("--high-confidence-threshold", type=float, default=0.8)
    parser.add_argument("--high-confidence-error-count", type=int, default=20)
    args = parser.parse_args(argv)
    result = analyze_error_patterns(
        metrics_path=args.metrics,
        predictions_path=args.predictions,
        output_path=args.output,
        report_path=args.report,
        low_f1_count=args.low_f1_count,
        confusion_pair_count=args.confusion_pair_count,
        high_confidence_threshold=args.high_confidence_threshold,
        high_confidence_error_count=args.high_confidence_error_count,
    )
    print(
        json.dumps(
            {
                "status": "completed",
                "class_count": result.class_count,
                "sample_count": result.sample_count,
                "error_count": result.error_count,
                "high_confidence_error_count": result.high_confidence_error_count,
                "error_analysis": str(result.error_analysis_path),
                "report": str(result.report_path) if result.report_path is not None else None,
            },
            ensure_ascii=False,
        )
    )


def attention_review_main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Create an editable Week 4 Grad-CAM attention review template"
    )
    parser.add_argument("--atlas-manifest", type=Path, required=True)
    parser.add_argument("--error-analysis", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, default=Path("reports/week4_attention_review.md"))
    args = parser.parse_args(argv)
    result = create_attention_review_template(
        atlas_manifest_path=args.atlas_manifest,
        output_path=args.output,
        error_analysis_path=args.error_analysis,
        report_path=args.report,
    )
    print(
        json.dumps(
            {
                "status": "completed",
                "sample_count": result.sample_count,
                "needs_review_count": result.needs_review_count,
                "high_confidence_error_count": result.high_confidence_error_count,
                "attention_review": str(result.review_path),
                "report": str(result.report_path) if result.report_path is not None else None,
            },
            ensure_ascii=False,
        )
    )


def calibration_main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Analyze top-label calibration and generate a reliability diagram"
    )
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, default=Path("reports/week4_calibration.md"))
    parser.add_argument(
        "--figure",
        type=Path,
        default=Path("reports/figures/week4_reliability_diagram.png"),
    )
    parser.add_argument("--bins", type=int, default=10)
    args = parser.parse_args(argv)
    result = analyze_calibration(
        predictions_path=args.predictions,
        output_path=args.output,
        report_path=args.report,
        figure_path=args.figure,
        num_bins=args.bins,
    )
    print(
        json.dumps(
            {
                "status": "completed",
                "sample_count": result.sample_count,
                "top_label_ece": result.top_label_ece,
                "top_label_mce": result.top_label_mce,
                "calibration": str(result.calibration_path),
                "report": str(result.report_path) if result.report_path is not None else None,
                "figure": str(result.figure_path) if result.figure_path is not None else None,
            },
            ensure_ascii=False,
        )
    )
