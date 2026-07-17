import tomllib
from pathlib import Path
from types import SimpleNamespace

import pytest
from PIL import Image

import plantdisease.vlm.backends as backends_module
from plantdisease.vlm.backends import (
    MLXVLMBackend,
    MockVLMBackend,
    VLMBackend,
    VLMSetupError,
)


def test_vlm_dependency_group_is_apple_silicon_only() -> None:
    project_root = Path(__file__).resolve().parents[2]
    pyproject = tomllib.loads((project_root / "pyproject.toml").read_text(encoding="utf-8"))

    dependencies = pyproject["dependency-groups"]["vlm"]

    assert len(dependencies) == 1
    assert dependencies[0].startswith("mlx-vlm>=0.5,<0.6")
    assert "sys_platform == 'darwin'" in dependencies[0]
    assert "platform_machine == 'arm64'" in dependencies[0]
    assert not any(
        forbidden in dependency
        for dependency in dependencies
        for forbidden in ("flash-attn", "bitsandbytes", "auto-gptq")
    )


def test_mock_backend_satisfies_protocol_and_is_deterministic() -> None:
    image = object()
    backend = MockVLMBackend(
        {
            "Which plant is shown?": "Apple",
            "Is it healthy?": "healthy",
        }
    )

    assert isinstance(backend, VLMBackend)
    assert backend.generate(image, "Which plant is shown?") == "Apple"
    assert backend.generate(image, "Which plant is shown?") == "Apple"
    assert backend.calls == [
        (image, "Which plant is shown?"),
        (image, "Which plant is shown?"),
    ]
    with pytest.raises(KeyError, match="No mock response"):
        backend.generate(image, "Unknown question")


def test_mlx_backend_defers_import_and_reports_missing_dependency(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    imports: list[str] = []

    def missing_import(name: str):
        imports.append(name)
        raise ModuleNotFoundError(name)

    monkeypatch.setattr(backends_module.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(backends_module.platform, "machine", lambda: "arm64")
    monkeypatch.setattr(backends_module.importlib, "import_module", missing_import)

    backend = MLXVLMBackend()

    assert imports == []
    with pytest.raises(VLMSetupError, match="uv sync --group vlm"):
        backend.generate(Image.new("RGB", (4, 4)), "Which plant is shown?")
    assert imports == ["mlx_vlm"]


def test_mlx_backend_does_not_download_missing_weights_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    load_called = False

    def fake_load(_model_path: str):
        nonlocal load_called
        load_called = True
        return object(), object()

    def local_snapshot_missing(**_kwargs):
        raise OSError("snapshot is not cached")

    modules = {
        "mlx_vlm": SimpleNamespace(load=fake_load, generate=lambda *_args, **_kwargs: ""),
        "mlx_vlm.prompt_utils": SimpleNamespace(apply_chat_template=lambda *_args, **_kwargs: ""),
        "huggingface_hub": SimpleNamespace(snapshot_download=local_snapshot_missing),
    }
    monkeypatch.setattr(backends_module.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(backends_module.platform, "machine", lambda: "arm64")
    monkeypatch.setattr(backends_module.importlib, "import_module", modules.__getitem__)

    backend = MLXVLMBackend()

    with pytest.raises(VLMSetupError, match="allow-model-download"):
        backend.generate(Image.new("RGB", (4, 4)), "Which plant is shown?")
    assert load_called is False


def test_mlx_backend_applies_chat_template_and_deterministic_generation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}
    model = SimpleNamespace(config={"model_type": "qwen3_vl"})
    processor = object()

    def fake_load(model_path: str):
        captured["model_path"] = model_path
        return model, processor

    def fake_apply_chat_template(
        actual_processor: object,
        config: object,
        question: str,
        *,
        num_images: int,
    ) -> str:
        captured["template"] = (actual_processor, config, question, num_images)
        return f"formatted::{question}"

    def fake_generate(
        actual_model: object,
        actual_processor: object,
        prompt: str,
        image: list[object],
        *,
        max_tokens: int,
        temperature: float,
        verbose: bool,
    ) -> object:
        captured["generate"] = {
            "model": actual_model,
            "processor": actual_processor,
            "prompt": prompt,
            "image": image,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "verbose": verbose,
        }
        return SimpleNamespace(text="  Apple\n")

    modules = {
        "mlx_vlm": SimpleNamespace(load=fake_load, generate=fake_generate),
        "mlx_vlm.prompt_utils": SimpleNamespace(apply_chat_template=fake_apply_chat_template),
    }
    monkeypatch.setattr(backends_module.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(backends_module.platform, "machine", lambda: "arm64")
    monkeypatch.setattr(backends_module.importlib, "import_module", modules.__getitem__)

    image = Image.new("RGB", (4, 4))
    backend = MLXVLMBackend(allow_model_download=True, max_tokens=32)

    answer = backend.generate(image, "Which plant is shown?")

    assert answer == "Apple"
    assert captured["model_path"] == "mlx-community/Qwen3-VL-4B-Instruct-4bit"
    assert captured["template"] == (
        processor,
        model.config,
        "Which plant is shown?",
        1,
    )
    assert captured["generate"] == {
        "model": model,
        "processor": processor,
        "prompt": "formatted::Which plant is shown?",
        "image": [image],
        "max_tokens": 32,
        "temperature": 0.0,
        "verbose": False,
    }
