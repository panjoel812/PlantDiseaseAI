"""FastAPI adapter for the classifier and Grad-CAM demo service."""

from __future__ import annotations

import base64
import pickle
from collections.abc import Sequence
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Annotated, Literal, Protocol
from urllib.parse import urlsplit

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from PIL import Image
from pydantic import BaseModel, Field, field_validator

from plantdisease.serving.cache import get_cached_service
from plantdisease.serving.images import InputValidationError, decode_rgb_image
from plantdisease.serving.service import InferenceResult, InferenceServiceError
from plantdisease.vlm.assistant import ClassifierContext
from plantdisease.vlm.cloud_advice import (
    AdviceContext,
    CloudAdviceError,
    CloudProviderStatus,
    ManagementAdvice,
    get_cloud_advice_service,
)
from plantdisease.vlm.interactive import (
    InteractiveQwenResult,
    QwenRuntimeStatus,
    QwenUnavailableError,
    get_qwen_service,
)

DEFAULT_CHECKPOINT = Path(
    "outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/checkpoint.pt"
)
DEFAULT_CROP_CHECKPOINT = Path(
    "outputs/plantvillage/crop_mobilenet_v2_seed42/checkpoint.pt"
)
DEFAULT_EXAMPLE_IMAGE = Path("app/examples/field_corn_leaf.jpeg")
DEFAULT_CORS_ORIGINS = (
    "http://127.0.0.1:4173",
    "http://127.0.0.1:5173",
    "http://localhost:4173",
    "http://localhost:5173",
)
VALID_DEVICES = frozenset({"auto", "cpu", "cuda", "mps"})
LOCAL_CORS_HOSTS = frozenset({"127.0.0.1", "localhost"})


class ClassifierService(Protocol):
    """Narrow inference interface required by the HTTP adapter."""

    def predict(
        self,
        image_bytes: bytes,
        *,
        top_k: int = 5,
        include_gradcam: bool = True,
    ) -> InferenceResult: ...


class ServiceProvider(Protocol):
    """Construct or retrieve a classifier service for one runtime configuration."""

    def __call__(
        self,
        checkpoint_path: Path,
        *,
        crop_checkpoint_path: Path | None = None,
        device_name: str = "cpu",
        target_layer_name: str | None = None,
    ) -> ClassifierService: ...


class QwenService(Protocol):
    """Interactive Qwen interface required by the HTTP adapter."""

    def status(self) -> QwenRuntimeStatus: ...

    def ask(
        self,
        image_bytes: bytes,
        question: str,
        classifier_context: ClassifierContext | None,
    ) -> InteractiveQwenResult: ...


class QwenProvider(Protocol):
    """Construct or retrieve the process-wide optional Qwen service."""

    def __call__(self) -> QwenService: ...


class AdviceService(Protocol):
    """Manually routed cloud advice interface required by the HTTP adapter."""

    def statuses(self) -> list[CloudProviderStatus]: ...

    def configure(
        self,
        provider: str,
        api_key: str,
        model_id: str | None = None,
    ) -> CloudProviderStatus: ...

    def clear(self, provider: str) -> CloudProviderStatus: ...

    def ask(
        self,
        provider: str,
        question: str,
        context: AdviceContext,
    ) -> ManagementAdvice: ...


class AdviceProvider(Protocol):
    """Construct or retrieve the process-wide cloud advice service."""

    def __call__(self) -> AdviceService: ...


class AdviceRequest(BaseModel):
    """Bounded, non-secret evidence sent from the React demo."""

    provider: Literal["openai", "anthropic", "gemini"]
    question: str = Field(min_length=1, max_length=2_000)
    selected_crop: str = Field(min_length=1, max_length=160)
    crop_probability: float = Field(ge=0.0, le=1.0)
    selected_condition: str = Field(min_length=1, max_length=240)
    condition_probability: float = Field(ge=0.0, le=1.0)
    warnings: list[str] = Field(default_factory=list, max_length=20)
    visual_observation: str | None = Field(default=None, max_length=4_000)


class ProviderConfigureRequest(BaseModel):
    """One temporary provider credential accepted only by the local API."""

    api_key: str = Field(min_length=1, max_length=8_192)
    model_id: str | None = Field(default=None, max_length=200)

    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("api_key must not be blank")
        return normalized


@dataclass(frozen=True)
class DemoSettings:
    """Local classifier API configuration."""

    checkpoint: Path = DEFAULT_CHECKPOINT
    crop_checkpoint: Path | None = DEFAULT_CROP_CHECKPOINT
    default_device: str = "auto"
    example_image: Path = DEFAULT_EXAMPLE_IMAGE
    target_layer: str | None = None
    cors_origins: tuple[str, ...] = DEFAULT_CORS_ORIGINS


def create_app(
    settings: DemoSettings | None = None,
    *,
    service_provider: ServiceProvider = get_cached_service,
    qwen_provider: QwenProvider = get_qwen_service,
    advice_provider: AdviceProvider = get_cloud_advice_service,
) -> FastAPI:
    """Build the classifier API without loading model weights."""
    resolved = settings or DemoSettings()
    cors_origins = _validate_cors_origins(resolved.cors_origins)
    app = FastAPI(title="PlantDiseaseAI Demo API", version="1")
    app.state.settings = resolved
    app.state.service_provider = service_provider
    app.state.qwen_provider = qwen_provider
    app.state.advice_provider = advice_provider
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(cors_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["*"],
    )
    _register_routes(app)
    return app


def _register_routes(app: FastAPI) -> None:
    @app.get("/api/health")
    def health() -> dict[str, object]:
        return _health_payload(app.state.settings, _get_qwen_status(app))

    @app.get("/api/qwen/status")
    def qwen_status() -> dict[str, object]:
        return _serialize_qwen_status(_get_qwen_status(app))

    @app.get("/api/advice/providers")
    def advice_providers() -> dict[str, object]:
        service = _get_advice_service(app)
        return {
            "providers": [
                _serialize_advice_provider_status(status)
                for status in service.statuses()
            ]
        }

    @app.post("/api/advice/providers/{provider}/configure")
    def configure_advice_provider(
        provider: Literal["openai", "anthropic", "gemini"],
        request: ProviderConfigureRequest,
    ) -> dict[str, object]:
        service = _get_advice_service(app)
        try:
            status = service.configure(provider, request.api_key, request.model_id)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return _serialize_advice_provider_status(status)

    @app.delete("/api/advice/providers/{provider}/configure")
    def clear_advice_provider(
        provider: Literal["openai", "anthropic", "gemini"],
    ) -> dict[str, object]:
        service = _get_advice_service(app)
        try:
            status = service.clear(provider)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return _serialize_advice_provider_status(status)

    @app.get("/api/example", response_class=FileResponse)
    def example() -> FileResponse:
        settings: DemoSettings = app.state.settings
        if not settings.example_image.is_file():
            raise HTTPException(status_code=404, detail="example image is unavailable")
        return FileResponse(
            settings.example_image,
            media_type="image/jpeg",
            headers={"X-Example-Ground-Truth": "unavailable"},
        )

    @app.post("/api/classify")
    def classify(
        image: Annotated[UploadFile, File(description="Leaf image")],
        top_k: Annotated[int, Form(ge=1, le=10)] = 5,
        include_gradcam: Annotated[bool, Form()] = True,
        device: Annotated[str | None, Form()] = None,
        target_layer: Annotated[str | None, Form()] = None,
    ) -> dict[str, object]:
        settings: DemoSettings = app.state.settings
        if not settings.checkpoint.is_file():
            raise HTTPException(
                status_code=503,
                detail="classifier checkpoint is unavailable",
            )
        resolved_device = device or settings.default_device
        if resolved_device not in VALID_DEVICES:
            raise HTTPException(
                status_code=422,
                detail="device must be one of: auto, cpu, cuda, mps",
            )
        image_bytes = image.file.read()
        try:
            decode_rgb_image(image_bytes)
        except InputValidationError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        provider: ServiceProvider = app.state.service_provider
        service = _get_service(
            provider,
            checkpoint=settings.checkpoint,
            crop_checkpoint=(
                settings.crop_checkpoint
                if settings.crop_checkpoint is not None
                and settings.crop_checkpoint.is_file()
                else None
            ),
            device=resolved_device,
            target_layer=target_layer or settings.target_layer,
        )
        try:
            result = service.predict(
                image_bytes,
                top_k=top_k,
                include_gradcam=include_gradcam,
            )
        except InputValidationError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except InferenceServiceError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        return _serialize_result(result)

    @app.post("/api/qwen/ask", response_model=None)
    def ask_qwen(
        image: Annotated[UploadFile, File(description="Leaf image")],
        question: Annotated[str, Form()],
        classifier_top_class_name: Annotated[str | None, Form()] = None,
        classifier_confidence: Annotated[float | None, Form(ge=0.0, le=1.0)] = None,
        classifier_warnings: Annotated[list[str] | None, Form()] = None,
    ) -> dict[str, object] | JSONResponse:
        normalized_question = question.strip()
        if not normalized_question:
            raise HTTPException(status_code=422, detail="question must be non-empty")
        image_bytes = image.file.read()
        try:
            decode_rgb_image(image_bytes)
        except InputValidationError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        classifier_context = _build_classifier_context(
            top_class_name=classifier_top_class_name,
            confidence=classifier_confidence,
            warnings=classifier_warnings,
        )
        service = _get_qwen_service(app)
        try:
            result = service.ask(
                image_bytes,
                normalized_question,
                classifier_context,
            )
        except (InputValidationError, ValueError) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except QwenUnavailableError as exc:
            return JSONResponse(
                status_code=503,
                content=_serialize_qwen_status(exc.status),
            )
        return _serialize_qwen_result(result)

    @app.post("/api/advice/ask")
    def ask_advice(request: AdviceRequest) -> dict[str, object]:
        service = _get_advice_service(app)
        try:
            context = AdviceContext(
                selected_crop=request.selected_crop.strip(),
                crop_probability=request.crop_probability,
                selected_condition=request.selected_condition.strip(),
                condition_probability=request.condition_probability,
                warnings=tuple(warning.strip() for warning in request.warnings),
                visual_observation=(
                    request.visual_observation.strip()
                    if request.visual_observation
                    else None
                ),
            )
            result = service.ask(
                request.provider,
                request.question.strip(),
                context,
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except CloudAdviceError as exc:
            raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
        return _serialize_management_advice(result)


def _health_payload(
    settings: DemoSettings,
    qwen_status: QwenRuntimeStatus,
) -> dict[str, object]:
    disease_ready = settings.checkpoint.is_file()
    crop_ready = settings.crop_checkpoint is not None and settings.crop_checkpoint.is_file()
    ready = disease_ready and crop_ready
    return {
        "status": "ok" if ready else "degraded",
        "classifier": {
            "ready": disease_ready,
            "checkpoint": str(settings.checkpoint),
            "device": settings.default_device,
            "target_layer": settings.target_layer,
            "detail": "ready" if disease_ready else "checkpoint not found",
        },
        "crop_classifier": {
            "ready": crop_ready,
            "checkpoint": str(settings.crop_checkpoint) if settings.crop_checkpoint else None,
            "detail": (
                "ready"
                if crop_ready
                else "crop checkpoint not found; joint crop gate fallback"
            ),
        },
        "qwen": _serialize_qwen_status(qwen_status),
    }


def _get_qwen_service(app: FastAPI) -> QwenService:
    provider: QwenProvider = app.state.qwen_provider
    return provider()


def _get_qwen_status(app: FastAPI) -> QwenRuntimeStatus:
    return _get_qwen_service(app).status()


def _get_advice_service(app: FastAPI) -> AdviceService:
    provider: AdviceProvider = app.state.advice_provider
    return provider()


def _build_classifier_context(
    *,
    top_class_name: str | None,
    confidence: float | None,
    warnings: list[str] | None,
) -> ClassifierContext | None:
    if top_class_name is None and confidence is None and not warnings:
        return None
    if top_class_name is None or confidence is None:
        raise HTTPException(
            status_code=422,
            detail=(
                "classifier_top_class_name and classifier_confidence must be supplied together"
            ),
        )
    return ClassifierContext(
        top_class_name=top_class_name,
        confidence=confidence,
        warnings=warnings or [],
    )


def _serialize_qwen_status(status: QwenRuntimeStatus) -> dict[str, object]:
    return {
        "supported_platform": status.supported_platform,
        "dependency_available": status.dependency_available,
        "weights_cached": status.weights_cached,
        "ready": status.ready,
        "model_id": status.model_id,
        "detail": status.detail,
    }


def _serialize_qwen_result(result: InteractiveQwenResult) -> dict[str, object]:
    response = result.assistant_response
    return {
        "raw_answer": result.raw_answer,
        "observations": list(result.observations),
        "message": response.message,
        "action": response.action,
        "refused": response.refused,
        "reasons": list(response.reasons),
        "sources": list(response.sources),
        "model_id": result.model_id,
        "scope": result.scope,
        "evidence_boundary": result.evidence_boundary,
    }


def _serialize_advice_provider_status(
    status: CloudProviderStatus,
) -> dict[str, object]:
    return {
        "provider": status.provider,
        "display_name": status.display_name,
        "configured": status.configured,
        "model_id": status.model_id,
        "detail": status.detail,
    }


def _serialize_management_advice(result: ManagementAdvice) -> dict[str, object]:
    return {
        "provider": result.provider,
        "model_id": result.model_id,
        "message": result.message,
        "action": result.action,
        "refused": result.refused,
        "reasons": list(result.reasons),
        "sources": list(result.sources),
        "scope": result.scope,
        "evidence_boundary": result.evidence_boundary,
    }


def _get_service(
    provider: ServiceProvider,
    *,
    checkpoint: Path,
    crop_checkpoint: Path | None,
    device: str,
    target_layer: str | None,
) -> ClassifierService:
    try:
        return provider(
            checkpoint,
            crop_checkpoint_path=crop_checkpoint,
            device_name=device,
            target_layer_name=target_layer,
        )
    except (OSError, ValueError, RuntimeError, KeyError, pickle.UnpicklingError) as exc:
        raise HTTPException(status_code=503, detail="classifier is unavailable") from exc


def _validate_cors_origins(origins: tuple[str, ...]) -> tuple[str, ...]:
    for origin in origins:
        parsed = urlsplit(origin)
        try:
            port = parsed.port
        except ValueError as exc:
            raise ValueError(
                f"CORS origin must be a local development origin: {origin}"
            ) from exc
        if (
            parsed.scheme != "http"
            or parsed.hostname not in LOCAL_CORS_HOSTS
            or port is None
            or parsed.username is not None
            or parsed.password is not None
            or parsed.path
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError(
                f"CORS origin must be a local development origin: {origin}"
            )
    return origins


def _serialize_result(result: InferenceResult) -> dict[str, object]:
    gradcam: dict[str, object] | None = None
    if result.gradcam is not None:
        gradcam = {
            "target_class_index": result.gradcam.target_class_index,
            "target_class_name": result.gradcam.target_class_name,
            "heatmap_data_url": _png_data_url(result.gradcam.heatmap),
            "overlay_data_url": _png_data_url(result.gradcam.overlay),
        }
    lesion_analysis: dict[str, object] | None = None
    if result.lesion_analysis is not None:
        analysis = result.lesion_analysis
        lesion_analysis = {
            "method": analysis.method,
            "image_size": list(analysis.image_size),
            "leaf_area_pixels": analysis.leaf_area_pixels,
            "leaf_coverage_percent": analysis.leaf_coverage_percent,
            "lesion_area_pixels": analysis.lesion_area_pixels,
            "lesion_coverage_percent": analysis.lesion_coverage_percent,
            "lesion_count": analysis.lesion_count,
            "median_lesion_area_percent": analysis.median_lesion_area_percent,
            "largest_lesion_area_percent": analysis.largest_lesion_area_percent,
            "mean_circularity": analysis.mean_circularity,
            "dominant_colors": [
                {"name": color.name, "proportion": color.proportion}
                for color in analysis.dominant_colors
            ],
            "distribution": analysis.distribution,
            "regions": [
                {
                    "x": region.x,
                    "y": region.y,
                    "width": region.width,
                    "height": region.height,
                    "centroid_x": region.centroid_x,
                    "centroid_y": region.centroid_y,
                    "area_pixels": region.area_pixels,
                    "area_percent_of_leaf": region.area_percent_of_leaf,
                    "circularity": region.circularity,
                    "aspect_ratio": region.aspect_ratio,
                    "shape": region.shape,
                    "color": region.color,
                }
                for region in analysis.regions
            ],
            "overlay_data_url": _png_data_url(analysis.overlay),
        }
    knowledge: dict[str, object] | None = None
    if result.knowledge is not None:
        knowledge = {
            "class_name": result.knowledge.class_name,
            "plant": result.knowledge.plant,
            "condition": result.knowledge.condition,
            "is_healthy": result.knowledge.is_healthy,
            "symptoms": result.knowledge.symptoms,
            "educational_note": result.knowledge.educational_note,
        }
    return {
        "predictions": [
            {
                "class_index": prediction.class_index,
                "class_name": prediction.class_name,
                "probability": prediction.probability,
            }
            for prediction in result.predictions
        ],
        "hierarchy": {
            "method": result.hierarchy.method,
            "selected_crop": result.hierarchy.selected_crop,
            "selected_class_name": result.hierarchy.selected_class_name,
            "crop_confident": result.hierarchy.crop_confident,
            "crop_margin": result.hierarchy.crop_margin,
            "confidence_threshold": result.hierarchy.confidence_threshold,
            "margin_threshold": result.hierarchy.margin_threshold,
            "decision_reason": result.hierarchy.decision_reason,
            "crop_source": result.hierarchy.crop_source,
            "disease_confident": result.hierarchy.disease_confident,
            "disease_confidence": result.hierarchy.disease_confidence,
            "disease_margin": result.hierarchy.disease_margin,
            "disease_confidence_threshold": result.hierarchy.disease_confidence_threshold,
            "disease_margin_threshold": result.hierarchy.disease_margin_threshold,
            "disease_decision_reason": result.hierarchy.disease_decision_reason,
            "crops": [
                {
                    "plant": crop.plant,
                    "probability": crop.probability,
                }
                for crop in result.hierarchy.crops
            ],
            "conditions": [
                {
                    "class_index": condition.class_index,
                    "class_name": condition.class_name,
                    "plant": condition.plant,
                    "condition": condition.condition,
                    "joint_probability": condition.joint_probability,
                    "conditional_probability": condition.conditional_probability,
                }
                for condition in result.hierarchy.conditions
            ],
        },
        "knowledge": knowledge,
        "lesion_analysis": lesion_analysis,
        "model_name": result.model_name,
        "checkpoint_path": result.checkpoint_path,
        "checkpoint_id": result.checkpoint_id,
        "image_size": result.image_size,
        "input_size": list(result.input_size),
        "target_layer_name": result.target_layer_name,
        "timings": {
            "preprocess_ms": result.timings.preprocess_ms,
            "prediction_ms": result.timings.prediction_ms,
            "gradcam_ms": result.timings.gradcam_ms,
            "total_ms": result.timings.total_ms,
        },
        "warnings": list(result.warnings),
        "gradcam": gradcam,
    }


def _png_data_url(image: Image.Image) -> str:
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


app = create_app()

__all__: Sequence[str] = [
    "AdviceProvider",
    "DEFAULT_CHECKPOINT",
    "DEFAULT_CROP_CHECKPOINT",
    "DemoSettings",
    "QwenProvider",
    "ServiceProvider",
    "app",
    "create_app",
]
