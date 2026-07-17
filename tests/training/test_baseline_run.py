import json
from pathlib import Path

import torch
from PIL import Image

from plantdisease.data.dataset import ImageRecord
from plantdisease.models.checkpoint import load_checkpoint
from plantdisease.training.baseline import run_baseline_training


def _records(prefix: str, count_per_class: int) -> list[ImageRecord]:
    records: list[ImageRecord] = []
    for label in range(2):
        for index in range(count_per_class):
            color = (40, 130 + index, 45) if label == 0 else (130, 70 + index, 35)
            image = Image.new("RGB", (32, 32), color)
            records.append(ImageRecord(image, label, f"{prefix}-{label}-{index}"))
    return records


class FakeLazySplit:
    column_names = ["image", "label"]

    def __init__(self, records: list[ImageRecord]) -> None:
        self.records = records
        self.image_access_count = 0

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, index):
        if index == "label":
            return [record.label for record in self.records]
        self.image_access_count += 1
        record = self.records[index]
        return {"image": record.image, "label": record.label}

    def select(self, indices):
        return FakeLazySplit([self.records[index] for index in indices])


def test_baseline_training_writes_real_run_artifacts(tmp_path: Path, monkeypatch) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
data:
  image_size: 32
  batch_size: 4
  num_workers: 0
  train_ratio: 0.75
  validation_ratio: 0.25
  test_ratio: 0.0
model:
  name: mobilenet_v2
  pretrained: false
training:
  seed: 13
  epochs: 1
  learning_rate: 0.05
  device: cpu
""".strip(),
        encoding="utf-8",
    )

    train_split = FakeLazySplit(_records("train", 6))
    test_split = FakeLazySplit(_records("test", 3))

    def fake_loader(cache_dir, max_samples_per_split=None):
        return {"train": train_split, "test": test_split}, [
            "healthy",
            "synthetic_blight",
        ]

    def fail_eager_loader(*args, **kwargs):
        raise AssertionError("baseline training must use lazy dataset splits")

    monkeypatch.setattr(
        "plantdisease.training.baseline.hf_data.load_plantvillage_splits",
        fail_eager_loader,
    )
    monkeypatch.setattr(
        "plantdisease.training.baseline.hf_data.load_plantvillage_dataset_splits",
        fake_loader,
    )
    messages: list[str] = []

    result = run_baseline_training(
        config_path=config_path,
        cache_dir=tmp_path / "cache",
        output_dir=tmp_path / "run",
        samples_per_class=2,
        log_every=1,
        logger=messages.append,
    )

    assert result.status == "completed"
    expected_files = {
        "config.yaml",
        "split.json",
        "checkpoint.pt",
        "metrics.json",
        "validation_metrics.json",
        "training_curve.json",
        "training_curve.png",
        "run_manifest.json",
    }
    assert expected_files.issubset({path.name for path in (tmp_path / "run").iterdir()})

    metrics = json.loads((tmp_path / "run" / "metrics.json").read_text(encoding="utf-8"))
    manifest = json.loads((tmp_path / "run" / "run_manifest.json").read_text(encoding="utf-8"))
    split = json.loads((tmp_path / "run" / "split.json").read_text(encoding="utf-8"))

    assert metrics["sample_count"] == 4
    assert manifest["validation_scope"] == "plantvillage_official_test"
    assert manifest["data_loading"] == "lazy_huggingface"
    assert manifest["sampling_strategy"] == "balanced_per_class"
    assert manifest["samples_per_class"] == 2
    assert manifest["train_sample_count"] == 2
    assert manifest["validation_sample_count"] == 2
    assert manifest["test_sample_count"] == 4
    assert "run_manifest.json" in manifest["artifacts"]
    assert manifest["checkpoint_selection"] == "best_validation_macro_f1"
    assert manifest["best_epoch"] == 1
    assert manifest["best_validation_macro_f1"] >= 0.0
    assert split["sampling"]["strategy"] == "balanced_per_class"
    assert split["sampling"]["samples_per_class"] == 2
    assert split["split_sources"] == {
        "train": "hf_train",
        "validation": "hf_train",
        "test": "hf_test",
    }
    assert train_split.image_access_count < len(train_split) * 3
    assert any("epoch 1/1 batch" in message for message in messages)

    _, class_names, checkpoint_config = load_checkpoint(
        tmp_path / "run" / "checkpoint.pt", torch.device("cpu")
    )
    assert class_names == ["healthy", "synthetic_blight"]
    assert checkpoint_config["model_name"] == "mobilenet_v2"
    assert checkpoint_config["checkpoint_selection"] == "best_validation_macro_f1"
    assert checkpoint_config["best_epoch"] == 1


def test_baseline_training_records_week3_method_config(
    tmp_path: Path, monkeypatch
) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
data:
  image_size: 32
  batch_size: 4
  num_workers: 0
  train_ratio: 0.75
  validation_ratio: 0.25
  test_ratio: 0.0
model:
  name: mobilenet_v2
  pretrained: false
training:
  seed: 17
  epochs: 1
  learning_rate: 0.05
  device: cpu
augmentation:
  randaugment_enabled: true
  randaugment_num_ops: 2
  randaugment_magnitude: 5
  random_erasing_enabled: true
  random_erasing_probability: 0.0
  mixup_alpha: 0.2
loss:
  name: cross_entropy
  label_smoothing: 0.05
scheduler:
  name: cosine
  eta_min: 0.001
ema:
  enabled: true
  decay: 0.9
""".strip(),
        encoding="utf-8",
    )

    train_split = FakeLazySplit(_records("train", 6))
    test_split = FakeLazySplit(_records("test", 3))

    def fake_loader(cache_dir, max_samples_per_split=None):
        return {"train": train_split, "test": test_split}, [
            "healthy",
            "synthetic_blight",
        ]

    monkeypatch.setattr(
        "plantdisease.training.baseline.hf_data.load_plantvillage_dataset_splits",
        fake_loader,
    )

    result = run_baseline_training(
        config_path=config_path,
        cache_dir=tmp_path / "cache",
        output_dir=tmp_path / "run",
        samples_per_class=2,
        log_every=0,
        logger=lambda _: None,
    )

    manifest = json.loads((tmp_path / "run" / "run_manifest.json").read_text(encoding="utf-8"))
    _, _, checkpoint_config = load_checkpoint(
        tmp_path / "run" / "checkpoint.pt", torch.device("cpu")
    )

    assert result.status == "completed"
    assert manifest["augmentation"]["randaugment_enabled"] is True
    assert manifest["augmentation"]["random_erasing_enabled"] is True
    assert manifest["augmentation"]["mixup_alpha"] == 0.2
    assert manifest["loss"]["label_smoothing"] == 0.05
    assert manifest["scheduler"]["name"] == "cosine"
    assert manifest["scheduler"]["eta_min"] == 0.001
    assert manifest["ema"] == {"enabled": True, "decay": 0.9}
    assert checkpoint_config["loss"]["name"] == "cross_entropy"
    assert checkpoint_config["scheduler"]["name"] == "cosine"
    assert checkpoint_config["ema"]["enabled"] is True
