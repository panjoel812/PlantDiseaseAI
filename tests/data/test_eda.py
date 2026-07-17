from pathlib import Path

from PIL import Image

from plantdisease.data.dataset import ImageRecord
from plantdisease.data.eda import generate_eda


def test_generate_eda_writes_expected_figures(tmp_path: Path) -> None:
    records = [
        ImageRecord(Image.new("RGB", (16, 12), color=(20, 100, 30)), 0, "a"),
        ImageRecord(Image.new("RGB", (16, 12), color=(30, 110, 40)), 0, "b"),
        ImageRecord(Image.new("RGB", (12, 16), color=(120, 60, 30)), 1, "c"),
        ImageRecord(Image.new("RGB", (12, 16), color=(130, 50, 20)), 1, "d"),
    ]

    artifacts = generate_eda(records, ["healthy", "disease"], tmp_path, max_samples=4)

    assert set(artifacts) == {
        "class_distribution",
        "image_size_distribution",
        "sample_grid",
    }
    assert all(path.exists() and path.stat().st_size > 0 for path in artifacts.values())
