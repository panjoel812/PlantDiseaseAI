"""Generate the public hierarchical-serving architecture as SVG and PNG."""

from __future__ import annotations

import argparse
import os
import tempfile
from collections.abc import Sequence
from pathlib import Path

os.environ.setdefault(
    "MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "plantdisease-matplotlib")
)

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

STAGES = (
    ("01", "Target leaf", "auto isolate or one click"),
    ("02", "Plant identity", "local 114-class routing catalog"),
    ("03", "Crop support gate", "abstain outside supported hosts"),
    ("04", "OpenCV morphology", "coverage · axis · shape · color"),
    ("05A", "Corn abiotic gate", "suspected stress or continue"),
    ("05B", "Crop-specific conditions", "PlantVillage closed set"),
    ("06", "Evidence & guidance gates", "Grad-CAM · Qwen · cloud advice"),
)

INK = "#153A34"
MUTED = "#58766F"
BLUE = "#58A9D2"
GREEN = "#55B889"
MINT = "#DDF4E9"
SKY = "#E4F3FB"
WARM = "#FFF2D9"
CORAL = "#E89C78"
WHITE = "#FFFFFF"


def _background(ax: Axes) -> None:
    width, height = 1200, 675
    x = np.linspace(0, 1, width)[None, :]
    y = np.linspace(0, 1, height)[:, None]
    base = np.ones((height, width, 3), dtype=float)
    base[..., 0] = 0.965 - 0.035 * x + 0.010 * y
    base[..., 1] = 0.985 - 0.005 * x + 0.005 * y
    base[..., 2] = 0.982 + 0.005 * x - 0.025 * y
    ax.imshow(base, extent=(0, 1, 0, 1), origin="lower", aspect="auto", zorder=0)
    for cx, cy, radius, color, alpha in (
        (0.10, 0.18, 0.22, SKY, 0.75),
        (0.88, 0.76, 0.28, MINT, 0.72),
        (0.74, 0.08, 0.16, WARM, 0.45),
    ):
        circle = plt.Circle((cx, cy), radius, color=color, alpha=alpha, linewidth=0)
        ax.add_patch(circle)


def _card(
    ax: Axes,
    *,
    xy: tuple[float, float],
    size: tuple[float, float],
    number: str,
    title: str,
    detail: str,
    tint: str,
    title_size: float = 13.5,
) -> FancyBboxPatch:
    x, y = xy
    width, height = size
    shadow = FancyBboxPatch(
        (x + 0.004, y - 0.008),
        width,
        height,
        boxstyle="round,pad=0.012,rounding_size=0.022",
        linewidth=0,
        facecolor="#6F9E95",
        alpha=0.11,
        zorder=2,
    )
    ax.add_patch(shadow)
    box = FancyBboxPatch(
        (x, y),
        width,
        height,
        boxstyle="round,pad=0.012,rounding_size=0.022",
        linewidth=1.15,
        edgecolor=WHITE,
        facecolor=WHITE,
        alpha=0.86,
        zorder=3,
    )
    ax.add_patch(box)
    badge = FancyBboxPatch(
        (x + 0.014, y + height - 0.047),
        0.040,
        0.030,
        boxstyle="round,pad=0.004,rounding_size=0.012",
        linewidth=0,
        facecolor=tint,
        alpha=0.95,
        zorder=4,
    )
    ax.add_patch(badge)
    ax.text(
        x + 0.034,
        y + height - 0.032,
        number,
        ha="center",
        va="center",
        fontsize=8.2,
        color=INK,
        weight="bold",
        zorder=5,
    )
    ax.text(
        x + 0.014,
        y + height - 0.073,
        title,
        ha="left",
        va="top",
        fontsize=title_size,
        color=INK,
        weight="bold",
        zorder=5,
    )
    ax.text(
        x + 0.014,
        y + 0.028,
        detail,
        ha="left",
        va="bottom",
        fontsize=8.8,
        color=MUTED,
        linespacing=1.25,
        zorder=5,
    )
    return box


def _arrow(
    ax: Axes,
    start: tuple[float, float],
    end: tuple[float, float],
    *,
    color: str = "#7EAAA2",
    dashed: bool = False,
    connectionstyle: str = "arc3,rad=0",
) -> None:
    patch = FancyArrowPatch(
        start,
        end,
        arrowstyle="-|>",
        mutation_scale=12,
        linewidth=1.6,
        linestyle="--" if dashed else "-",
        color=color,
        alpha=0.9,
        connectionstyle=connectionstyle,
        zorder=2,
    )
    ax.add_patch(patch)


def _pill(ax: Axes, x: float, label: str, color: str, width: float) -> None:
    pill = FancyBboxPatch(
        (x, 0.802),
        width,
        0.042,
        boxstyle="round,pad=0.006,rounding_size=0.018",
        linewidth=0,
        facecolor=color,
        alpha=0.88,
        zorder=2,
    )
    ax.add_patch(pill)
    ax.text(
        x + width / 2,
        0.823,
        label,
        ha="center",
        va="center",
        fontsize=8.8,
        color=INK,
        weight="bold",
        zorder=3,
    )


def _evidence_band(
    ax: Axes,
    *,
    x: float,
    width: float,
    title: str,
    detail: str,
    color: str,
) -> None:
    ax.plot([x, x + width], [0.118, 0.118], color=color, linewidth=4.2, solid_capstyle="round")
    ax.text(x, 0.088, title, ha="left", va="center", fontsize=9.8, color=INK, weight="bold")
    ax.text(x, 0.055, detail, ha="left", va="center", fontsize=7.8, color=MUTED)


def build_figure() -> tuple[Figure, Axes]:
    """Return the configured architecture figure and axes."""

    mpl.rcParams["font.family"] = ["Helvetica Neue", "Arial", "DejaVu Sans"]
    mpl.rcParams["svg.fonttype"] = "none"
    fig, ax = plt.subplots(figsize=(16, 9), dpi=200)
    fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    _background(ax)

    ax.text(
        0.045,
        0.932,
        "Evidence-gated plant analysis",
        ha="left",
        va="center",
        fontsize=27,
        color=INK,
        weight="bold",
    )
    ax.text(
        0.045,
        0.885,
        "Identity before condition · morphology before claims · abstention before guidance",
        ha="left",
        va="center",
        fontsize=12.5,
        color=MUTED,
    )
    _pill(ax, 0.628, "VERIFIED CORE", SKY, 0.105)
    _pill(ax, 0.746, "IMPLEMENTED GATES", MINT, 0.128)
    _pill(ax, 0.887, "EXPERIMENTAL", WARM, 0.088)

    main_y, main_h, main_w = 0.535, 0.205, 0.135
    x_positions = (0.045, 0.205, 0.365, 0.525)
    for index, x in enumerate(x_positions):
        number, title, detail = STAGES[index]
        _card(
            ax,
            xy=(x, main_y),
            size=(main_w, main_h),
            number=number,
            title=title,
            detail=detail,
            tint=MINT if index != 3 else SKY,
            title_size=12.8,
        )
        if index:
            _arrow(
                ax,
                (x_positions[index - 1] + main_w + 0.004, 0.638),
                (x - 0.004, 0.638),
            )

    _card(
        ax,
        xy=(0.685, 0.555),
        size=(0.132, 0.185),
        number=STAGES[4][0],
        title=STAGES[4][1],
        detail=STAGES[4][2],
        tint=WARM,
        title_size=12.2,
    )
    _card(
        ax,
        xy=(0.685, 0.295),
        size=(0.132, 0.185),
        number=STAGES[5][0],
        title=STAGES[5][1],
        detail=STAGES[5][2],
        tint=SKY,
        title_size=11.4,
    )
    _card(
        ax,
        xy=(0.845, 0.395),
        size=(0.125, 0.245),
        number=STAGES[6][0],
        title=STAGES[6][1],
        detail="Grad-CAM relevance\nQwen morphology\noptional cloud advice",
        tint=MINT,
        title_size=11.7,
    )

    _arrow(ax, (0.673, 0.638), (0.681, 0.648), connectionstyle="arc3,rad=-0.10")
    _arrow(ax, (0.660, 0.610), (0.681, 0.405), connectionstyle="arc3,rad=0.18")
    ax.text(
        0.661,
        0.661,
        "CORN",
        ha="center",
        va="bottom",
        fontsize=7.4,
        color=CORAL,
        weight="bold",
    )
    ax.text(
        0.662,
        0.477,
        "OTHER HOST",
        ha="center",
        va="bottom",
        fontsize=7.4,
        color=BLUE,
        weight="bold",
    )
    _arrow(ax, (0.829, 0.645), (0.838, 0.555), connectionstyle="arc3,rad=0.12")
    _arrow(ax, (0.829, 0.390), (0.838, 0.474), connectionstyle="arc3,rad=-0.12")

    abstain = FancyBboxPatch(
        (0.378, 0.340),
        0.109,
        0.085,
        boxstyle="round,pad=0.010,rounding_size=0.020",
        linewidth=1.1,
        edgecolor="#F0C6A7",
        facecolor=WARM,
        alpha=0.92,
        zorder=3,
    )
    ax.add_patch(abstain)
    ax.text(
        0.4325,
        0.390,
        "ABSTAIN",
        ha="center",
        va="center",
        fontsize=9.6,
        color=INK,
        weight="bold",
    )
    ax.text(0.4325, 0.365, "no disease claim", ha="center", va="center", fontsize=7.8, color=MUTED)
    _arrow(ax, (0.432, 0.523), (0.432, 0.435), color=CORAL, dashed=True)

    ax.text(
        0.2725,
        0.483,
        "Optional Pl@ntNet only when local identity is uncertain and a key is configured",
        ha="center",
        va="center",
        fontsize=7.5,
        color=MUTED,
    )

    _evidence_band(
        ax,
        x=0.055,
        width=0.265,
        title="VERIFIED EXPERIMENTAL CORE",
        detail="frozen PlantVillage metrics · ablation · error audit · calibration",
        color=BLUE,
    )
    _evidence_band(
        ax,
        x=0.365,
        width=0.275,
        title="IMPLEMENTED SERVING GATES",
        detail="target leaf · host support · morphology · suppression",
        color=GREEN,
    )
    _evidence_band(
        ax,
        x=0.685,
        width=0.270,
        title="EXPERIMENTAL EXTENSIONS",
        detail="broad identity · lesion focus · Qwen · provider guidance",
        color="#E7B36A",
    )
    ax.text(
        0.5,
        0.018,
        "OpenCV = heuristic evidence · Grad-CAM = non-causal relevance · educational use only",
        ha="center",
        va="center",
        fontsize=8.2,
        color=MUTED,
    )
    return fig, ax


def render_architecture(svg_path: Path, png_path: Path) -> None:
    """Render the architecture to SVG and a 3200×1800 PNG."""

    svg_path.parent.mkdir(parents=True, exist_ok=True)
    png_path.parent.mkdir(parents=True, exist_ok=True)
    fig, _ = build_figure()
    try:
        fig.savefig(svg_path, format="svg", dpi=200, facecolor=fig.get_facecolor())
        fig.savefig(png_path, format="png", dpi=200, facecolor=fig.get_facecolor())
    finally:
        plt.close(fig)


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--svg", type=Path, required=True)
    parser.add_argument("--png", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Render requested outputs and return a process status."""

    args = build_parser().parse_args(argv)
    render_architecture(args.svg, args.png)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
