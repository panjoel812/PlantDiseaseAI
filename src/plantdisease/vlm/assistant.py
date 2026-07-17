"""Safety-bounded Week 6 agricultural assistant prototype."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from plantdisease.serving.knowledge import lookup_disease_knowledge

LOW_CONFIDENCE_THRESHOLD = 0.8

_HIGH_RISK_TERMS = (
    "chemical",
    "concentration",
    "dose",
    "dosage",
    "fungicide",
    "herbicide",
    "insecticide",
    "liter",
    "litre",
    "ml",
    "pesticide",
    "ppm",
    "rate",
    "spray",
)
_OUT_OF_SCOPE_WARNING_TERMS = ("non-leaf", "out-of-domain", "outside", "unknown")
_VISUAL_EVIDENCE_TERMS = (
    "appearance",
    "color",
    "colour",
    "discoloration",
    "distribution",
    "edge",
    "lesion",
    "margin",
    "morphology",
    "pattern",
    "shape",
    "spot",
    "texture",
    "visible",
    "斑",
    "颜色",
    "形态",
    "形状",
    "边缘",
    "纹理",
    "分布",
    "可见",
)
_NON_VISUAL_REQUEST_TERMS = (
    "cure",
    "diagnos",
    "disease",
    "healthy",
    "manage",
    "recommend",
    "treat",
    "what is this",
    "病害",
    "诊断",
    "治疗",
    "防治",
    "用药",
    "健康",
)


@dataclass(frozen=True)
class ClassifierContext:
    """Structured classifier context made available to the assistant."""

    top_class_name: str
    confidence: float
    warnings: Sequence[str] = field(default_factory=tuple)


@dataclass(frozen=True)
class AssistantResponse:
    """A bounded assistant answer with explicit action and provenance."""

    message: str
    action: str
    refused: bool
    reasons: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)


def is_visual_evidence_question(question: str) -> bool:
    """Return whether a question requests observation without diagnosis or advice."""

    normalized = question.strip().casefold()
    if not normalized or _contains_any(normalized, _NON_VISUAL_REQUEST_TERMS):
        return False
    if _contains_any(normalized, _HIGH_RISK_TERMS):
        return False
    return _contains_any(normalized, _VISUAL_EVIDENCE_TERMS)


def build_assistant_response(
    question: str,
    *,
    classifier_context: ClassifierContext,
    vqa_answer: str | None = None,
    answer_source: str | None = None,
    low_confidence_threshold: float = LOW_CONFIDENCE_THRESHOLD,
) -> AssistantResponse:
    """Build a safe educational response from classifier and optional VQA context.

    The prototype intentionally avoids prescriptive agricultural actions. It refuses
    pesticide dosage requests, low-confidence disease claims, and inputs outside the
    verified PlantVillage leaf-classification scope.
    """

    if _contains_any(question, _HIGH_RISK_TERMS):
        return AssistantResponse(
            message=(
                "I cannot recommend pesticide, fungicide, spray, dose, or dilution "
                "instructions. Please consult a local plant-health professional or "
                "agricultural extension office and follow local regulations."
            ),
            action="refuse_high_risk",
            refused=True,
            reasons=["Dose or pesticide instructions are high risk and out of scope."],
            sources=[],
        )

    if _is_low_confidence(classifier_context, low_confidence_threshold):
        return AssistantResponse(
            message=(
                "The classifier context is low confidence, so this assistant cannot "
                "provide a disease claim. Use this only as an educational demo and "
                "ask a qualified plant-health professional for diagnosis."
            ),
            action="refuse_low_confidence",
            refused=True,
            reasons=["Low confidence classifier context."],
            sources=_classifier_sources(classifier_context),
        )

    if _is_out_of_scope(classifier_context):
        return AssistantResponse(
            message=(
                "This request is outside the verified PlantVillage leaf scope. The "
                "assistant should not infer a disease for unknown, non-leaf, or "
                "out-of-domain images."
            ),
            action="refuse_out_of_scope",
            refused=True,
            reasons=["Input is outside the verified PlantVillage leaf scope."],
            sources=[],
        )

    knowledge = lookup_disease_knowledge(classifier_context.top_class_name)
    vqa_sentence = (
        f" The VQA smoke answer was `{vqa_answer}`." if vqa_answer is not None else ""
    )
    message = (
        "Educational summary only: the classifier top result is "
        f"{knowledge.plant} / {knowledge.condition} "
        f"({classifier_context.confidence:.1%} confidence).{vqa_sentence} "
        f"{knowledge.symptoms} This is not a professional agricultural diagnosis."
    )
    return AssistantResponse(
        message=message,
        action="educational_summary",
        refused=False,
        reasons=[],
        sources=_classifier_sources(classifier_context)
        + ([f"vqa:{answer_source}"] if answer_source and vqa_answer is not None else []),
    )


def _contains_any(text: str, terms: Sequence[str]) -> bool:
    normalized = text.casefold()
    return any(term in normalized for term in terms)


def _is_low_confidence(context: ClassifierContext, threshold: float) -> bool:
    return context.confidence < threshold or _contains_any(
        " ".join(context.warnings), ("low confidence",)
    )


def _is_out_of_scope(context: ClassifierContext) -> bool:
    class_name = context.top_class_name.strip()
    if not class_name or class_name.casefold() == "unknown" or "___" not in class_name:
        return True
    return _contains_any(" ".join(context.warnings), _OUT_OF_SCOPE_WARNING_TERMS)


def _classifier_sources(context: ClassifierContext) -> list[str]:
    class_name = context.top_class_name.strip()
    return [f"classifier:{class_name}"] if class_name else []
