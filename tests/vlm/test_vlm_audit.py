import json
import subprocess
import sys
from pathlib import Path

from plantdisease.vlm.audit import build_audit_entries, write_audit_markdown
from plantdisease.vlm.schema import VQASample, write_jsonl


def make_sample(sample_id: str, question: str, answer: str) -> VQASample:
    return VQASample(
        sample_id=sample_id,
        image_id=f"image-{sample_id}",
        image_ref="hf-test-1",
        question=question,
        answer=answer,
        question_type="condition",
        source="plantvillage_label",
        split="test",
        audit_status="pending",
    )


def test_build_audit_entries_marks_pending_review_and_model_risk_hints() -> None:
    samples = [
        make_sample("q1", "What condition?", "Leaf Mold"),
        make_sample("q2", "What condition?", "healthy"),
    ]
    analysis = {
        "result_analyses": [
            {
                "risk_flags": [
                    {
                        "sample_id": "q1",
                        "markers": ["virus"],
                        "raw_answer": "Tomato leaf curl virus",
                    }
                ],
                "error_records": [
                    {
                        "sample_id": "q1",
                        "normalized_prediction": "tomato leaf curl virus",
                    }
                ],
            }
        ]
    }

    entries = build_audit_entries(samples, analysis)

    assert entries[0]["sample_id"] == "q1"
    assert entries[0]["review_status"] == "pending_human_review"
    assert entries[0]["model_risk_markers"] == ["virus"]
    assert entries[0]["model_prediction_hint"] == "tomato leaf curl virus"
    assert entries[0]["checks"] == {
        "answer_traceable_to_source": None,
        "answer_unambiguous": None,
        "language_quality_ok": None,
        "question_not_duplicate_problem": None,
    }
    assert entries[1]["model_risk_markers"] == []


def test_write_audit_markdown_and_cli(tmp_path: Path) -> None:
    dataset_path = tmp_path / "vqa.jsonl"
    analysis_path = tmp_path / "analysis.json"
    output_json = tmp_path / "audit.json"
    output_md = tmp_path / "audit.md"
    write_jsonl(dataset_path, [make_sample("q1", "What condition?", "Leaf Mold")])
    analysis_path.write_text(json.dumps({"result_analyses": []}), encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            "scripts/build_vqa_audit_template.py",
            "--dataset",
            str(dataset_path),
            "--analysis",
            str(analysis_path),
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
    assert payload["status"] == "pending_human_review"
    assert payload["entry_count"] == 1
    report = output_md.read_text(encoding="utf-8")
    assert "Manual VQA Audit Template" in report
    assert "pending_human_review" in report

    rendered = write_audit_markdown(payload)
    assert "What condition?" in rendered
