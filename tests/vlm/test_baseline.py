import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
from PIL import Image

import plantdisease.vlm.baseline as baseline_module
from plantdisease.vlm.backends import MockVLMBackend
from plantdisease.vlm.baseline import (
    format_prompt,
    normalize_answer,
    resolve_plantvillage_images,
    run_baseline,
)
from plantdisease.vlm.schema import VQASample, write_jsonl


def make_sample(
    sample_id: str,
    image_id: str,
    image_ref: str,
    question: str,
    answer: str,
    *,
    split: str = "test",
    question_type: str = "plant",
) -> VQASample:
    return VQASample(
        sample_id=sample_id,
        image_id=image_id,
        image_ref=image_ref,
        question=question,
        answer=answer,
        question_type=question_type,
        source="plantvillage_label",
        split=split,
        audit_status="passed",
    )


def test_normalize_answer_supports_closed_question_exact_match() -> None:
    assert normalize_answer("  Leaf-Mold.\n") == "leaf mold"
    assert normalize_answer("Corn (maize)") == "corn maize"


def test_run_baseline_selects_split_and_resolves_each_unique_image_once(
    tmp_path: Path,
) -> None:
    dataset_path = tmp_path / "vqa.jsonl"
    output_path = tmp_path / "result.json"
    cache_dir = tmp_path / "cache"
    samples = [
        make_sample("q1", "image-1", "hf-test-1", "Plant one?", "Apple"),
        make_sample("q2", "image-1", "hf-test-1", "Status one?", "healthy"),
        make_sample("q3", "image-2", "hf-test-2", "Plant two?", "Tomato"),
        make_sample(
            "q4",
            "image-3",
            "hf-test-3",
            "Validation only?",
            "ignored",
            split="validation",
        ),
    ]
    write_jsonl(dataset_path, samples)
    images = {
        "hf-test-1": Image.new("RGB", (4, 4), "red"),
        "hf-test-2": Image.new("RGB", (4, 4), "green"),
    }
    loader_calls: list[tuple[tuple[str, ...], Path | None]] = []

    def image_loader(
        image_refs: tuple[str, ...], actual_cache_dir: Path | None
    ) -> dict[str, object]:
        loader_calls.append((image_refs, actual_cache_dir))
        return images

    backend = MockVLMBackend(
        {
            "Plant one?": " apple. ",
            "Status one?": "diseased",
            "Plant two?": "Tomato",
        }
    )

    result = run_baseline(
        dataset_path,
        output_path,
        backend,
        split="test",
        cache_dir=cache_dir,
        image_loader=image_loader,
        command=["python", "scripts/run_vlm_baseline.py"],
    )

    assert loader_calls == [(('hf-test-1', 'hf-test-2'), cache_dir)]
    assert backend.calls == [
        (images["hf-test-1"], "Plant one?"),
        (images["hf-test-1"], "Status one?"),
        (images["hf-test-2"], "Plant two?"),
    ]
    assert result["status"] == "completed"
    assert result["run_scope"] == "zero_shot_smoke_baseline"
    assert result["split"] == "test"
    assert result["backend"] == "MockVLMBackend"
    assert result["dataset"]["selected_question_count"] == 3
    assert result["dataset"]["unique_image_count"] == 2
    assert result["metrics"] == {
        "normalized_exact_match": pytest.approx(2 / 3),
        "correct_count": 2,
        "failure_count": 0,
        "question_count": 3,
    }
    assert result["records"][0]["expected_answer"] == "Apple"
    assert result["records"][0]["raw_answer"] == " apple. "
    assert result["records"][0]["normalized_exact_match"] is True
    assert result["records"][1]["normalized_exact_match"] is False
    assert result["records"][0]["prompt"] == "Plant one?"
    assert result["command"] == ["python", "scripts/run_vlm_baseline.py"]
    assert result["environment"]["python"]
    assert result["duration_seconds"] >= 0
    assert json.loads(output_path.read_text(encoding="utf-8")) == result


def test_run_baseline_records_generation_failures_without_changing_ground_truth(
    tmp_path: Path,
) -> None:
    dataset_path = tmp_path / "vqa.jsonl"
    output_path = tmp_path / "result.json"
    write_jsonl(
        dataset_path,
        [make_sample("q1", "image-1", "hf-test-1", "Plant?", "Apple")],
    )

    class FailingBackend:
        def generate(self, image: object, question: str) -> str:
            raise RuntimeError("generation failed")

    result = run_baseline(
        dataset_path,
        output_path,
        FailingBackend(),
        image_loader=lambda _refs, _cache_dir: {"hf-test-1": object()},
    )

    assert result["status"] == "completed_with_failures"
    assert result["metrics"]["failure_count"] == 1
    assert result["metrics"]["normalized_exact_match"] == 0.0
    assert result["records"][0]["expected_answer"] == "Apple"
    assert result["records"][0]["raw_answer"] is None
    assert result["records"][0]["error"] == "RuntimeError: generation failed"
    assert result["failures"] == [
        {"sample_id": "q1", "error": "RuntimeError: generation failed"}
    ]


def test_run_baseline_short_prompt_style_requests_label_only_answers(tmp_path: Path) -> None:
    dataset_path = tmp_path / "vqa.jsonl"
    output_path = tmp_path / "result.json"
    sample = make_sample(
        "q1",
        "image-1",
        "hf-test-1",
        "Which plant is shown according to the PlantVillage label?",
        "Tomato",
        question_type="plant",
    )
    write_jsonl(dataset_path, [sample])

    expected_prompt = (
        "Answer with exactly one plant/crop label and no explanation.\n"
        "Question: Which plant is shown according to the PlantVillage label?\n"
        "Short answer:"
    )
    backend = MockVLMBackend({expected_prompt: "Tomato"})
    image = object()

    result = run_baseline(
        dataset_path,
        output_path,
        backend,
        image_loader=lambda _refs, _cache_dir: {"hf-test-1": image},
        prompt_style="short",
    )

    assert backend.calls == [(image, expected_prompt)]
    assert result["prompt_style"] == "short"
    assert result["records"][0]["original_question"] == sample.question
    assert result["records"][0]["prompt"] == expected_prompt
    assert result["records"][0]["prompt_style"] == "short"
    assert result["metrics"]["correct_count"] == 1


def test_choice_prompt_style_lists_candidate_answers_and_matches_option_letters(
    tmp_path: Path,
) -> None:
    dataset_path = tmp_path / "vqa.jsonl"
    output_path = tmp_path / "result.json"
    samples = [
        make_sample(
            "train-apple",
            "image-train-1",
            "hf-test-1",
            "Which plant is shown according to the PlantVillage label?",
            "Apple",
            split="train",
            question_type="plant",
        ),
        make_sample(
            "test-tomato",
            "image-test-1",
            "hf-test-2",
            "Which plant is shown according to the PlantVillage label?",
            "Tomato",
            split="test",
            question_type="plant",
        ),
    ]
    write_jsonl(dataset_path, samples)
    expected_prompt = format_prompt(samples[1], "choice", all_samples=samples)
    backend = MockVLMBackend({expected_prompt: "B. Tomato"})

    result = run_baseline(
        dataset_path,
        output_path,
        backend,
        image_loader=lambda _refs, _cache_dir: {"hf-test-2": object()},
        prompt_style="choice",
    )

    assert "Options:" in expected_prompt
    assert "A. Apple" in expected_prompt
    assert "B. Tomato" in expected_prompt
    assert result["records"][0]["answer_choices"] == ["Apple", "Tomato"]
    assert result["records"][0]["matched_choice"] == "Tomato"
    assert result["records"][0]["normalized_answer"] == "tomato"
    assert result["metrics"]["correct_count"] == 1


def test_few_shot_choice_prompt_uses_train_examples_without_test_leakage() -> None:
    samples = [
        make_sample(
            "train-leaf-mold",
            "image-train-1",
            "hf-test-1",
            "What labeled condition does this PlantVillage image show?",
            "Leaf Mold",
            split="train",
            question_type="condition",
        ),
        make_sample(
            "validation-healthy",
            "image-validation-1",
            "hf-test-2",
            "What labeled condition does this PlantVillage image show?",
            "healthy",
            split="validation",
            question_type="condition",
        ),
        make_sample(
            "test-target-spot",
            "image-test-1",
            "hf-test-3",
            "What labeled condition does this PlantVillage image show?",
            "Target Spot",
            split="test",
            question_type="condition",
        ),
    ]

    prompt = format_prompt(samples[2], "few_shot_choice", all_samples=samples)

    assert "Examples from other training images:" in prompt
    assert "Leaf Mold" in prompt
    assert "Target Spot" in prompt
    assert "validation-healthy" not in prompt
    assert "test-target-spot" not in prompt
    assert prompt.count("Answer:") == 2


def test_resolver_loads_hf_test_images_once_and_keeps_them_in_memory(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    images = [Image.new("RGB", (4, 4), "red") for _ in range(3)]

    class FakeSplit:
        def __init__(self) -> None:
            self.requested: list[int] = []

        def __len__(self) -> int:
            return len(images)

        def __getitem__(self, index: int) -> dict[str, Any]:
            self.requested.append(index)
            return {"image": images[index], "label": 0}

    split = FakeSplit()
    adapter_calls: list[Path | None] = []

    def fake_load_splits(cache_dir: Path | None = None):
        adapter_calls.append(cache_dir)
        return {"test": split}, ["Apple___healthy"]

    monkeypatch.setattr(
        baseline_module,
        "load_plantvillage_dataset_splits",
        fake_load_splits,
    )

    resolved = resolve_plantvillage_images(
        ("hf-test-2", "hf-test-1", "hf-test-2"),
        tmp_path / "cache",
    )

    assert adapter_calls == [tmp_path / "cache"]
    assert split.requested == [1, 2]
    assert set(resolved) == {"hf-test-1", "hf-test-2"}
    assert all(isinstance(image, Image.Image) for image in resolved.values())
    assert all(not isinstance(image, (str, Path)) for image in resolved.values())


def test_resolver_rejects_non_hf_test_reference_without_loading_data(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called = False

    def fake_load_splits(cache_dir: Path | None = None):
        nonlocal called
        called = True
        return {}, []

    monkeypatch.setattr(
        baseline_module,
        "load_plantvillage_dataset_splits",
        fake_load_splits,
    )

    with pytest.raises(ValueError, match="hf-test"):
        resolve_plantvillage_images(("local-image.png",), None)
    assert called is False


def test_cli_can_record_explicit_skip_without_loading_model(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[2]
    output_path = tmp_path / "skipped.json"

    completed = subprocess.run(
        [
            sys.executable,
            str(project_root / "scripts/run_vlm_baseline.py"),
            "--output",
            str(output_path),
            "--prompt-style",
            "short",
            "--skip-reason",
            "model download not approved",
        ],
        cwd=project_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    result = json.loads(output_path.read_text(encoding="utf-8"))
    assert result["status"] == "skipped"
    assert result["reason"] == "model download not approved"
    assert result["run_scope"] == "zero_shot_smoke_baseline"
    assert result["prompt_style"] == "short"
    assert result["backend"] == "MLXVLMBackend"
    assert result["model_id"] == "mlx-community/Qwen3-VL-4B-Instruct-4bit"
    assert result["records"] == []
    assert result["metrics"] is None
