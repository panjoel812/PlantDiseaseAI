from pathlib import Path

import torch
from PIL import Image

from plantdisease.explainability.visualization import (
    heatmap_to_image,
    overlay_heatmap,
    safe_filename,
    save_gradcam_panel,
)


def test_heatmap_overlay_and_panel_write_rgb_images(tmp_path: Path) -> None:
    image = Image.new("RGB", (12, 8), (40, 120, 60))
    heatmap = torch.linspace(0, 1, 96).reshape(8, 12)

    heatmap_image = heatmap_to_image(heatmap)
    overlay = overlay_heatmap(image, heatmap, alpha=0.5)
    output = tmp_path / "panel.png"
    save_gradcam_panel(
        original=image,
        heatmap_image=heatmap_image,
        overlay=overlay,
        metadata={
            "group": "correct_high_confidence",
            "sample_id": "hf-test-7",
            "test_index": 7,
            "true_class_name": "healthy",
            "predicted_class_name": "healthy",
            "confidence": 0.99,
            "target_class_name": "healthy",
        },
        output_path=output,
    )

    assert heatmap_image.mode == "RGB"
    assert overlay.mode == "RGB"
    assert heatmap_image.size == (12, 8)
    assert output.exists()
    assert Image.open(output).size[0] > 12


def test_safe_filename_removes_path_unsafe_characters() -> None:
    assert safe_filename("Tomato / Late blight?") == "Tomato_Late_blight"
