from __future__ import annotations

import inspect
import pickle
from collections.abc import Callable
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.api import DemoSettings, create_app
from plantdisease.inference import Prediction
from plantdisease.serving.hierarchy import (
    ConditionPrediction,
    CropPrediction,
    TaxonomyHierarchy,
)
from plantdisease.serving.knowledge import DiseaseKnowledge
from plantdisease.serving.service import (
    GradCAMImages,
    InferenceResult,
    InferenceServiceError,
    TimingBreakdown,
)
from plantdisease.vlm.assistant import AssistantResponse, ClassifierContext
from plantdisease.vlm.backends import QWEN3_VL_MODEL_ID, MockVLMBackend
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

    def predict(
        self,
        image_bytes: bytes,
        *,
        top_k: int = 5,
        include_gradcam: bool = True,
    ) -> InferenceResult:
        self.calls.append((image_bytes, top_k, include_gradcam))
        probabilities = [0.50, 0.20, 0.12, 0.10, 0.08]
        predictions = [
            Prediction(index, f"Corn___class_{index}", probability)
            for index, probability in enumerate(probabilities)
        ]
        return InferenceResult(
            predictions=predictions[:top_k],
            hierarchy=TaxonomyHierarchy(
                method="single_model_taxonomy_aggregation_v1",
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
        self.result = result or _qwen_result(raw_answer="diseased")
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
        assistant_response=AssistantResponse(
            message=(
                "This request is outside the verified scope."
                if refused
                else "Educational summary only; this is not a professional diagnosis."
            ),
            action="refuse_high_risk" if refused else "educational_summary",
            refused=refused,
            reasons=["High risk and out of scope."] if refused else [],
            sources=[]
            if refused
            else [
                "classifier:Corn_(maize)___Northern_Leaf_Blight",
                f"vqa:{QWEN3_VL_MODEL_ID}",
            ],
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
        device_name: str,
        target_layer_name: str | None,
    ) -> FakeService:
        provider_calls.append((checkpoint_path, device_name, target_layer_name))
        assert checkpoint_path.name == "checkpoint.pt"
        assert device_name == "cpu"
        assert target_layer_name == "layer4.2"
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
    assert payload["hierarchy"]["method"] == "single_model_taxonomy_aggregation_v1"
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
            "question": "Is this leaf healthy?",
            "classifier_top_class_name": "Corn_(maize)___Northern_Leaf_Blight",
            "classifier_confidence": "0.91",
            "classifier_warnings": DOMAIN_WARNING,
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "raw_answer": "diseased",
        "message": "Educational summary only; this is not a professional diagnosis.",
        "action": "educational_summary",
        "refused": False,
        "reasons": [],
        "sources": [
            "classifier:Corn_(maize)___Northern_Leaf_Blight",
            f"vqa:{QWEN3_VL_MODEL_ID}",
        ],
        "model_id": QWEN3_VL_MODEL_ID,
        "scope": "exploratory_smoke",
        "evidence_boundary": EVIDENCE_BOUNDARY,
    }
    assert service.ask_calls == [
        (
            FIELD_BYTES,
            "Is this leaf healthy?",
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
        data={"question": "Is this leaf healthy?"},
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
        data={"question": "Is this leaf healthy?"},
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
    accepted_question = "x" * 500
    accepted_backend = MockVLMBackend({accepted_question: "diseased"})
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
    assert accepted_backend.calls[0][1] == accepted_question
    assert rejected.status_code == 422
    assert rejected_backend.calls == []


def test_qwen_ask_rejects_partial_classifier_context() -> None:
    service = FakeQwenService()
    response = TestClient(create_app(qwen_provider=lambda: service)).post(
        "/api/qwen/ask",
        files={"image": ("leaf.jpeg", FIELD_BYTES, "image/jpeg")},
        data={
            "question": "Is this leaf healthy?",
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
