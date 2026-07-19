from __future__ import annotations

from io import BytesIO
from pathlib import Path
from types import SimpleNamespace

import pytest
import torch
from PIL import Image, ImageDraw
from torch import nn

from plantdisease.inference import Prediction
from plantdisease.openworld.index import OpenSetDecision
from plantdisease.openworld.leaf_pipeline import TargetPoint, isolate_leaf
from plantdisease.serving.abiotic import CornAbioticEvidence
from plantdisease.serving.images import InputValidationError
from plantdisease.serving.service import (
    InferenceService,
    InferenceServiceError,
    LeafSelectionRequiredError,
)


class TinyGradCamModel(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.conv = nn.Conv2d(3, 3, kernel_size=1, bias=False)
        self.pool = nn.AdaptiveAvgPool2d((1, 1))
        self.classifier = nn.Linear(3, 3)
        self.forward_calls = 0
        with torch.no_grad():
            self.conv.weight.zero_()
            self.conv.weight[0, 0, 0, 0] = 0.10
            self.conv.weight[1, 1, 0, 0] = 0.20
            self.conv.weight[2, 2, 0, 0] = 0.30
            self.classifier.weight.copy_(torch.eye(3))
            self.classifier.bias.copy_(torch.tensor([0.0, 2.0, 1.0]))

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        self.forward_calls += 1
        features = torch.relu(self.conv(inputs))
        pooled = self.pool(features).flatten(1)
        return self.classifier(pooled)


class BadShapeModel(nn.Module):
    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        return torch.ones(inputs.shape[0])


class HierarchicalModel(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.logits = nn.Parameter(torch.log(torch.tensor([0.34, 0.15, 0.16, 0.21, 0.14])))
        self.forward_calls = 0
        self.last_inputs: torch.Tensor | None = None

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        self.forward_calls += 1
        self.last_inputs = inputs.detach().cpu().clone()
        return self.logits.unsqueeze(0).expand(inputs.shape[0], -1)


def _image_bytes(size: tuple[int, int] = (40, 40)) -> bytes:
    buffer = BytesIO()
    Image.new("RGB", size, (64, 128, 32)).save(buffer, format="PNG")
    return buffer.getvalue()


def _service(
    model: nn.Module | None = None,
    *,
    confidence_warning_threshold: float = 0.80,
    max_upload_bytes: int = 10 * 1024 * 1024,
) -> InferenceService:
    model = model or TinyGradCamModel()
    return InferenceService(
        model=model,
        class_names=[
            "Apple___healthy",
            "Tomato___Late_blight",
            "Potato___Early_blight",
        ],
        config={"model_name": "tiny", "image_size": 32},
        checkpoint_path=Path("outputs/example/checkpoint.pt"),
        device=torch.device("cpu"),
        target_layer=model.conv if isinstance(model, TinyGradCamModel) else None,
        target_layer_name="conv" if isinstance(model, TinyGradCamModel) else None,
        checkpoint_id="tiny-checkpoint",
        confidence_warning_threshold=confidence_warning_threshold,
        max_upload_bytes=max_upload_bytes,
    )


def _hierarchy_service(model: HierarchicalModel) -> InferenceService:
    return InferenceService(
        model=model,
        class_names=[
            "Apple___Black_rot",
            "Grape___Black_rot",
            "Apple___healthy",
            "Grape___Leaf_blight",
            "Tomato___healthy",
        ],
        config={"model_name": "hierarchical", "image_size": 32},
        checkpoint_path=Path("outputs/example/checkpoint.pt"),
        device=torch.device("cpu"),
        checkpoint_id="hierarchical-checkpoint",
        crop_confidence_threshold=0.45,
    )


def _abiotic_evidence(*, suspected: bool) -> CornAbioticEvidence:
    return CornAbioticEvidence(
        method="opencv_corn_midrib_stress_v1",
        status=(
            "suspected_abiotic_nutrient_stress"
            if suspected
            else "unknown_visible_stress"
        ),
        suspected=suspected,
        abnormal_coverage_percent=18.0 if suspected else 2.0,
        central_axis_share=0.72 if suspected else 0.20,
        longitudinal_continuity=0.81 if suspected else 0.30,
        bilateral_similarity=0.68 if suspected else 0.25,
        off_axis_lesion_coverage_percent=1.2 if suspected else 7.0,
        abnormal_coverage_threshold=8.0,
        central_axis_share_threshold=0.55,
        longitudinal_continuity_threshold=0.60,
        bilateral_similarity_threshold=0.50,
        off_axis_lesion_coverage_threshold=5.0,
        reason=(
            "Compatible with abiotic stress; cannot identify a specific nutrient."
            if suspected
            else "Unknown visible stress."
        ),
        evidence_boundary="Morphology evidence only.",
        overlay=Image.new("RGB", (32, 32), (42, 96, 58)),
    )


def _corn_service() -> InferenceService:
    model = TinyGradCamModel()
    service = InferenceService(
        model=model,
        class_names=[
            "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot",
            "Corn_(maize)___healthy",
            "Tomato___Late_blight",
        ],
        config={"model_name": "tiny", "image_size": 32},
        checkpoint_path=Path("outputs/example/checkpoint.pt"),
        device=torch.device("cpu"),
        target_layer=model.conv,
        target_layer_name="conv",
        checkpoint_id="corn-checkpoint",
    )
    service.crop_classifier = SimpleNamespace(
        input_preprocessing="opencv_exg_single_leaf_v1",
        identity_source="local_leaf114_checkpoint",
        predict_prepared=lambda _image: [
            Prediction(0, "Corn (maize)", 0.99),
            Prediction(1, "Grape", 0.01),
        ],
    )
    return service


def _clear_leaf_bytes() -> bytes:
    image = Image.new("RGB", (160, 120), (24, 25, 27))
    ImageDraw.Draw(image).ellipse((24, 12, 136, 108), fill=(54, 149, 62))
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def test_predict_returns_top5_metadata_timings_and_safety_warnings() -> None:
    result = _service().predict(_image_bytes(), top_k=5, include_gradcam=False)

    assert result.model_name == "tiny"
    assert result.checkpoint_id == "tiny-checkpoint"
    assert result.image_size == 32
    assert result.target_layer_name == "conv"
    assert result.input_size == (40, 40)
    assert result.predictions[0].class_name == "Tomato___Late_blight"
    assert len(result.predictions) == 3
    assert sum(item.probability for item in result.predictions) == pytest.approx(1.0)
    assert result.gradcam is None
    assert result.lesion_analysis is not None
    assert result.lesion_analysis.image_size == (40, 40)
    assert result.knowledge.plant == "Tomato"
    assert result.knowledge.condition == "Late blight"
    assert result.timings.total_ms >= result.timings.prediction_ms >= 0.0
    assert any("educational" in warning.lower() for warning in result.warnings)
    assert any("PlantVillage" in warning for warning in result.warnings)


def test_predict_derives_crop_first_hierarchy_from_one_model_forward() -> None:
    model = HierarchicalModel()

    result = _hierarchy_service(model).predict(
        _image_bytes(), top_k=3, include_gradcam=False
    )

    assert model.forward_calls == 1
    assert len(result.predictions) == 3
    assert result.predictions[0].class_name == "Apple___Black_rot"
    assert result.hierarchy.selected_crop == "Apple"
    assert result.hierarchy.selected_class_name == "Apple___Black_rot"
    assert [item.condition for item in result.hierarchy.conditions] == [
        "Black rot",
        "healthy",
    ]
    assert result.knowledge.plant == "Apple"


def test_predict_rejects_invalid_empty_and_oversized_inputs() -> None:
    service = _service(max_upload_bytes=8)

    with pytest.raises(InputValidationError, match="empty"):
        service.predict(b"")
    with pytest.raises(InputValidationError, match="larger than"):
        service.predict(b"0123456789")
    with pytest.raises(InputValidationError, match="decode"):
        _service().predict(b"not an image")


def test_leaf_checkpoint_rejects_non_leaf_before_disease_inference() -> None:
    service = _service()
    model = service.model
    assert isinstance(model, TinyGradCamModel)
    service.crop_classifier = SimpleNamespace(
        input_preprocessing="opencv_exg_single_leaf_v1"
    )
    buffer = BytesIO()
    Image.new("RGB", (80, 64), (25, 25, 25)).save(buffer, format="PNG")

    with pytest.raises(LeafSelectionRequiredError) as error:
        service.predict(buffer.getvalue(), include_gradcam=False)

    assert error.value.isolation.accepted is False
    assert model.forward_calls == 0


def test_target_point_reaches_leaf_isolation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = _service()
    service.crop_classifier = SimpleNamespace(
        input_preprocessing="opencv_exg_single_leaf_v1",
        identity_source="local_leaf114_checkpoint",
        predict_prepared=lambda _image: [Prediction(0, "Tomato", 1.0)],
    )
    image = Image.new("RGB", (120, 96), (25, 26, 28))
    ImageDraw.Draw(image).ellipse((14, 8, 106, 88), fill=(55, 150, 63))
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    captured: list[TargetPoint | None] = []

    def capture_target(
        source: Image.Image,
        *,
        target_point: TargetPoint | None = None,
    ):
        captured.append(target_point)
        return isolate_leaf(source, target_point=target_point)

    monkeypatch.setattr(
        "plantdisease.openworld.leaf_pipeline.isolate_leaf",
        capture_target,
    )

    service.predict(
        buffer.getvalue(),
        include_gradcam=False,
        target_point=TargetPoint(0.5, 0.5),
    )

    assert captured == [TargetPoint(0.5, 0.5)]


def test_prototype_rejection_withholds_disease_after_leaf_isolation() -> None:
    service = _service()
    service.crop_classifier = SimpleNamespace(
        input_preprocessing="opencv_exg_single_leaf_v1",
        predict_prepared=lambda _image: [
            Prediction(0, "Tomato", 0.92),
            Prediction(1, "Apple", 0.08),
        ],
        embed_prepared=lambda _image: torch.tensor([1.0, 0.0]),
    )
    service.prototype_index = SimpleNamespace(
        similarity_threshold=0.8,
        margin_threshold=0.1,
        predict=lambda _embedding: OpenSetDecision(
            accepted=False,
            plant_id=None,
            candidate_plant_id="Tomato",
            similarity=0.61,
            margin=0.22,
            alternatives=(("Tomato", 0.61), ("Apple", 0.39)),
            reason="Similarity 0.610 is below the calibrated threshold 0.800.",
        ),
    )
    image = Image.new("RGB", (120, 96), (25, 26, 28))
    ImageDraw.Draw(image).ellipse((14, 8, 106, 88), fill=(55, 150, 63))
    buffer = BytesIO()
    image.save(buffer, format="PNG")

    result = service.predict(buffer.getvalue(), include_gradcam=False)

    assert result.leaf_isolation is not None
    assert result.leaf_isolation.accepted is True
    assert result.plant_novelty is not None
    assert result.plant_novelty.accepted is False
    assert result.hierarchy.selected_crop == "Tomato"
    assert result.hierarchy.crop_confident is False
    assert result.hierarchy.conditions == []
    assert result.hierarchy.selected_class_name is None
    assert result.knowledge is None
    assert result.gradcam is None


def test_external_species_override_still_runs_leaf_isolation_without_local_crop_head() -> None:
    model = HierarchicalModel()
    service = _hierarchy_service(model)
    image = Image.new("RGB", (160, 120), (24, 25, 27))
    ImageDraw.Draw(image).ellipse((24, 12, 136, 108), fill=(54, 149, 62))
    buffer = BytesIO()
    image.save(buffer, format="PNG")

    result = service.predict(
        buffer.getvalue(),
        include_gradcam=False,
        crop_predictions_override=[
            Prediction(0, "Grape", 0.92),
            Prediction(1, "Apple", 0.08),
        ],
        crop_prediction_source="plantnet_api",
    )

    assert result.leaf_isolation is not None
    assert result.leaf_isolation.accepted is True
    assert result.hierarchy.crop_source == "plantnet_api"
    assert result.hierarchy.selected_crop == "Grape"
    assert result.disease_input_method == "opencv_isolated_leaf_neutral_background_v1"
    assert result.disease_input_size == result.leaf_isolation.species_image.size
    assert model.last_inputs is not None
    expected = service._transform(result.leaf_isolation.species_image)
    original = service._transform(image)
    assert torch.allclose(model.last_inputs[0], expected)
    assert not torch.allclose(model.last_inputs[0], original)


def test_visible_grape_lesions_veto_healthy_and_remain_evidence_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model = HierarchicalModel()
    service = InferenceService(
        model=model,
        class_names=[
            "Grape___Black_rot",
            "Grape___Esca_(Black_Measles)",
            "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)",
            "Grape___healthy",
            "Tomato___Late_blight",
        ],
        config={"model_name": "hierarchical", "image_size": 32},
        checkpoint_path=Path("outputs/example/checkpoint.pt"),
        device=torch.device("cpu"),
        checkpoint_id="hierarchical-checkpoint",
        crop_confidence_threshold=0.6,
    )
    service.crop_classifier = SimpleNamespace(
        input_preprocessing="opencv_exg_single_leaf_v1",
        identity_source="local_leaf114_checkpoint",
        predict_prepared=lambda _image: [
            Prediction(0, "Grape", 0.92),
            Prediction(1, "Apple", 0.08),
        ],
    )
    responses = iter(
        [
            [
                Prediction(4, "Tomato___Late_blight", 0.90),
                Prediction(3, "Grape___healthy", 0.0616),
                Prediction(0, "Grape___Black_rot", 0.0307),
                Prediction(1, "Grape___Esca_(Black_Measles)", 0.0067),
                Prediction(2, "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)", 0.0010),
            ],
            [
                Prediction(4, "Tomato___Late_blight", 0.80),
                Prediction(0, "Grape___Black_rot", 0.1185),
                Prediction(3, "Grape___healthy", 0.0527),
                Prediction(1, "Grape___Esca_(Black_Measles)", 0.0239),
                Prediction(2, "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)", 0.0049),
            ],
            [
                Prediction(4, "Tomato___Late_blight", 0.84),
                Prediction(0, "Grape___Black_rot", 0.0804),
                Prediction(3, "Grape___healthy", 0.0479),
                Prediction(1, "Grape___Esca_(Black_Measles)", 0.0263),
                Prediction(2, "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)", 0.0054),
            ],
        ]
    )
    monkeypatch.setattr(
        "plantdisease.serving.service.predict_topk",
        lambda *_args, **_kwargs: next(responses),
    )
    monkeypatch.setattr(
        "plantdisease.serving.service.analyze_corn_abiotic_pattern",
        lambda *_args, **_kwargs: pytest.fail("Corn abiotic gate ran for Grape"),
        raising=False,
    )
    image = Image.new("RGB", (180, 140), (24, 25, 27))
    draw = ImageDraw.Draw(image)
    draw.ellipse((18, 12, 162, 128), fill=(54, 149, 62))
    draw.ellipse((48, 38, 82, 66), fill=(205, 184, 137))
    draw.ellipse((105, 72, 138, 101), fill=(214, 191, 145))
    buffer = BytesIO()
    image.save(buffer, format="PNG")

    result = service.predict(buffer.getvalue(), include_gradcam=False)

    assert result.lesion_focus is not None
    assert result.lesion_focus.applied is True
    assert result.hierarchy.conditions[0].condition == "Black rot"
    assert result.hierarchy.disease_confident is False
    assert result.hierarchy.selected_class_name is None
    assert result.knowledge is None
    assert result.disease_input_method == "opencv_isolated_leaf_plus_lesion_rois_v2"


def test_positive_corn_abiotic_evidence_withholds_infectious_disease(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    evidence = _abiotic_evidence(suspected=True)
    monkeypatch.setattr(
        "plantdisease.serving.service.analyze_corn_abiotic_pattern",
        lambda *_args, **_kwargs: evidence,
        raising=False,
    )

    result = _corn_service().predict(
        _clear_leaf_bytes(),
        include_gradcam=True,
    )

    assert result.hierarchy.selected_crop == "Corn (maize)"
    assert result.hierarchy.crop_confident is True
    assert result.hierarchy.selected_class_name is None
    assert result.hierarchy.disease_confident is False
    assert result.hierarchy.conditions
    assert result.knowledge is None
    assert result.gradcam is None
    assert result.lesion_focus is None
    assert result.abiotic_evidence is evidence
    assert "infectious disease label is withheld" in " ".join(result.warnings).lower()


def test_unknown_corn_stress_keeps_existing_disease_gate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    evidence = _abiotic_evidence(suspected=False)
    monkeypatch.setattr(
        "plantdisease.serving.service.analyze_corn_abiotic_pattern",
        lambda *_args, **_kwargs: evidence,
        raising=False,
    )

    result = _corn_service().predict(
        _clear_leaf_bytes(),
        include_gradcam=False,
    )

    assert result.abiotic_evidence is evidence
    assert result.hierarchy.selected_class_name is not None


def test_predict_adds_low_confidence_warning_below_threshold() -> None:
    result = _service(confidence_warning_threshold=0.99).predict(
        _image_bytes(), top_k=3, include_gradcam=False
    )

    assert any("Low confidence" in warning for warning in result.warnings)


def test_predict_generates_gradcam_overlay_for_top_prediction() -> None:
    result = _service().predict(_image_bytes(), top_k=3, include_gradcam=True)

    assert result.gradcam is not None
    assert result.gradcam.target_class_index == result.predictions[0].class_index
    assert result.gradcam.heatmap.size == (32, 32)
    assert result.gradcam.overlay.size == (32, 32)
    assert result.gradcam.overlay.mode == "RGB"
    assert result.timings.gradcam_ms > 0.0


def test_predict_wraps_unexpected_inference_failures() -> None:
    with pytest.raises(InferenceServiceError, match="inference failed"):
        _service(BadShapeModel()).predict(_image_bytes(), top_k=3)
