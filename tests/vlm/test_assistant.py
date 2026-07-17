from plantdisease.vlm.assistant import (
    ClassifierContext,
    build_assistant_response,
    is_visual_evidence_question,
)


def test_visual_evidence_policy_allows_morphology_without_diagnosis() -> None:
    assert is_visual_evidence_question(
        "What spots, colors, shapes, margins, textures, and distributions are visible?"
    ) is True


def test_visual_evidence_policy_rejects_diagnosis_and_treatment_requests() -> None:
    assert is_visual_evidence_question("What disease is this?") is False
    assert is_visual_evidence_question("How should I treat this plant?") is False
    assert is_visual_evidence_question("Which fungicide should I spray?") is False


def test_assistant_refuses_pesticide_dosage_requests() -> None:
    response = build_assistant_response(
        "How many ml of fungicide should I spray per liter?",
        classifier_context=ClassifierContext(
            top_class_name="Tomato___Late_blight",
            confidence=0.96,
            warnings=[],
        ),
        vqa_answer="diseased",
        answer_source="qwen3-vl-smoke",
    )

    assert response.refused is True
    assert response.action == "refuse_high_risk"
    assert "dose" in " ".join(response.reasons).lower()
    assert "local plant-health professional" in response.message
    assert response.sources == []


def test_assistant_refuses_low_confidence_classifier_context() -> None:
    response = build_assistant_response(
        "What does this plant likely show?",
        classifier_context=ClassifierContext(
            top_class_name="Tomato___Late_blight",
            confidence=0.42,
            warnings=["Low confidence prediction; do not treat this as definitive."],
        ),
        vqa_answer="diseased",
        answer_source="qwen3-vl-smoke",
    )

    assert response.refused is True
    assert response.action == "refuse_low_confidence"
    assert "low confidence" in response.message.lower()
    assert "cannot provide a disease claim" in response.message


def test_assistant_refuses_unknown_or_non_leaf_context() -> None:
    response = build_assistant_response(
        "Is this disease dangerous?",
        classifier_context=ClassifierContext(
            top_class_name="unknown",
            confidence=0.91,
            warnings=["Non-leaf or out-of-domain image."],
        ),
    )

    assert response.refused is True
    assert response.action == "refuse_out_of_scope"
    assert "outside the verified PlantVillage leaf scope" in response.message


def test_assistant_gives_bounded_educational_answer_with_sources() -> None:
    response = build_assistant_response(
        "What can I learn from this result?",
        classifier_context=ClassifierContext(
            top_class_name="Tomato___Late_blight",
            confidence=0.93,
            warnings=["Educational demo only."],
        ),
        vqa_answer="diseased",
        answer_source="qwen3-vl-short-smoke",
    )

    assert response.refused is False
    assert response.action == "educational_summary"
    assert "Tomato" in response.message
    assert "Late blight" in response.message
    assert "diseased" in response.message
    assert "educational" in response.message.lower()
    assert response.sources == ["classifier:Tomato___Late_blight", "vqa:qwen3-vl-short-smoke"]
