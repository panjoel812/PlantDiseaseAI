from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from PIL import Image


def _load_generator():
    path = Path("scripts/generate_hierarchical_architecture.py")
    spec = spec_from_file_location("hierarchical_architecture", path)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_architecture_generator_writes_required_stages(tmp_path: Path) -> None:
    module = _load_generator()
    svg = tmp_path / "architecture.svg"
    png = tmp_path / "architecture.png"

    module.render_architecture(svg, png)

    text = svg.read_text(encoding="utf-8")
    for label in (
        "Target leaf",
        "Plant identity",
        "Crop support gate",
        "OpenCV morphology",
        "Corn abiotic gate",
        "Crop-specific conditions",
        "Evidence &amp; guidance gates",
    ):
        assert label in text
    with Image.open(png) as image:
        assert image.size == (3200, 1800)
        assert image.mode in {"RGB", "RGBA"}
