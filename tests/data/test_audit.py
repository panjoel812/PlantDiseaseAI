from pathlib import Path

from PIL import Image

from plantdisease.data.audit import audit_records, save_audit_report
from plantdisease.data.dataset import ImageRecord


def test_audit_reports_classes_dimensions_modes_and_duplicates(tmp_path: Path) -> None:
    duplicate = Image.new("RGB", (12, 10), color=(30, 90, 20))
    records = [
        ImageRecord(duplicate.copy(), 0, "a"),
        ImageRecord(duplicate.copy(), 0, "b"),
        ImageRecord(Image.new("L", (8, 8), color=80), 1, "c"),
    ]

    report = audit_records(records, ["healthy", "disease"])

    assert report.sample_count == 3
    assert report.class_counts == {"healthy": 2, "disease": 1}
    assert report.image_sizes == {"12x10": 2, "8x8": 1}
    assert report.color_modes == {"RGB": 2, "L": 1}
    assert report.duplicate_groups == (("a", "b"),)
    assert report.invalid_samples == ()

    path = tmp_path / "audit.json"
    save_audit_report(report, path)
    assert '"sample_count": 3' in path.read_text(encoding="utf-8")


def test_audit_marks_out_of_range_label_invalid() -> None:
    records = [ImageRecord(Image.new("RGB", (8, 8)), 2, "bad-label")]

    report = audit_records(records, ["healthy", "disease"])

    assert report.invalid_samples == ("bad-label: label 2 is out of range",)
