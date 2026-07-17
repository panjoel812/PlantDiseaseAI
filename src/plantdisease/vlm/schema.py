"""Schema helpers for PlantDiseaseAI VQA records."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

VQA_SCHEMA_VERSION = 1
VQA_SPLITS = frozenset({"train", "validation", "test"})
VQA_AUDIT_STATUSES = frozenset({"pending", "passed", "failed", "needs_review"})
VQA_SOURCES = frozenset({"plantvillage_label", "knowledge_card", "classifier_context"})
VQA_QUESTION_TYPES = frozenset(
    {"plant", "condition", "health_status", "symptom", "safety", "diagnosis_context"}
)


@dataclass(frozen=True)
class VQASample:
    """A single source-grounded visual question-answer sample."""

    sample_id: str
    image_id: str
    image_ref: str
    question: str
    answer: str
    question_type: str
    source: str
    split: str
    audit_status: str
    schema_version: int = VQA_SCHEMA_VERSION
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_non_empty("sample_id", self.sample_id)
        _require_non_empty("image_id", self.image_id)
        _require_non_empty("image_ref", self.image_ref)
        _require_non_empty("question", self.question)
        _require_non_empty("answer", self.answer)
        _require_allowed("split", self.split, VQA_SPLITS)
        _require_allowed("audit_status", self.audit_status, VQA_AUDIT_STATUSES)
        _require_allowed("source", self.source, VQA_SOURCES)
        _require_allowed("question_type", self.question_type, VQA_QUESTION_TYPES)
        if self.schema_version != VQA_SCHEMA_VERSION:
            msg = f"schema_version must be {VQA_SCHEMA_VERSION}, got {self.schema_version}"
            raise ValueError(msg)

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> VQASample:
        """Build a sample from a JSON-compatible mapping."""

        return cls(
            schema_version=int(data.get("schema_version", VQA_SCHEMA_VERSION)),
            sample_id=str(data["sample_id"]),
            image_id=str(data["image_id"]),
            image_ref=str(data["image_ref"]),
            question=str(data["question"]),
            answer=str(data["answer"]),
            question_type=str(data["question_type"]),
            source=str(data["source"]),
            split=str(data["split"]),
            audit_status=str(data["audit_status"]),
            metadata=dict(data.get("metadata", {})),
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible representation."""

        return asdict(self)


def write_jsonl(path: str | Path, samples: Sequence[VQASample]) -> None:
    """Write VQA samples to UTF-8 JSONL."""

    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for sample in samples:
            handle.write(json.dumps(sample.to_dict(), ensure_ascii=False, sort_keys=True))
            handle.write("\n")


def read_jsonl(path: str | Path) -> list[VQASample]:
    """Read VQA samples from UTF-8 JSONL."""

    samples: list[VQASample] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                msg = f"Invalid JSONL at line {line_number}: {exc}"
                raise ValueError(msg) from exc
            samples.append(VQASample.from_mapping(payload))
    return samples


def assert_entity_split_integrity(samples: Iterable[VQASample]) -> None:
    """Raise if questions for one image appear in multiple splits."""

    image_to_split: dict[str, str] = {}
    for sample in samples:
        previous_split = image_to_split.setdefault(sample.image_id, sample.split)
        if previous_split != sample.split:
            msg = (
                f"image_id {sample.image_id!r} appears in multiple splits: "
                f"{previous_split!r} and {sample.split!r}"
            )
            raise ValueError(msg)


def _require_non_empty(field_name: str, value: str) -> None:
    if not value.strip():
        msg = f"{field_name} must be a non-empty string"
        raise ValueError(msg)


def _require_allowed(field_name: str, value: str, allowed: frozenset[str]) -> None:
    if value not in allowed:
        options = ", ".join(sorted(allowed))
        msg = f"{field_name} must be one of: {options}; got {value!r}"
        raise ValueError(msg)
