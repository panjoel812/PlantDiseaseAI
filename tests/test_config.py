from pathlib import Path

import pytest

from plantdisease.config import ExperimentConfig

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WEEK3_ABLATION_CONFIG_DIR = PROJECT_ROOT / "configs" / "week3_ablation"


def test_experiment_config_loads_yaml(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    path.write_text(
        """
data:
  image_size: 64
  batch_size: 4
  num_workers: 0
  train_ratio: 0.6
  validation_ratio: 0.2
  test_ratio: 0.2
model:
  name: mobilenet_v2
  pretrained: false
training:
  seed: 42
  epochs: 1
  learning_rate: 0.01
  device: cpu
""".strip(),
        encoding="utf-8",
    )

    config = ExperimentConfig.from_yaml(path)

    assert config.data.image_size == 64
    assert config.model.name == "mobilenet_v2"
    assert config.training.seed == 42


def test_experiment_config_loads_week3_sections(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    path.write_text(
        """
data:
  image_size: 64
model:
  name: resnet50
training:
  seed: 42
  epochs: 5
  learning_rate: 0.001
augmentation:
  randaugment_enabled: true
  randaugment_num_ops: 2
  randaugment_magnitude: 9
  random_erasing_enabled: true
  random_erasing_probability: 0.25
  mixup_alpha: 0.2
loss:
  name: cross_entropy
  label_smoothing: 0.1
scheduler:
  name: cosine
  eta_min: 0.00001
ema:
  enabled: true
  decay: 0.999
""".strip(),
        encoding="utf-8",
    )

    config = ExperimentConfig.from_yaml(path)

    assert config.augmentation.randaugment_enabled is True
    assert config.augmentation.random_erasing_enabled is True
    assert config.augmentation.mixup_alpha == pytest.approx(0.2)
    assert config.loss.label_smoothing == pytest.approx(0.1)
    assert config.scheduler.name == "cosine"
    assert config.ema.enabled is True


def test_experiment_config_rejects_mixup_and_cutmix_together(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    path.write_text(
        """
augmentation:
  mixup_alpha: 0.2
  cutmix_alpha: 1.0
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="mixup_alpha and cutmix_alpha"):
        ExperimentConfig.from_yaml(path)


def test_experiment_config_rejects_invalid_image_size(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    path.write_text(
        """
data:
  image_size: 0
model:
  name: mobilenet_v2
training:
  seed: 42
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="image_size"):
        ExperimentConfig.from_yaml(path)


def test_week3_ablation_configs_parse_and_share_frozen_protocol() -> None:
    expected_names = {
        "00_resnet50_baseline.yaml",
        "01_label_smoothing.yaml",
        "02_focal_loss.yaml",
        "03_cosine_scheduler.yaml",
        "04_ema.yaml",
        "05_randaugment.yaml",
        "06_random_erasing.yaml",
        "07_mixup.yaml",
        "08_cutmix.yaml",
        "09_combo_candidate.yaml",
    }
    paths = sorted(WEEK3_ABLATION_CONFIG_DIR.glob("*.yaml"))

    assert {path.name for path in paths} == expected_names

    baseline = ExperimentConfig.from_yaml(
        WEEK3_ABLATION_CONFIG_DIR / "00_resnet50_baseline.yaml"
    )
    for path in paths:
        config = ExperimentConfig.from_yaml(path)

        assert config.data == baseline.data
        assert config.model == baseline.model
        assert config.training == baseline.training


def test_week3_single_variable_ablation_configs_change_only_one_method_group() -> None:
    baseline = ExperimentConfig.from_yaml(
        WEEK3_ABLATION_CONFIG_DIR / "00_resnet50_baseline.yaml"
    )
    expected_changed_groups = {
        "01_label_smoothing.yaml": {"loss"},
        "02_focal_loss.yaml": {"loss"},
        "03_cosine_scheduler.yaml": {"scheduler"},
        "04_ema.yaml": {"ema"},
        "05_randaugment.yaml": {"augmentation"},
        "06_random_erasing.yaml": {"augmentation"},
        "07_mixup.yaml": {"augmentation"},
        "08_cutmix.yaml": {"augmentation"},
        "09_combo_candidate.yaml": {"loss", "scheduler"},
    }

    for name, expected in expected_changed_groups.items():
        config = ExperimentConfig.from_yaml(WEEK3_ABLATION_CONFIG_DIR / name)
        actual = set()
        if config.augmentation != baseline.augmentation:
            actual.add("augmentation")
        if config.loss != baseline.loss:
            actual.add("loss")
        if config.scheduler != baseline.scheduler:
            actual.add("scheduler")
        if config.ema != baseline.ema:
            actual.add("ema")

        assert actual == expected
