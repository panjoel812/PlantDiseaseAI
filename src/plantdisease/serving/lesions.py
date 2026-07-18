"""Deterministic OpenCV lesion localization and morphology evidence.

This module deliberately reports visible geometry and colour only.  It does not
map those measurements to a disease label; that would require a separately
validated fusion model rather than hand-written diagnostic rules.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import cv2
import numpy as np
from PIL import Image

LESION_METHOD = "opencv_exg_hsv_components_v1"
MAX_REPORTED_REGIONS = 12


@dataclass(frozen=True)
class ColorShare:
    """One coarse visible colour and its share of lesion pixels."""

    name: str
    proportion: float


@dataclass(frozen=True)
class LesionRegion:
    """Geometry and colour summary for one connected lesion candidate."""

    x: int
    y: int
    width: int
    height: int
    centroid_x: float
    centroid_y: float
    area_pixels: int
    area_percent_of_leaf: float
    circularity: float
    aspect_ratio: float
    shape: str
    color: str


@dataclass(frozen=True)
class LesionAnalysis:
    """Visible leaf and lesion evidence plus an annotated image."""

    method: str
    image_size: tuple[int, int]
    leaf_area_pixels: int
    leaf_coverage_percent: float
    lesion_area_pixels: int
    lesion_coverage_percent: float
    lesion_count: int
    median_lesion_area_percent: float
    largest_lesion_area_percent: float
    mean_circularity: float
    dominant_colors: tuple[ColorShare, ...]
    distribution: str
    regions: tuple[LesionRegion, ...]
    overlay: Image.Image


def analyze_lesions(image: Image.Image) -> LesionAnalysis:
    """Locate non-green regions inside green leaf silhouettes.

    The segmentation is intentionally conservative and resolution-aware.  Kernel
    sizes and component thresholds scale with the image dimensions and estimated
    leaf area so a 224 px model input is not treated like a full-resolution image.
    """

    rgb = np.asarray(image.convert("RGB"), dtype=np.uint8)
    if rgb.ndim != 3 or rgb.shape[2] != 3:
        raise ValueError("expected an RGB image")
    height, width = rgb.shape[:2]
    if height < 16 or width < 16:
        raise ValueError("image is too small for lesion analysis")

    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    red = rgb[:, :, 0].astype(np.int16)
    green = rgb[:, :, 1].astype(np.int16)
    blue = rgb[:, :, 2].astype(np.int16)
    excess_green = 2 * green - red - blue

    healthy_green = (
        (excess_green > 35)
        & (green > 42)
        & (hsv[:, :, 0] >= 30)
        & (hsv[:, :, 0] <= 100)
        & (hsv[:, :, 1] >= 32)
    )
    base = (healthy_green.astype(np.uint8)) * 255
    scale = max(3, _odd(round(min(width, height) * 0.008)))
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (scale, scale))
    base = cv2.morphologyEx(base, cv2.MORPH_OPEN, kernel)
    base = cv2.morphologyEx(base, cv2.MORPH_CLOSE, kernel, iterations=2)

    contours, _ = cv2.findContours(base, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    image_area = width * height
    minimum_leaf_component = max(32.0, image_area * 0.0015)
    leaf_contours = [
        contour for contour in contours if cv2.contourArea(contour) >= minimum_leaf_component
    ]
    leaf_mask = np.zeros((height, width), dtype=np.uint8)
    if leaf_contours:
        cv2.drawContours(leaf_mask, leaf_contours, -1, 255, thickness=cv2.FILLED)
    else:
        leaf_mask = base

    leaf_area = int(cv2.countNonZero(leaf_mask))
    if leaf_area == 0:
        return _empty_analysis(image, LESION_METHOD)

    hue = hsv[:, :, 0]
    saturation = hsv[:, :, 1]
    value = hsv[:, :, 2]
    non_green = ~(
        (hue >= 30)
        & (hue <= 100)
        & (excess_green > 28)
        & (saturation >= 32)
    )
    pale_or_gray = (saturation < 130) & (value > 58)
    tan_or_brown = ((hue < 42) | (hue > 168)) & (value > 38)
    lesion_candidate = (
        (leaf_mask > 0)
        & non_green
        & (pale_or_gray | tan_or_brown)
    )
    lesion_mask = lesion_candidate.astype(np.uint8) * 255
    lesion_kernel_size = max(3, _odd(round(min(width, height) * 0.004)))
    lesion_kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE,
        (lesion_kernel_size, lesion_kernel_size),
    )
    lesion_mask = cv2.morphologyEx(lesion_mask, cv2.MORPH_OPEN, lesion_kernel)
    lesion_mask = cv2.morphologyEx(lesion_mask, cv2.MORPH_CLOSE, lesion_kernel)

    lesion_contours, _ = cv2.findContours(
        lesion_mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE,
    )
    minimum_lesion_area = max(9.0, leaf_area * 0.0002)
    maximum_lesion_area = leaf_area * 0.45
    accepted = [
        contour
        for contour in lesion_contours
        if minimum_lesion_area <= cv2.contourArea(contour) <= maximum_lesion_area
    ]
    accepted.sort(key=cv2.contourArea, reverse=True)

    filtered_mask = np.zeros_like(lesion_mask)
    if accepted:
        cv2.drawContours(filtered_mask, accepted, -1, 255, thickness=cv2.FILLED)
    lesion_area = int(cv2.countNonZero(filtered_mask))

    region_rows = tuple(
        _summarize_region(contour, rgb, filtered_mask, leaf_area)
        for contour in accepted[:MAX_REPORTED_REGIONS]
    )
    area_percentages = [
        float(cv2.contourArea(contour)) / leaf_area * 100.0 for contour in accepted
    ]
    circularities = [_circularity(contour) for contour in accepted]
    dominant_colors = _dominant_colors(rgb, filtered_mask)
    overlay = _render_overlay(rgb, leaf_contours, accepted)

    return LesionAnalysis(
        method=LESION_METHOD,
        image_size=(width, height),
        leaf_area_pixels=leaf_area,
        leaf_coverage_percent=leaf_area / image_area * 100.0,
        lesion_area_pixels=lesion_area,
        lesion_coverage_percent=lesion_area / leaf_area * 100.0,
        lesion_count=len(accepted),
        median_lesion_area_percent=(
            float(np.median(area_percentages)) if area_percentages else 0.0
        ),
        largest_lesion_area_percent=max(area_percentages, default=0.0),
        mean_circularity=float(np.mean(circularities)) if circularities else 0.0,
        dominant_colors=dominant_colors,
        distribution=_distribution_label(region_rows, width, height),
        regions=region_rows,
        overlay=overlay,
    )


def _summarize_region(
    contour: np.ndarray,
    rgb: np.ndarray,
    lesion_mask: np.ndarray,
    leaf_area: int,
) -> LesionRegion:
    x, y, width, height = cv2.boundingRect(contour)
    moments = cv2.moments(contour)
    if moments["m00"]:
        centroid_x = float(moments["m10"] / moments["m00"])
        centroid_y = float(moments["m01"] / moments["m00"])
    else:
        centroid_x = x + width / 2.0
        centroid_y = y + height / 2.0
    area = max(1, round(cv2.contourArea(contour)))
    component = np.zeros_like(lesion_mask)
    cv2.drawContours(component, [contour], -1, 255, thickness=cv2.FILLED)
    pixels = rgb[component > 0]
    mean_rgb = tuple(float(value) for value in pixels.mean(axis=0)) if pixels.size else (0, 0, 0)
    circularity = _circularity(contour)
    aspect_ratio = max(width, height) / max(1, min(width, height))
    return LesionRegion(
        x=int(x),
        y=int(y),
        width=int(width),
        height=int(height),
        centroid_x=centroid_x,
        centroid_y=centroid_y,
        area_pixels=int(area),
        area_percent_of_leaf=area / leaf_area * 100.0,
        circularity=circularity,
        aspect_ratio=aspect_ratio,
        shape=_shape_label(circularity, aspect_ratio),
        color=_color_name(mean_rgb),
    )


def _circularity(contour: np.ndarray) -> float:
    area = float(cv2.contourArea(contour))
    perimeter = float(cv2.arcLength(contour, True))
    if area <= 0.0 or perimeter <= 0.0:
        return 0.0
    return max(0.0, min(1.0, 4.0 * math.pi * area / (perimeter * perimeter)))


def _shape_label(circularity: float, aspect_ratio: float) -> str:
    if aspect_ratio >= 3.0:
        return "linear"
    if circularity >= 0.72 and aspect_ratio <= 1.45:
        return "round"
    if aspect_ratio >= 1.8:
        return "elongated"
    return "irregular"


def _color_name(rgb: tuple[float, float, float]) -> str:
    red, green, blue = rgb
    maximum = max(rgb)
    minimum = min(rgb)
    if maximum < 62:
        return "dark brown"
    if maximum - minimum < 24:
        return "gray" if maximum < 175 else "pale gray"
    if red > green * 1.25 and red > blue * 1.35:
        return "reddish brown"
    if red > blue * 1.2 and green > blue * 1.15:
        return "tan" if maximum > 145 else "brown"
    if maximum > 185 and minimum > 120:
        return "pale"
    return "mixed"


def _dominant_colors(rgb: np.ndarray, mask: np.ndarray) -> tuple[ColorShare, ...]:
    pixels = rgb[mask > 0]
    if not pixels.size:
        return ()
    bins: dict[str, int] = {}
    for pixel in pixels[:: max(1, len(pixels) // 4000)]:
        name = _color_name(tuple(float(value) for value in pixel))
        bins[name] = bins.get(name, 0) + 1
    total = sum(bins.values())
    return tuple(
        ColorShare(name=name, proportion=count / total)
        for name, count in sorted(bins.items(), key=lambda item: (-item[1], item[0]))[:3]
    )


def _distribution_label(
    regions: tuple[LesionRegion, ...],
    width: int,
    height: int,
) -> str:
    if not regions:
        return "no stable lesion components"
    xs = np.asarray([region.centroid_x / width for region in regions])
    ys = np.asarray([region.centroid_y / height for region in regions])
    if len(regions) >= 6 and float(np.std(xs) + np.std(ys)) > 0.34:
        return "widely scattered"
    if float(np.mean(xs)) < 0.35:
        return "left-weighted"
    if float(np.mean(xs)) > 0.65:
        return "right-weighted"
    if float(np.mean(ys)) < 0.35:
        return "upper-weighted"
    if float(np.mean(ys)) > 0.65:
        return "lower-weighted"
    return "clustered near the centre"


def _render_overlay(
    rgb: np.ndarray,
    leaf_contours: list[np.ndarray],
    lesion_contours: list[np.ndarray],
) -> Image.Image:
    overlay = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    tint = overlay.copy()
    if lesion_contours:
        cv2.drawContours(tint, lesion_contours, -1, (74, 119, 242), thickness=cv2.FILLED)
        overlay = cv2.addWeighted(tint, 0.25, overlay, 0.75, 0.0)
        cv2.drawContours(overlay, lesion_contours, -1, (66, 105, 232), thickness=2)
    if leaf_contours:
        cv2.drawContours(overlay, leaf_contours, -1, (103, 186, 93), thickness=2)
    return Image.fromarray(cv2.cvtColor(overlay, cv2.COLOR_BGR2RGB))


def _empty_analysis(image: Image.Image, method: str) -> LesionAnalysis:
    width, height = image.size
    return LesionAnalysis(
        method=method,
        image_size=(width, height),
        leaf_area_pixels=0,
        leaf_coverage_percent=0.0,
        lesion_area_pixels=0,
        lesion_coverage_percent=0.0,
        lesion_count=0,
        median_lesion_area_percent=0.0,
        largest_lesion_area_percent=0.0,
        mean_circularity=0.0,
        dominant_colors=(),
        distribution="leaf not isolated",
        regions=(),
        overlay=image.convert("RGB").copy(),
    )


def _odd(value: int) -> int:
    return value if value % 2 else value + 1


__all__ = [
    "ColorShare",
    "LESION_METHOD",
    "LesionAnalysis",
    "LesionRegion",
    "analyze_lesions",
]
