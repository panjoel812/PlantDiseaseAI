"""Frozen image embedding extraction for low-compute prototype training."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Protocol

import numpy as np
import torch
from PIL import Image
from torch import nn
from torch.utils.data import DataLoader, Dataset
from torchvision.models import MobileNet_V2_Weights, mobilenet_v2

from plantdisease.openworld.manifest import OpenWorldRecord


class FrozenImageEncoder(Protocol):
    encoder_id: str
    embedding_dimension: int

    def encode_batch(self, images: torch.Tensor) -> torch.Tensor: ...


class MobileNetV2ImageNetEncoder:
    """Small default encoder; downloaded weights are frozen and never fine-tuned."""

    encoder_id = "torchvision/mobilenet_v2-imagenet1k-v2"
    embedding_dimension = 1280

    def __init__(self, device: torch.device) -> None:
        self.device = device
        self.weights = MobileNet_V2_Weights.DEFAULT
        model = mobilenet_v2(weights=self.weights)
        self.features: nn.Module = model.features.to(device).eval()

    def encode_batch(self, images: torch.Tensor) -> torch.Tensor:
        with torch.inference_mode():
            features = self.features(images.to(self.device))
            pooled = torch.nn.functional.adaptive_avg_pool2d(features, (1, 1))
            return torch.flatten(pooled, 1).cpu()


class _ManifestImageDataset(Dataset[tuple[torch.Tensor, str, str]]):
    def __init__(
        self,
        records: Sequence[OpenWorldRecord],
        image_root: Path,
        transform,
    ) -> None:
        self.records = list(records)
        self.image_root = image_root
        self.transform = transform

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, index: int) -> tuple[torch.Tensor, str, str]:
        record = self.records[index]
        image_path = self.image_root / record.image_path
        with Image.open(image_path) as image:
            tensor = self.transform(image.convert("RGB"))
        return tensor, record.plant_id, record.image_id


def extract_embeddings(
    records: Sequence[OpenWorldRecord],
    *,
    image_root: Path,
    encoder: FrozenImageEncoder,
    transform,
    batch_size: int = 32,
) -> tuple[np.ndarray, list[str], list[str]]:
    """Encode a manifest subset once; all later index updates are CPU-only."""
    if not records:
        raise ValueError("records must not be empty")
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")
    loader = DataLoader(
        _ManifestImageDataset(records, image_root, transform),
        batch_size=batch_size,
        shuffle=False,
        num_workers=0,
    )
    batches: list[np.ndarray] = []
    plant_ids: list[str] = []
    image_ids: list[str] = []
    for images, batch_plants, batch_images in loader:
        embeddings = encoder.encode_batch(images)
        if embeddings.ndim != 2 or embeddings.shape[1] != encoder.embedding_dimension:
            raise ValueError("encoder returned an unexpected embedding shape")
        batches.append(embeddings.numpy().astype(np.float32, copy=False))
        plant_ids.extend(batch_plants)
        image_ids.extend(batch_images)
    return np.concatenate(batches), plant_ids, image_ids
