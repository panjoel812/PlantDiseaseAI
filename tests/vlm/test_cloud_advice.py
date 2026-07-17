from __future__ import annotations

from typing import Any

import pytest

from plantdisease.vlm.cloud_advice import (
    AdviceContext,
    CloudAdviceError,
    CloudAdviceService,
    HTTPTransportError,
)


class RecordingTransport:
    def __init__(self, responses: list[dict[str, Any]]) -> None:
        self.responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    def post_json(
        self,
        url: str,
        *,
        headers: dict[str, str],
        payload: dict[str, Any],
        timeout_seconds: float,
    ) -> dict[str, Any]:
        self.calls.append(
            {
                "url": url,
                "headers": headers,
                "payload": payload,
                "timeout_seconds": timeout_seconds,
            }
        )
        return self.responses.pop(0)


def _context() -> AdviceContext:
    return AdviceContext(
        selected_crop="Grape",
        crop_probability=0.82,
        selected_condition="Black rot",
        condition_probability=0.64,
        warnings=("Out-of-domain field image.",),
        visual_observation="Circular tan spots with dark margins are visible.",
    )


def test_provider_status_exposes_configuration_without_secrets() -> None:
    service = CloudAdviceService(
        transport=RecordingTransport([]),
        environ={
            "OPENAI_API_KEY": "sk-openai-secret",
            "OPENAI_MODEL": "gpt-custom",
            "ANTHROPIC_MODEL": "claude-custom",
        },
    )

    statuses = service.statuses()

    assert [(item.provider, item.configured) for item in statuses] == [
        ("openai", True),
        ("anthropic", False),
        ("gemini", False),
    ]
    assert statuses[0].model_id == "gpt-custom"
    assert statuses[1].model_id == "claude-custom"
    serialized = repr(statuses)
    assert "sk-openai-secret" not in serialized


def test_runtime_key_configures_without_echo_or_network() -> None:
    transport = RecordingTransport([])
    service = CloudAdviceService(transport=transport, environ={})

    status = service.configure("openai", "sk-runtime-secret", "gpt-runtime")

    assert status.configured is True
    assert status.model_id == "gpt-runtime"
    assert "sk-runtime-secret" not in repr(status)
    assert "sk-runtime-secret" not in repr(service.statuses())
    assert transport.calls == []


def test_runtime_key_takes_precedence_then_clear_restores_environment() -> None:
    service = CloudAdviceService(
        transport=RecordingTransport([]),
        environ={"OPENAI_API_KEY": "environment-key", "OPENAI_MODEL": "gpt-env"},
    )

    service.configure("openai", "runtime-key", "gpt-runtime")
    assert service.statuses()[0].model_id == "gpt-runtime"
    cleared = service.clear("openai")

    assert cleared.configured is True
    assert cleared.model_id == "gpt-env"
    assert service.clear("openai") == cleared


def test_invalid_runtime_key_does_not_mutate_existing_configuration() -> None:
    service = CloudAdviceService(transport=RecordingTransport([]), environ={})
    service.configure("openai", "valid-key")

    with pytest.raises(ValueError, match="api_key"):
        service.configure("openai", "   ")

    assert service.statuses()[0].configured is True


@pytest.mark.parametrize(
    ("provider", "environment", "response", "expected_url", "expected_text"),
    [
        (
            "openai",
            {"OPENAI_API_KEY": "openai-key", "OPENAI_MODEL": "gpt-test"},
            {"output_text": "OpenAI guidance"},
            "https://api.openai.com/v1/responses",
            "OpenAI guidance",
        ),
        (
            "anthropic",
            {
                "ANTHROPIC_API_KEY": "anthropic-key",
                "ANTHROPIC_MODEL": "claude-test",
            },
            {"content": [{"type": "text", "text": "Claude guidance"}]},
            "https://api.anthropic.com/v1/messages",
            "Claude guidance",
        ),
        (
            "gemini",
            {"GEMINI_API_KEY": "gemini-key", "GEMINI_MODEL": "gemini-test"},
            {"output_text": "Gemini guidance"},
            "https://generativelanguage.googleapis.com/v1/interactions",
            "Gemini guidance",
        ),
    ],
)
def test_manual_provider_routing_uses_native_api_contract(
    provider: str,
    environment: dict[str, str],
    response: dict[str, Any],
    expected_url: str,
    expected_text: str,
) -> None:
    transport = RecordingTransport([response])
    service = CloudAdviceService(transport=transport, environ=environment)

    result = service.ask(provider, "What management steps should I consider?", _context())

    assert result.provider == provider
    assert result.message == expected_text
    assert result.action == "educational_guidance"
    assert result.refused is False
    assert result.scope == "educational_management_guidance"
    assert transport.calls[0]["url"] == expected_url
    assert transport.calls[0]["timeout_seconds"] == 30.0
    payload_text = repr(transport.calls[0]["payload"])
    assert "Grape" in payload_text
    assert "Black rot" in payload_text
    assert "Circular tan spots" in payload_text


def test_provider_specific_headers_and_bodies_are_not_flattened() -> None:
    openai_transport = RecordingTransport([{"output_text": "ok"}])
    CloudAdviceService(
        transport=openai_transport,
        environ={"OPENAI_API_KEY": "openai-key", "OPENAI_MODEL": "gpt-test"},
    ).ask("openai", "What next?", _context())
    openai_call = openai_transport.calls[0]
    assert openai_call["headers"]["Authorization"] == "Bearer openai-key"
    assert openai_call["payload"]["model"] == "gpt-test"
    assert openai_call["payload"]["max_output_tokens"] == 800
    assert "instructions" in openai_call["payload"]

    anthropic_transport = RecordingTransport(
        [{"content": [{"type": "text", "text": "ok"}]}]
    )
    CloudAdviceService(
        transport=anthropic_transport,
        environ={
            "ANTHROPIC_API_KEY": "anthropic-key",
            "ANTHROPIC_MODEL": "claude-test",
        },
    ).ask("anthropic", "What next?", _context())
    anthropic_call = anthropic_transport.calls[0]
    assert anthropic_call["headers"]["x-api-key"] == "anthropic-key"
    assert anthropic_call["headers"]["anthropic-version"] == "2023-06-01"
    assert anthropic_call["payload"]["messages"][0]["role"] == "user"

    gemini_transport = RecordingTransport([{"output_text": "ok"}])
    CloudAdviceService(
        transport=gemini_transport,
        environ={"GEMINI_API_KEY": "gemini-key", "GEMINI_MODEL": "gemini-test"},
    ).ask("gemini", "What next?", _context())
    gemini_call = gemini_transport.calls[0]
    assert gemini_call["headers"]["x-goog-api-key"] == "gemini-key"
    assert gemini_call["payload"]["model"] == "gemini-test"
    assert "input" in gemini_call["payload"]


def test_unconfigured_provider_fails_before_network_call() -> None:
    transport = RecordingTransport([])
    service = CloudAdviceService(transport=transport, environ={})

    with pytest.raises(CloudAdviceError, match="not configured"):
        service.ask("openai", "What next?", _context())

    assert transport.calls == []


def test_exact_chemical_rate_request_is_bounded_without_provider_call() -> None:
    transport = RecordingTransport([])
    service = CloudAdviceService(
        transport=transport,
        environ={"OPENAI_API_KEY": "openai-key"},
    )

    result = service.ask(
        "openai",
        "Which fungicide should I use and how many ml per litre?",
        _context(),
    )

    assert result.refused is True
    assert result.action == "bounded_chemical_request"
    assert "registered product label" in result.message
    assert transport.calls == []


def test_unknown_provider_is_rejected_before_network_call() -> None:
    transport = RecordingTransport([])
    service = CloudAdviceService(transport=transport, environ={})

    with pytest.raises(ValueError, match="provider"):
        service.ask("automatic", "What next?", _context())

    assert transport.calls == []


def test_upstream_failure_is_sanitized_and_does_not_leak_key() -> None:
    class FailingTransport:
        def post_json(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
            raise HTTPTransportError(
                status_code=401,
                detail="Authorization failed for sk-sensitive-secret",
            )

    service = CloudAdviceService(
        transport=FailingTransport(),
        environ={"OPENAI_API_KEY": "sk-sensitive-secret"},
    )

    with pytest.raises(CloudAdviceError) as captured:
        service.ask("openai", "What next?", _context())

    assert captured.value.status_code == 502
    assert "authentication" in str(captured.value).lower()
    assert "sk-sensitive-secret" not in str(captured.value)
