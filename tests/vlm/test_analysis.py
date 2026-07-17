import json
import subprocess
import sys
from pathlib import Path

from plantdisease.vlm.analysis import analyze_result, audit_samples, write_analysis_report
from plantdisease.vlm.schema import VQASample, write_jsonl


def make_sample(
    sample_id: str,
    question: str,
    answer: str,
    question_type: str,
) -> VQASample:
    return VQASample(
        sample_id=sample_id,
        image_id=f"image-{sample_id}",
        image_ref="hf-test-1",
        question=question,
        answer=answer,
        question_type=question_type,
        source="plantvillage_label",
        split="test",
        audit_status="pending",
    )


def make_result() -> dict[str, object]:
    return {
        "status": "completed",
        "model_id": "mlx-community/Qwen3-VL-4B-Instruct-4bit",
        "prompt_style": "short",
        "records": [
            {
                "sample_id": "q-plant",
                "image_id": "image-q-plant",
                "question_type": "plant",
                "expected_answer": "Tomato",
                "raw_answer": "Tomato",
                "normalized_answer": "tomato",
                "normalized_expected_answer": "tomato",
                "normalized_exact_match": True,
                "error": None,
            },
            {
                "sample_id": "q-condition-1",
                "image_id": "image-q-condition-1",
                "question_type": "condition",
                "expected_answer": "Leaf Mold",
                "raw_answer": "Tomato leaf curl virus",
                "normalized_answer": "tomato leaf curl virus",
                "normalized_expected_answer": "leaf mold",
                "normalized_exact_match": False,
                "error": None,
            },
            {
                "sample_id": "q-condition-2",
                "image_id": "image-q-condition-2",
                "question_type": "condition",
                "expected_answer": "Leaf Mold",
                "raw_answer": "Leaf spot disease",
                "normalized_answer": "leaf spot disease",
                "normalized_expected_answer": "leaf mold",
                "normalized_exact_match": False,
                "error": None,
            },
        ],
        "metrics": {"question_count": 3, "correct_count": 1, "failure_count": 0},
    }


def test_analyze_result_breaks_down_accuracy_confusions_and_risk_terms() -> None:
    analysis = analyze_result(make_result())

    assert analysis["question_type_metrics"] == {
        "condition": {
            "correct_count": 0,
            "exact_match": 0.0,
            "question_count": 2,
        },
        "plant": {
            "correct_count": 1,
            "exact_match": 1.0,
            "question_count": 1,
        },
    }
    assert analysis["confusions"] == [
        {
            "count": 1,
            "expected_answer": "Leaf Mold",
            "normalized_prediction": "leaf spot disease",
            "question_type": "condition",
        },
        {
            "count": 1,
            "expected_answer": "Leaf Mold",
            "normalized_prediction": "tomato leaf curl virus",
            "question_type": "condition",
        },
    ]
    assert analysis["risk_flags"] == [
        {
            "markers": ["virus"],
            "raw_answer": "Tomato leaf curl virus",
            "sample_id": "q-condition-1",
        }
    ]


def test_audit_samples_reports_repeated_questions_pending_status_and_sources() -> None:
    samples = [
        make_sample("q1", "Which plant is shown?", "Tomato", "plant"),
        make_sample("q2", "Which plant is shown?", "Apple", "plant"),
        make_sample("q3", "What condition?", "Leaf Mold", "condition"),
    ]

    audit = audit_samples(samples)

    assert audit["sample_count"] == 3
    assert audit["audit_status_counts"] == {"pending": 3}
    assert audit["source_counts"] == {"plantvillage_label": 3}
    assert audit["repeated_question_count"] == 1
    assert audit["repeated_questions"] == [{"count": 2, "question": "Which plant is shown?"}]
    assert audit["empty_answer_count"] == 0
    assert audit["automated_quality_status"] == "needs_human_audit"


def test_write_analysis_report_and_cli(tmp_path: Path) -> None:
    dataset_path = tmp_path / "vqa.jsonl"
    result_path = tmp_path / "result.json"
    output_json = tmp_path / "analysis.json"
    output_md = tmp_path / "analysis.md"
    write_jsonl(
        dataset_path,
        [make_sample("q1", "Which plant is shown?", "Tomato", "plant")],
    )
    result_path.write_text(json.dumps(make_result()), encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            "scripts/analyze_vlm_results.py",
            "--dataset",
            str(dataset_path),
            "--result",
            str(result_path),
            "--output-json",
            str(output_json),
            "--report",
            str(output_md),
        ],
        cwd=Path(__file__).resolve().parents[2],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(output_json.read_text(encoding="utf-8"))
    assert payload["dataset_audit"]["sample_count"] == 1
    assert payload["result_analyses"][0]["result_path"] == str(result_path)
    report = output_md.read_text(encoding="utf-8")
    assert "VLM Result Analysis" in report
    assert "condition" in report

    rendered = write_analysis_report(payload)
    assert "needs_human_audit" in rendered
