from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import torch

import plantdisease.serving.cache as cache
from plantdisease.serving.cache import get_cached_service


@dataclass(frozen=True)
class ServiceMarker:
    checkpoint_path: Path
    device: torch.device
    target_layer_name: str | None


def test_get_cached_service_reuses_loaded_instance_for_identical_key(monkeypatch) -> None:
    calls: list[tuple[Path, torch.device, str | None]] = []

    def fake_from_checkpoint(
        checkpoint_path: Path,
        *,
        device: torch.device,
        target_layer_name: str | None = None,
        crop_checkpoint_path: Path | None = None,
        prototype_index_path: Path | None = None,
    ) -> ServiceMarker:
        calls.append((checkpoint_path, device, target_layer_name))
        return ServiceMarker(checkpoint_path, device, target_layer_name)

    monkeypatch.setattr(cache.InferenceService, "from_checkpoint", fake_from_checkpoint)
    get_cached_service.cache_clear()

    first = get_cached_service(Path("model.pt"), device_name="cpu")
    second = get_cached_service(Path("model.pt"), device_name="cpu")
    with_layer = get_cached_service(
        Path("model.pt"),
        device_name="cpu",
        target_layer_name="layer4.2",
    )

    assert first is second
    assert with_layer is not first
    assert calls == [
        (Path("model.pt"), torch.device("cpu"), None),
        (Path("model.pt"), torch.device("cpu"), "layer4.2"),
    ]
