from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

import streamlit as st

from plantdisease.serving.cache import get_cached_service
from plantdisease.serving.images import InputValidationError
from plantdisease.serving.service import InferenceServiceError

DEFAULT_CHECKPOINT = Path(
    "outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/checkpoint.pt"
)
DEFAULT_CROP_CHECKPOINT = Path(
    "outputs/openleaf/leaf114_uci100_pv14_balanced_seed42/checkpoint.pt"
)
DEFAULT_EXAMPLE_IMAGE = Path("app/examples/field_corn_leaf.jpeg")
_FIXED_EXAMPLE_STATE_KEY = "fixed_example_bytes"
RESEARCH_DEMO_COPY = "Research demo · PlantVillage closed set"
FIXED_EXAMPLE_COPY = (
    "User-supplied field corn leaf · no verified ground truth · out-of-domain example"
)
SAFETY_BOUNDARY_COPY = (
    "Educational use only — not a professional diagnosis. "
    "Unknown diseases and field images may fail; consult a local plant-health expert."
)

APPLE_THEME_CSS = """
<style>
:root {
  --pda-ink: #050608;
  --pda-paper: #F5F5F7;
  --pda-text: #1D1D1F;
  --pda-muted: #6E6E73;
  --pda-blue: #0071E3;
  --pda-green: #30D158;
  --pda-amber: #FF9F0A;
  --pda-red: #FF453A;
}
.stApp { background: var(--pda-paper); color: var(--pda-text); }
[data-testid="stHeader"] { background: rgba(245, 245, 247, 0.78); }
.pda-hero {
  background: var(--pda-ink);
  border-radius: 32px;
  padding: 48px 52px;
  color: var(--pda-paper);
}
.pda-kicker {
  color: var(--pda-green);
  font-weight: 700;
  letter-spacing: .12em;
  text-transform: uppercase;
}
.pda-hero h1 {
  color: var(--pda-paper);
  font-size: clamp(3rem, 7vw, 6rem);
  letter-spacing: -.055em;
  line-height: .94;
}
.pda-hero p { color: rgba(245, 245, 247, .78); font-size: 1.18rem; max-width: 760px; }
.pda-safety {
  border-left: 4px solid var(--pda-amber);
  padding: 16px 20px;
  background: var(--pda-paper);
  border-radius: 18px;
}
[data-testid="stMetric"] {
  background: var(--pda-paper);
  border: 1px solid rgba(5, 6, 8, .06);
  border-radius: 20px;
  padding: 18px;
}
[data-testid="stMain"] .stButton > button:not([kind="primary"]),
[data-testid="stMain"] [data-testid="stFileUploader"] button {
  background: var(--pda-paper) !important;
  color: var(--pda-text) !important;
  border: 1px solid var(--pda-text) !important;
}
[data-testid="stMain"] .stButton > button[kind="primary"] {
  background: var(--pda-ink) !important;
  color: var(--pda-paper) !important;
  border: 1px solid var(--pda-ink) !important;
}
[data-testid="stMain"] .stButton > button *,
[data-testid="stMain"] [data-testid="stFileUploader"] button * {
  color: inherit !important;
}
[data-testid="stMain"] .stButton > button:focus-visible,
[data-testid="stMain"] [data-testid="stFileUploader"] button:focus-visible {
  outline: 3px solid var(--pda-blue) !important;
  outline-offset: 3px;
}
[data-testid="stMain"] [data-testid="stMetricLabel"],
[data-testid="stMain"] [data-testid="stMetricLabel"] *,
[data-testid="stMain"] [data-testid="stMetricValue"],
[data-testid="stMain"] [data-testid="stMetricValue"] *,
[data-testid="stMain"] [data-testid="stTable"] th,
[data-testid="stMain"] [data-testid="stTable"] td,
[data-testid="stMain"] [data-testid^="stAlertContent"],
[data-testid="stMain"] [data-testid^="stAlertContent"] * {
  color: var(--pda-text) !important;
}
</style>
"""


def _inject_apple_theme() -> None:
    st.markdown(APPLE_THEME_CSS, unsafe_allow_html=True)


def _format_result_status(prediction_count: int) -> str:
    return f"Inference complete · Top-{prediction_count} prediction evidence"


def _resolve_image_bytes(
    *,
    uploaded_bytes: bytes | None,
    selected_example_bytes: bytes | None,
    persisted_example_bytes: bytes | None,
) -> tuple[bytes | None, bytes | None]:
    stored_example_bytes = (
        selected_example_bytes
        if selected_example_bytes is not None
        else persisted_example_bytes
    )
    if uploaded_bytes is not None:
        return uploaded_bytes, stored_example_bytes
    return stored_example_bytes, stored_example_bytes


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the PlantDiseaseAI Streamlit demo")
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda", "mps"], default="cpu")
    parser.add_argument("--target-layer")
    parser.add_argument("--top-k", type=int, default=5)
    return parser.parse_args(argv)


@st.cache_resource(show_spinner=False)
def _streamlit_cached_service(
    checkpoint_path: Path,
    device_name: str,
    target_layer_name: str | None,
):
    return get_cached_service(
        checkpoint_path,
        crop_checkpoint_path=(
            DEFAULT_CROP_CHECKPOINT if DEFAULT_CROP_CHECKPOINT.is_file() else None
        ),
        device_name=device_name,
        target_layer_name=target_layer_name,
    )


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    st.set_page_config(page_title="PlantDiseaseAI Demo", layout="wide")
    _inject_apple_theme()
    st.markdown(
        f"""
        <section class="pda-hero">
          <div class="pda-kicker">{RESEARCH_DEMO_COPY}</div>
          <h1>Evidence before diagnosis.</h1>
          <p>Top-5 classification, Grad-CAM relevance, and explicit limits
          from one auditable serving layer.</p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        checkpoint_path = Path(
            st.text_input("Checkpoint", value=str(args.checkpoint), help="Local .pt path")
        )
        device_name = st.selectbox(
            "Device",
            ["cpu", "auto", "cuda", "mps"],
            index=["cpu", "auto", "cuda", "mps"].index(args.device),
        )
        target_layer = st.text_input("Grad-CAM target layer", value=args.target_layer or "")
        top_k = st.slider("Top-K", min_value=1, max_value=10, value=args.top_k)
        include_gradcam = st.checkbox("Grad-CAM", value=True)

    uploaded = st.file_uploader("上传叶片图片", type=["png", "jpg", "jpeg", "webp"])
    use_example = DEFAULT_EXAMPLE_IMAGE.exists() and st.button("使用固定示例")
    st.caption(FIXED_EXAMPLE_COPY)
    selected_example_bytes = DEFAULT_EXAMPLE_IMAGE.read_bytes() if use_example else None
    image_bytes, stored_example_bytes = _resolve_image_bytes(
        uploaded_bytes=uploaded.getvalue() if uploaded is not None else None,
        selected_example_bytes=selected_example_bytes,
        persisted_example_bytes=st.session_state.get(_FIXED_EXAMPLE_STATE_KEY),
    )
    if stored_example_bytes is not None:
        st.session_state[_FIXED_EXAMPLE_STATE_KEY] = stored_example_bytes

    if not checkpoint_path.exists():
        st.warning(f"未找到 checkpoint：{checkpoint_path}")

    if image_bytes is None:
        st.info("上传图片或使用固定示例后开始预测。")
        return

    if st.button("开始预测", type="primary"):
        try:
            with st.spinner("正在推理..."):
                service = _streamlit_cached_service(
                    checkpoint_path,
                    device_name,
                    target_layer or None,
                )
                result = service.predict(
                    image_bytes,
                    top_k=top_k,
                    include_gradcam=include_gradcam,
                )
        except InputValidationError as exc:
            st.error(f"输入图片不可用：{exc}")
            return
        except InferenceServiceError as exc:
            st.error(f"推理失败：{exc}")
            return
        except (OSError, ValueError) as exc:
            st.error(f"配置不可用：{exc}")
            return
        _render_result(result)


def _render_result(result) -> None:
    top = result.predictions[0]
    st.caption(_format_result_status(len(result.predictions)))
    st.subheader(f"{top.class_name} · {top.probability:.2%}")
    metric_cols = st.columns(4)
    metric_cols[0].metric("Model", result.model_name)
    metric_cols[1].metric("Total", f"{result.timings.total_ms:.1f} ms")
    metric_cols[2].metric("Prediction", f"{result.timings.prediction_ms:.1f} ms")
    metric_cols[3].metric("Grad-CAM", f"{result.timings.gradcam_ms:.1f} ms")

    st.table(
        [
            {
                "rank": index + 1,
                "class": item.class_name,
                "probability": f"{item.probability:.4f}",
            }
            for index, item in enumerate(result.predictions)
        ]
    )

    knowledge = result.knowledge
    st.markdown(
        "\n".join(
            [
                f"**Plant:** {knowledge.plant}",
                f"**Condition:** {knowledge.condition}",
                f"**Symptoms:** {knowledge.symptoms}",
                f"**Note:** {knowledge.educational_note}",
            ]
        )
    )
    for warning in result.warnings:
        st.warning(warning)

    if result.gradcam is not None:
        image_cols = st.columns(2)
        image_cols[0].image(result.gradcam.heatmap, caption="Grad-CAM heatmap")
        image_cols[1].image(result.gradcam.overlay, caption="Overlay")

    st.caption(
        f"checkpoint={result.checkpoint_path} · id={result.checkpoint_id} · "
        f"image_size={result.image_size} · target_layer={result.target_layer_name}"
    )
    st.markdown(
        f'<div class="pda-safety">{SAFETY_BOUNDARY_COPY}</div>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
