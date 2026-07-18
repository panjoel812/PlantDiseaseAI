from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import torch
from PIL import Image
from torchvision import transforms

from plantdisease.openworld.encoder import extract_embeddings
from plantdisease.openworld.manifest import OpenWorldRecord


@dataclass
class FakeEncoder:
    encoder_id: str = "fake"
    embedding_dimension: int = 3

    def encode_batch(self, images: torch.Tensor) -> torch.Tensor:
        return images.mean(dim=(2, 3))


def test_extract_embeddings_preserves_manifest_order(tmp_path: Path) -> None:
    Image.new("RGB", (8, 8), (255, 0, 0)).save(tmp_path / "red.png")
    Image.new("RGB", (8, 8), (0, 255, 0)).save(tmp_path / "green.png")
    records = [
        OpenWorldRecord("one", "red.png", "grape", None, "train", "x", "CC0", "one"),
        OpenWorldRecord(
            "two", "green.png", "tomato", None, "train", "x", "CC0", "two"
        ),
    ]

    embeddings, plant_ids, image_ids = extract_embeddings(
        records,
        image_root=tmp_path,
        encoder=FakeEncoder(),
        transform=transforms.ToTensor(),
        batch_size=2,
    )

    assert embeddings.shape == (2, 3)
    assert plant_ids == ["grape", "tomato"]
    assert image_ids == ["one", "two"]
    assert embeddings[0].tolist() == [1.0, 0.0, 0.0]
