"""Visual-language model backend boundaries for Week 6 smoke runs."""

from __future__ import annotations

import importlib
import platform
from collections.abc import Callable, Mapping
from typing import Any, Protocol, cast, runtime_checkable

QWEN3_VL_MODEL_ID = "mlx-community/Qwen3-VL-4B-Instruct-4bit"


class VLMSetupError(RuntimeError):
    """Raised when a real VLM backend cannot be prepared safely."""


@runtime_checkable
class VLMBackend(Protocol):
    """Minimal interface shared by deterministic and real VLM backends."""

    def generate(self, image: object, question: str) -> str:
        """Generate an answer for one image and question."""


class _MLXModel(Protocol):
    """Subset of the dynamically imported MLX model used by the adapter."""

    config: object


class MockVLMBackend:
    """Return question-keyed answers without network or model dependencies."""

    def __init__(self, responses: Mapping[str, str]) -> None:
        self.responses = dict(responses)
        self.calls: list[tuple[object, str]] = []

    def generate(self, image: object, question: str) -> str:
        self.calls.append((image, question))
        try:
            return self.responses[question]
        except KeyError as exc:
            msg = f"No mock response configured for question: {question!r}"
            raise KeyError(msg) from exc


class MLXVLMBackend:
    """Lazy MLX-VLM adapter for Qwen3-VL on Apple Silicon Metal."""

    def __init__(
        self,
        model_id: str = QWEN3_VL_MODEL_ID,
        *,
        allow_model_download: bool = False,
        max_tokens: int = 32,
    ) -> None:
        if not model_id.strip():
            raise ValueError("model_id must be non-empty")
        if max_tokens <= 0:
            raise ValueError("max_tokens must be positive")
        self.model_id = model_id
        self.allow_model_download = allow_model_download
        self.max_tokens = max_tokens
        self._model: object | None = None
        self._processor: object | None = None
        self._generate_fn: Callable[..., object] | None = None
        self._apply_chat_template_fn: Callable[..., str] | None = None

    def generate(self, image: object, question: str) -> str:
        """Generate one deterministic, token-bounded answer from an in-memory image."""

        if not question.strip():
            raise ValueError("question must be non-empty")
        self._ensure_loaded()
        if self._generate_fn is None or self._apply_chat_template_fn is None:
            raise RuntimeError("MLX-VLM runtime was not initialized")

        prompt = self._apply_chat_template_fn(
            self._processor,
            cast(_MLXModel, self._model).config,
            question,
            num_images=1,
        )
        output = self._generate_fn(
            self._model,
            self._processor,
            prompt,
            [image],
            max_tokens=self.max_tokens,
            temperature=0.0,
            verbose=False,
        )
        text = output if isinstance(output, str) else getattr(output, "text", None)
        if not isinstance(text, str):
            msg = f"MLX-VLM returned an unsupported generation result: {type(output).__name__}"
            raise RuntimeError(msg)
        return text.strip()

    def _ensure_loaded(self) -> None:
        if self._model is not None:
            return
        if platform.system() != "Darwin" or platform.machine() != "arm64":
            raise VLMSetupError(
                "MLXVLMBackend requires Apple Silicon macOS (Darwin arm64) and uses MLX/Metal."
            )

        try:
            mlx_vlm = importlib.import_module("mlx_vlm")
            prompt_utils = importlib.import_module("mlx_vlm.prompt_utils")
        except (ImportError, ModuleNotFoundError) as exc:
            raise VLMSetupError(
                "MLX-VLM is not installed. Run `uv sync --group vlm` on Apple Silicon macOS."
            ) from exc

        model_path = self.model_id
        if not self.allow_model_download:
            try:
                huggingface_hub = importlib.import_module("huggingface_hub")
                model_path = huggingface_hub.snapshot_download(
                    repo_id=self.model_id,
                    local_files_only=True,
                )
            except Exception as exc:
                raise VLMSetupError(
                    f"Model weights for {self.model_id!r} are not available in the local "
                    "Hugging Face cache. Re-run the CLI with `--allow-model-download` only "
                    "after the download is approved."
                ) from exc

        try:
            model, processor = mlx_vlm.load(model_path)
        except Exception as exc:
            mode = "download/load" if self.allow_model_download else "load from local cache"
            raise VLMSetupError(
                f"Unable to {mode} MLX-VLM model {self.model_id!r}: {exc}"
            ) from exc

        self._model = model
        self._processor = processor
        self._generate_fn = _require_callable(mlx_vlm, "generate")
        self._apply_chat_template_fn = _require_callable(prompt_utils, "apply_chat_template")


def _require_callable(module: object, name: str) -> Callable[..., Any]:
    value = getattr(module, name, None)
    if not callable(value):
        msg = f"MLX-VLM runtime does not expose callable {name!r}"
        raise VLMSetupError(msg)
    return value
