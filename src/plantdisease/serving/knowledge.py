"""Small educational disease knowledge cards for demo predictions."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DiseaseKnowledge:
    class_name: str
    plant: str
    condition: str
    is_healthy: bool
    symptoms: str
    educational_note: str


_SYMPTOMS_BY_CONDITION = {
    "apple scab": (
        "Often associated with dark, scabby leaf or fruit lesions in susceptible apple "
        "cultivars."
    ),
    "early blight": (
        "Often associated with concentric brown leaf spots, yellowing tissue, and older "
        "leaf decline."
    ),
    "late blight": (
        "Often associated with irregular leaf lesions that can expand quickly under cool, "
        "humid conditions."
    ),
    "healthy": "The image is mapped to the healthy class in this closed-set dataset.",
}

_EDUCATIONAL_NOTE = (
    "Educational summary only. Confirm symptoms with local agricultural extension or a "
    "qualified plant-health professional before making management decisions."
)


def lookup_disease_knowledge(class_name: str) -> DiseaseKnowledge:
    """Return a compact, non-prescriptive knowledge card for a predicted class."""
    plant, condition = _parse_plantvillage_label(class_name)
    condition_key = condition.lower()
    is_healthy = condition_key == "healthy"
    symptoms = _SYMPTOMS_BY_CONDITION.get(
        condition_key,
        "No curated disease note is available for this class yet.",
    )
    return DiseaseKnowledge(
        class_name=class_name,
        plant=plant,
        condition=condition,
        is_healthy=is_healthy,
        symptoms=symptoms,
        educational_note=_EDUCATIONAL_NOTE,
    )


def _parse_plantvillage_label(class_name: str) -> tuple[str, str]:
    if "___" not in class_name:
        return "Unknown", _clean_label(class_name)
    plant, condition = class_name.split("___", maxsplit=1)
    return _clean_label(plant), _clean_label(condition)


def _clean_label(value: str) -> str:
    return value.replace("_", " ").strip() or "Unknown"
