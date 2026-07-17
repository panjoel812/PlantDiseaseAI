from __future__ import annotations

import importlib.util
import re
from pathlib import Path
from types import ModuleType


def _load_streamlit_module() -> ModuleType:
    module_path = Path("app/streamlit_app.py")
    spec = importlib.util.spec_from_file_location("streamlit_app_for_test", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _css_color(css: str, variable: str) -> str:
    match = re.search(rf"--pda-{variable}: (#[0-9A-Fa-f]{{6}});", css)
    assert match is not None
    return match.group(1)


def _relative_luminance(color: str) -> float:
    channels = [int(color[index : index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [
        value / 12.92
        if value <= 0.04045
        else ((value + 0.055) / 1.055) ** 2.4
        for value in channels
    ]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _contrast_ratio(first: str, second: str) -> float:
    lighter, darker = sorted(
        (_relative_luminance(first), _relative_luminance(second)),
        reverse=True,
    )
    return (lighter + 0.05) / (darker + 0.05)


def test_streamlit_app_import_does_not_require_checkpoint() -> None:
    module = _load_streamlit_module()

    assert callable(module.main)
    assert module.DEFAULT_CHECKPOINT.name == "checkpoint.pt"


def test_streamlit_app_exposes_apple_showcase_contract() -> None:
    module = _load_streamlit_module()

    approved_palette = (
        "#F5F5F7",
        "#050608",
        "#1D1D1F",
        "#6E6E73",
        "#0071E3",
        "#30D158",
        "#FF9F0A",
        "#FF453A",
    )
    for color in approved_palette:
        assert color in module.APPLE_THEME_CSS
    assert "white" not in module.APPLE_THEME_CSS.lower()
    assert "#C7C7CC" not in module.APPLE_THEME_CSS
    assert "Research demo" in module.RESEARCH_DEMO_COPY
    assert "not a professional diagnosis" in module.SAFETY_BOUNDARY_COPY
    assert module.DEFAULT_EXAMPLE_IMAGE.name == "field_corn_leaf.jpeg"
    assert "user-supplied" in module.FIXED_EXAMPLE_COPY.lower()
    assert "field" in module.FIXED_EXAMPLE_COPY.lower()
    assert "no verified ground truth" in module.FIXED_EXAMPLE_COPY.lower()
    assert "out-of-domain" in module.FIXED_EXAMPLE_COPY.lower()
    assert callable(module._inject_apple_theme)


def test_streamlit_theme_scopes_main_result_readability() -> None:
    module = _load_streamlit_module()

    readability_selectors = (
        '[data-testid="stMain"] [data-testid="stMetricLabel"]',
        '[data-testid="stMain"] [data-testid="stMetricValue"]',
        '[data-testid="stMain"] [data-testid="stTable"] th',
        '[data-testid="stMain"] [data-testid="stTable"] td',
        '[data-testid="stMain"] [data-testid^="stAlertContent"]',
    )
    for selector in readability_selectors:
        assert selector in module.APPLE_THEME_CSS
    assert "color: var(--pda-text) !important;" in module.APPLE_THEME_CSS
    assert ".stApp *" not in module.APPLE_THEME_CSS


def test_streamlit_theme_scopes_interactive_control_contrast() -> None:
    module = _load_streamlit_module()
    normalized_css = " ".join(module.APPLE_THEME_CSS.split())

    expected_rules = (
        (
            '[data-testid="stMain"] .stButton > button:not([kind="primary"]), '
            '[data-testid="stMain"] [data-testid="stFileUploader"] button { '
            "background: var(--pda-paper) !important; "
            "color: var(--pda-text) !important; "
            "border: 1px solid var(--pda-text) !important; }"
        ),
        (
            '[data-testid="stMain"] .stButton > button[kind="primary"] { '
            "background: var(--pda-ink) !important; "
            "color: var(--pda-paper) !important; "
            "border: 1px solid var(--pda-ink) !important; }"
        ),
        (
            '[data-testid="stMain"] .stButton > button *, '
            '[data-testid="stMain"] [data-testid="stFileUploader"] button * { '
            "color: inherit !important; }"
        ),
        (
            '[data-testid="stMain"] .stButton > button:focus-visible, '
            '[data-testid="stMain"] [data-testid="stFileUploader"] button:focus-visible { '
            "outline: 3px solid var(--pda-blue) !important; "
            "outline-offset: 3px; }"
        ),
    )
    for rule in expected_rules:
        assert rule in normalized_css
    paper = _css_color(module.APPLE_THEME_CSS, "paper")
    ink = _css_color(module.APPLE_THEME_CSS, "ink")
    blue = _css_color(module.APPLE_THEME_CSS, "blue")
    assert _contrast_ratio(paper, ink) >= 4.5
    assert _contrast_ratio(blue, paper) >= 3.0
    assert _contrast_ratio(blue, ink) >= 3.0
    assert ".stApp *" not in module.APPLE_THEME_CSS


def test_streamlit_result_status_uses_actual_prediction_count() -> None:
    module = _load_streamlit_module()

    assert module._format_result_status(1) == "Inference complete · Top-1 prediction evidence"
    assert module._format_result_status(5) == "Inference complete · Top-5 prediction evidence"
    assert module._format_result_status(10) == "Inference complete · Top-10 prediction evidence"


def test_streamlit_fixed_example_persists_across_reruns() -> None:
    module = _load_streamlit_module()
    fixed_example = b"fixed-example"

    first_image, stored_example = module._resolve_image_bytes(
        uploaded_bytes=None,
        selected_example_bytes=fixed_example,
        persisted_example_bytes=None,
    )
    second_image, stored_example = module._resolve_image_bytes(
        uploaded_bytes=None,
        selected_example_bytes=None,
        persisted_example_bytes=stored_example,
    )
    uploaded_image, stored_example = module._resolve_image_bytes(
        uploaded_bytes=b"uploaded-image",
        selected_example_bytes=None,
        persisted_example_bytes=stored_example,
    )

    assert first_image == fixed_example
    assert second_image == fixed_example
    assert uploaded_image == b"uploaded-image"
    assert stored_example == fixed_example
