import json
from pathlib import Path

import pytest
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from plantdisease.explainability.predictions import (
    collect_prediction_records,
    save_prediction_records,
)


class EncodedLogitModel(nn.Module):
    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        return inputs[:, :, 0, 0]


def _loader() -> DataLoader:
    images = torch.zeros(3, 3, 2, 2)
    images[0, :, 0, 0] = torch.tensor([4.0, 1.0, 0.0])
    images[1, :, 0, 0] = torch.tensor([0.0, 2.0, 4.0])
    images[2, :, 0, 0] = torch.tensor([0.0, 5.0, 1.0])
    labels = torch.tensor([0, 1, 1])
    return DataLoader(TensorDataset(images, labels), batch_size=2, shuffle=False)


def test_collect_prediction_records_exports_json_ready_sample_predictions() -> None:
    messages: list[str] = []

    records = collect_prediction_records(
        EncodedLogitModel(),
        _loader(),
        ["healthy", "early_blight", "late_blight"],
        test_indices=[10, 11, 12],
        top_k=2,
        progress_logger=messages.append,
        progress_log_every=1,
    )

    assert len(messages) == 2
    assert messages[0].startswith("predict [")
    assert "batch 1/2" in messages[0]
    assert "samples=2/3" in messages[0]
    assert "batch 2/2" in messages[1]
    assert "samples=3/3" in messages[1]
    assert [record["test_index"] for record in records] == [10, 11, 12]
    assert records[0]["sample_id"] == "hf-test-10"
    assert records[0]["true_class_name"] == "healthy"
    assert records[0]["predicted_class_name"] == "healthy"
    assert records[0]["correct"] is True
    assert records[1]["true_class_name"] == "early_blight"
    assert records[1]["predicted_class_name"] == "late_blight"
    assert records[1]["correct"] is False
    assert records[1]["confidence"] == pytest.approx(
        float(torch.softmax(torch.tensor([0.0, 2.0, 4.0]), dim=0)[2])
    )
    top_k = records[1]["top_k"]
    assert top_k[0]["class_index"] == 2
    assert top_k[0]["class_name"] == "late_blight"
    assert top_k[0]["probability"] == pytest.approx(
        float(torch.softmax(torch.tensor([0.0, 2.0, 4.0]), dim=0)[2])
    )
    assert top_k[1]["class_index"] == 1
    assert top_k[1]["class_name"] == "early_blight"
    assert top_k[1]["probability"] == pytest.approx(
        float(torch.softmax(torch.tensor([0.0, 2.0, 4.0]), dim=0)[1])
    )


def test_save_prediction_records_writes_json(tmp_path: Path) -> None:
    records = collect_prediction_records(
        EncodedLogitModel(),
        _loader(),
        ["healthy", "early_blight", "late_blight"],
        test_indices=[10, 11, 12],
        top_k=2,
    )
    output = tmp_path / "predictions.json"

    save_prediction_records(records, output)

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload[0]["sample_id"] == "hf-test-10"
    assert payload[1]["predicted_class_name"] == "late_blight"


def test_collect_prediction_records_rejects_index_count_mismatch() -> None:
    with pytest.raises(ValueError, match="test_indices length"):
        collect_prediction_records(
            EncodedLogitModel(),
            _loader(),
            ["healthy", "early_blight", "late_blight"],
            test_indices=[10],
            top_k=2,
        )
