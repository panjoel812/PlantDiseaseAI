"""Manually routed cloud LLM adapters for bounded management guidance."""

from __future__ import annotations

import json
import os
import threading
import urllib.error
import urllib.request
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any, Literal, Protocol, cast

CloudProvider = Literal["openai", "anthropic", "gemini"]

ADVICE_SCOPE = "educational_management_guidance"
ADVICE_BOUNDARY = (
    "Educational, conditional management guidance only; not a verified diagnosis or "
    "pesticide prescription. Follow registered labels and local regulations."
)
MAX_ADVICE_QUESTION_CHARACTERS = 2_000
DEFAULT_TIMEOUT_SECONDS = 30.0
MAX_RESPONSE_BYTES = 65_536
MAX_API_KEY_CHARACTERS = 8_192
MAX_MODEL_ID_CHARACTERS = 200

_SYSTEM_INSTRUCTION = """You are an educational plant-health guidance assistant.
Separate visible evidence, classifier hypotheses, and management options. The supplied
PlantVillage result is a closed-set prediction, not ground truth and not evidence of
field accuracy. Give cautious integrated-pest-management next steps such as monitoring,
sampling, sanitation, airflow, moisture management, isolation, and when to contact a
local extension or plant-health professional. Do not prescribe pesticide products,
concentrations, mixing ratios, application rates, re-entry intervals, pre-harvest
intervals, or claim regulatory approval. Never turn uncertainty into a diagnosis.
"""

_PRECISE_CHEMICAL_TERMS = (
    "application rate",
    "concentration",
    "dilut",
    "dose",
    "dosage",
    "fungicide",
    "herbicide",
    "insecticide",
    "mixing ratio",
    " ml",
    "pesticide",
    "ppm",
    "pre-harvest",
    "product label",
    "re-entry",
    "spray rate",
    "剂量",
    "浓度",
    "稀释",
    "配比",
    "农药",
    "杀菌剂",
)


@dataclass(frozen=True)
class AdviceContext:
    """Structured, uncertainty-preserving evidence supplied to a cloud provider."""

    selected_crop: str
    crop_probability: float
    selected_condition: str
    condition_probability: float
    warnings: Sequence[str] = field(default_factory=tuple)
    visual_observation: str | None = None

    def __post_init__(self) -> None:
        if not self.selected_crop.strip() or not self.selected_condition.strip():
            raise ValueError("crop and condition must be non-empty")
        for name, probability in (
            ("crop_probability", self.crop_probability),
            ("condition_probability", self.condition_probability),
        ):
            if not 0.0 <= probability <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")


@dataclass(frozen=True)
class CloudProviderStatus:
    """Non-secret provider configuration exposed to the browser."""

    provider: CloudProvider
    display_name: str
    configured: bool
    model_id: str
    detail: str


@dataclass(frozen=True)
class ManagementAdvice:
    """One provider answer with explicit scope and provenance."""

    provider: CloudProvider
    model_id: str
    message: str
    action: str
    refused: bool
    reasons: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    scope: str = ADVICE_SCOPE
    evidence_boundary: str = ADVICE_BOUNDARY


class HTTPTransportError(RuntimeError):
    """Low-level HTTP failure retained inside the provider boundary."""

    def __init__(self, *, status_code: int | None, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


class CloudAdviceError(RuntimeError):
    """Sanitized provider error safe to serialize."""

    def __init__(self, message: str, *, status_code: int) -> None:
        super().__init__(message)
        self.status_code = status_code


class JsonTransport(Protocol):
    """Small injectable JSON POST boundary used by all native adapters."""

    def post_json(
        self,
        url: str,
        *,
        headers: dict[str, str],
        payload: dict[str, Any],
        timeout_seconds: float,
    ) -> dict[str, Any]: ...


class UrllibJsonTransport:
    """Dependency-free JSON transport with bounded response reads."""

    def post_json(
        self,
        url: str,
        *,
        headers: dict[str, str],
        payload: dict[str, Any],
        timeout_seconds: float,
    ) -> dict[str, Any]:
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                body = response.read(MAX_RESPONSE_BYTES + 1)
        except urllib.error.HTTPError as exc:
            raise HTTPTransportError(
                status_code=exc.code,
                detail=f"upstream HTTP {exc.code}",
            ) from exc
        except TimeoutError as exc:
            raise HTTPTransportError(status_code=None, detail="upstream timeout") from exc
        except urllib.error.URLError as exc:
            raise HTTPTransportError(status_code=None, detail="upstream unavailable") from exc
        if len(body) > MAX_RESPONSE_BYTES:
            raise HTTPTransportError(status_code=None, detail="upstream response too large")
        try:
            decoded = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise HTTPTransportError(status_code=None, detail="malformed upstream JSON") from exc
        if not isinstance(decoded, dict):
            raise HTTPTransportError(status_code=None, detail="invalid upstream JSON object")
        return cast(dict[str, Any], decoded)


@dataclass(frozen=True)
class _ProviderConfig:
    provider: CloudProvider
    display_name: str
    key_name: str
    model_name: str
    default_model: str


@dataclass(frozen=True)
class _RuntimeCredential:
    api_key: str
    model_id: str | None


_PROVIDER_CONFIGS = (
    _ProviderConfig("openai", "OpenAI", "OPENAI_API_KEY", "OPENAI_MODEL", "gpt-5.4-mini"),
    _ProviderConfig(
        "anthropic",
        "Claude",
        "ANTHROPIC_API_KEY",
        "ANTHROPIC_MODEL",
        "claude-sonnet-5",
    ),
    _ProviderConfig(
        "gemini",
        "Gemini",
        "GEMINI_API_KEY",
        "GEMINI_MODEL",
        "gemini-3.5-flash",
    ),
)


class CloudAdviceService:
    """Route one request to the explicitly selected provider without fallback."""

    def __init__(
        self,
        *,
        transport: JsonTransport | None = None,
        environ: Mapping[str, str] | None = None,
    ) -> None:
        self._transport = transport or UrllibJsonTransport()
        self._environ = os.environ if environ is None else environ
        self._credential_lock = threading.RLock()
        self._runtime_credentials: dict[CloudProvider, _RuntimeCredential] = {}

    def statuses(self) -> list[CloudProviderStatus]:
        """Return stable non-secret configuration status in UI order."""

        return [self._status(config) for config in _PROVIDER_CONFIGS]

    def configure(
        self,
        provider: str,
        api_key: str,
        model_id: str | None = None,
    ) -> CloudProviderStatus:
        """Set one process-memory credential without making a provider call."""

        config = _lookup_provider(provider)
        key = api_key.strip()
        model = model_id.strip() if model_id else None
        if not key or len(key) > MAX_API_KEY_CHARACTERS:
            raise ValueError("api_key must be non-empty and at most 8192 characters")
        if model is not None and len(model) > MAX_MODEL_ID_CHARACTERS:
            raise ValueError("model_id must be at most 200 characters")
        with self._credential_lock:
            self._runtime_credentials[config.provider] = _RuntimeCredential(key, model)
        return self._status(config)

    def clear(self, provider: str) -> CloudProviderStatus:
        """Remove one runtime override and reveal the environment-backed status."""

        config = _lookup_provider(provider)
        with self._credential_lock:
            self._runtime_credentials.pop(config.provider, None)
        return self._status(config)

    def ask(
        self,
        provider: str,
        question: str,
        context: AdviceContext,
    ) -> ManagementAdvice:
        """Request conditional guidance from exactly one selected provider."""

        config = _lookup_provider(provider)
        normalized_question = question.strip()
        if not normalized_question:
            raise ValueError("question must be non-empty")
        if len(normalized_question) > MAX_ADVICE_QUESTION_CHARACTERS:
            raise ValueError(
                "question must be at most "
                f"{MAX_ADVICE_QUESTION_CHARACTERS} characters"
            )
        api_key, model_id = self._credentials(config)
        if not api_key:
            raise CloudAdviceError(
                f"{config.display_name} is not configured on this server.",
                status_code=503,
            )
        if _contains_precise_chemical_request(normalized_question):
            return ManagementAdvice(
                provider=config.provider,
                model_id=model_id,
                message=(
                    "I can discuss general management options, but I cannot select a "
                    "pesticide product or provide a dose, dilution, mixing ratio, or "
                    "application interval. Follow the registered product label for your "
                    "crop and location, and consult local agricultural extension or a "
                    "qualified plant-health professional."
                ),
                action="bounded_chemical_request",
                refused=True,
                reasons=["Exact chemical instructions require authoritative local labels."],
                sources=["local:safety-boundary"],
            )

        prompt = _build_user_prompt(normalized_question, context)
        try:
            response = self._request(
                config=config,
                api_key=api_key,
                model_id=model_id,
                prompt=prompt,
            )
            message = _extract_text(config.provider, response)
        except HTTPTransportError as exc:
            raise _sanitized_upstream_error(config, exc) from exc
        return ManagementAdvice(
            provider=config.provider,
            model_id=model_id,
            message=message,
            action="educational_guidance",
            refused=False,
            reasons=[],
            sources=_context_sources(context),
        )

    def _status(self, config: _ProviderConfig) -> CloudProviderStatus:
        api_key, model_id = self._credentials(config)
        configured = bool(api_key)
        detail = "Ready" if configured else f"Set {config.key_name} on the API server."
        return CloudProviderStatus(
            provider=config.provider,
            display_name=config.display_name,
            configured=configured,
            model_id=model_id,
            detail=detail,
        )

    def _credentials(self, config: _ProviderConfig) -> tuple[str, str]:
        with self._credential_lock:
            runtime = self._runtime_credentials.get(config.provider)
        environment_model = self._environ.get(
            config.model_name,
            config.default_model,
        ).strip()
        fallback_model = environment_model or config.default_model
        if runtime is not None:
            return runtime.api_key, runtime.model_id or fallback_model
        return self._environ.get(config.key_name, "").strip(), fallback_model

    def _request(
        self,
        *,
        config: _ProviderConfig,
        api_key: str,
        model_id: str,
        prompt: str,
    ) -> dict[str, Any]:
        common_headers = {"Content-Type": "application/json"}
        if config.provider == "openai":
            return self._transport.post_json(
                "https://api.openai.com/v1/responses",
                headers={**common_headers, "Authorization": f"Bearer {api_key}"},
                payload={
                    "model": model_id,
                    "instructions": _SYSTEM_INSTRUCTION,
                    "input": prompt,
                    "max_output_tokens": 800,
                },
                timeout_seconds=DEFAULT_TIMEOUT_SECONDS,
            )
        if config.provider == "anthropic":
            return self._transport.post_json(
                "https://api.anthropic.com/v1/messages",
                headers={
                    **common_headers,
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                },
                payload={
                    "model": model_id,
                    "max_tokens": 800,
                    "system": _SYSTEM_INSTRUCTION,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout_seconds=DEFAULT_TIMEOUT_SECONDS,
            )
        return self._transport.post_json(
            "https://generativelanguage.googleapis.com/v1/interactions",
            headers={**common_headers, "x-goog-api-key": api_key},
            payload={
                "model": model_id,
                "input": f"{_SYSTEM_INSTRUCTION}\n\n{prompt}",
                "store": False,
            },
            timeout_seconds=DEFAULT_TIMEOUT_SECONDS,
        )


def _lookup_provider(provider: str) -> _ProviderConfig:
    normalized = provider.strip().casefold()
    for config in _PROVIDER_CONFIGS:
        if config.provider == normalized:
            return config
    raise ValueError("provider must be one of: openai, anthropic, gemini")


def _contains_precise_chemical_request(question: str) -> bool:
    normalized = question.casefold()
    return any(term in normalized for term in _PRECISE_CHEMICAL_TERMS)


def _build_user_prompt(question: str, context: AdviceContext) -> str:
    evidence = {
        "user_question": question,
        "classifier_hypothesis": {
            "selected_crop": context.selected_crop,
            "crop_probability": context.crop_probability,
            "selected_condition": context.selected_condition,
            "condition_probability": context.condition_probability,
            "warnings": list(context.warnings),
        },
        "local_qwen_visual_observation": context.visual_observation,
    }
    return (
        "Use the following unverified evidence. State uncertainty before management "
        "options and do not convert the classifier hypothesis into ground truth.\n"
        + json.dumps(evidence, ensure_ascii=False, indent=2)
    )


def _extract_text(provider: CloudProvider, response: dict[str, Any]) -> str:
    if provider in {"openai", "gemini"}:
        for key in ("output_text", "outputText"):
            value = response.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        for collection_key in ("output", "outputs"):
            collection = response.get(collection_key)
            text = _extract_nested_text(collection)
            if text:
                return text
    if provider == "anthropic":
        text = _extract_nested_text(response.get("content"))
        if text:
            return text
    raise HTTPTransportError(status_code=None, detail="upstream response contained no text")


def _extract_nested_text(value: Any) -> str | None:
    if not isinstance(value, list):
        return None
    parts: list[str] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        text = item.get("text")
        if isinstance(text, str) and text.strip():
            parts.append(text.strip())
        for child_key in ("content", "parts"):
            child = _extract_nested_text(item.get(child_key))
            if child:
                parts.append(child)
    return "\n".join(parts) or None


def _context_sources(context: AdviceContext) -> list[str]:
    sources = [
        f"classifier-crop:{context.selected_crop}",
        f"classifier-condition:{context.selected_condition}",
    ]
    if context.visual_observation:
        sources.append("qwen:visual-evidence")
    return sources


def _sanitized_upstream_error(
    config: _ProviderConfig,
    error: HTTPTransportError,
) -> CloudAdviceError:
    if error.status_code in {401, 403}:
        reason = "authentication failed"
    elif error.status_code == 429:
        reason = "rate limit reached"
    elif "timeout" in error.detail:
        reason = "request timed out"
    else:
        reason = "service unavailable or returned an invalid response"
    return CloudAdviceError(
        f"{config.display_name} {reason}.",
        status_code=502,
    )


@lru_cache(maxsize=1)
def get_cloud_advice_service() -> CloudAdviceService:
    """Return the process-wide environment-configured cloud advice service."""

    return CloudAdviceService()


__all__ = [
    "ADVICE_BOUNDARY",
    "ADVICE_SCOPE",
    "AdviceContext",
    "CloudAdviceError",
    "CloudAdviceService",
    "CloudProvider",
    "CloudProviderStatus",
    "HTTPTransportError",
    "ManagementAdvice",
    "get_cloud_advice_service",
]
