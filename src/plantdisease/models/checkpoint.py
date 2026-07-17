"""Versioned, portable checkpoint persistence."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import cast

import torch
from torch import nn

from plantdisease.models.factory import create_model


def save_checkpoint(
    path: Path,
    model: nn.Module,
    class_names: Sequence[str],
    config: Mapping[str, object],
) -> None:
    if len(class_names) != int(cast(int | float | str, config.get("num_classes", -1))):
        raise ValueError("class_names length must match config num_classes")
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "schema_version": 1,
            "state_dict": model.state_dict(),
            "class_names": list(class_names),
            "config": dict(config),
        },
        path,
    )


def load_checkpoint(
    path: Path, device: torch.device
) -> tuple[nn.Module, list[str], dict[str, object]]:
    payload = torch.load(path, map_location=device, weights_only=True)
    if payload.get("schema_version") != 1:
        raise ValueError("unsupported checkpoint schema_version")
    config = dict(payload["config"])
    class_names = list(payload["class_names"])
    model = create_model(
        str(config["model_name"]),
        int(config["num_classes"]),
        pretrained=False,
    )
    model.load_state_dict(payload["state_dict"])
    return model.to(device), class_names, config
