"""Leaf-only OpenCV preparation for plant-first hierarchical recognition."""

from __future__ import annotations

import math
from dataclasses import dataclass, replace

import cv2
import numpy as np
from PIL import Image

from plantdisease.serving.lesions import LesionAnalysis, analyze_lesions

LEAF_ISOLATION_METHOD = "opencv_target_leaf_v2"
LEAF_COVERAGE_RANGE = (3.0, 85.0)
MAX_BORDER_TOUCH_RATIO = 0.18
MIN_PROBABLE_FOREGROUND_RETENTION = 0.60
MIN_AXIS_BAND_RETENTION = 0.80


@dataclass(frozen=True)
class TargetPoint:
    """One normalized source-image point selected by the user."""

    x: float
    y: float

    def __post_init__(self) -> None:
        if not (
            math.isfinite(self.x)
            and math.isfinite(self.y)
            and 0.0 <= self.x <= 1.0
            and 0.0 <= self.y <= 1.0
        ):
            raise ValueError("target coordinates must be finite numbers between 0 and 1")


@dataclass(frozen=True)
class LeafShapeFeatures:
    """Scale-independent outline measurements for audit or later feature fusion."""

    area_pixels: int
    coverage_percent: float
    aspect_ratio: float
    circularity: float
    solidity: float
    extent: float
    border_touch_ratio: float
    component_dominance: float

    def as_vector(self) -> tuple[float, ...]:
        return (
            self.aspect_ratio,
            self.circularity,
            self.solidity,
            self.extent,
            self.border_touch_ratio,
            self.component_dominance,
        )


@dataclass(frozen=True)
class LeafPurityEvidence:
    """Auditable mask-quality measurements used before model inference."""

    accepted: bool
    coverage_percent: float
    border_touch_ratio: float
    fragment_count: int
    click_contained: bool | None
    probable_foreground_retention: float | None
    principal_axis_aspect_ratio: float
    axis_band_retention: float | None
    coverage_range: tuple[float, float]
    max_border_touch_ratio: float
    min_probable_foreground_retention: float
    min_axis_band_retention: float
    reason: str


@dataclass(frozen=True)
class LeafIsolation:
    """Accepted leaf mask and model-ready cutout, or an explicit rejection."""

    method: str
    selection_mode: str
    target_point: TargetPoint | None
    purity: LeafPurityEvidence
    accepted: bool
    reason: str
    image_size: tuple[int, int]
    bounding_box: tuple[int, int, int, int] | None
    shape: LeafShapeFeatures | None
    mask: np.ndarray
    cutout_rgba: Image.Image | None
    species_image: Image.Image | None


@dataclass(frozen=True)
class PreparedLeaf:
    """One leaf-only species input plus lesion evidence/crops for condition routing."""

    isolation: LeafIsolation
    lesions: LesionAnalysis | None
    lesion_crops: tuple[Image.Image, ...]


def isolate_leaf(
    image: Image.Image,
    *,
    target_point: TargetPoint | None = None,
    neutral_rgb: tuple[int, int, int] = (124, 124, 124),
) -> LeafIsolation:
    """Extract one clear green leaf and reject cluttered or truncated silhouettes.

    This deterministic baseline intentionally targets a single leaf whose outline is
    visible. It is not a general semantic-segmentation model.
    """

    rgb = np.asarray(image.convert("RGB"), dtype=np.uint8)
    if rgb.ndim != 3 or rgb.shape[2] != 3:
        raise ValueError("expected an RGB image")
    height, width = rgb.shape[:2]
    if height < 32 or width < 32:
        raise ValueError("image is too small for leaf isolation")

    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    red = rgb[:, :, 0].astype(np.int16)
    green = rgb[:, :, 1].astype(np.int16)
    blue = rgb[:, :, 2].astype(np.int16)
    excess_green = 2 * green - red - blue
    candidate = (
        (excess_green > 28)
        & (green > 38)
        & (hsv[:, :, 0] >= 28)
        & (hsv[:, :, 0] <= 105)
        & (hsv[:, :, 1] >= 28)
    ).astype(np.uint8) * 255

    kernel_size = max(3, _odd(round(min(width, height) * 0.009)))
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    candidate = cv2.morphologyEx(candidate, cv2.MORPH_OPEN, kernel)
    candidate = cv2.morphologyEx(candidate, cv2.MORPH_CLOSE, kernel, iterations=3)

    if target_point is not None:
        return _isolate_clicked_leaf(
            image,
            rgb,
            candidate,
            target_point,
            neutral_rgb=neutral_rgb,
        )

    contours, _ = cv2.findContours(
        candidate,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE,
    )
    image_area = width * height
    viable = [
        contour
        for contour in contours
        if cv2.contourArea(contour) >= max(64.0, image_area * 0.02)
    ]
    viable.sort(key=cv2.contourArea, reverse=True)
    empty_mask = np.zeros((height, width), dtype=np.uint8)
    if not viable:
        reason = "No clear green leaf component was found."
        return _rejected(
            image,
            empty_mask,
            reason,
            purity=_empty_purity(reason),
        )

    viable_area = sum(float(cv2.contourArea(contour)) for contour in viable)
    measured = [
        (
            contour,
            *_measure_contour(
                contour,
                width=width,
                height=height,
                viable_area=viable_area,
            ),
        )
        for contour in viable
    ]
    accepted = [item for item in measured if _quality_rejection(item[2]) is None]
    candidates = accepted or measured
    primary, box, shape = max(candidates, key=lambda item: _contour_quality(item[2]))
    x, y, box_width, box_height = box
    rejection = _quality_rejection(shape)
    mask = empty_mask.copy()
    cv2.drawContours(mask, [primary], -1, 255, thickness=cv2.FILLED)
    purity = _assess_purity(
        mask,
        shape=shape,
        fragment_count=len(viable),
        selection_mode="automatic",
    )
    if rejection is not None or not purity.accepted:
        return _rejected(
            image,
            mask,
            purity.reason if not purity.accepted else rejection,
            shape=shape,
            box=(x, y, box_width, box_height),
            purity=purity,
        )

    cutout, species_image = _build_cutout(
        rgb,
        mask,
        (x, y, box_width, box_height),
        neutral_rgb=neutral_rgb,
    )
    if len(viable) > 1:
        reason = (
            f"Selected the best-quality leaf from {len(viable)} green components; "
            "other leaves were excluded before plant recognition."
        )
    else:
        reason = "One clear leaf passed coverage, border, and contour-quality gates."
    return LeafIsolation(
        method=LEAF_ISOLATION_METHOD,
        selection_mode="automatic",
        target_point=None,
        purity=purity,
        accepted=True,
        reason=reason,
        image_size=(width, height),
        bounding_box=(x, y, box_width, box_height),
        shape=shape,
        mask=mask,
        cutout_rgba=cutout,
        species_image=species_image,
    )


def prepare_leaf(image: Image.Image, *, max_lesion_crops: int = 12) -> PreparedLeaf:
    """Create species input first, then leaf-constrained lesion evidence and crops."""

    if max_lesion_crops <= 0:
        raise ValueError("max_lesion_crops must be positive")
    isolation = isolate_leaf(image)
    if not isolation.accepted:
        return PreparedLeaf(isolation=isolation, lesions=None, lesion_crops=())
    lesions = analyze_lesions(image, leaf_mask=isolation.mask)
    source = image.convert("RGB")
    crops: list[Image.Image] = []
    for region in lesions.regions[:max_lesion_crops]:
        padding = max(3, round(max(region.width, region.height) * 0.20))
        left = max(0, region.x - padding)
        top = max(0, region.y - padding)
        right = min(source.width, region.x + region.width + padding)
        bottom = min(source.height, region.y + region.height + padding)
        crops.append(source.crop((left, top, right, bottom)))
    return PreparedLeaf(isolation=isolation, lesions=lesions, lesion_crops=tuple(crops))


def _quality_rejection(shape: LeafShapeFeatures) -> str | None:
    if shape.coverage_percent < LEAF_COVERAGE_RANGE[0]:
        return "Leaf coverage is below 3%; the outline is too small."
    if shape.coverage_percent > LEAF_COVERAGE_RANGE[1]:
        return "Leaf coverage exceeds 85%; background separation is unreliable."
    if shape.border_touch_ratio > MAX_BORDER_TOUCH_RATIO:
        return "The leaf is truncated by the image border."
    if shape.solidity < 0.35:
        return "The extracted contour is too fragmented for leaf-shape recognition."
    return None


def _measure_contour(
    contour: np.ndarray,
    *,
    width: int,
    height: int,
    viable_area: float,
) -> tuple[tuple[int, int, int, int], LeafShapeFeatures]:
    area = float(cv2.contourArea(contour))
    image_area = width * height
    x, y, box_width, box_height = cv2.boundingRect(contour)
    perimeter = float(cv2.arcLength(contour, True))
    hull_area = float(cv2.contourArea(cv2.convexHull(contour)))
    circularity = 4.0 * math.pi * area / (perimeter * perimeter) if perimeter > 0 else 0.0
    border_margin = max(2, round(min(width, height) * 0.01))
    perimeter_mask = np.zeros((height, width), dtype=np.uint8)
    cv2.drawContours(perimeter_mask, [contour], -1, 255, thickness=1)
    perimeter_rows, perimeter_columns = np.nonzero(perimeter_mask)
    touching = (
        (perimeter_columns <= border_margin)
        | (perimeter_columns >= width - 1 - border_margin)
        | (perimeter_rows <= border_margin)
        | (perimeter_rows >= height - 1 - border_margin)
    )
    shape = LeafShapeFeatures(
        area_pixels=round(area),
        coverage_percent=area / image_area * 100.0,
        aspect_ratio=max(box_width, box_height) / max(1, min(box_width, box_height)),
        circularity=max(0.0, min(1.0, circularity)),
        solidity=area / hull_area if hull_area > 0 else 0.0,
        extent=area / max(1, box_width * box_height),
        border_touch_ratio=float(np.mean(touching)),
        component_dominance=area / max(area, viable_area),
    )
    return (x, y, box_width, box_height), shape


def _contour_quality(shape: LeafShapeFeatures) -> float:
    """Prefer large, intact, non-truncated leaves without requiring a single leaf."""

    return (
        shape.area_pixels
        * max(0.0, min(1.0, shape.solidity))
        * max(0.05, 1.0 - shape.border_touch_ratio)
    )


def _principal_axis_aspect(mask: np.ndarray) -> float:
    aspect, _ = _axis_evidence(mask)
    return aspect


def _axis_evidence(mask: np.ndarray) -> tuple[float, float | None]:
    rows, columns = np.nonzero(mask)
    if len(rows) < 3:
        return 0.0, None
    coordinates = np.column_stack((columns, rows)).astype(np.float64)
    centered = coordinates - coordinates.mean(axis=0)
    eigenvalues, eigenvectors = np.linalg.eigh(np.cov(centered, rowvar=False))
    aspect = math.sqrt(float(eigenvalues[-1]) / max(float(eigenvalues[0]), 1e-6))
    if aspect < 2.0:
        return aspect, None
    principal_axis = eigenvectors[:, -1]
    cross_axis = eigenvectors[:, 0]
    longitudinal_positions = centered @ principal_axis
    cross_distances = np.abs(centered @ cross_axis)
    bin_edges = np.linspace(
        float(longitudinal_positions.min()),
        float(longitudinal_positions.max()),
        33,
    )
    local_half_widths: list[float] = []
    cross_positions = centered @ cross_axis
    for index in range(32):
        upper_inclusive = index == 31
        selected = (longitudinal_positions >= bin_edges[index]) & (
            (longitudinal_positions <= bin_edges[index + 1])
            if upper_inclusive
            else (longitudinal_positions < bin_edges[index + 1])
        )
        values = cross_positions[selected]
        if len(values) >= 5:
            local_half_widths.append(
                float((np.quantile(values, 0.90) - np.quantile(values, 0.10)) / 2.0)
            )
    median_half_width = (
        float(np.median(local_half_widths))
        if local_half_widths
        else float(np.median(cross_distances))
    )
    band_limit = 3.0 * max(median_half_width, 1.0)
    return aspect, float(np.mean(cross_distances <= band_limit))


def _assess_purity(
    mask: np.ndarray,
    *,
    shape: LeafShapeFeatures,
    fragment_count: int,
    selection_mode: str,
    click_contained: bool | None = None,
    probable_foreground_retention: float | None = None,
) -> LeafPurityEvidence:
    reason = _quality_rejection(shape)
    if (
        reason is None
        and selection_mode == "automatic"
        and fragment_count >= 2
        and shape.component_dominance < 0.90
    ):
        reason = (
            "Multiple plausible green components are visible; select one target leaf "
            "before analysis."
        )
    axis_aspect, axis_retention = _axis_evidence(mask)
    if reason is None and selection_mode == "click_grabcut" and click_contained is not True:
        reason = "The selected point is not contained in a probable leaf foreground."
    if (
        reason is None
        and selection_mode == "click_grabcut"
        and (
            probable_foreground_retention is None
            or probable_foreground_retention < MIN_PROBABLE_FOREGROUND_RETENTION
        )
    ):
        reason = "The selected mask retained too little probable leaf foreground."
    if (
        reason is None
        and selection_mode == "click_grabcut"
        and axis_aspect >= 2.0
        and axis_retention is not None
        and axis_retention < MIN_AXIS_BAND_RETENTION
    ):
        reason = "The selected mask failed the principal-axis purity gate."
    accepted = reason is None
    return LeafPurityEvidence(
        accepted=accepted,
        coverage_percent=shape.coverage_percent,
        border_touch_ratio=shape.border_touch_ratio,
        fragment_count=fragment_count,
        click_contained=click_contained,
        probable_foreground_retention=probable_foreground_retention,
        principal_axis_aspect_ratio=axis_aspect,
        axis_band_retention=axis_retention,
        coverage_range=LEAF_COVERAGE_RANGE,
        max_border_touch_ratio=MAX_BORDER_TOUCH_RATIO,
        min_probable_foreground_retention=MIN_PROBABLE_FOREGROUND_RETENTION,
        min_axis_band_retention=MIN_AXIS_BAND_RETENTION,
        reason=(
            "Click-seeded mask passed coverage, border, and axis-purity gates."
            if accepted and selection_mode == "click_grabcut"
            else "Automatic mask passed coverage, border, and component-purity gates."
            if accepted
            else reason
        ),
    )


def _empty_purity(
    reason: str,
    *,
    fragment_count: int = 0,
    click_contained: bool | None = None,
    probable_foreground_retention: float | None = None,
) -> LeafPurityEvidence:
    return LeafPurityEvidence(
        accepted=False,
        coverage_percent=0.0,
        border_touch_ratio=0.0,
        fragment_count=fragment_count,
        click_contained=click_contained,
        probable_foreground_retention=probable_foreground_retention,
        principal_axis_aspect_ratio=0.0,
        axis_band_retention=None,
        coverage_range=LEAF_COVERAGE_RANGE,
        max_border_touch_ratio=MAX_BORDER_TOUCH_RATIO,
        min_probable_foreground_retention=MIN_PROBABLE_FOREGROUND_RETENTION,
        min_axis_band_retention=MIN_AXIS_BAND_RETENTION,
        reason=reason,
    )


def _isolate_clicked_leaf(
    image: Image.Image,
    rgb: np.ndarray,
    candidate: np.ndarray,
    target_point: TargetPoint,
    *,
    neutral_rgb: tuple[int, int, int],
) -> LeafIsolation:
    height, width = candidate.shape
    pixel_x = min(width - 1, round(target_point.x * (width - 1)))
    pixel_y = min(height - 1, round(target_point.y * (height - 1)))
    if candidate[pixel_y, pixel_x] == 0:
        reason = "The selected point is not contained in a probable green leaf."
        return _rejected(
            image,
            np.zeros_like(candidate),
            reason,
            selection_mode="click_grabcut",
            target_point=target_point,
            purity=_empty_purity(reason, click_contained=False),
        )

    selected_mask, retention, fragment_count = _click_grabcut_mask(
        rgb,
        candidate,
        pixel_x=pixel_x,
        pixel_y=pixel_y,
    )
    contours, _ = cv2.findContours(
        selected_mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE,
    )
    if not contours:
        reason = "GrabCut did not retain a target-leaf foreground."
        return _rejected(
            image,
            selected_mask,
            reason,
            selection_mode="click_grabcut",
            target_point=target_point,
            purity=_empty_purity(
                reason,
                fragment_count=fragment_count,
                click_contained=False,
                probable_foreground_retention=retention,
            ),
        )

    primary = max(contours, key=cv2.contourArea)
    box, shape = _measure_contour(
        primary,
        width=width,
        height=height,
        viable_area=float(cv2.contourArea(primary)),
    )
    source_border_touch = _clicked_component_border_touch(
        candidate,
        pixel_x=pixel_x,
        pixel_y=pixel_y,
    )
    shape = replace(
        shape,
        border_touch_ratio=max(shape.border_touch_ratio, source_border_touch),
    )
    purity = _assess_purity(
        selected_mask,
        shape=shape,
        fragment_count=fragment_count,
        selection_mode="click_grabcut",
        click_contained=bool(selected_mask[pixel_y, pixel_x]),
        probable_foreground_retention=retention,
    )
    if not purity.accepted:
        return _rejected(
            image,
            selected_mask,
            purity.reason,
            shape=shape,
            box=box,
            selection_mode="click_grabcut",
            target_point=target_point,
            purity=purity,
        )

    cutout, species_image = _build_cutout(
        rgb,
        selected_mask,
        box,
        neutral_rgb=neutral_rgb,
    )
    return LeafIsolation(
        method=LEAF_ISOLATION_METHOD,
        selection_mode="click_grabcut",
        target_point=target_point,
        purity=purity,
        accepted=True,
        reason="The click-seeded target leaf passed GrabCut and mask-purity gates.",
        image_size=image.size,
        bounding_box=box,
        shape=shape,
        mask=selected_mask,
        cutout_rgba=cutout,
        species_image=species_image,
    )


def _click_grabcut_mask(
    rgb: np.ndarray,
    candidate: np.ndarray,
    *,
    pixel_x: int,
    pixel_y: int,
) -> tuple[np.ndarray, float, int]:
    height, width = candidate.shape
    labels = np.full((height, width), cv2.GC_PR_BGD, dtype=np.uint8)
    labels[candidate > 0] = cv2.GC_PR_FGD
    labels[:4, :] = cv2.GC_BGD
    labels[-4:, :] = cv2.GC_BGD
    labels[:, :4] = cv2.GC_BGD
    labels[:, -4:] = cv2.GC_BGD
    radius = max(3, round(min(width, height) * 0.025))
    cv2.circle(labels, (pixel_x, pixel_y), radius, cv2.GC_FGD, thickness=-1)
    background_model = np.zeros((1, 65), dtype=np.float64)
    foreground_model = np.zeros((1, 65), dtype=np.float64)
    cv2.grabCut(
        cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR),
        labels,
        (1, 1, max(1, width - 2), max(1, height - 2)),
        background_model,
        foreground_model,
        5,
        cv2.GC_INIT_WITH_MASK,
    )
    foreground = np.where(
        (labels == cv2.GC_FGD) | (labels == cv2.GC_PR_FGD),
        255,
        0,
    ).astype(np.uint8)
    component_count, components = cv2.connectedComponents(foreground)
    selected_label = int(components[pixel_y, pixel_x])
    if selected_label == 0:
        return np.zeros_like(candidate), 0.0, max(0, component_count - 1)
    selected = np.where(components == selected_label, 255, 0).astype(np.uint8)
    x, y, box_width, box_height = cv2.boundingRect(selected)
    probable_in_box = candidate[y : y + box_height, x : x + box_width] > 0
    selected_in_box = selected[y : y + box_height, x : x + box_width] > 0
    retained = np.count_nonzero(probable_in_box & selected_in_box)
    retention = retained / max(1, np.count_nonzero(probable_in_box))
    return selected, float(retention), max(0, component_count - 1)


def _clicked_component_border_touch(
    candidate: np.ndarray,
    *,
    pixel_x: int,
    pixel_y: int,
) -> float:
    component_count, labels = cv2.connectedComponents(candidate)
    selected_label = int(labels[pixel_y, pixel_x])
    if component_count <= 1 or selected_label == 0:
        return 0.0
    selected = np.where(labels == selected_label, 255, 0).astype(np.uint8)
    contours, _ = cv2.findContours(selected, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return 0.0
    primary = max(contours, key=cv2.contourArea)
    _, shape = _measure_contour(
        primary,
        width=candidate.shape[1],
        height=candidate.shape[0],
        viable_area=float(cv2.contourArea(primary)),
    )
    return shape.border_touch_ratio


def _build_cutout(
    rgb: np.ndarray,
    mask: np.ndarray,
    box: tuple[int, int, int, int],
    *,
    neutral_rgb: tuple[int, int, int],
) -> tuple[Image.Image, Image.Image]:
    height, width = mask.shape
    x, y, box_width, box_height = box
    padding = max(4, round(max(box_width, box_height) * 0.06))
    left = max(0, x - padding)
    top = max(0, y - padding)
    right = min(width, x + box_width + padding)
    bottom = min(height, y + box_height + padding)
    alpha = mask[top:bottom, left:right]
    crop_rgb = rgb[top:bottom, left:right]
    rgba = np.dstack((crop_rgb, alpha))
    cutout = Image.fromarray(rgba, mode="RGBA")
    background = Image.new("RGBA", cutout.size, (*neutral_rgb, 255))
    background.alpha_composite(cutout)
    return cutout, background.convert("RGB")


def _rejected(
    image: Image.Image,
    mask: np.ndarray,
    reason: str,
    *,
    shape: LeafShapeFeatures | None = None,
    box: tuple[int, int, int, int] | None = None,
    purity: LeafPurityEvidence | None = None,
    selection_mode: str = "automatic",
    target_point: TargetPoint | None = None,
) -> LeafIsolation:
    return LeafIsolation(
        method=LEAF_ISOLATION_METHOD,
        selection_mode=selection_mode,
        target_point=target_point,
        purity=purity or _empty_purity(reason),
        accepted=False,
        reason=reason,
        image_size=image.size,
        bounding_box=box,
        shape=shape,
        mask=mask,
        cutout_rgba=None,
        species_image=None,
    )


def _odd(value: int) -> int:
    return value if value % 2 else value + 1


__all__ = [
    "LEAF_ISOLATION_METHOD",
    "LeafIsolation",
    "LeafPurityEvidence",
    "LeafShapeFeatures",
    "PreparedLeaf",
    "TargetPoint",
    "isolate_leaf",
    "prepare_leaf",
]
