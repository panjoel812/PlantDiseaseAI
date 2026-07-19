from __future__ import annotations

import inspect
import pickle
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw

from app.api import DemoSettings, create_app
from plantdisease.inference import Prediction
from plantdisease.openworld.leaf_pipeline import LeafIsolation, TargetPoint, isolate_leaf
from plantdisease.serving.abiotic import CornAbioticEvidence
from plantdisease.serving.hierarchy import (
    ConditionPrediction,
    CropPrediction,
    TaxonomyHierarchy,
)
from plantdisease.serving.knowledge import DiseaseKnowledge
from plantdisease.serving.plant_identity import (
    PlantIdentityResult,
    PlantIdentityStatus,
    PlantSpeciesPrediction,
)
from plantdisease.serving.service import (
    GradCAMImages,
    InferenceResult,
    InferenceServiceError,
    LeafSelectionRequiredError,
    TimingBreakdown,
)
from plantdisease.vlm.assistant import AssistantResponse, ClassifierContext
from plantdisease.vlm.backends import QWEN3_VL_MODEL_ID, MockVLMBackend
from plantdisease.vlm.cloud_advice import (
    AdviceContext,
    CloudAdviceError,
    CloudProviderStatus,
    ManagementAdvice,
)
from plantdisease.vlm.interactive import (
    EVIDENCE_BOUNDARY,
    InteractiveQwenResult,
    InteractiveQwenService,
    QwenRuntimeStatus,
    QwenUnavailableError,
)

FIELD_BYTES = Path("app/examples/field_corn_leaf.jpeg").read_bytes()
DOMAIN_WARNING = "Results may not generalize to field images."


class FakeService:
    def __init__(self) -> None:
        self.calls: list[tuple[bytes, int, bool]] = []
        self.crop_override_calls: list[tuple[list[Prediction] | None, str | None]] = []
        self.target_points: list[TargetPoint | None] = []
        self.leaf_isolation: LeafIsolation | None = None

    def predict(
        self,
        image_bytes: bytes,
        *,
        top_k: int = 5,
        include_gradcam: bool = True,
        crop_predictions_override: list[Prediction] | None = None,
        crop_prediction_source: str | None = None,
        target_point: TargetPoint | None = None,
    ) -> InferenceResult:
        self.calls.append((image_bytes, top_k, include_gradcam))
        self.target_points.append(target_point)
        self.crop_override_calls.append(
            (crop_predictions_override, crop_prediction_source)
        )
        probabilities = [0.50, 0.20, 0.12, 0.10, 0.08]
        predictions = [
            Prediction(index, f"Corn___class_{index}", probability)
            for index, probability in enumerate(probabilities)
        ]
        return InferenceResult(
            predictions=predictions[:top_k],
            hierarchy=TaxonomyHierarchy(
                method="crop_first_rejection_v2",
                selected_crop="Corn",
                selected_class_name="Corn___class_0",
                crops=[CropPrediction(plant="Corn", probability=1.0)],
                conditions=[
                    ConditionPrediction(
                        class_index=prediction.class_index,
                        class_name=prediction.class_name,
                        plant="Corn",
                        condition=f"class {prediction.class_index}",
                        joint_probability=prediction.probability,
                        conditional_probability=prediction.probability,
                    )
                    for prediction in predictions
                ],
            ),
            knowledge=DiseaseKnowledge(
                class_name="Corn___class_0",
                plant="Corn",
                condition="class 0",
                is_healthy=False,
                symptoms="Illustrative symptoms.",
                educational_note="Educational summary only.",
            ),
            model_name="fake-resnet50",
            checkpoint_path="outputs/fake/checkpoint.pt",
            checkpoint_id="fake-checkpoint",
            image_size=224,
            input_size=(1024, 768),
            target_layer_name="layer4.2",
            timings=TimingBreakdown(
                preprocess_ms=1.0,
                prediction_ms=2.0,
                gradcam_ms=3.0,
                total_ms=6.0,
            ),
            warnings=[
                "Educational demo only.",
                "Results may not generalize to field images.",
            ],
            leaf_isolation=self.leaf_isolation,
            gradcam=GradCAMImages(
                target_class_index=0,
                target_class_name="Corn___class_0",
                heatmap=Image.new("L", (8, 8), 127),
                overlay=Image.new("RGB", (8, 8), (32, 64, 16)),
            ),
        )


class FakeQwenService:
    def __init__(
        self,
        *,
        status: QwenRuntimeStatus | None = None,
        result: InteractiveQwenResult | None = None,
        ask_error: QwenUnavailableError | None = None,
    ) -> None:
        self.runtime_status = status or _qwen_status(ready=True)
        self.result = result or _qwen_result(
            raw_answer="Elongated tan-brown spots with dark margins are visible."
        )
        self.ask_error = ask_error
        self.status_calls = 0
        self.ask_calls: list[tuple[bytes, str, ClassifierContext | None]] = []

    def status(self) -> QwenRuntimeStatus:
        self.status_calls += 1
        return self.runtime_status

    def ask(
        self,
        image_bytes: bytes,
        question: str,
        classifier_context: ClassifierContext | None,
    ) -> InteractiveQwenResult:
        self.ask_calls.append((image_bytes, question, classifier_context))
        if self.ask_error is not None:
            raise self.ask_error
        return self.result


class FakeAdviceService:
    def __init__(
        self,
        *,
        ask_error: CloudAdviceError | None = None,
    ) -> None:
        self.ask_error = ask_error
        self.ask_calls: list[tuple[str, str, AdviceContext]] = []
        self.configure_calls: list[tuple[str, str, str | None]] = []
        self.clear_calls: list[str] = []
        self.secret = "server-only-secret"

    def statuses(self) -> list[CloudProviderStatus]:
        return [
            CloudProviderStatus("openai", "OpenAI", True, "gpt-test", "Ready"),
            CloudProviderStatus(
                "anthropic", "Claude", True, "claude-test", "Ready"
            ),
            CloudProviderStatus(
                "gemini",
                "Gemini",
                False,
                "gemini-test",
                "Set GEMINI_API_KEY on the API server.",
            ),
        ]

    def ask(
        self,
        provider: str,
        question: str,
        context: AdviceContext,
    ) -> ManagementAdvice:
        self.ask_calls.append((provider, question, context))
        if self.ask_error is not None:
            raise self.ask_error
        return ManagementAdvice(
            provider="anthropic",
            model_id="claude-test",
            message="Monitor spread and consult local extension before treatment.",
            action="educational_guidance",
            refused=False,
            sources=["classifier-crop:Grape", "qwen:visual-evidence"],
        )

    def configure(
        self,
        provider: str,
        api_key: str,
        model_id: str | None = None,
    ) -> CloudProviderStatus:
        self.configure_calls.append((provider, api_key, model_id))
        return CloudProviderStatus(provider, "OpenAI", True, model_id or "gpt-test", "Ready")

    def clear(self, provider: str) -> CloudProviderStatus:
        self.clear_calls.append(provider)
        return CloudProviderStatus(provider, "OpenAI", False, "gpt-test", "Not configured")


class FakePlantIdentityService:
    def __init__(self, *, configured: bool = False) -> None:
        self.configured = configured
        self.identify_calls: list[bytes] = []

    def status(self) -> PlantIdentityStatus:
        return PlantIdentityStatus(
            provider="plantnet",
            display_name="Pl@ntNet",
            configured=self.configured,
            scope="Broad field species identity (100+ species)",
            detail="Ready" if self.configured else "Add a key",
        )

    def configure(self, api_key: str) -> PlantIdentityStatus:
        assert api_key == "temporary-key"
        self.configured = True
        return self.status()

    def clear(self) -> PlantIdentityStatus:
        self.configured = False
        return self.status()

    def identify(self, image_bytes: bytes) -> PlantIdentityResult:
        self.identify_calls.append(image_bytes)
        return PlantIdentityResult(
            provider="plantnet",
            method="plantnet_leaf_species_v2",
            model_version="test-engine",
            remaining_requests=42,
            predictions=(
                PlantSpeciesPrediction(
                    scientific_name="Vitis vinifera",
                    common_name="Common grape vine",
                    family="Vitaceae",
                    genus="Vitis",
                    score=0.93,
                    routed_plant="Grape",
                ),
                PlantSpeciesPrediction(
                    scientific_name="Parthenocissus quinquefolia",
                    common_name="Virginia creeper",
                    family="Vitaceae",
                    genus="Parthenocissus",
                    score=0.04,
                    routed_plant=None,
                ),
            ),
            evidence_boundary="External species evidence; not ground truth.",
        )


def _qwen_status(*, ready: bool) -> QwenRuntimeStatus:
    return QwenRuntimeStatus(
        supported_platform=True,
        dependency_available=True,
        weights_cached=ready,
        ready=ready,
        model_id=QWEN3_VL_MODEL_ID,
        detail="ready" if ready else "weights are not cached; no automatic download",
    )


def _qwen_result(*, raw_answer: str | None) -> InteractiveQwenResult:
    refused = raw_answer is None
    return InteractiveQwenResult(
        raw_answer=raw_answer,
        observations=() if refused else (raw_answer or "",),
        assistant_response=AssistantResponse(
            message=(
                "This request is outside the verified scope."
                if refused
                else raw_answer or ""
            ),
            action="refuse_high_risk" if refused else "visual_evidence",
            refused=refused,
            reasons=["High risk and out of scope."] if refused else [],
            sources=[]
            if refused
            else [f"vqa:{QWEN3_VL_MODEL_ID}"],
        ),
        model_id=QWEN3_VL_MODEL_ID,
    )


@pytest.fixture
def service() -> FakeService:
    return FakeService()


@pytest.fixture
def provider(
    service: FakeService,
    provider_calls: list[tuple[Path, str, str | None]],
) -> Callable[..., FakeService]:
    def provide(
        checkpoint_path: Path,
        *,
        crop_checkpoint_path: Path | None = None,
        prototype_index_path: Path | None = None,
        device_name: str,
        target_layer_name: str | None,
    ) -> FakeService:
        provider_calls.append((checkpoint_path, device_name, target_layer_name))
        assert checkpoint_path.name == "checkpoint.pt"
        assert device_name == "cpu"
        assert target_layer_name == "layer4.2"
        assert crop_checkpoint_path is None or crop_checkpoint_path.is_file()
        assert prototype_index_path is None or (prototype_index_path / "index.json").is_file()
        return service

    return provide


@pytest.fixture
def provider_calls() -> list[tuple[Path, str, str | None]]:
    return []


@pytest.fixture
def qwen_service() -> FakeQwenService:
    return FakeQwenService()


@pytest.fixture
def client(
    tmp_path: Path,
    provider: Callable[..., FakeService],
    qwen_service: FakeQwenService,
) -> TestClient:
    checkpoint = tmp_path / "checkpoint.pt"
    checkpoint.write_bytes(b"checkpoint marker")
    settings = DemoSettings(
        checkpoint=checkpoint,
        crop_checkpoint=None,
        default_device="auto",
        example_image=Path("app/examples/field_corn_leaf.jpeg"),
        target_layer="layer4.2",
    )
    return TestClient(
        create_app(
            settings,
            service_provider=provider,
            qwen_provider=lambda: qwen_service,
        )
    )


def test_health_reports_classifier_readiness(
    client: TestClient,
    service: FakeService,
    provider_calls: list[tuple[Path, str, str | None]],
) -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["classifier"]["ready"] is True
    assert provider_calls == []
    assert service.calls == []


def test_health_reports_missing_checkpoint_without_loading_service(
    tmp_path: Path,
) -> None:
    provider_called = False

    def provider(*_args: object, **_kwargs: object) -> FakeService:
        nonlocal provider_called
        provider_called = True
        return FakeService()

    app = create_app(
        DemoSettings(checkpoint=tmp_path / "missing.pt"),
        service_provider=provider,
        qwen_provider=lambda: FakeQwenService(),
    )
    response = TestClient(app).get("/api/health")

    assert response.status_code == 200
    assert response.json()["classifier"]["ready"] is False
    assert provider_called is False


def test_plant_identity_key_can_be_configured_and_cleared_through_local_api() -> None:
    identity = FakePlantIdentityService()
    client = TestClient(
        create_app(plant_identity_provider=lambda: identity)
    )

    initial = client.get("/api/plant-identity/status")
    configured = client.post(
        "/api/plant-identity/configure",
        json={"api_key": "temporary-key"},
    )
    cleared = client.delete("/api/plant-identity/configure")

    assert initial.json()["configured"] is False
    assert configured.json()["configured"] is True
    assert cleared.json()["configured"] is False
    assert "temporary-key" not in configured.text


def test_configured_broad_identity_receives_isolated_leaf_and_routes_crop_override(
    tmp_path: Path,
) -> None:
    checkpoint = tmp_path / "checkpoint.pt"
    checkpoint.write_bytes(b"checkpoint marker")
    classifier = FakeService()
    clear_leaf = Image.new("RGB", (180, 140), (24, 25, 27))
    ImageDraw.Draw(clear_leaf).ellipse((20, 12, 160, 128), fill=(54, 149, 62))
    classifier.leaf_isolation = isolate_leaf(clear_leaf)
    assert classifier.leaf_isolation.accepted is True
    identity = FakePlantIdentityService(configured=True)
    app = create_app(
        DemoSettings(checkpoint=checkpoint, crop_checkpoint=None),
        service_provider=lambda *_args, **_kwargs: classifier,
        plant_identity_provider=lambda: identity,
    )

    response = TestClient(app).post(
        "/api/classify",
        files={"image": ("leaf.jpeg", FIELD_BYTES, "image/jpeg")},
        data={
            "include_gradcam": "false",
            "target_x": "0.25",
            "target_y": "0.75",
        },
    )

    assert response.status_code == 200
    assert len(identity.identify_calls) == 1
    assert classifier.crop_override_calls[0] == (None, None)
    override, source = classifier.crop_override_calls[-1]
    assert source == "plantnet_api"
    assert override is not None
    assert [item.class_name for item in override] == ["Grape", "Virginia creeper"]
    assert classifier.target_points == [
        TargetPoint(0.25, 0.75),
        TargetPoint(0.25, 0.75),
    ]
    assert response.json()["plant_identity"]["predictions"][0] == {
        "scientific_name": "Vitis vinifera",
        "common_name": "Common grape vine",
        "family": "Vitaceae",
        "genus": "Vitis",
        "score": 0.93,
        "routed_plant": "Grape",
    }


def test_classify_serializes_top5_gradcam_and_boundaries(
    client: TestClient,
    service: FakeService,
    provider_calls: list[tuple[Path, str, str | None]],
) -> None:
    response = client.post(
        "/api/classify",
        files={"image": ("leaf.jpeg", FIELD_BYTES, "image/jpeg")},
        data={"top_k": "5", "include_gradcam": "true", "device": "cpu"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["predictions"]) == 5
    assert payload["predictions"][0] == {
        "class_index": 0,
        "class_name": "Corn___class_0",
        "probability": 0.5,
    }
    assert payload["hierarchy"]["method"] == "crop_first_rejection_v2"
    assert payload["hierarchy"]["crop_confident"] is True
    assert payload["hierarchy"]["selected_crop"] == "Corn"
    assert payload["hierarchy"]["conditions"][0] == {
        "class_index": 0,
        "class_name": "Corn___class_0",
        "plant": "Corn",
        "condition": "class 0",
        "joint_probability": 0.5,
        "conditional_probability": 0.5,
    }
    assert payload["knowledge"]["plant"] == "Corn"
    assert payload["timings"]["total_ms"] == 6.0
    assert payload["input_size"] == [1024, 768]
    assert payload["gradcam"]["target_class_index"] == 0
    assert payload["gradcam"]["heatmap_data_url"].startswith(
        "data:image/png;base64,"
    )
    assert payload["gradcam"]["overlay_data_url"].startswith(
        "data:image/png;base64,"
    )
    assert any("field images" in item for item in payload["warnings"])
    assert provider_calls == [
        (client.app.state.settings.checkpoint, "cpu", "layer4.2")
    ]
    assert service.calls == [(FIELD_BYTES, 5, True)]


def test_classify_valid_target_coordinates_reach_service(
    client: TestClient,
    service: FakeService,
) -> None:
    response = client.post(
        "/api/classify",
        files={"image": ("leaf.jpeg", FIELD_BYTES, "image/jpeg")},
        data={
            "target_x": "0.25",
            "target_y": "0.75",
            "device": "cpu",
        },
    )

    assert response.status_code == 200
    assert service.target_points == [TargetPoint(0.25, 0.75)]


def test_classify_rejects_incomplete_target_coordinate_pair(
    client: TestClient,
    service: FakeService,
) -> None:
    response = client.post(
        "/api/classify",
        files={"image": ("leaf.jpeg", FIELD_BYTES, "image/jpeg")},
        data={"target_x": "0.25"},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == (
        "target_x and target_y must be supplied together"
    )
    assert service.calls == []


@pytest.mark.parametrize(
    ("target_x", "target_y"),
    [("nan", "0.5"), ("-0.1", "0.5"), ("0.5", "1.1")],
)
def test_classify_rejects_invalid_target_coordinates(
    client: TestClient,
    service: FakeService,
    target_x: str,
    target_y: str,
) -> None:
    response = client.post(
        "/api/classify",
        files={"image": ("leaf.jpeg", FIELD_BYTES, "image/jpeg")},
        data={"target_x": target_x, "target_y": target_y},
    )

    assert response.status_code == 422
    assert "finite numbers between 0 and 1" in response.json()["detail"]
    assert service.calls == []


def test_classify_returns_structured_selection_required_response(
    tmp_path: Path,
) -> None:
    checkpoint = tmp_path / "checkpoint.pt"
    checkpoint.write_bytes(b"checkpoint marker")
    image = Image.new("RGB", (240, 160), (25, 25, 27))
    draw = ImageDraw.Draw(image)
    draw.ellipse((15, 30, 108, 135), fill=(52, 145, 61))
    draw.ellipse((132, 25, 225, 130), fill=(55, 151, 65))
    isolation = isolate_leaf(image)
    assert isolation.accepted is False

    class SelectingService(FakeService):
        def predict(self, *_args: object, **_kwargs: object) -> InferenceResult:
            raise LeafSelectionRequiredError(isolation)

    app = create_app(
        DemoSettings(checkpoint=checkpoint),
        service_provider=lambda *_args, **_kwargs: SelectingService(),
    )
    response = TestClient(app).post(
        "/api/classify",
        files={"image": ("leaf.jpeg", FIELD_BYTES, "image/jpeg")},
    )

    assert response.status_code == 409
    detail = response.json()["detail"]
    assert detail["code"] == "leaf_selection_required"
    assert detail["leaf_isolation"]["accepted"] is False
    assert detail["leaf_isolation"]["selection_mode"] == "automatic"
    assert detail["leaf_isolation"]["target_point"] is None
    assert detail["leaf_isolation"]["purity"]["fragment_count"] == 2
    assert "predictions" not in detail


def test_classify_serializes_positive_abiotic_evidence(
    tmp_path: Path,
) -> None:
    checkpoint = tmp_path / "checkpoint.pt"
    checkpoint.write_bytes(b"checkpoint marker")
    evidence = CornAbioticEvidence(
        method="opencv_corn_midrib_stress_v1",
        status="suspected_abiotic_nutrient_stress",
        suspected=True,
        abnormal_coverage_percent=18.0,
        central_axis_share=0.72,
        longitudinal_continuity=0.81,
        bilateral_similarity=0.68,
        off_axis_lesion_coverage_percent=1.2,
        abnormal_coverage_threshold=8.0,
        central_axis_share_threshold=0.55,
        longitudinal_continuity_threshold=0.60,
        bilateral_similarity_threshold=0.50,
        off_axis_lesion_coverage_threshold=5.0,
        reason="Morphology evidence only; cannot identify a specific nutrient.",
        evidence_boundary="Soil or tissue testing may be required.",
        overlay=Image.new("RGB", (16, 16), (48, 110, 70)),
    )

    class AbioticService(FakeService):
        def predict(self, *args: object, **kwargs: object) -> InferenceResult:
            result = super().predict(*args, **kwargs)
            return replace(
                result,
                hierarchy=replace(
                    result.hierarchy,
                    selected_class_name=None,
                    disease_confident=False,
                ),
                knowledge=None,
                gradcam=None,
                abiotic_evidence=evidence,
            )

    app = create_app(
        DemoSettings(checkpoint=checkpoint),
        service_provider=lambda *_args, **_kwargs: AbioticService(),
    )
    response = TestClient(app).post(
        "/api/classify",
        files={"image": ("leaf.jpeg", FIELD_BYTES, "image/jpeg")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["hierarchy"]["selected_class_name"] is None
    assert payload["knowledge"] is None
    assert payload["gradcam"] is None
    serialized_evidence = dict(payload["abiotic_evidence"])
    overlay_data_url = serialized_evidence.pop("overlay_data_url")
    assert serialized_evidence == {
        "method": "opencv_corn_midrib_stress_v1",
        "status": "suspected_abiotic_nutrient_stress",
        "suspected": True,
        "abnormal_coverage_percent": 18.0,
        "central_axis_share": 0.72,
        "longitudinal_continuity": 0.81,
        "bilateral_similarity": 0.68,
        "off_axis_lesion_coverage_percent": 1.2,
        "abnormal_coverage_threshold": 8.0,
        "central_axis_share_threshold": 0.55,
        "longitudinal_continuity_threshold": 0.6,
        "bilateral_similarity_threshold": 0.5,
        "off_axis_lesion_coverage_threshold": 5.0,
        "reason": "Morphology evidence only; cannot identify a specific nutrient.",
        "evidence_boundary": "Soil or tissue testing may be required.",
    }
    assert overlay_data_url.startswith("data:image/png;base64,")


def test_classify_rejects_corrupt_upload_before_loading_service(
    client: TestClient,
    service: FakeService,
    provider_calls: list[tuple[Path, str, str | None]],
) -> None:
    response = client.post(
        "/api/classify",
        files={"image": ("bad.jpeg", b"not an image", "image/jpeg")},
    )

    assert response.status_code == 422
    assert "decode" in response.json()["detail"]
    assert provider_calls == []
    assert service.calls == []


@pytest.mark.parametrize(
    "load_error",
    [
        OSError("checkpoint cannot be read"),
        ValueError("unsupported checkpoint schema"),
        RuntimeError("incompatible state dict"),
        KeyError("model_name"),
        pickle.UnpicklingError("corrupt checkpoint"),
    ],
)
def test_classify_maps_checkpoint_construction_errors_to_stable_503(
    tmp_path: Path,
    load_error: Exception,
) -> None:
    checkpoint = tmp_path / "checkpoint.pt"
    checkpoint.write_bytes(b"corrupt checkpoint marker")
    provider_calls = 0

    def failing_provider(*_args: object, **_kwargs: object) -> FakeService:
        nonlocal provider_calls
        provider_calls += 1
        raise load_error

    app = create_app(
        DemoSettings(checkpoint=checkpoint),
        service_provider=failing_provider,
    )
    response = TestClient(app, raise_server_exceptions=False).post(
        "/api/classify",
        files={"image": ("leaf.jpeg", FIELD_BYTES, "image/jpeg")},
    )

    assert response.status_code == 503
    assert response.json() == {"detail": "classifier is unavailable"}
    assert provider_calls == 1


def test_classify_does_not_swallow_provider_programming_errors(tmp_path: Path) -> None:
    checkpoint = tmp_path / "checkpoint.pt"
    checkpoint.write_bytes(b"checkpoint marker")

    def broken_provider(*_args: object, **_kwargs: object) -> FakeService:
        raise TypeError("provider bug")

    app = create_app(
        DemoSettings(checkpoint=checkpoint),
        service_provider=broken_provider,
    )

    with pytest.raises(TypeError, match="provider bug"):
        TestClient(app).post(
            "/api/classify",
            files={"image": ("leaf.jpeg", FIELD_BYTES, "image/jpeg")},
        )


def test_classify_keeps_inference_service_error_mapping_separate(tmp_path: Path) -> None:
    checkpoint = tmp_path / "checkpoint.pt"
    checkpoint.write_bytes(b"checkpoint marker")

    class FailingService:
        def predict(self, *_args: object, **_kwargs: object) -> InferenceResult:
            raise InferenceServiceError("inference failed")

    app = create_app(
        DemoSettings(checkpoint=checkpoint),
        service_provider=lambda *_args, **_kwargs: FailingService(),
    )
    response = TestClient(app).post(
        "/api/classify",
        files={"image": ("leaf.jpeg", FIELD_BYTES, "image/jpeg")},
    )

    assert response.status_code == 500
    assert response.json() == {"detail": "inference failed"}


def test_classify_endpoint_is_sync_for_threadpool_execution(client: TestClient) -> None:
    route = next(
        route
        for route in client.app.routes
        if getattr(route, "path", None) == "/api/classify"
    )

    assert inspect.iscoroutinefunction(route.endpoint) is False


def test_example_returns_supplied_jpeg_without_ground_truth(client: TestClient) -> None:
    response = client.get("/api/example")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    assert response.headers["x-example-ground-truth"] == "unavailable"
    assert response.content == FIELD_BYTES


def test_cors_allows_only_configured_local_frontend(client: TestClient) -> None:
    allowed = client.options(
        "/api/classify",
        headers={
            "Origin": "http://127.0.0.1:5173",
            "Access-Control-Request-Method": "POST",
        },
    )
    blocked = client.options(
        "/api/classify",
        headers={
            "Origin": "https://example.com",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert allowed.headers["access-control-allow-origin"] == "http://127.0.0.1:5173"
    assert blocked.headers.get("access-control-allow-origin") is None


@pytest.mark.parametrize(
    "origin",
    ["*", "https://example.com", "http://localhost.example:5173"],
)
def test_cors_rejects_non_local_configured_origins(origin: str) -> None:
    with pytest.raises(ValueError, match="local development origin"):
        create_app(DemoSettings(cors_origins=(origin,)))


def test_health_and_qwen_status_use_injected_provider(tmp_path: Path) -> None:
    checkpoint = tmp_path / "checkpoint.pt"
    checkpoint.write_bytes(b"checkpoint marker")
    service = FakeQwenService()
    provider_calls = 0

    def qwen_provider() -> FakeQwenService:
        nonlocal provider_calls
        provider_calls += 1
        return service

    app = create_app(
        DemoSettings(checkpoint=checkpoint),
        qwen_provider=qwen_provider,
    )
    client = TestClient(app)

    health = client.get("/api/health")
    status = client.get("/api/qwen/status")

    assert health.status_code == 200
    assert health.json()["qwen"] == {
        "supported_platform": True,
        "dependency_available": True,
        "weights_cached": True,
        "ready": True,
        "model_id": QWEN3_VL_MODEL_ID,
        "detail": "ready",
    }
    assert status.status_code == 200
    assert status.json() == health.json()["qwen"]
    assert provider_calls == 2
    assert service.ask_calls == []


def test_qwen_ask_serializes_generated_answer_and_classifier_context(
    tmp_path: Path,
) -> None:
    service = FakeQwenService()
    app = create_app(qwen_provider=lambda: service)
    response = TestClient(app).post(
        "/api/qwen/ask",
        files={"image": ("leaf.jpeg", FIELD_BYTES, "image/jpeg")},
        data={
            "question": "What spots, colors, and shapes are visible?",
            "classifier_top_class_name": "Corn_(maize)___Northern_Leaf_Blight",
            "classifier_confidence": "0.91",
            "classifier_warnings": DOMAIN_WARNING,
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "raw_answer": "Elongated tan-brown spots with dark margins are visible.",
        "observations": [
            "Elongated tan-brown spots with dark margins are visible."
        ],
        "message": "Elongated tan-brown spots with dark margins are visible.",
        "action": "visual_evidence",
        "refused": False,
        "reasons": [],
        "sources": [f"vqa:{QWEN3_VL_MODEL_ID}"],
        "model_id": QWEN3_VL_MODEL_ID,
        "scope": "visual_evidence_only",
        "evidence_boundary": EVIDENCE_BOUNDARY,
    }
    assert service.ask_calls == [
        (
            FIELD_BYTES,
            "What spots, colors, and shapes are visible?",
            ClassifierContext(
                top_class_name="Corn_(maize)___Northern_Leaf_Blight",
                confidence=0.91,
                warnings=[DOMAIN_WARNING],
            ),
        )
    ]


def test_qwen_ask_returns_200_for_safe_refusal() -> None:
    service = FakeQwenService(result=_qwen_result(raw_answer=None))
    response = TestClient(create_app(qwen_provider=lambda: service)).post(
        "/api/qwen/ask",
        files={"image": ("leaf.jpeg", FIELD_BYTES, "image/jpeg")},
        data={"question": "How much pesticide should I use?"},
    )

    assert response.status_code == 200
    assert response.json()["refused"] is True
    assert response.json()["raw_answer"] is None


def test_qwen_ask_returns_status_payload_when_runtime_is_unavailable() -> None:
    unavailable = _qwen_status(ready=False)
    service = FakeQwenService(
        status=unavailable,
        ask_error=QwenUnavailableError(unavailable),
    )
    response = TestClient(create_app(qwen_provider=lambda: service)).post(
        "/api/qwen/ask",
        files={"image": ("leaf.jpeg", FIELD_BYTES, "image/jpeg")},
        data={"question": "What spots, colors, and shapes are visible?"},
    )

    assert response.status_code == 503
    assert response.json() == {
        "supported_platform": True,
        "dependency_available": True,
        "weights_cached": False,
        "ready": False,
        "model_id": QWEN3_VL_MODEL_ID,
        "detail": "weights are not cached; no automatic download",
    }
    assert len(service.ask_calls) == 1


@pytest.mark.parametrize(
    "data",
    [
        {"question": "How much pesticide should I use?"},
        {
            "question": "What disease is this?",
            "classifier_top_class_name": "Tomato___Late_blight",
            "classifier_confidence": "0.42",
            "classifier_warnings": "Low confidence prediction.",
        },
        {
            "question": "What disease is this?",
            "classifier_top_class_name": "unknown",
            "classifier_confidence": "0.95",
            "classifier_warnings": "Non-leaf or out-of-domain image.",
        },
    ],
)
def test_qwen_unavailable_still_returns_safe_pre_generation_refusal(
    data: dict[str, str],
) -> None:
    backend = MockVLMBackend({})
    unavailable = _qwen_status(ready=False)
    service = InteractiveQwenService(
        backend=backend,
        status_probe=lambda _model_id: unavailable,
    )

    response = TestClient(create_app(qwen_provider=lambda: service)).post(
        "/api/qwen/ask",
        files={"image": ("leaf.jpeg", FIELD_BYTES, "image/jpeg")},
        data=data,
    )

    assert response.status_code == 200
    assert response.json()["refused"] is True
    assert response.json()["raw_answer"] is None
    assert backend.calls == []


def test_qwen_ask_translates_lazy_mlx_setup_failure_to_503() -> None:
    failed = QwenRuntimeStatus(
        supported_platform=True,
        dependency_available=True,
        weights_cached=True,
        ready=False,
        model_id=QWEN3_VL_MODEL_ID,
        detail="MLX model setup failed",
    )
    service = FakeQwenService(ask_error=QwenUnavailableError(failed))
    response = TestClient(create_app(qwen_provider=lambda: service)).post(
        "/api/qwen/ask",
        files={"image": ("leaf.jpeg", FIELD_BYTES, "image/jpeg")},
        data={"question": "What spots, colors, and shapes are visible?"},
    )

    assert response.status_code == 503
    assert response.json()["ready"] is False
    assert response.json()["detail"] == "MLX model setup failed"


@pytest.mark.parametrize(
    ("files", "data"),
    [
        ({"image": ("leaf.jpeg", FIELD_BYTES, "image/jpeg")}, {"question": "   "}),
        ({"image": ("bad.jpeg", b"not an image", "image/jpeg")}, {"question": "ok"}),
    ],
)
def test_qwen_ask_rejects_invalid_input_before_service_call(
    files: dict[str, tuple[str, bytes, str]],
    data: dict[str, str],
) -> None:
    service = FakeQwenService()
    response = TestClient(create_app(qwen_provider=lambda: service)).post(
        "/api/qwen/ask",
        files=files,
        data=data,
    )

    assert response.status_code == 422
    assert service.status_calls == 0
    assert service.ask_calls == []


def test_qwen_ask_validates_question_length_after_trimming() -> None:
    prefix = "What visible spots, colors, shapes, and margins are present? "
    accepted_question = prefix + "x" * (500 - len(prefix))
    accepted_prompt = (
        "Inspect only visible pixels. Do not diagnose disease or recommend treatment.\n"
        "Return at most six complete observations, one per line, using only these labels:\n"
        "Spots, Colors, Shapes, Margins, Textures, Distribution. Keep each line under\n"
        "18 words. Do not add an introduction, Markdown, or unfinished text.\n\n"
        f"Question: {accepted_question}"
    )
    accepted_backend = MockVLMBackend({accepted_prompt: "Visible evidence."})
    accepted_service = InteractiveQwenService(
        backend=accepted_backend,
        status_probe=lambda model_id: _qwen_status(ready=True),
    )
    common_context = {
        "classifier_top_class_name": "Corn_(maize)___Northern_Leaf_Blight",
        "classifier_confidence": "0.91",
        "classifier_warnings": DOMAIN_WARNING,
    }

    accepted = TestClient(
        create_app(qwen_provider=lambda: accepted_service)
    ).post(
        "/api/qwen/ask",
        files={"image": ("leaf.jpeg", FIELD_BYTES, "image/jpeg")},
        data={"question": f" {accepted_question} ", **common_context},
    )

    rejected_backend = MockVLMBackend({})
    rejected_service = InteractiveQwenService(
        backend=rejected_backend,
        status_probe=lambda model_id: _qwen_status(ready=True),
    )
    rejected = TestClient(
        create_app(qwen_provider=lambda: rejected_service)
    ).post(
        "/api/qwen/ask",
        files={"image": ("leaf.jpeg", FIELD_BYTES, "image/jpeg")},
        data={"question": f" {'x' * 501} ", **common_context},
    )

    assert accepted.status_code == 200
    assert accepted_backend.calls[0][1] == accepted_prompt
    assert rejected.status_code == 422
    assert rejected_backend.calls == []


def test_qwen_ask_rejects_partial_classifier_context() -> None:
    service = FakeQwenService()
    response = TestClient(create_app(qwen_provider=lambda: service)).post(
        "/api/qwen/ask",
        files={"image": ("leaf.jpeg", FIELD_BYTES, "image/jpeg")},
        data={
            "question": "What spots, colors, and shapes are visible?",
            "classifier_top_class_name": "Corn_(maize)___Northern_Leaf_Blight",
        },
    )

    assert response.status_code == 422
    assert service.ask_calls == []


def test_qwen_ask_endpoint_is_sync_for_threadpool_execution() -> None:
    app = create_app(qwen_provider=lambda: FakeQwenService())
    route = next(
        route
        for route in app.routes
        if getattr(route, "path", None) == "/api/qwen/ask"
    )

    assert inspect.iscoroutinefunction(route.endpoint) is False


def test_advice_provider_status_is_non_secret_and_preserves_manual_order() -> None:
    service = FakeAdviceService()
    response = TestClient(
        create_app(
            qwen_provider=lambda: FakeQwenService(),
            advice_provider=lambda: service,
        )
    ).get("/api/advice/providers")

    assert response.status_code == 200
    assert response.json() == {
        "providers": [
            {
                "provider": "openai",
                "display_name": "OpenAI",
                "configured": True,
                "model_id": "gpt-test",
                "detail": "Ready",
            },
            {
                "provider": "anthropic",
                "display_name": "Claude",
                "configured": True,
                "model_id": "claude-test",
                "detail": "Ready",
            },
            {
                "provider": "gemini",
                "display_name": "Gemini",
                "configured": False,
                "model_id": "gemini-test",
                "detail": "Set GEMINI_API_KEY on the API server.",
            },
        ]
    }
    assert service.secret not in response.text


def test_advice_provider_can_be_configured_and_cleared_without_key_echo() -> None:
    service = FakeAdviceService()
    client = TestClient(create_app(advice_provider=lambda: service))

    configured = client.post(
        "/api/advice/providers/openai/configure",
        json={"api_key": "sk-browser-secret", "model_id": "gpt-runtime"},
    )
    cleared = client.delete("/api/advice/providers/openai/configure")

    assert configured.status_code == 200
    assert configured.json()["configured"] is True
    assert configured.json()["model_id"] == "gpt-runtime"
    assert "sk-browser-secret" not in configured.text
    assert service.configure_calls == [
        ("openai", "sk-browser-secret", "gpt-runtime")
    ]
    assert cleared.status_code == 200
    assert "sk-browser-secret" not in cleared.text
    assert service.clear_calls == ["openai"]


def test_blank_provider_configuration_is_rejected_before_mutation() -> None:
    service = FakeAdviceService()
    response = TestClient(create_app(advice_provider=lambda: service)).post(
        "/api/advice/providers/openai/configure",
        json={"api_key": "   "},
    )

    assert response.status_code == 422
    assert service.configure_calls == []


def test_advice_ask_routes_only_to_explicit_provider_with_qwen_evidence() -> None:
    service = FakeAdviceService()
    response = TestClient(
        create_app(
            qwen_provider=lambda: FakeQwenService(),
            advice_provider=lambda: service,
        )
    ).post(
        "/api/advice/ask",
        json={
            "provider": "anthropic",
            "question": "What management steps should I consider?",
            "selected_crop": "Grape",
            "crop_probability": 0.82,
            "selected_condition": "Black rot",
            "condition_probability": 0.64,
            "warnings": ["Out-of-domain field image."],
            "visual_observation": "Circular tan spots with dark margins are visible.",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "provider": "anthropic",
        "model_id": "claude-test",
        "message": "Monitor spread and consult local extension before treatment.",
        "action": "educational_guidance",
        "refused": False,
        "reasons": [],
        "sources": ["classifier-crop:Grape", "qwen:visual-evidence"],
        "scope": "educational_management_guidance",
        "evidence_boundary": (
            "Educational, conditional management guidance only; not a verified "
            "diagnosis or pesticide prescription. Follow registered labels and local "
            "regulations."
        ),
    }
    assert len(service.ask_calls) == 1
    provider, question, context = service.ask_calls[0]
    assert provider == "anthropic"
    assert question == "What management steps should I consider?"
    assert context.selected_crop == "Grape"
    assert context.visual_observation == (
        "Circular tan spots with dark margins are visible."
    )


def test_advice_ask_rejects_unknown_provider_before_service_call() -> None:
    service = FakeAdviceService()
    response = TestClient(
        create_app(
            qwen_provider=lambda: FakeQwenService(),
            advice_provider=lambda: service,
        )
    ).post(
        "/api/advice/ask",
        json={
            "provider": "automatic",
            "question": "What next?",
            "selected_crop": "Grape",
            "crop_probability": 0.82,
            "selected_condition": "Black rot",
            "condition_probability": 0.64,
        },
    )

    assert response.status_code == 422
    assert service.ask_calls == []


def test_advice_ask_returns_sanitized_provider_failure() -> None:
    service = FakeAdviceService(
        ask_error=CloudAdviceError(
            "Claude authentication failed.",
            status_code=502,
        )
    )
    response = TestClient(
        create_app(
            qwen_provider=lambda: FakeQwenService(),
            advice_provider=lambda: service,
        )
    ).post(
        "/api/advice/ask",
        json={
            "provider": "anthropic",
            "question": "What next?",
            "selected_crop": "Grape",
            "crop_probability": 0.82,
            "selected_condition": "Black rot",
            "condition_probability": 0.64,
        },
    )

    assert response.status_code == 502
    assert response.json() == {"detail": "Claude authentication failed."}
    assert service.secret not in response.text


def test_advice_endpoints_are_sync_for_threadpool_execution() -> None:
    app = create_app(
        qwen_provider=lambda: FakeQwenService(),
        advice_provider=lambda: FakeAdviceService(),
    )
    routes = {
        route.path: route
        for route in app.routes
        if getattr(route, "path", None) in {
            "/api/advice/providers",
            "/api/advice/ask",
        }
    }

    assert inspect.iscoroutinefunction(routes["/api/advice/providers"].endpoint) is False
    assert inspect.iscoroutinefunction(routes["/api/advice/ask"].endpoint) is False
