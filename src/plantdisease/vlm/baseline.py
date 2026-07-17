"""Fixed-set VLM smoke-baseline execution and PlantVillage image resolution."""

from __future__ import annotations

import json
import platform
import re
import sys
import unicodedata
from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any

from PIL import Image

from plantdisease.data.huggingface import load_plantvillage_dataset_splits
from plantdisease.vlm.backends import VLMBackend, VLMSetupError
from plantdisease.vlm.schema import (
    VQA_SPLITS,
    VQASample,
    assert_entity_split_integrity,
    read_jsonl,
)

ImageLoader = Callable[[tuple[str, ...], Path | None], Mapping[str, object]]
PROMPT_STYLES = frozenset({"choice", "few_shot_choice", "original", "short"})
CHOICE_PROMPT_STYLES = frozenset({"choice", "few_shot_choice"})


def normalize_answer(answer: str) -> str:
    """Normalize a closed-question answer for exact-match scoring."""

    normalized = unicodedata.normalize("NFKC", answer).casefold()
    words = "".join(character if character.isalnum() else " " for character in normalized)
    return " ".join(words.split())


def format_prompt(
    sample: VQASample,
    prompt_style: str = "original",
    *,
    all_samples: Sequence[VQASample] | None = None,
    few_shot_count: int = 2,
) -> str:
    """Format one VQA prompt for the selected zero-shot baseline style."""

    _validate_prompt_style(prompt_style)
    if prompt_style == "original":
        return sample.question

    instruction_by_type = {
        "plant": "Answer with exactly one plant/crop label and no explanation.",
        "condition": "Answer with exactly one disease/condition label and no explanation.",
        "health_status": "Answer with exactly one word: healthy or diseased.",
    }
    instruction = instruction_by_type.get(
        sample.question_type,
        "Answer with exactly one short label and no explanation.",
    )
    if prompt_style == "short":
        return f"{instruction}\nQuestion: {sample.question}\nShort answer:"

    choices = build_answer_choices(sample, all_samples or (sample,))
    options = _format_choices(choices)
    choice_instruction = (
        "Choose exactly one option from the list. Answer with only the option text "
        "and no explanation."
    )
    if prompt_style == "choice":
        return (
            f"{choice_instruction}\n"
            f"Options:\n{options}\n"
            f"Question: {sample.question}\n"
            "Answer:"
        )

    examples = build_few_shot_examples(
        sample,
        all_samples or (sample,),
        max_examples=few_shot_count,
    )
    lines = [choice_instruction]
    if examples:
        lines.append("Examples from other training images:")
        for index, example in enumerate(examples, start=1):
            lines.extend(
                [
                    f"Example {index}:",
                    f"Question: {example.question}",
                    f"Options:\n{options}",
                    f"Answer: {example.answer}",
                ]
            )
    lines.extend(
        [
            "Now answer for the current image.",
            f"Options:\n{options}",
            f"Question: {sample.question}",
            "Answer:",
        ]
    )
    return "\n".join(lines)


def build_answer_choices(
    sample: VQASample,
    all_samples: Sequence[VQASample],
) -> list[str]:
    """Build a stable closed-answer choice list for one question type."""

    choices_by_normalized: dict[str, str] = {}
    for candidate in all_samples:
        if candidate.question_type != sample.question_type:
            continue
        normalized = normalize_answer(candidate.answer)
        choices_by_normalized.setdefault(normalized, candidate.answer)

    expected_normalized = normalize_answer(sample.answer)
    choices_by_normalized.setdefault(expected_normalized, sample.answer)
    return [
        choices_by_normalized[normalized]
        for normalized in sorted(choices_by_normalized)
        if normalized
    ]


def build_few_shot_examples(
    sample: VQASample,
    all_samples: Sequence[VQASample],
    *,
    max_examples: int = 2,
) -> list[VQASample]:
    """Select deterministic train-split text examples without target-image leakage."""

    if max_examples <= 0:
        return []
    examples = [
        candidate
        for candidate in all_samples
        if candidate.split == "train"
        and candidate.question_type == sample.question_type
        and candidate.image_id != sample.image_id
    ]
    examples.sort(key=lambda candidate: candidate.sample_id)
    return examples[:max_examples]


def match_choice_answer(raw_answer: str, choices: Sequence[str]) -> str | None:
    """Return the matched choice text for an option-style answer, if unambiguous."""

    normalized_raw = normalize_answer(raw_answer)
    if not normalized_raw:
        return None
    for index, choice in enumerate(choices):
        label = _choice_label(index).casefold()
        normalized_choice = normalize_answer(choice)
        accepted = {
            normalized_choice,
            label,
            f"option {label}",
            f"{label} {normalized_choice}",
            f"option {label} {normalized_choice}",
        }
        if normalized_raw in accepted or normalized_raw.startswith(f"{normalized_choice} "):
            return choice
    return None


def resolve_plantvillage_images(
    image_refs: Sequence[str], cache_dir: Path | None
) -> dict[str, object]:
    """Resolve Hugging Face PlantVillage references to in-memory images."""

    reference_pattern = re.compile(r"hf-test-(\d+)")
    unique_refs = sorted(set(image_refs))
    indices: dict[str, int] = {}
    for image_ref in unique_refs:
        match = reference_pattern.fullmatch(image_ref)
        if match is None:
            raise ValueError(f"image_ref must match 'hf-test-<index>', got {image_ref!r}")
        indices[image_ref] = int(match.group(1))
    if not unique_refs:
        return {}

    splits, _class_names = load_plantvillage_dataset_splits(cache_dir)
    if "test" not in splits:
        raise ValueError(f"PlantVillage dataset does not expose a test split: {list(splits)}")
    test_split = splits["test"]

    resolved: dict[str, object] = {}
    for image_ref, index in sorted(indices.items(), key=lambda item: item[1]):
        if index >= len(test_split):
            raise ValueError(
                f"image_ref {image_ref!r} is outside PlantVillage test split "
                f"with {len(test_split)} samples"
            )
        image = test_split[index]["image"]
        if not isinstance(image, Image.Image):
            raise ValueError(
                f"PlantVillage image {image_ref!r} decoded to {type(image).__name__}, "
                "expected PIL.Image.Image"
            )
        resolved[image_ref] = image.convert("RGB")
    return resolved


def run_baseline(
    dataset_path: str | Path,
    output_path: str | Path,
    backend: VLMBackend,
    *,
    split: str = "test",
    cache_dir: Path | None = None,
    image_loader: ImageLoader = resolve_plantvillage_images,
    command: Sequence[str] | None = None,
    prompt_style: str = "original",
) -> dict[str, Any]:
    """Run a fixed VQA split and save machine-readable results."""

    if split not in VQA_SPLITS:
        options = ", ".join(sorted(VQA_SPLITS))
        raise ValueError(f"split must be one of: {options}; got {split!r}")
    _validate_prompt_style(prompt_style)

    samples = read_jsonl(dataset_path)
    assert_entity_split_integrity(samples)
    selected = [sample for sample in samples if sample.split == split]
    if not selected:
        raise ValueError(f"VQA dataset has no samples in split {split!r}")

    image_refs = tuple(sorted({sample.image_ref for sample in selected}))
    images = dict(image_loader(image_refs, cache_dir))
    missing_refs = sorted(set(image_refs) - set(images))
    if missing_refs:
        raise ValueError(f"image loader did not resolve references: {missing_refs}")

    started_at = datetime.now(UTC)
    started_timer = perf_counter()
    records: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    correct_count = 0

    for sample in selected:
        record_started = perf_counter()
        raw_answer: str | None = None
        normalized_prediction: str | None = None
        matched_choice: str | None = None
        answer_choices = (
            build_answer_choices(sample, samples) if prompt_style in CHOICE_PROMPT_STYLES else []
        )
        is_match = False
        error: str | None = None
        prompt = format_prompt(sample, prompt_style, all_samples=samples)
        try:
            raw_answer = backend.generate(images[sample.image_ref], prompt)
            if answer_choices:
                matched_choice = match_choice_answer(raw_answer, answer_choices)
            normalized_prediction = normalize_answer(matched_choice or raw_answer)
            is_match = normalized_prediction == normalize_answer(sample.answer)
            correct_count += int(is_match)
        except VLMSetupError:
            raise
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
            failures.append({"sample_id": sample.sample_id, "error": error})

        records.append(
            {
                "sample_id": sample.sample_id,
                "image_id": sample.image_id,
                "image_ref": sample.image_ref,
                "question_type": sample.question_type,
                "source": sample.source,
                "audit_status": sample.audit_status,
                "original_question": sample.question,
                "prompt": prompt,
                "prompt_style": prompt_style,
                "expected_answer": sample.answer,
                "raw_answer": raw_answer,
                "answer_choices": answer_choices,
                "matched_choice": matched_choice,
                "normalized_expected_answer": normalize_answer(sample.answer),
                "normalized_answer": normalized_prediction,
                "normalized_exact_match": is_match,
                "duration_seconds": perf_counter() - record_started,
                "error": error,
            }
        )

    duration_seconds = perf_counter() - started_timer
    finished_at = datetime.now(UTC)
    question_count = len(selected)
    backend_name = type(backend).__name__
    model_id = getattr(backend, "model_id", None)
    result: dict[str, Any] = {
        "schema_version": 1,
        "run_id": f"{started_at:%Y%m%d-%H%M%S}-vlm-zero-shot-smoke",
        "status": "completed" if not failures else "completed_with_failures",
        "run_scope": "zero_shot_smoke_baseline",
        "split": split,
        "prompt_style": prompt_style,
        "backend": backend_name,
        "model_id": model_id,
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "duration_seconds": duration_seconds,
        "command": list(command) if command is not None else None,
        "environment": _environment_metadata(),
        "dataset": {
            "path": str(Path(dataset_path)),
            "selected_question_count": question_count,
            "unique_image_count": len(image_refs),
        },
        "metrics": {
            "normalized_exact_match": correct_count / question_count,
            "correct_count": correct_count,
            "failure_count": len(failures),
            "question_count": question_count,
        },
        "records": records,
        "failures": failures,
    }
    _write_result(output_path, result)
    return result


def write_skipped_baseline(
    output_path: str | Path,
    reason: str,
    *,
    split: str,
    backend_name: str,
    model_id: str | None,
    command: Sequence[str] | None = None,
    prompt_style: str = "original",
) -> dict[str, Any]:
    """Record an explicit skipped smoke run without loading data or model weights."""

    if not reason.strip():
        raise ValueError("skip reason must be non-empty")
    _validate_prompt_style(prompt_style)
    now = datetime.now(UTC)
    result: dict[str, Any] = {
        "schema_version": 1,
        "run_id": f"{now:%Y%m%d-%H%M%S}-vlm-zero-shot-smoke",
        "status": "skipped",
        "reason": reason,
        "run_scope": "zero_shot_smoke_baseline",
        "split": split,
        "prompt_style": prompt_style,
        "backend": backend_name,
        "model_id": model_id,
        "started_at": now.isoformat(),
        "finished_at": now.isoformat(),
        "duration_seconds": 0.0,
        "command": list(command) if command is not None else None,
        "environment": _environment_metadata(),
        "dataset": None,
        "metrics": None,
        "records": [],
        "failures": [],
    }
    _write_result(output_path, result)
    return result


def _environment_metadata() -> dict[str, str]:
    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "system": platform.system(),
        "machine": platform.machine(),
        "runtime": "MLX/Metal" if platform.system() == "Darwin" else "unsupported",
    }


def _write_result(output_path: str | Path, result: Mapping[str, Any]) -> None:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _validate_prompt_style(prompt_style: str) -> None:
    if prompt_style not in PROMPT_STYLES:
        options = ", ".join(sorted(PROMPT_STYLES))
        raise ValueError(f"prompt_style must be one of: {options}; got {prompt_style!r}")


def _format_choices(choices: Sequence[str]) -> str:
    return "\n".join(f"{_choice_label(index)}. {choice}" for index, choice in enumerate(choices))


def _choice_label(index: int) -> str:
    if index < 26:
        return chr(ord("A") + index)
    return str(index + 1)
