import json
from pathlib import Path

import pytest
import torch
from torch import nn

from plantdisease.explainability.layers import TargetLayer
from plantdisease.explainability.workflow import freeze_explainability_samples


class FakeSplit:
    column_names = ["image", "label"]

    def __len__(self) -> int:
        return 2

    def __getitem__(self, index: int) -> dict[str, object]:
        raise AssertionError("test should not decode images when prediction collection is patched")

    def select(self, indices: list[int]) -> "FakeSplit":
        assert indices == [0, 1]
        return self


class FakeModel(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.conv = nn.Conv2d(3, 2, kernel_size=1)


def _prediction(test_index: int, confidence: float, correct: bool) -> dict[str, object]:
    return {
        "test_index": test_index,
        "sample_id": f"hf-test-{test_index}",
        "true_class_index": 0 if correct else 1,
        "true_class_name": "healthy" if correct else "disease",
        "predicted_class_index": 0,
        "predicted_class_name": "healthy",
        "confidence": confidence,
        "correct": correct,
        "top_k": [],
    }


def test_freeze_explainability_samples_writes_prediction_and_sample_files(
    tmp_path: Path, monkeypatch
) -> None:
    checkpoint_path = tmp_path / "checkpoint.pt"
    split_path = tmp_path / "split.json"
    split_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "class_names": ["healthy", "disease"],
                "splits": {"test": [0, 1]},
                "sampling": {
                    "source_indices": {
                        "hf_test": [0, 1],
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    def fake_load_checkpoint(path: Path, device: torch.device):
        assert path == checkpoint_path
        assert device.type == "cpu"
        return FakeModel(), ["healthy", "disease"], {"model_name": "resnet50", "image_size": 32}

    def fake_load_splits(cache_dir: Path | None):
        assert cache_dir == tmp_path / "cache"
        return {"test": FakeSplit()}, ["healthy", "disease"]

    def fake_resolve_target_layer(model: nn.Module, model_name: str) -> TargetLayer:
        assert model_name == "resnet50"
        return TargetLayer("layer4.2", model.conv)

    def fake_collect_predictions(
        model: nn.Module,
        loader,
        class_names: list[str],
        *,
        test_indices: list[int],
        top_k: int,
        progress_logger,
        progress_log_every: int,
    ) -> list[dict[str, object]]:
        assert class_names == ["healthy", "disease"]
        assert test_indices == [0, 1]
        assert top_k == 3
        assert callable(progress_logger)
        assert progress_log_every == 1
        assert loader.batch_size == 2
        progress_logger("predict [########################] batch 1/1 samples=2/2")
        return [_prediction(0, 0.95, True), _prediction(1, 0.90, False)]

    monkeypatch.setattr(
        "plantdisease.explainability.workflow.load_checkpoint",
        fake_load_checkpoint,
    )
    monkeypatch.setattr(
        "plantdisease.explainability.workflow.hf_data.load_plantvillage_dataset_splits",
        fake_load_splits,
    )
    monkeypatch.setattr(
        "plantdisease.explainability.workflow.resolve_target_layer",
        fake_resolve_target_layer,
    )
    monkeypatch.setattr(
        "plantdisease.explainability.workflow.collect_prediction_records",
        fake_collect_predictions,
    )

    messages: list[str] = []
    result = freeze_explainability_samples(
        checkpoint_path=checkpoint_path,
        split_manifest_path=split_path,
        output_dir=tmp_path / "week4",
        cache_dir=tmp_path / "cache",
        samples_per_group=1,
        top_k=3,
        batch_size=2,
        device_name="cpu",
        logger=messages.append,
        progress_log_every=1,
    )

    predictions = json.loads(result.prediction_path.read_text(encoding="utf-8"))
    frozen = json.loads(result.frozen_samples_path.read_text(encoding="utf-8"))
    assert result.prediction_count == 2
    assert result.target_layer == "layer4.2"
    assert "load split manifest" in messages[0]
    assert any("collect predictions" in message for message in messages)
    assert any("batch 1/1" in message for message in messages)
    assert any("write frozen samples" in message for message in messages)
    assert predictions[0]["sample_id"] == "hf-test-0"
    assert frozen["model"] == {
        "checkpoint_path": str(checkpoint_path),
        "model_name": "resnet50",
        "target_layer": "layer4.2",
    }
    assert frozen["inputs"]["prediction_path"] == str(result.prediction_path)
    assert frozen["selection"]["selected_counts"]["error_high_confidence"] == 1


def test_freeze_explainability_samples_rejects_stale_target_layer(
    tmp_path: Path, monkeypatch
) -> None:
    checkpoint_path = tmp_path / "checkpoint.pt"
    split_path = tmp_path / "split.json"
    split_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "class_names": ["healthy", "disease"],
                "splits": {"test": [0, 1]},
            }
        ),
        encoding="utf-8",
    )

    def fake_load_checkpoint(path: Path, device: torch.device):
        assert path == checkpoint_path
        assert device.type == "cpu"
        return FakeModel(), ["healthy", "disease"], {"model_name": "resnet50", "image_size": 32}

    def fake_resolve_target_layer(model: nn.Module, model_name: str) -> TargetLayer:
        assert model_name == "resnet50"
        return TargetLayer("layer4.2", model.conv)

    def fake_load_splits(_cache_dir: Path | None):
        raise AssertionError("dataset should not load after target-layer mismatch")

    monkeypatch.setattr(
        "plantdisease.explainability.workflow.load_checkpoint",
        fake_load_checkpoint,
    )
    monkeypatch.setattr(
        "plantdisease.explainability.workflow.resolve_target_layer",
        fake_resolve_target_layer,
    )
    monkeypatch.setattr(
        "plantdisease.explainability.workflow.hf_data.load_plantvillage_dataset_splits",
        fake_load_splits,
    )

    with pytest.raises(ValueError, match="target_layer must be layer4.2 for resnet50"):
        freeze_explainability_samples(
            checkpoint_path=checkpoint_path,
            split_manifest_path=split_path,
            output_dir=tmp_path / "week4",
            device_name="cpu",
            target_layer="layer4.2.conv3",
        )
