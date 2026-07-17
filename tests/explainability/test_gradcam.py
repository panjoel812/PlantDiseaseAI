import pytest
import torch
from torch import nn

from plantdisease.explainability.gradcam import GradCAM


class TinyCamModel(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.conv = nn.Conv2d(3, 4, kernel_size=3, padding=1)
        self.relu = nn.ReLU()
        self.pool = nn.AdaptiveAvgPool2d(1)
        self.fc = nn.Linear(4, 3)

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        features = self.relu(self.conv(inputs))
        return self.fc(self.pool(features).flatten(1))


class InvalidOutputModel(TinyCamModel):
    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        return self.relu(self.conv(inputs))


class UnusedLayerModel(TinyCamModel):
    def __init__(self) -> None:
        super().__init__()
        self.unused = nn.Conv2d(3, 4, kernel_size=1)


def make_model() -> TinyCamModel:
    torch.manual_seed(7)
    return TinyCamModel()


def test_generate_returns_aligned_normalized_cpu_heatmaps() -> None:
    model = make_model()
    inputs = torch.randn(1, 3, 11, 13)

    with GradCAM(model, model.conv) as gradcam:
        heatmaps = gradcam.generate(inputs, torch.tensor([1]))

    assert heatmaps.shape == (1, 11, 13)
    assert heatmaps.device.type == "cpu"
    assert heatmaps.dtype == torch.float32
    assert torch.isfinite(heatmaps).all()
    assert float(heatmaps.min()) >= 0.0
    assert float(heatmaps.max()) <= 1.0


def test_generate_supports_per_sample_batch_targets() -> None:
    model = make_model()
    inputs = torch.randn(2, 3, 9, 7)

    with GradCAM(model, model.conv) as gradcam:
        heatmaps = gradcam.generate(inputs, torch.tensor([0, 2]))

    assert heatmaps.shape == (2, 9, 7)


def test_default_targets_match_explicit_predicted_classes() -> None:
    model = make_model().eval()
    inputs = torch.randn(2, 3, 8, 10)
    with torch.inference_mode():
        predicted_classes = model(inputs).argmax(dim=1)

    with GradCAM(model, model.conv) as gradcam:
        implicit = gradcam.generate(inputs)
        explicit = gradcam.generate(inputs, predicted_classes)

    assert torch.allclose(implicit, explicit)


def test_generate_enables_autograd_inside_outer_inference_mode() -> None:
    model = make_model().eval()
    inputs = torch.randn(1, 3, 8, 10)

    with GradCAM(model, model.conv) as gradcam, torch.inference_mode():
        heatmaps = gradcam.generate(inputs)

    assert heatmaps.shape == (1, 8, 10)
    assert torch.isfinite(heatmaps).all()


def test_zero_activations_return_zero_heatmap_without_nan() -> None:
    model = make_model()
    nn.init.zeros_(model.conv.weight)
    nn.init.zeros_(model.conv.bias)

    with GradCAM(model, model.conv) as gradcam:
        heatmaps = gradcam.generate(torch.randn(1, 3, 6, 6), torch.tensor([0]))

    assert torch.equal(heatmaps, torch.zeros_like(heatmaps))
    assert torch.isfinite(heatmaps).all()


@pytest.mark.parametrize(
    ("inputs", "message"),
    [
        (torch.zeros(3, 8, 8), "NCHW"),
        (torch.zeros(1, 3, 8, 8, dtype=torch.long), "floating point"),
        (torch.zeros(0, 3, 8, 8), "non-empty"),
    ],
)
def test_generate_rejects_invalid_inputs(inputs: torch.Tensor, message: str) -> None:
    model = make_model()

    with GradCAM(model, model.conv) as gradcam, pytest.raises(ValueError, match=message):
        gradcam.generate(inputs)


@pytest.mark.parametrize(
    ("targets", "message"),
    [
        (torch.tensor([[0]]), "shape"),
        (torch.tensor([0.0]), "integer"),
        (torch.tensor([3]), "range"),
    ],
)
def test_generate_rejects_invalid_target_classes(
    targets: torch.Tensor,
    message: str,
) -> None:
    model = make_model()

    with GradCAM(model, model.conv) as gradcam, pytest.raises(ValueError, match=message):
        gradcam.generate(torch.randn(1, 3, 8, 8), targets)


def test_generate_rejects_non_logit_model_output() -> None:
    model = InvalidOutputModel()

    with (
        GradCAM(model, model.conv) as gradcam,
        pytest.raises(ValueError, match="two-dimensional logits"),
    ):
        gradcam.generate(torch.randn(1, 3, 8, 8))


def test_generate_rejects_target_layer_not_used_by_forward() -> None:
    model = UnusedLayerModel()

    with (
        GradCAM(model, model.unused) as gradcam,
        pytest.raises(RuntimeError, match="target layer was not executed"),
    ):
        gradcam.generate(torch.randn(1, 3, 8, 8))


def test_generate_preserves_parameter_gradients() -> None:
    model = make_model()
    first_parameter = next(model.parameters())
    first_parameter.grad = torch.ones_like(first_parameter)
    before = {
        name: None if parameter.grad is None else parameter.grad.clone()
        for name, parameter in model.named_parameters()
    }

    with GradCAM(model, model.conv) as gradcam:
        gradcam.generate(torch.randn(1, 3, 8, 8))

    for name, parameter in model.named_parameters():
        expected = before[name]
        if expected is None:
            assert parameter.grad is None
        else:
            assert torch.equal(parameter.grad, expected)


def test_generate_restores_training_state_after_success() -> None:
    model = make_model().train()

    with GradCAM(model, model.conv) as gradcam:
        gradcam.generate(torch.randn(1, 3, 8, 8))
        assert model.training


def test_generate_restores_training_state_after_error() -> None:
    model = make_model().train()

    with GradCAM(model, model.conv) as gradcam:
        with pytest.raises(ValueError, match="range"):
            gradcam.generate(torch.randn(1, 3, 8, 8), torch.tensor([9]))
        assert model.training


def test_context_removes_hook_without_accumulating_hooks() -> None:
    model = make_model()
    hook_count = len(model.conv._forward_hooks)

    with GradCAM(model, model.conv) as gradcam:
        assert len(model.conv._forward_hooks) == hook_count + 1
        gradcam.generate(torch.randn(1, 3, 8, 8))
        gradcam.generate(torch.randn(1, 3, 8, 8))
        assert len(model.conv._forward_hooks) == hook_count + 1

    assert len(model.conv._forward_hooks) == hook_count


def test_close_is_idempotent() -> None:
    model = make_model()
    hook_count = len(model.conv._forward_hooks)
    gradcam = GradCAM(model, model.conv)

    gradcam.close()
    gradcam.close()

    assert len(model.conv._forward_hooks) == hook_count


def test_closed_instance_rejects_generate() -> None:
    model = make_model()
    gradcam = GradCAM(model, model.conv)
    gradcam.close()

    with pytest.raises(RuntimeError, match="closed"):
        gradcam.generate(torch.randn(1, 3, 8, 8))


def test_generate_rejects_model_input_device_mismatch() -> None:
    model = make_model().to("meta")

    with (
        GradCAM(model, model.conv) as gradcam,
        pytest.raises(ValueError, match="same device"),
    ):
        gradcam.generate(torch.randn(1, 3, 8, 8))
