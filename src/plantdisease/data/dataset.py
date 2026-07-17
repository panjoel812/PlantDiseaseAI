"""Dataset primitives shared by training, evaluation, and smoke tests."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from PIL import Image
from torch import Tensor
from torch.utils.data import Dataset


@dataclass(frozen=True)
class ImageRecord:
    image: Image.Image
    label: int
    sample_id: str


class RecordDataset(Dataset[tuple[Tensor | Image.Image, int]]):
    def __init__(
        self,
        records: Sequence[ImageRecord],
        transform: Callable[[Image.Image], Tensor] | None = None,
    ) -> None:
        if any(record.label < 0 for record in records):
            raise ValueError("record labels must be non-negative")
        self.records = records
        self.transform = transform

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, index: int) -> tuple[Tensor | Image.Image, int]:
        record = self.records[index]
        image = record.image.copy()
        if self.transform is not None:
            image = self.transform(image)
        return image, record.label


class HuggingFaceImageDataset(Dataset[tuple[Tensor | Image.Image, int]]):
    """Lazy image dataset wrapper around a Hugging Face split."""

    def __init__(
        self,
        split,
        transform: Callable[[Image.Image], Tensor] | None = None,
    ) -> None:
        if "image" not in split.column_names or "label" not in split.column_names:
            raise ValueError(f"expected image/label columns, got {split.column_names}")
        self.split = split
        self.transform = transform

    def __len__(self) -> int:
        return len(self.split)

    def __getitem__(self, index: int) -> tuple[Tensor | Image.Image, int]:
        sample = self.split[index]
        image = sample["image"]
        if hasattr(image, "copy"):
            image = image.copy()
        if self.transform is not None:
            image = self.transform(image)
        return image, int(sample["label"])
