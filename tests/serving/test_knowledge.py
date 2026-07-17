from plantdisease.serving.knowledge import lookup_disease_knowledge


def test_lookup_disease_knowledge_parses_common_plantvillage_label() -> None:
    knowledge = lookup_disease_knowledge("Tomato___Late_blight")

    assert knowledge.plant == "Tomato"
    assert knowledge.condition == "Late blight"
    assert knowledge.is_healthy is False
    assert "leaf" in knowledge.symptoms.lower()
    assert "educational" in knowledge.educational_note.lower()


def test_lookup_disease_knowledge_handles_healthy_and_unknown_labels() -> None:
    healthy = lookup_disease_knowledge("Apple___healthy")
    unknown = lookup_disease_knowledge("Unmapped_Class")

    assert healthy.is_healthy is True
    assert healthy.condition == "healthy"
    assert "healthy" in healthy.symptoms.lower()
    assert unknown.plant == "Unknown"
    assert unknown.condition == "Unmapped Class"
    assert "No curated" in unknown.symptoms
