from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from PIL import Image

from plantdisease.models.checkpoint import save_checkpoint
from plantdisease.models.factory import create_model


def _load_demo_module():
    module_path = Path("scripts/demo_e2e.py")
    spec = importlib.util.spec_from_file_location("demo_e2e_for_test", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_demo_e2e_writes_prediction_json_for_checkpoint(tmp_path) -> None:
    checkpoint_path = tmp_path / "checkpoint.pt"
    image_path = tmp_path / "leaf.png"
    output_path = tmp_path / "result.json"

    model = create_model("mobilenet_v2", num_classes=3, pretrained=False)
    save_checkpoint(
        checkpoint_path,
        model,
        ["Apple___healthy", "Tomato___Late_blight", "Potato___Early_blight"],
        {"model_name": "mobilenet_v2", "num_classes": 3, "image_size": 32},
    )
    Image.new("RGB", (40, 40), (64, 128, 32)).save(image_path)

    module = _load_demo_module()
    module.main(
        [
            "--checkpoint",
            str(checkpoint_path),
            "--image",
            str(image_path),
            "--output",
            str(output_path),
            "--top-k",
            "3",
            "--no-gradcam",
        ]
    )

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["status"] == "completed"
    assert payload["model_name"] == "mobilenet_v2"
    assert len(payload["predictions"]) == 3
    assert payload["gradcam_overlay"] is None
    if payload["knowledge"] is None:
        assert payload["hierarchy"]["selected_class_name"] is None
        assert payload["hierarchy"]["disease_confident"] is False
    else:
        assert payload["knowledge"]["plant"] in {"Apple", "Tomato", "Potato"}
