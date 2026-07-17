from datasets import ClassLabel
from PIL import Image

from plantdisease.data.huggingface import (
    balanced_indices_by_label,
    load_plantvillage,
    load_plantvillage_splits,
)


class FakeSplit:
    column_names = ["image", "label"]
    features = {"label": ClassLabel(names=["healthy", "disease"])}

    def __init__(self, samples: list[dict[str, object]]) -> None:
        self.samples = samples

    def __len__(self) -> int:
        return len(self.samples)

    def __iter__(self):
        return iter(self.samples)

    def select(self, indices: range) -> "FakeSplit":
        return FakeSplit([self.samples[index] for index in indices])


def test_loader_uses_inspected_remote_script_and_limits_before_decode(monkeypatch) -> None:
    captured: dict[str, object] = {}
    split = FakeSplit(
        [
            {"image": Image.new("RGB", (8, 8)), "label": 0},
            {"image": Image.new("RGB", (8, 8)), "label": 1},
            {"image": Image.new("RGB", (8, 8)), "label": 0},
        ]
    )

    def fake_hf_hub_download(**kwargs):
        captured["download"] = kwargs
        return "/tmp/plant_village.py"

    def fake_load_dataset(script_path: str, **kwargs):
        captured.update({"script_path": script_path, **kwargs})
        return {"train": split}

    monkeypatch.setattr("huggingface_hub.hf_hub_download", fake_hf_hub_download)
    monkeypatch.setattr("datasets.load_dataset", fake_load_dataset)

    records, class_names = load_plantvillage(max_samples=2)

    assert captured["script_path"] == "/tmp/plant_village.py"
    assert captured["name"] == "default"
    assert captured["trust_remote_code"] is True
    assert captured["download"]["filename"] == "plant_village.py"
    assert captured["download"]["revision"] == "9e97599868962bd0079b8db4b7f1efa9185fa1e7"
    assert len(records) == 2
    assert class_names == ["healthy", "disease"]


def test_split_loader_preserves_official_train_and_test(monkeypatch) -> None:
    captured: dict[str, object] = {}
    train = FakeSplit(
        [
            {"image": Image.new("RGB", (8, 8)), "label": 0},
            {"image": Image.new("RGB", (8, 8)), "label": 1},
            {"image": Image.new("RGB", (8, 8)), "label": 0},
        ]
    )
    test = FakeSplit(
        [
            {"image": Image.new("RGB", (8, 8)), "label": 1},
            {"image": Image.new("RGB", (8, 8)), "label": 0},
        ]
    )

    def fake_hf_hub_download(**kwargs):
        return "/tmp/plant_village.py"

    def fake_load_dataset(script_path: str, **kwargs):
        captured.update({"script_path": script_path, **kwargs})
        return {"train": train, "test": test}

    monkeypatch.setattr("huggingface_hub.hf_hub_download", fake_hf_hub_download)
    monkeypatch.setattr("datasets.load_dataset", fake_load_dataset)

    splits, class_names = load_plantvillage_splits(max_samples_per_split=2)

    assert captured["script_path"] == "/tmp/plant_village.py"
    assert set(splits) == {"train", "test"}
    assert len(splits["train"]) == 2
    assert len(splits["test"]) == 2
    assert splits["train"][0].sample_id == "hf-train-0"
    assert splits["test"][0].sample_id == "hf-test-0"
    assert class_names == ["healthy", "disease"]


def test_balanced_indices_by_label_caps_each_class_reproducibly() -> None:
    labels = [0, 0, 0, 1, 1, 1, 2]

    first = balanced_indices_by_label(labels, samples_per_class=2, seed=11)
    second = balanced_indices_by_label(labels, samples_per_class=2, seed=11)

    assert first == second
    assert len([index for index in first if labels[index] == 0]) == 2
    assert len([index for index in first if labels[index] == 1]) == 2
    assert len([index for index in first if labels[index] == 2]) == 1
