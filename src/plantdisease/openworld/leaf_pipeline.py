"""Leaf-only OpenCV preparation for plant-first hierarchical recognition."""

from __future__ import annotations

import math
from dataclasses import dataclass

import cv2
import numpy as np
from PIL import Image

from plantdisease.serving.lesions import LesionAnalysis, analyze_lesions

LEAF_ISOLATION_METHOD = "opencv_exg_single_leaf_v1"


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
class LeafIsolation:
    """Accepted leaf mask and model-ready cutout, or an explicit rejection."""

    method: str
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
        return _rejected(image, empty_mask, "No clear green leaf component was found.")

    primary = viable[0]
    primary_area = float(cv2.contourArea(primary))
    viable_area = sum(float(cv2.contourArea(contour)) for contour in viable)
    dominance = primary_area / max(primary_area, viable_area)
    x, y, box_width, box_height = cv2.boundingRect(primary)
    perimeter = float(cv2.arcLength(primary, True))
    hull = cv2.convexHull(primary)
    hull_area = float(cv2.contourArea(hull))
    circularity = (
        4.0 * math.pi * primary_area / (perimeter * perimeter) if perimeter > 0 else 0.0
    )
    border_margin = max(2, round(min(width, height) * 0.01))
    contour_points = primary.reshape(-1, 2)
    touching = (
        (contour_points[:, 0] <= border_margin)
        | (contour_points[:, 0] >= width - 1 - border_margin)
        | (contour_points[:, 1] <= border_margin)
        | (contour_points[:, 1] >= height - 1 - border_margin)
    )
    border_touch_ratio = float(np.mean(touching))
    coverage = primary_area / image_area
    shape = LeafShapeFeatures(
        area_pixels=round(primary_area),
        coverage_percent=coverage * 100.0,
        aspect_ratio=max(box_width, box_height) / max(1, min(box_width, box_height)),
        circularity=max(0.0, min(1.0, circularity)),
        solidity=primary_area / hull_area if hull_area > 0 else 0.0,
        extent=primary_area / max(1, box_width * box_height),
        border_touch_ratio=border_touch_ratio,
        component_dominance=dominance,
    )

    rejection = _quality_rejection(shape)
    mask = empty_mask.copy()
    cv2.drawContours(mask, [primary], -1, 255, thickness=cv2.FILLED)
    if rejection is not None:
        return _rejected(image, mask, rejection, shape=shape, box=(x, y, box_width, box_height))

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
    species_image = background.convert("RGB")
    return LeafIsolation(
        method=LEAF_ISOLATION_METHOD,
        accepted=True,
        reason="One clear leaf passed coverage, border, and component-dominance gates.",
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
    if shape.coverage_percent < 5.0:
        return "Leaf coverage is below 5%; the outline is too small."
    if shape.coverage_percent > 90.0:
        return "Leaf coverage exceeds 90%; background separation is unreliable."
    if shape.component_dominance < 0.60:
        return "Multiple large green components are present; provide one clear leaf."
    if shape.border_touch_ratio > 0.18:
        return "The leaf is truncated by the image border."
    if shape.solidity < 0.35:
        return "The extracted contour is too fragmented for leaf-shape recognition."
    return None


def _rejected(
    image: Image.Image,
    mask: np.ndarray,
    reason: str,
    *,
    shape: LeafShapeFeatures | None = None,
    box: tuple[int, int, int, int] | None = None,
) -> LeafIsolation:
    return LeafIsolation(
        method=LEAF_ISOLATION_METHOD,
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
    "LeafShapeFeatures",
    "PreparedLeaf",
    "isolate_leaf",
    "prepare_leaf",
]
