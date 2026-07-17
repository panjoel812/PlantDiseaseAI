import pytest
import torch
from PIL import Image
from torch.utils.data import DataLoader

from plantdisease.data.dataset import ImageRecord, RecordDataset
from plantdisease.data.transforms import build_eval_transform, build_train_transform


def make_image(color: tuple[int, int, int], size: tuple[int, int] = (32, 24)) -> Image.Image:
    return Image.new("RGB", size, color=color)


def test_record_dataset_produces_expected_batch() -> None:
    records = [
        ImageRecord(make_image((20, 120, 40)), 0, "healthy-1"),
        ImageRecord(make_image((120, 30, 20)), 1, "disease-1"),
    ]
    dataset = RecordDataset(records, transform=build_eval_transform(32))

    images, labels = next(iter(DataLoader(dataset, batch_size=2)))

    assert images.shape == (2, 3, 32, 32)
    assert images.dtype == torch.float32
    assert labels.dtype == torch.int64
    assert labels.tolist() == [0, 1]
    assert torch.isfinite(images).all()


def test_eval_transform_is_deterministic() -> None:
    image = make_image((40, 80, 120), size=(43, 27))
    transform = build_eval_transform(32)

    assert torch.equal(transform(image), transform(image))


def test_train_transform_has_expected_shape() -> None:
    tensor = build_train_transform(32)(make_image((10, 90, 30)))

    assert tensor.shape == (3, 32, 32)
    assert tensor.dtype == torch.float32


def test_record_dataset_supports_worker_process_loading() -> None:
    records = [
        ImageRecord(make_image((20, 120, 40)), 0, "healthy-1"),
        ImageRecord(make_image((120, 30, 20)), 1, "disease-1"),
    ]
    loader = DataLoader(
        RecordDataset(records, transform=build_eval_transform(32)),
        batch_size=2,
        num_workers=1,
    )

    images, labels = next(iter(loader))

    assert images.shape == (2, 3, 32, 32)
    assert labels.tolist() == [0, 1]


def test_record_dataset_rejects_negative_label() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        RecordDataset([ImageRecord(make_image((1, 2, 3)), -1, "bad")])
