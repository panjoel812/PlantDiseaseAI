"""Native PyTorch Grad-CAM with explicit lifecycle guarantees."""

from __future__ import annotations

import torch
from torch import nn
from torch.nn import functional as F
from torch.utils.hooks import RemovableHandle


class GradCAM:
    """Generate normalized class-activation heatmaps for a spatial target module."""

    def __init__(self, model: nn.Module, target_layer: nn.Module) -> None:
        self.model = model
        self.target_layer = target_layer
        self._activation: torch.Tensor | None = None
        self._closed = False
        self._hook: RemovableHandle | None = target_layer.register_forward_hook(
            self._capture_activation
        )

    def _capture_activation(
        self,
        _module: nn.Module,
        _inputs: tuple[object, ...],
        output: object,
    ) -> None:
        if not isinstance(output, torch.Tensor) or output.ndim != 4:
            raise RuntimeError("Grad-CAM target layer must return an NCHW tensor")
        self._activation = output

    def _model_device(self) -> torch.device | None:
        parameter = next(self.model.parameters(), None)
        if parameter is not None:
            return parameter.device
        buffer = next(self.model.buffers(), None)
        return None if buffer is None else buffer.device

    def _validate_inputs(self, inputs: torch.Tensor) -> None:
        if inputs.ndim != 4:
            raise ValueError("inputs must be an NCHW tensor")
        if not torch.is_floating_point(inputs):
            raise ValueError("inputs must use a floating point dtype")
        if inputs.shape[0] == 0:
            raise ValueError("inputs batch must be non-empty")
        model_device = self._model_device()
        if model_device is not None and model_device != inputs.device:
            raise ValueError("model and inputs must be on the same device")

    @staticmethod
    def _validate_logits(logits: object, batch_size: int) -> torch.Tensor:
        if not isinstance(logits, torch.Tensor) or logits.ndim != 2:
            raise ValueError("model must return two-dimensional logits")
        if logits.shape[0] != batch_size or logits.shape[1] == 0:
            raise ValueError("model logits shape must be (batch, classes)")
        return logits

    @staticmethod
    def _select_targets(
        logits: torch.Tensor,
        target_classes: torch.Tensor | None,
    ) -> torch.Tensor:
        if target_classes is None:
            return logits.argmax(dim=1)
        if target_classes.shape != (logits.shape[0],):
            raise ValueError("target_classes shape must be (batch,)")
        integer_dtypes = {
            torch.uint8,
            torch.int8,
            torch.int16,
            torch.int32,
            torch.int64,
        }
        if target_classes.dtype not in integer_dtypes:
            raise ValueError("target_classes must use an integer dtype")
        targets = target_classes.clone().to(device=logits.device, dtype=torch.long)
        if bool(((targets < 0) | (targets >= logits.shape[1])).any()):
            raise ValueError("target_classes values are outside the class range")
        return targets

    @staticmethod
    def _normalize(heatmaps: torch.Tensor) -> torch.Tensor:
        shifted = heatmaps - heatmaps.amin(dim=(1, 2), keepdim=True)
        maxima = shifted.amax(dim=(1, 2), keepdim=True)
        normalized = shifted / maxima.clamp_min(torch.finfo(shifted.dtype).eps)
        return torch.where(maxima > 0, normalized, torch.zeros_like(normalized))

    def generate(
        self,
        inputs: torch.Tensor,
        target_classes: torch.Tensor | None = None,
    ) -> torch.Tensor:
        """Return one input-aligned, normalized heatmap per batch item."""
        if self._closed:
            raise RuntimeError("GradCAM instance is closed")
        self._validate_inputs(inputs)
        original_training = self.model.training
        self._activation = None
        try:
            self.model.eval()
            with torch.inference_mode(False), torch.enable_grad():
                logits = self._validate_logits(self.model(inputs), inputs.shape[0])
                activation = self._activation
                if activation is None:
                    raise RuntimeError("Grad-CAM target layer was not executed")
                targets = self._select_targets(logits, target_classes)
                scores = logits.gather(1, targets.unsqueeze(1)).sum()
                gradients = torch.autograd.grad(scores, activation)[0]
                weights = gradients.mean(dim=(2, 3), keepdim=True)
                heatmaps = torch.relu((weights * activation).sum(dim=1, keepdim=True))
                heatmaps = F.interpolate(
                    heatmaps,
                    size=inputs.shape[-2:],
                    mode="bilinear",
                    align_corners=False,
                ).squeeze(1)
                heatmaps = self._normalize(heatmaps)
                return heatmaps.detach().to(device="cpu", dtype=torch.float32)
        finally:
            self.model.train(original_training)

    def close(self) -> None:
        """Remove the registered hook; repeated calls are safe."""
        if self._hook is not None:
            self._hook.remove()
            self._hook = None
        self._activation = None
        self._closed = True

    def __enter__(self) -> GradCAM:
        if self._closed:
            raise RuntimeError("GradCAM instance is closed")
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()
