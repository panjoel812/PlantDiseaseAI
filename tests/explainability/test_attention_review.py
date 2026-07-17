import json
from pathlib import Path

import pytest

from plantdisease.explainability.attention_review import create_attention_review_template


def _sample(
    test_index: int,
    true_index: int,
    pred_index: int,
    *,
    confidence: float,
    group: str,
) -> dict[str, object]:
    class_names = ["Apple___healthy", "Tomato___Late_blight", "Potato___Late_blight"]
    return {
        "test_index": test_index,
        "sample_id": f"hf-test-{test_index}",
        "true_class_index": true_index,
        "true_class_name": class_names[true_index],
        "predicted_class_index": pred_index,
        "predicted_class_name": class_names[pred_index],
        "confidence": confidence,
        "correct": true_index == pred_index,
        "group": group,
        "target_class_index": pred_index,
        "target_class_name": class_names[pred_index],
        "panel_path": f"atlas/{test_index}.png",
    }


def _write_atlas(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "model": {"model_name": "resnet50", "target_layer": "layer4.2"},
                "visualization": {"target_mode": "predicted"},
                "samples": [
                    _sample(
                        10,
                        0,
                        0,
                        confidence=0.95,
                        group="correct_high_confidence",
                    ),
                    _sample(
                        198,
                        1,
                        2,
                        confidence=0.87,
                        group="error_high_confidence",
                    ),
                    _sample(
                        3453,
                        1,
                        0,
                        confidence=0.42,
                        group="error_low_confidence",
                    ),
                ],
            }
        ),
        encoding="utf-8",
    )


def _write_error_analysis(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "low_f1_classes": [
                    {"class_index": 1, "class_name": "Tomato___Late_blight"}
                ],
                "confusion_pairs": [
                    {
                        "true_class_index": 1,
                        "true_class_name": "Tomato___Late_blight",
                        "predicted_class_index": 2,
                        "predicted_class_name": "Potato___Late_blight",
                        "count": 6,
                        "true_class_error_rate": 0.4,
                    }
                ],
                "high_confidence_errors": [
                    {
                        "test_index": 198,
                        "true_class_name": "Tomato___Late_blight",
                        "predicted_class_name": "Potato___Late_blight",
                        "confidence": 0.87,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )


def test_create_attention_review_template_writes_json_and_report(tmp_path: Path) -> None:
    atlas_path = tmp_path / "atlas_manifest.json"
    error_analysis_path = tmp_path / "error_analysis.json"
    output_path = tmp_path / "attention_review.json"
    report_path = tmp_path / "attention_review.md"
    _write_atlas(atlas_path)
    _write_error_analysis(error_analysis_path)

    result = create_attention_review_template(
        atlas_manifest_path=atlas_path,
        output_path=output_path,
        error_analysis_path=error_analysis_path,
        report_path=report_path,
    )

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    report = report_path.read_text(encoding="utf-8")
    assert result.review_path == output_path
    assert result.report_path == report_path
    assert result.sample_count == 3
    assert result.needs_review_count == 2
    assert payload["summary"]["high_confidence_error_count"] == 1
    assert payload["review_schema"]["attention_region_allowed_values"] == [
        "leaf",
        "lesion",
        "background",
        "shadow",
        "border",
        "mixed",
        "unclear",
    ]
    assert payload["samples"][0]["error_type"] == "not_error"
    assert payload["samples"][0]["attention_region"] is None
    assert payload["samples"][1]["evidence_flags"] == [
        "high_confidence_error",
        "frequent_confusion_pair",
        "low_f1_related",
    ]
    assert payload["samples"][1]["candidate_error_types"] == [
        "visual_similarity",
        "background_bias",
        "label_question",
        "unclear",
    ]
    assert payload["samples"][2]["evidence_flags"] == ["low_f1_related"]
    assert "## 待人工审阅样本" in report
    assert "high_confidence_error" in report


def test_create_attention_review_template_rejects_manifest_without_samples(
    tmp_path: Path,
) -> None:
    atlas_path = tmp_path / "atlas_manifest.json"
    atlas_path.write_text(json.dumps({"schema_version": 1}), encoding="utf-8")

    with pytest.raises(ValueError, match="atlas manifest must contain samples"):
        create_attention_review_template(
            atlas_manifest_path=atlas_path,
            output_path=tmp_path / "attention_review.json",
        )
