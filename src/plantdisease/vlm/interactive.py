"""Optional, locally cached Qwen3-VL service for the interactive demo."""

from __future__ import annotations

import importlib
import platform
import re
import textwrap
import threading
from collections.abc import Callable
from dataclasses import dataclass, replace
from functools import lru_cache

from plantdisease.serving.images import decode_rgb_image
from plantdisease.vlm.assistant import (
    AssistantResponse,
    ClassifierContext,
    build_assistant_response,
    is_visual_evidence_question,
)
from plantdisease.vlm.backends import (
    QWEN3_VL_MODEL_ID,
    MLXVLMBackend,
    VLMBackend,
    VLMSetupError,
)

MAX_QUESTION_CHARACTERS = 500
MAX_VISUAL_OBSERVATIONS = 6
MAX_VISUAL_OBSERVATION_CHARACTERS = 180
EVIDENCE_BOUNDARY = (
    "Local Qwen visual evidence only; no diagnosis or treatment. Fixed smoke: "
    "choice/few-shot 11/15; fine-grained condition 1/5."
)
_VISUAL_PREFIX = (
    "Inspect only visible pixels. Do not diagnose disease or recommend treatment.\n"
    "Return at most six short, complete observations about spots, colors, shapes,\n"
    "margins, textures, and distribution. Do not add an introduction.\n\n"
    "Question: "
)

_REGULATORY_PATTERN = re.compile(
    r"\b(?:legal|illegal|permitted|approved|regulations?|regulatory)\b"
    r"|\blocal\s+(?:law|rules?)\b",
    flags=re.IGNORECASE,
)


@dataclass(frozen=True)
class QwenRuntimeStatus:
    """Local platform, dependency, and model-cache readiness."""

    supported_platform: bool
    dependency_available: bool
    weights_cached: bool
    ready: bool
    model_id: str
    detail: str


@dataclass(frozen=True)
class InteractiveQwenResult:
    """One raw model answer plus its bounded educational wrapper."""

    raw_answer: str | None
    assistant_response: AssistantResponse
    model_id: str
    observations: tuple[str, ...] = ()
    scope: str = "visual_evidence_only"
    evidence_boundary: str = EVIDENCE_BOUNDARY


class QwenUnavailableError(RuntimeError):
    """Raised when local Qwen setup fails without fabricating an answer."""

    def __init__(self, status: QwenRuntimeStatus) -> None:
        super().__init__(status.detail)
        self.status = status


StatusProbe = Callable[[str], QwenRuntimeStatus]


def probe_qwen_runtime(model_id: str = QWEN3_VL_MODEL_ID) -> QwenRuntimeStatus:
    """Inspect Apple Silicon, MLX-VLM, and the local-only model cache."""

    if platform.system() != "Darwin" or platform.machine() != "arm64":
        return QwenRuntimeStatus(
            supported_platform=False,
            dependency_available=False,
            weights_cached=False,
            ready=False,
            model_id=model_id,
            detail="Qwen requires Apple Silicon macOS (Darwin arm64) with MLX/Metal.",
        )

    try:
        importlib.import_module("mlx_vlm")
    except (ImportError, ModuleNotFoundError):
        return QwenRuntimeStatus(
            supported_platform=True,
            dependency_available=False,
            weights_cached=False,
            ready=False,
            model_id=model_id,
            detail="MLX-VLM is unavailable. Run `uv sync --group vlm` locally.",
        )

    try:
        huggingface_hub = importlib.import_module("huggingface_hub")
        snapshot_download = huggingface_hub.snapshot_download
    except (AttributeError, ImportError, ModuleNotFoundError):
        return QwenRuntimeStatus(
            supported_platform=True,
            dependency_available=False,
            weights_cached=False,
            ready=False,
            model_id=model_id,
            detail="The local Hugging Face cache runtime is unavailable.",
        )

    try:
        snapshot_download(repo_id=model_id, local_files_only=True)
    except OSError:
        return QwenRuntimeStatus(
            supported_platform=True,
            dependency_available=True,
            weights_cached=False,
            ready=False,
            model_id=model_id,
            detail=(
                f"Model weights for {model_id!r} are not in the local cache. "
                "The API never downloads them automatically."
            ),
        )

    return QwenRuntimeStatus(
        supported_platform=True,
        dependency_available=True,
        weights_cached=True,
        ready=True,
        model_id=model_id,
        detail="ready",
    )


class InteractiveQwenService:
    """Serialize one cached backend and apply safety before and after generation."""

    def __init__(
        self,
        backend: VLMBackend,
        model_id: str = QWEN3_VL_MODEL_ID,
        *,
        status_probe: StatusProbe = probe_qwen_runtime,
    ) -> None:
        if not model_id.strip():
            raise ValueError("model_id must be non-empty")
        self.backend = backend
        self.model_id = model_id
        self._status_probe = status_probe
        self._generation_lock = threading.Lock()
        self._status_lock = threading.Lock()
        self._failed_status: QwenRuntimeStatus | None = None

    def status(self) -> QwenRuntimeStatus:
        """Return current readiness, including a prior lazy-load failure."""

        with self._status_lock:
            failed_status = self._failed_status
        return failed_status or self._status_probe(self.model_id)

    def ask(
        self,
        image_bytes: bytes,
        question: str,
        classifier_context: ClassifierContext | None,
    ) -> InteractiveQwenResult:
        """Answer one bounded question or return a pre-generation refusal."""

        normalized_question = question.strip()
        if not normalized_question:
            raise ValueError("question must be non-empty")
        if len(normalized_question) > MAX_QUESTION_CHARACTERS:
            raise ValueError(
                f"question must be at most {MAX_QUESTION_CHARACTERS} characters"
            )

        image = decode_rgb_image(image_bytes)
        context = classifier_context or ClassifierContext(
            top_class_name="unknown",
            confidence=0.0,
            warnings=("No classifier context was supplied.",),
        )
        preflight = _build_preflight_response(normalized_question, context)
        if preflight.refused:
            return InteractiveQwenResult(
                raw_answer=None,
                assistant_response=preflight,
                model_id=self.model_id,
            )

        runtime_status = self.status()
        if not runtime_status.ready:
            raise QwenUnavailableError(runtime_status)

        with self._generation_lock:
            runtime_status = self.status()
            if not runtime_status.ready:
                raise QwenUnavailableError(runtime_status)
            try:
                raw_answer = self.backend.generate(
                    image,
                    _build_visual_prompt(normalized_question),
                )
            except VLMSetupError as exc:
                failed_status = replace(runtime_status, ready=False, detail=str(exc))
                with self._status_lock:
                    self._failed_status = failed_status
                raise QwenUnavailableError(failed_status) from exc

        observations = _normalize_visual_observations(raw_answer)
        wrapped = AssistantResponse(
            message=" ".join(observations),
            action="visual_evidence",
            refused=False,
            reasons=[],
            sources=[f"vqa:{self.model_id}"],
        )
        return InteractiveQwenResult(
            raw_answer=raw_answer,
            assistant_response=wrapped,
            model_id=self.model_id,
            observations=observations,
        )


def _build_visual_prompt(question: str) -> str:
    """Constrain the local model to concise, visible morphology only."""

    return _VISUAL_PREFIX + question.strip()


def _normalize_visual_observations(raw_answer: str) -> tuple[str, ...]:
    """Convert common VLM prose/Markdown into bounded, deduplicated rows."""

    normalized = re.sub(r"\*\*([^*]+)\*\*", r"\n\1", raw_answer)
    observations: list[str] = []
    seen: set[str] = set()
    for fragment in normalized.splitlines():
        item = re.sub(r"^[\s*#•\-\d.)]+", "", fragment).strip()
        if re.match(r"(?i)^based on (?:the )?(?:image|provided image)", item):
            continue
        item = re.sub(
            r"^([A-Za-z][\w /-]{1,32}:)\s*[-•]\s*",
            r"\1 ",
            item,
        )
        item = re.sub(r"\s+", " ", item).strip()
        if not item or re.fullmatch(r"[A-Za-z][\w /-]{1,32}:", item):
            continue
        if len(item) > MAX_VISUAL_OBSERVATION_CHARACTERS:
            item = textwrap.shorten(
                item,
                width=MAX_VISUAL_OBSERVATION_CHARACTERS,
                placeholder="…",
            )
        item = item.rstrip(" ,;:-")
        if item and item[-1] not in ".!?…":
            item += "."
        key = item.casefold()
        if not item or key in seen:
            continue
        seen.add(key)
        observations.append(item)
        if len(observations) == MAX_VISUAL_OBSERVATIONS:
            break
    return tuple(observations or ("No concise visual observation was returned.",))


def _build_preflight_response(
    question: str,
    context: ClassifierContext,
) -> AssistantResponse:
    bounded_response = build_assistant_response(question, classifier_context=context)
    if bounded_response.action == "refuse_high_risk":
        return bounded_response
    if _contains_regulatory_term(question):
        return AssistantResponse(
            message=(
                "I cannot interpret pesticide or agricultural regulations. Please "
                "consult a local plant-health professional or agricultural extension "
                "office and follow the applicable local rules."
            ),
            action="refuse_high_risk",
            refused=True,
            reasons=["Regulatory instructions are high risk and out of scope."],
            sources=[],
        )
    if not is_visual_evidence_question(question):
        return AssistantResponse(
            message=(
                "Local Qwen is limited to visible evidence. Ask about spots, colors, "
                "shapes, margins, textures, or distribution; use Management guidance "
                "for diagnosis hypotheses or treatment questions."
            ),
            action="refuse_non_visual_question",
            refused=True,
            reasons=["The question is not limited to visible image evidence."],
            sources=[],
        )
    return AssistantResponse(
        message="Visual evidence request accepted.",
        action="allow_visual_evidence",
        refused=False,
        reasons=[],
        sources=[],
    )


def _contains_regulatory_term(question: str) -> bool:
    return _REGULATORY_PATTERN.search(question) is not None


@lru_cache(maxsize=1)
def get_qwen_service() -> InteractiveQwenService:
    """Return the process-wide, download-disabled local Qwen service."""

    return InteractiveQwenService(
        backend=MLXVLMBackend(allow_model_download=False, max_tokens=192),
        model_id=QWEN3_VL_MODEL_ID,
    )


__all__ = [
    "EVIDENCE_BOUNDARY",
    "InteractiveQwenResult",
    "InteractiveQwenService",
    "MAX_QUESTION_CHARACTERS",
    "QwenRuntimeStatus",
    "QwenUnavailableError",
    "get_qwen_service",
    "probe_qwen_runtime",
]
