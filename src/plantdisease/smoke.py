"""Offline Week 1 smoke pipeline using small synthetic leaf images."""

from __future__ import annotations

import json
import os
import platform
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import cast

os.environ.setdefault("MPLCONFIGDIR", str(Path.cwd() / ".cache" / "matplotlib"))

import matplotlib.pyplot as plt
import torch
import yaml
from PIL import Image, ImageDraw
from torch import nn
from torch.utils.data import DataLoader, Subset

from plantdisease.config import DataConfig, ExperimentConfig, ModelConfig, TrainingConfig
from plantdisease.data.audit import audit_records, save_audit_report
from plantdisease.data.dataset import ImageRecord, RecordDataset
from plantdisease.data.eda import generate_eda
from plantdisease.data.splits import save_split_manifest, stratified_split_indices
from plantdisease.data.transforms import build_eval_transform, build_train_transform
from plantdisease.evaluation.metrics import save_metrics
from plantdisease.inference import predict_topk
from plantdisease.models.checkpoint import save_checkpoint
from plantdisease.models.factory import create_model
from plantdisease.training.engine import evaluate, overfit_single_batch, train_one_epoch
from plantdisease.training.seed import seed_everything


@dataclass(frozen=True)
class SmokeResult:
    status: str
    run_id: str
    output_dir: Path
    metrics: dict[str, object]


def _synthetic_records(image_size: int) -> list[ImageRecord]:
    records: list[ImageRecord] = []
    canvas_size = max(image_size, 32)
    for label in range(2):
        for index in range(6):
            background = (220, 235, 210) if label == 0 else (235, 220, 205)
            image = Image.new("RGB", (canvas_size, canvas_size), color=background)
            draw = ImageDraw.Draw(image)
            leaf_color = (35 + index * 3, 125 + index * 2, 45) if label == 0 else (125, 85, 35)
            margin = 4 + index % 3
            draw.ellipse(
                (margin, 2 + margin, canvas_size - margin, canvas_size - 2 - margin),
                fill=leaf_color,
            )
            draw.line(
                (canvas_size // 2, margin, canvas_size // 2, canvas_size - margin),
                fill=(220, 230, 180),
                width=1,
            )
            if label == 1:
                spot_x = 9 + index * 2
                spot_y = 12 + (index % 2) * 5
                draw.ellipse((spot_x, spot_y, spot_x + 5, spot_y + 5), fill=(75, 35, 20))
            records.append(ImageRecord(image, label, f"synthetic-{label}-{index}"))
    return records


def run_smoke(output_dir: Path, seed: int = 42, image_size: int = 32) -> SmokeResult:
    """Train and reload MobileNetV2 on synthetic images, saving audit evidence."""

    seed_everything(seed)
    output_dir.mkdir(parents=True, exist_ok=True)
    class_names = ["healthy", "synthetic_blight"]
    config = ExperimentConfig(
        data=DataConfig(
            image_size=image_size,
            batch_size=4,
            num_workers=0,
            train_ratio=0.5,
            validation_ratio=0.25,
            test_ratio=0.25,
        ),
        model=ModelConfig(name="mobilenet_v2", pretrained=False),
        training=TrainingConfig(seed=seed, epochs=1, learning_rate=0.05, device="cpu"),
    )
    (output_dir / "config.yaml").write_text(
        yaml.safe_dump(config.as_dict(), sort_keys=False),
        encoding="utf-8",
    )

    records = _synthetic_records(image_size)
    records[0].image.save(output_dir / "example_input.png")
    labels = [record.label for record in records]
    audit = audit_records(records, class_names)
    save_audit_report(audit, output_dir / "audit.json")
    generate_eda(records, class_names, output_dir, max_samples=8)
    splits = stratified_split_indices(labels, config.data.split_ratios, seed)
    save_split_manifest(output_dir / "split.json", splits, labels, class_names, seed)

    train_dataset = RecordDataset(records, build_train_transform(image_size))
    eval_dataset = RecordDataset(records, build_eval_transform(image_size))
    generator = torch.Generator().manual_seed(seed)
    train_loader = DataLoader(
        Subset(train_dataset, splits["train"]),
        batch_size=config.data.batch_size,
        shuffle=True,
        generator=generator,
        num_workers=0,
    )
    test_loader = DataLoader(
        Subset(eval_dataset, splits["test"]),
        batch_size=config.data.batch_size,
        shuffle=False,
        num_workers=0,
    )

    device = torch.device("cpu")
    overfit_model = create_model("mobilenet_v2", len(class_names), pretrained=False).to(device)
    for parameter in overfit_model.get_submodule("features").parameters():
        parameter.requires_grad = False
    cast(nn.Sequential, overfit_model.get_submodule("classifier"))[0] = nn.Identity()
    overfit_batch = next(iter(train_loader))
    overfit_losses = overfit_single_batch(
        overfit_model,
        overfit_batch,
        device,
        steps=12,
        learning_rate=0.2,
    )
    (output_dir / "single_batch_overfit.json").write_text(
        json.dumps(
            {
                "steps": len(overfit_losses),
                "initial_loss": overfit_losses[0],
                "final_loss": overfit_losses[-1],
                "losses": overfit_losses,
                "model": "mobilenet_v2",
                "validation_scope": "synthetic_fixed_batch",
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    model = create_model("mobilenet_v2", len(class_names), pretrained=False).to(device)
    for parameter in model.get_submodule("features").parameters():
        parameter.requires_grad = False
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.SGD(
        [parameter for parameter in model.parameters() if parameter.requires_grad],
        lr=config.training.learning_rate,
        momentum=0.9,
    )
    training_curve: list[dict[str, float | int]] = []
    for epoch in range(config.training.epochs):
        result = train_one_epoch(model, train_loader, criterion, optimizer, device)
        evaluation = evaluate(model, test_loader, criterion, device, class_names)
        training_curve.append(
            {
                "epoch": epoch + 1,
                "loss": result.loss,
                "test_accuracy": float(
                    cast(int | float | str, evaluation.metrics["accuracy"])
                ),
            }
        )
    (output_dir / "training_curve.json").write_text(
        json.dumps(training_curve, indent=2), encoding="utf-8"
    )
    figure, loss_axis = plt.subplots(figsize=(6, 4))
    epochs = [int(point["epoch"]) for point in training_curve]
    loss_axis.plot(epochs, [float(point["loss"]) for point in training_curve], marker="o")
    loss_axis.set_xlabel("Epoch")
    loss_axis.set_ylabel("Train loss")
    accuracy_axis = loss_axis.twinx()
    accuracy_axis.plot(
        epochs,
        [float(point["test_accuracy"]) for point in training_curve],
        marker="s",
        color="#4f8f57",
    )
    accuracy_axis.set_ylabel("Synthetic test accuracy")
    accuracy_axis.set_ylim(0.0, 1.0)
    figure.tight_layout()
    figure.savefig(output_dir / "training_curve.png", dpi=160)
    plt.close(figure)

    save_metrics(evaluation.metrics, output_dir / "metrics.json")
    checkpoint_config = {
        "model_name": "mobilenet_v2",
        "num_classes": len(class_names),
        "image_size": image_size,
        "pretrained": False,
        "validation_scope": "synthetic_data_only",
    }
    save_checkpoint(output_dir / "checkpoint.pt", model, class_names, checkpoint_config)

    predictions = []
    eval_transform = build_eval_transform(image_size)
    for index in splits["test"]:
        record = records[index]
        topk = predict_topk(model, eval_transform(record.image), class_names, k=2)
        predictions.append(
            {
                "sample_id": record.sample_id,
                "true_label": class_names[record.label],
                "topk": [asdict(prediction) for prediction in topk],
            }
        )
    (output_dir / "predictions.json").write_text(
        json.dumps(predictions, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    run_id = f"week1-synthetic-mobilenet_v2-seed{seed}"
    manifest = {
        "run_id": run_id,
        "status": "smoke_passed",
        "validation_scope": "synthetic_data_only",
        "seed": seed,
        "python": sys.version.split()[0],
        "torch": torch.__version__,
        "platform": platform.platform(),
        "device": str(device),
        "artifacts": sorted(path.name for path in output_dir.iterdir()),
    }
    (output_dir / "run_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return SmokeResult("smoke_passed", run_id, output_dir, evaluation.metrics)
