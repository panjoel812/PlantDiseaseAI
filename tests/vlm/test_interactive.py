from __future__ import annotations

import importlib
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace

import pytest

import plantdisease.vlm.interactive as interactive_module
from plantdisease.vlm.assistant import ClassifierContext
from plantdisease.vlm.backends import (
    QWEN3_VL_MODEL_ID,
    MLXVLMBackend,
    MockVLMBackend,
    VLMSetupError,
)
from plantdisease.vlm.interactive import (
    EVIDENCE_BOUNDARY,
    InteractiveQwenService,
    QwenRuntimeStatus,
    QwenUnavailableError,
    get_qwen_service,
)

FIELD_BYTES = Path("app/examples/field_corn_leaf.jpeg").read_bytes()
DOMAIN_WARNING = "Results may not generalize to field images."


def _ready_status(model_id: str = QWEN3_VL_MODEL_ID) -> QwenRuntimeStatus:
    return QwenRuntimeStatus(
        supported_platform=True,
        dependency_available=True,
        weights_cached=True,
        ready=True,
        model_id=model_id,
        detail="ready",
    )


def _valid_context() -> ClassifierContext:
    return ClassifierContext(
        top_class_name="Corn_(maize)___Northern_Leaf_Blight",
        confidence=0.91,
        warnings=[DOMAIN_WARNING],
    )


def test_interactive_qwen_uses_backend_answer_and_preserves_scope() -> None:
    backend = MockVLMBackend({"Is this leaf healthy?": "diseased"})
    service = InteractiveQwenService(
        backend=backend,
        model_id=QWEN3_VL_MODEL_ID,
        status_probe=_ready_status,
    )

    result = service.ask(
        FIELD_BYTES,
        "Is this leaf healthy?",
        classifier_context=_valid_context(),
    )

    assert result.raw_answer == "diseased"
    assert result.model_id == QWEN3_VL_MODEL_ID
    assert result.scope == "exploratory_smoke"
    assert result.evidence_boundary == EVIDENCE_BOUNDARY
    assert result.assistant_response.refused is False
    assert result.assistant_response.sources == [
        "classifier:Corn_(maize)___Northern_Leaf_Blight",
        f"vqa:{QWEN3_VL_MODEL_ID}",
    ]
    assert len(backend.calls) == 1


@pytest.mark.parametrize("question", ["", "   ", "x" * 501])
def test_interactive_qwen_rejects_invalid_question_without_backend_call(
    question: str,
) -> None:
    backend = MockVLMBackend({})
    service = InteractiveQwenService(backend=backend, status_probe=_ready_status)

    with pytest.raises(ValueError, match="question"):
        service.ask(FIELD_BYTES, question, classifier_context=_valid_context())

    assert backend.calls == []


@pytest.mark.parametrize(
    "question",
    [
        "How many ml of pesticide should I spray per liter?",
        "Which local pesticide regulation applies here?",
        "Is this treatment legal here?",
        "Is this treatment illegal here?",
        "Is this product permitted?",
        "Is it approved under local rules?",
    ],
)
def test_interactive_qwen_refuses_high_risk_questions_before_backend(
    question: str,
) -> None:
    backend = MockVLMBackend({})
    service = InteractiveQwenService(backend=backend, status_probe=_ready_status)

    result = service.ask(FIELD_BYTES, question, classifier_context=_valid_context())

    assert result.raw_answer is None
    assert result.assistant_response.refused is True
    assert result.assistant_response.action == "refuse_high_risk"
    assert backend.calls == []


@pytest.mark.parametrize(
    "context",
    [
        None,
        ClassifierContext(
            top_class_name="Tomato___Late_blight",
            confidence=0.42,
            warnings=["Low confidence prediction."],
        ),
        ClassifierContext(
            top_class_name="unknown",
            confidence=0.95,
            warnings=["Non-leaf or out-of-domain image."],
        ),
    ],
)
def test_interactive_qwen_refuses_unbounded_context_before_backend(
    context: ClassifierContext | None,
) -> None:
    backend = MockVLMBackend({})
    service = InteractiveQwenService(backend=backend, status_probe=_ready_status)

    result = service.ask(FIELD_BYTES, "What disease is this?", classifier_context=context)

    assert result.raw_answer is None
    assert result.assistant_response.refused is True
    assert backend.calls == []


def test_runtime_status_rejects_unsupported_platform_without_imports(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    imports: list[str] = []
    monkeypatch.setattr(interactive_module.platform, "system", lambda: "Linux")
    monkeypatch.setattr(interactive_module.platform, "machine", lambda: "x86_64")
    monkeypatch.setattr(
        interactive_module.importlib,
        "import_module",
        lambda name: imports.append(name),
    )

    status = interactive_module.probe_qwen_runtime()

    assert status.supported_platform is False
    assert status.dependency_available is False
    assert status.weights_cached is False
    assert status.ready is False
    assert "Apple Silicon" in status.detail
    assert imports == []


def test_runtime_status_reports_missing_dependency_without_cache_probe(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    imports: list[str] = []

    def missing_mlx(name: str) -> object:
        imports.append(name)
        raise ModuleNotFoundError(name)

    monkeypatch.setattr(interactive_module.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(interactive_module.platform, "machine", lambda: "arm64")
    monkeypatch.setattr(interactive_module.importlib, "import_module", missing_mlx)

    status = interactive_module.probe_qwen_runtime()

    assert status.supported_platform is True
    assert status.dependency_available is False
    assert status.weights_cached is False
    assert status.ready is False
    assert "uv sync --group vlm" in status.detail
    assert imports == ["mlx_vlm"]


def test_runtime_status_probes_only_local_cache(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshot_calls: list[dict[str, object]] = []

    def snapshot_download(**kwargs: object) -> str:
        snapshot_calls.append(kwargs)
        raise OSError("not cached")

    modules = {
        "mlx_vlm": SimpleNamespace(),
        "huggingface_hub": SimpleNamespace(snapshot_download=snapshot_download),
    }
    monkeypatch.setattr(interactive_module.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(interactive_module.platform, "machine", lambda: "arm64")
    monkeypatch.setattr(interactive_module.importlib, "import_module", modules.__getitem__)

    status = interactive_module.probe_qwen_runtime()

    assert status.dependency_available is True
    assert status.weights_cached is False
    assert status.ready is False
    assert "never downloads" in status.detail
    assert snapshot_calls == [
        {"repo_id": QWEN3_VL_MODEL_ID, "local_files_only": True}
    ]


def test_runtime_status_does_not_hide_cache_probe_programming_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def broken_snapshot(**_kwargs: object) -> str:
        raise RuntimeError("cache probe bug")

    modules = {
        "mlx_vlm": SimpleNamespace(),
        "huggingface_hub": SimpleNamespace(snapshot_download=broken_snapshot),
    }
    monkeypatch.setattr(interactive_module.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(interactive_module.platform, "machine", lambda: "arm64")
    monkeypatch.setattr(interactive_module.importlib, "import_module", modules.__getitem__)

    with pytest.raises(RuntimeError, match="cache probe bug"):
        interactive_module.probe_qwen_runtime()


def test_mlx_setup_error_changes_status_to_unavailable_without_fallback() -> None:
    class FailingBackend:
        def generate(self, _image: object, _question: str) -> str:
            raise VLMSetupError("MLX load failed")

    service = InteractiveQwenService(
        backend=FailingBackend(),
        status_probe=_ready_status,
    )

    with pytest.raises(QwenUnavailableError, match="MLX load failed"):
        service.ask(
            FIELD_BYTES,
            "Is this leaf healthy?",
            classifier_context=_valid_context(),
        )

    status = service.status()
    assert status.ready is False
    assert status.detail == "MLX load failed"


def test_interactive_service_blocks_backend_when_runtime_is_not_ready() -> None:
    backend = MockVLMBackend({"Is this leaf healthy?": "fabricated fallback"})

    def unavailable_status(model_id: str) -> QwenRuntimeStatus:
        return QwenRuntimeStatus(
            supported_platform=True,
            dependency_available=True,
            weights_cached=False,
            ready=False,
            model_id=model_id,
            detail="weights are not cached; no automatic download",
        )

    service = InteractiveQwenService(
        backend=backend,
        status_probe=unavailable_status,
    )

    with pytest.raises(QwenUnavailableError, match="no automatic download"):
        service.ask(
            FIELD_BYTES,
            "Is this leaf healthy?",
            classifier_context=_valid_context(),
        )

    assert backend.calls == []


def test_lazy_setup_failure_is_latched_before_next_waiting_generation() -> None:
    backend_entered = threading.Event()
    release_backend = threading.Event()
    second_precheck_complete = threading.Event()

    class LatchingBackend:
        def __init__(self) -> None:
            self.generate_calls = 0
            self.first_thread_id: int | None = None

        def generate(self, _image: object, _question: str) -> str:
            self.generate_calls += 1
            if self.first_thread_id is None:
                self.first_thread_id = threading.get_ident()
            backend_entered.set()
            if not release_backend.wait(timeout=2):
                raise AssertionError("test did not release backend")
            raise VLMSetupError("lazy MLX setup failed")

    def ready_status(model_id: str) -> QwenRuntimeStatus:
        if (
            backend_entered.is_set()
            and threading.get_ident() != backend.first_thread_id
        ):
            second_precheck_complete.set()
        return _ready_status(model_id)

    backend = LatchingBackend()
    service = InteractiveQwenService(
        backend=backend,
        status_probe=ready_status,
    )

    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(
            service.ask,
            FIELD_BYTES,
            "Is this leaf healthy?",
            _valid_context(),
        )
        assert backend_entered.wait(timeout=2)
        second = executor.submit(
            service.ask,
            FIELD_BYTES,
            "Is this leaf healthy?",
            _valid_context(),
        )
        assert second_precheck_complete.wait(timeout=2)
        release_backend.set()

        first_error = first.exception(timeout=2)
        second_error = second.exception(timeout=2)

    assert isinstance(first_error, QwenUnavailableError)
    assert isinstance(second_error, QwenUnavailableError)
    assert backend.generate_calls == 1
    assert service.status().ready is False


def test_generation_is_serialized_for_shared_backend() -> None:
    class ConcurrencyBackend:
        def __init__(self) -> None:
            self.active = 0
            self.max_active = 0
            self.guard = threading.Lock()

        def generate(self, _image: object, _question: str) -> str:
            with self.guard:
                self.active += 1
                self.max_active = max(self.max_active, self.active)
            time.sleep(0.02)
            with self.guard:
                self.active -= 1
            return "diseased"

    backend = ConcurrencyBackend()
    service = InteractiveQwenService(backend=backend, status_probe=_ready_status)

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(
                service.ask,
                FIELD_BYTES,
                "Is this leaf healthy?",
                _valid_context(),
            )
            for _ in range(2)
        ]
        results = [future.result() for future in futures]

    assert [result.raw_answer for result in results] == ["diseased", "diseased"]
    assert backend.max_active == 1


def test_get_qwen_service_is_cached_and_never_enables_download() -> None:
    get_qwen_service.cache_clear()

    first = get_qwen_service()
    second = get_qwen_service()

    assert first is second
    assert isinstance(first.backend, MLXVLMBackend)
    assert first.backend.allow_model_download is False
    assert first.backend.max_tokens == 96


def test_interactive_import_does_not_eagerly_import_mlx(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    imported: list[str] = []
    real_import = importlib.import_module

    def tracking_import(name: str, package: str | None = None) -> object:
        imported.append(name)
        return real_import(name, package)

    monkeypatch.setattr(importlib, "import_module", tracking_import)
    importlib.reload(interactive_module)

    assert "mlx_vlm" not in imported
