"""PlantVillage MobileNetV2 baseline training run."""

from __future__ import annotations

import json
import os
import platform
import shutil
import sys
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path
from time import perf_counter
from typing import cast

os.environ.setdefault("MPLCONFIGDIR", str(Path.cwd() / ".cache" / "matplotlib"))

import matplotlib.pyplot as plt
import torch
from torch import nn
from torch.utils.data import DataLoader, Subset

from plantdisease.config import ExperimentConfig
from plantdisease.data import huggingface as hf_data
from plantdisease.data.dataset import HuggingFaceImageDataset
from plantdisease.data.splits import stratified_train_validation_indices
from plantdisease.data.transforms import build_eval_transform, build_train_transform
from plantdisease.evaluation.metrics import save_metrics
from plantdisease.models.checkpoint import save_checkpoint
from plantdisease.models.factory import create_model
from plantdisease.training.ema import ModelEMA
from plantdisease.training.engine import evaluate, train_one_epoch
from plantdisease.training.losses import build_criterion
from plantdisease.training.mix import build_batch_mixer
from plantdisease.training.schedulers import build_scheduler
from plantdisease.training.seed import seed_everything


@dataclass(frozen=True)
class BaselineRunResult:
    status: str
    run_id: str
    output_dir: Path
    metrics: dict[str, object]


def _resolve_device(name: str) -> torch.device:
    if name == "auto":
        if torch.cuda.is_available():
            return torch.device("cuda")
        if torch.backends.mps.is_available():
            return torch.device("mps")
        return torch.device("cpu")
    device = torch.device(name)
    if device.type == "cuda" and not torch.cuda.is_available():
        raise ValueError("CUDA was requested but is not available")
    if device.type == "mps" and not torch.backends.mps.is_available():
        raise ValueError("MPS was requested but is not available")
    return device


def _validation_fraction(config: ExperimentConfig) -> float:
    train_validation_total = config.data.train_ratio + config.data.validation_ratio
    return config.data.validation_ratio / train_validation_total


def _save_split_manifest(
    path: Path,
    train_indices: list[int],
    validation_indices: list[int],
    test_indices: list[int],
    train_labels: list[int],
    test_labels: list[int],
    class_names: list[str],
    seed: int,
    sampling: dict[str, object],
) -> None:
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "seed": seed,
                "class_names": class_names,
                "split_sources": {
                    "train": "hf_train",
                    "validation": "hf_train",
                    "test": "hf_test",
                },
                "splits": {
                    "train": train_indices,
                    "validation": validation_indices,
                    "test": test_indices,
                },
                "labels": {
                    "hf_train": train_labels,
                    "hf_test": test_labels,
                },
                "sampling": sampling,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def _save_training_curve(curve: list[dict[str, float | int]], output_dir: Path) -> None:
    (output_dir / "training_curve.json").write_text(json.dumps(curve, indent=2), encoding="utf-8")
    figure, loss_axis = plt.subplots(figsize=(6, 4))
    epochs = [int(point["epoch"]) for point in curve]
    loss_axis.plot(epochs, [float(point["train_loss"]) for point in curve], marker="o")
    loss_axis.set_xlabel("Epoch")
    loss_axis.set_ylabel("Train loss")
    metric_axis = loss_axis.twinx()
    metric_axis.plot(
        epochs,
        [float(point["validation_macro_f1"]) for point in curve],
        marker="s",
        color="#4f8f57",
    )
    metric_axis.set_ylabel("Validation macro F1")
    metric_axis.set_ylim(0.0, 1.0)
    figure.tight_layout()
    figure.savefig(output_dir / "training_curve.png", dpi=160)
    plt.close(figure)


def _clone_state_dict_for_checkpoint(model: nn.Module) -> dict[str, torch.Tensor]:
    return {name: tensor.detach().cpu().clone() for name, tensor in model.state_dict().items()}


def _clone_evaluation_state_dict(
    model: nn.Module, ema: ModelEMA | None
) -> dict[str, torch.Tensor]:
    if ema is None:
        return _clone_state_dict_for_checkpoint(model)
    with ema.average_parameters(model):
        return _clone_state_dict_for_checkpoint(model)


def run_baseline_training(
    config_path: Path,
    cache_dir: Path | None,
    output_dir: Path,
    max_samples_per_split: int | None = None,
    samples_per_class: int | None = None,
    log_every: int = 20,
    logger: Callable[[str], None] = print,
) -> BaselineRunResult:
    """Train MobileNetV2 on PlantVillage using upstream test as final test split."""

    started = perf_counter()
    if max_samples_per_split is not None and samples_per_class is not None:
        raise ValueError("max_samples_per_split and samples_per_class are mutually exclusive")
    config = ExperimentConfig.from_yaml(config_path)
    seed_everything(config.training.seed)
    output_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(config_path, output_dir / "config.yaml")

    splits, class_names = hf_data.load_plantvillage_dataset_splits(cache_dir, max_samples_per_split)
    if "test" not in splits:
        raise ValueError("PlantVillage official test split is required for baseline training")
    train_split = splits["train"]
    test_split = splits["test"]
    train_labels = hf_data.labels_from_split(train_split)
    test_labels = hf_data.labels_from_split(test_split)
    sampling: dict[str, object] = {"strategy": "all_available"}
    if samples_per_class is not None:
        train_source_indices = hf_data.balanced_indices_by_label(
            train_labels, samples_per_class, config.training.seed
        )
        test_source_indices = hf_data.balanced_indices_by_label(
            test_labels, samples_per_class, config.training.seed
        )
        train_split = train_split.select(train_source_indices)
        test_split = test_split.select(test_source_indices)
        train_labels = hf_data.labels_from_split(train_split)
        test_labels = hf_data.labels_from_split(test_split)
        sampling = {
            "strategy": "balanced_per_class",
            "samples_per_class": samples_per_class,
            "source_indices": {
                "hf_train": train_source_indices,
                "hf_test": test_source_indices,
            },
        }
    train_validation = stratified_train_validation_indices(
        train_labels,
        validation_ratio=_validation_fraction(config),
        seed=config.training.seed,
    )
    test_indices = list(range(len(test_split)))
    _save_split_manifest(
        output_dir / "split.json",
        train_validation["train"],
        train_validation["validation"],
        test_indices,
        train_labels,
        test_labels,
        class_names,
        config.training.seed,
        sampling,
    )

    train_dataset = HuggingFaceImageDataset(
        train_split,
        build_train_transform(
            config.data.image_size,
            randaugment_enabled=config.augmentation.randaugment_enabled,
            randaugment_num_ops=config.augmentation.randaugment_num_ops,
            randaugment_magnitude=config.augmentation.randaugment_magnitude,
            random_erasing_enabled=config.augmentation.random_erasing_enabled,
            random_erasing_probability=config.augmentation.random_erasing_probability,
        ),
    )
    train_eval_dataset = HuggingFaceImageDataset(
        train_split, build_eval_transform(config.data.image_size)
    )
    test_dataset = HuggingFaceImageDataset(test_split, build_eval_transform(config.data.image_size))
    generator = torch.Generator().manual_seed(config.training.seed)
    train_loader = DataLoader(
        Subset(train_dataset, train_validation["train"]),
        batch_size=config.data.batch_size,
        shuffle=True,
        generator=generator,
        num_workers=config.data.num_workers,
    )
    validation_loader = DataLoader(
        Subset(train_eval_dataset, train_validation["validation"]),
        batch_size=config.data.batch_size,
        shuffle=False,
        num_workers=config.data.num_workers,
    )
    test_loader = DataLoader(
        Subset(test_dataset, test_indices),
        batch_size=config.data.batch_size,
        shuffle=False,
        num_workers=config.data.num_workers,
    )

    device = _resolve_device(config.training.device)
    model = create_model(
        config.model.name,
        len(class_names),
        pretrained=config.model.pretrained,
    ).to(device)
    criterion = build_criterion(config.loss)
    optimizer = torch.optim.AdamW(model.parameters(), lr=config.training.learning_rate)
    scheduler = build_scheduler(
        optimizer,
        config.scheduler,
        total_steps=len(train_loader) * config.training.epochs,
    )
    ema = ModelEMA(model, config.ema.decay) if config.ema.enabled else None
    batch_mixer = build_batch_mixer(config.augmentation, len(class_names))
    curve: list[dict[str, float | int]] = []
    validation_result = None
    best_epoch = 0
    best_validation_macro_f1 = -1.0
    best_state_dict: dict[str, torch.Tensor] | None = None
    best_validation_metrics: dict[str, object] | None = None

    for epoch in range(config.training.epochs):
        logger(
            f"epoch {epoch + 1}/{config.training.epochs} "
            f"train_batches={len(train_loader)} "
            f"validation_batches={len(validation_loader)}"
        )

        train_result = train_one_epoch(
            model,
            train_loader,
            criterion,
            optimizer,
            device,
            progress_prefix=f"epoch {epoch + 1}/{config.training.epochs}",
            log_every=log_every,
            logger=logger,
            batch_mixer=batch_mixer,
            scheduler=scheduler,
            ema=ema,
        )

        validation_result = evaluate(
            model, validation_loader, criterion, device, class_names, ema=ema
        )
        validation_accuracy = float(
            cast(int | float | str, validation_result.metrics["accuracy"])
        )
        validation_macro_f1 = float(
            cast(int | float | str, validation_result.metrics["macro_f1"])
        )

        logger(
            f"epoch {epoch + 1}/{config.training.epochs} "
            f"validation_accuracy={validation_accuracy:.4f} "
            f"validation_macro_f1={validation_macro_f1:.4f}"
        )

        if validation_macro_f1 > best_validation_macro_f1:
            best_epoch = epoch + 1
            best_validation_macro_f1 = validation_macro_f1
            best_state_dict = _clone_evaluation_state_dict(model, ema)
            best_validation_metrics = dict(validation_result.metrics)

        curve.append(
            {
                "epoch": epoch + 1,
                "train_loss": train_result.loss,
                "validation_loss": validation_result.epoch.loss,
                "validation_accuracy": validation_accuracy,
                "validation_macro_f1": validation_macro_f1,
            }
        )

    if validation_result is None or best_state_dict is None or best_validation_metrics is None:
        raise ValueError("training completed without validation")

    model.load_state_dict(best_state_dict)
    test_result = evaluate(model, test_loader, criterion, device, class_names)
    save_metrics(best_validation_metrics, output_dir / "validation_metrics.json")
    save_metrics(test_result.metrics, output_dir / "metrics.json")
    _save_training_curve(curve, output_dir)
    save_checkpoint(
        output_dir / "checkpoint.pt",
        model,
        class_names,
        {
            "model_name": config.model.name,
            "num_classes": len(class_names),
            "image_size": config.data.image_size,
            "pretrained": config.model.pretrained,
            "validation_scope": "plantvillage_official_test",
            "checkpoint_selection": "best_validation_macro_f1",
            "best_epoch": best_epoch,
            "best_validation_macro_f1": best_validation_macro_f1,
            "augmentation": asdict(config.augmentation),
            "loss": asdict(config.loss),
            "scheduler": asdict(config.scheduler),
            "ema": asdict(config.ema),
        },
    )

    run_id = f"plantvillage-{config.model.name}-seed{config.training.seed}"
    manifest = {
        "run_id": run_id,
        "status": "completed",
        "validation_scope": "plantvillage_official_test",
        "seed": config.training.seed,
        "python": sys.version.split()[0],
        "torch": torch.__version__,
        "platform": platform.platform(),
        "device": str(device),
        "data_loading": "lazy_huggingface",
        "sampling_strategy": sampling["strategy"],
        "samples_per_class": samples_per_class,
        "log_every": log_every,
        "augmentation": asdict(config.augmentation),
        "loss": asdict(config.loss),
        "scheduler": asdict(config.scheduler),
        "ema": asdict(config.ema),
        "duration_seconds": perf_counter() - started,
        "train_sample_count": len(train_validation["train"]),
        "validation_sample_count": len(train_validation["validation"]),
        "test_sample_count": len(test_indices),
        "artifacts": sorted({path.name for path in output_dir.iterdir()} | {"run_manifest.json"}),
        "checkpoint_selection": "best_validation_macro_f1",
        "best_epoch": best_epoch,
        "best_validation_macro_f1": best_validation_macro_f1,
    }
    (output_dir / "run_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return BaselineRunResult("completed", run_id, output_dir, test_result.metrics)
