"""Cached service construction for interactive demo runtimes."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import torch

from plantdisease.serving.service import InferenceService


@lru_cache(maxsize=4)
def get_cached_service(
    checkpoint_path: Path,
    *,
    crop_checkpoint_path: Path | None = None,
    device_name: str = "cpu",
    target_layer_name: str | None = None,
) -> InferenceService:
    """Return a cached `InferenceService` for a checkpoint/device/layer tuple."""
    return InferenceService.from_checkpoint(
        Path(checkpoint_path),
        device=_resolve_device(device_name),
        target_layer_name=target_layer_name,
        crop_checkpoint_path=crop_checkpoint_path,
    )


def _resolve_device(device_name: str) -> torch.device:
    if device_name == "auto":
        if torch.cuda.is_available():
            return torch.device("cuda")
        if torch.backends.mps.is_available():
            return torch.device("mps")
        return torch.device("cpu")
    if device_name not in {"cpu", "cuda", "mps"}:
        raise ValueError("device_name must be one of: auto, cpu, cuda, mps")
    if device_name == "cuda" and not torch.cuda.is_available():
        raise ValueError("CUDA device requested but not available")
    if device_name == "mps" and not torch.backends.mps.is_available():
        raise ValueError("MPS device requested but not available")
    return torch.device(device_name)
