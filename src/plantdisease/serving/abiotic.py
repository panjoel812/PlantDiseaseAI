"""Conservative morphology-only evidence for Corn abiotic-stress abstention."""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np
from PIL import Image

CORN_ABIOTIC_METHOD = "opencv_corn_midrib_stress_v1"
ABNORMAL_COVERAGE_THRESHOLD = 8.0
CENTRAL_AXIS_SHARE_THRESHOLD = 0.55
LONGITUDINAL_CONTINUITY_THRESHOLD = 0.60
BILATERAL_SIMILARITY_THRESHOLD = 0.50
OFF_AXIS_LESION_COVERAGE_THRESHOLD = 5.0
EVIDENCE_BOUNDARY = (
    "Morphology-only OpenCV evidence; it cannot identify a specific nutrient or "
    "confirm a diagnosis. Soil or tissue testing and local agronomic context may be "
    "required."
)


@dataclass(frozen=True)
class CornAbioticEvidence:
    """Visible Corn stress-pattern measurements and the fixed abstention decision."""

    method: str
    status: str
    suspected: bool
    abnormal_coverage_percent: float
    central_axis_share: float
    longitudinal_continuity: float
    bilateral_similarity: float
    off_axis_lesion_coverage_percent: float
    abnormal_coverage_threshold: float
    central_axis_share_threshold: float
    longitudinal_continuity_threshold: float
    bilateral_similarity_threshold: float
    off_axis_lesion_coverage_threshold: float
    reason: str
    evidence_boundary: str
    overlay: Image.Image


def analyze_corn_abiotic_pattern(
    image: Image.Image,
    leaf_mask: np.ndarray,
) -> CornAbioticEvidence:
    """Measure a continuous midrib-aligned yellow/tan/brown pattern.

    The result is a conservative routing signal, not a disease or deficiency class.
    """

    rgb = np.asarray(image.convert("RGB"), dtype=np.uint8)
    if leaf_mask.ndim != 2 or leaf_mask.shape != rgb.shape[:2]:
        raise ValueError("leaf mask shape must match image height and width")
    mask = leaf_mask > 0
    leaf_area = int(np.count_nonzero(mask))
    if leaf_area == 0:
        return _empty_evidence(image, "The supplied leaf mask is empty.")

    abnormal = _abnormal_mask(rgb, mask)
    abnormal_area = int(np.count_nonzero(abnormal))
    abnormal_coverage = abnormal_area / leaf_area * 100.0
    if abnormal_area == 0:
        return _evidence(
            image=image,
            mask=mask,
            abnormal=abnormal,
            central_band=np.zeros_like(mask),
            off_axis=np.zeros_like(mask),
            abnormal_coverage=0.0,
            central_share=0.0,
            continuity=0.0,
            bilateral_similarity=0.0,
            off_axis_coverage=0.0,
            suspected=False,
            reason="Visible abnormal coverage is below the fixed 8% gate.",
        )

    coordinates = _coordinates(mask)
    centre, principal_axis, cross_axis = _principal_axes(coordinates)
    leaf_longitudinal, leaf_cross = _project(coordinates, centre, principal_axis, cross_axis)
    abnormal_coordinates = _coordinates(abnormal)
    abnormal_longitudinal, abnormal_cross = _project(
        abnormal_coordinates,
        centre,
        principal_axis,
        cross_axis,
    )
    robust_width = float(np.quantile(leaf_cross, 0.95) - np.quantile(leaf_cross, 0.05))
    central_limit = max(2.0, robust_width * 0.18)
    central_flags = np.abs(abnormal_cross) <= central_limit
    central_share = float(np.mean(central_flags))
    continuity, bilateral_similarity = _longitudinal_evidence(
        abnormal_longitudinal,
        abnormal_cross,
        central_flags,
    )
    central_band = _band_mask(
        rgb.shape[:2],
        centre,
        cross_axis,
        central_limit,
        mask,
    )
    off_axis, off_axis_coverage = _off_axis_components(
        abnormal,
        centre,
        cross_axis,
        central_limit,
        leaf_area,
    )
    suspected = (
        abnormal_coverage >= ABNORMAL_COVERAGE_THRESHOLD
        and central_share >= CENTRAL_AXIS_SHARE_THRESHOLD
        and continuity >= LONGITUDINAL_CONTINUITY_THRESHOLD
        and bilateral_similarity >= BILATERAL_SIMILARITY_THRESHOLD
        and off_axis_coverage < OFF_AXIS_LESION_COVERAGE_THRESHOLD
    )
    if suspected:
        reason = (
            "Visible morphology is compatible with a midrib-aligned abiotic or "
            "nutrient-stress pattern, but OpenCV cannot identify a specific nutrient."
        )
    else:
        failures: list[str] = []
        if abnormal_coverage < ABNORMAL_COVERAGE_THRESHOLD:
            failures.append("abnormal coverage")
        if central_share < CENTRAL_AXIS_SHARE_THRESHOLD:
            failures.append("central-axis share")
        if continuity < LONGITUDINAL_CONTINUITY_THRESHOLD:
            failures.append("longitudinal continuity")
        if bilateral_similarity < BILATERAL_SIMILARITY_THRESHOLD:
            failures.append("bilateral similarity")
        if off_axis_coverage >= OFF_AXIS_LESION_COVERAGE_THRESHOLD:
            failures.append("off-axis discrete-lesion coverage")
        reason = "Unknown visible stress; failed fixed gates: " + ", ".join(failures) + "."
    return _evidence(
        image=image,
        mask=mask,
        abnormal=abnormal,
        central_band=central_band,
        off_axis=off_axis,
        abnormal_coverage=abnormal_coverage,
        central_share=central_share,
        continuity=continuity,
        bilateral_similarity=bilateral_similarity,
        off_axis_coverage=off_axis_coverage,
        suspected=suspected,
        reason=reason,
    )


def _abnormal_mask(rgb: np.ndarray, leaf_mask: np.ndarray) -> np.ndarray:
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)
    red = rgb[:, :, 0].astype(np.int16)
    green = rgb[:, :, 1].astype(np.int16)
    blue = rgb[:, :, 2].astype(np.int16)
    excess_green = 2 * green - red - blue
    hue = hsv[:, :, 0]
    saturation = hsv[:, :, 1]
    value = hsv[:, :, 2]
    yellow = (
        (hue >= 15)
        & (hue <= 38)
        & (saturation >= 35)
        & (value >= 70)
    )
    tan_brown = (
        (hue >= 4)
        & (hue <= 30)
        & (saturation >= 30)
        & (value >= 35)
        & (value <= 220)
        & (excess_green < 22)
    )
    lab_a = lab[:, :, 1].astype(np.float32) - 128.0
    lab_b = lab[:, :, 2].astype(np.float32) - 128.0
    lab_chroma = np.sqrt(lab_a * lab_a + lab_b * lab_b)
    pale = (lab[:, :, 0] >= 135) & (lab_chroma < 70) & (excess_green < 18)
    abnormal = ((yellow | tan_brown | pale) & leaf_mask).astype(np.uint8) * 255
    kernel_size = max(3, _odd(round(min(rgb.shape[:2]) * 0.006)))
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    abnormal = cv2.morphologyEx(abnormal, cv2.MORPH_OPEN, kernel)
    abnormal = cv2.morphologyEx(abnormal, cv2.MORPH_CLOSE, kernel)
    return (abnormal > 0) & leaf_mask


def _coordinates(mask: np.ndarray) -> np.ndarray:
    rows, columns = np.nonzero(mask)
    return np.column_stack((columns, rows)).astype(np.float64)


def _principal_axes(coordinates: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    centre = coordinates.mean(axis=0)
    _, eigenvectors = np.linalg.eigh(np.cov(coordinates - centre, rowvar=False))
    return centre, eigenvectors[:, -1], eigenvectors[:, 0]


def _project(
    coordinates: np.ndarray,
    centre: np.ndarray,
    principal_axis: np.ndarray,
    cross_axis: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    centered = coordinates - centre
    return centered @ principal_axis, centered @ cross_axis


def _longitudinal_evidence(
    longitudinal: np.ndarray,
    cross: np.ndarray,
    central_flags: np.ndarray,
) -> tuple[float, float]:
    if not np.any(central_flags):
        return 0.0, 0.0
    central_longitudinal = longitudinal[central_flags]
    lower = float(central_longitudinal.min())
    upper = float(central_longitudinal.max())
    if upper <= lower:
        return 0.0, 0.0
    edges = np.linspace(lower, upper, 33)
    occupied: list[bool] = []
    left_counts: list[int] = []
    right_counts: list[int] = []
    for index in range(32):
        selected = (longitudinal >= edges[index]) & (
            (longitudinal <= edges[index + 1])
            if index == 31
            else (longitudinal < edges[index + 1])
        )
        central_selected = selected & central_flags
        occupied.append(bool(np.any(central_selected)))
        left_counts.append(int(np.count_nonzero(selected & (cross < 0))))
        right_counts.append(int(np.count_nonzero(selected & (cross >= 0))))
    occupied_indices = [index for index, value in enumerate(occupied) if value]
    first = occupied_indices[0]
    last = occupied_indices[-1]
    continuity = sum(occupied[first : last + 1]) / (last - first + 1)
    left = np.asarray(left_counts, dtype=np.float64)
    right = np.asarray(right_counts, dtype=np.float64)
    similarity = 1.0 - float(np.abs(left - right).sum()) / max(
        1.0,
        float((left + right).sum()),
    )
    return float(continuity), max(0.0, min(1.0, similarity))


def _band_mask(
    shape: tuple[int, int],
    centre: np.ndarray,
    cross_axis: np.ndarray,
    limit: float,
    leaf_mask: np.ndarray,
) -> np.ndarray:
    rows, columns = np.indices(shape)
    coordinates = np.stack((columns, rows), axis=-1).astype(np.float64)
    cross = (coordinates - centre) @ cross_axis
    return (np.abs(cross) <= limit) & leaf_mask


def _off_axis_components(
    abnormal: np.ndarray,
    centre: np.ndarray,
    cross_axis: np.ndarray,
    central_limit: float,
    leaf_area: int,
) -> tuple[np.ndarray, float]:
    count, labels, stats, centroids = cv2.connectedComponentsWithStats(
        abnormal.astype(np.uint8),
        connectivity=8,
    )
    selected = np.zeros_like(abnormal)
    minimum_area = max(1.0, leaf_area * 0.0015)
    total_area = 0
    for label in range(1, count):
        area = int(stats[label, cv2.CC_STAT_AREA])
        centroid = centroids[label]
        cross_distance = abs(float((centroid - centre) @ cross_axis))
        if area >= minimum_area and cross_distance > central_limit:
            selected[labels == label] = True
            total_area += area
    return selected, total_area / leaf_area * 100.0


def _evidence(
    *,
    image: Image.Image,
    mask: np.ndarray,
    abnormal: np.ndarray,
    central_band: np.ndarray,
    off_axis: np.ndarray,
    abnormal_coverage: float,
    central_share: float,
    continuity: float,
    bilateral_similarity: float,
    off_axis_coverage: float,
    suspected: bool,
    reason: str,
) -> CornAbioticEvidence:
    overlay = _overlay(image, mask, abnormal, central_band, off_axis)
    return CornAbioticEvidence(
        method=CORN_ABIOTIC_METHOD,
        status=(
            "suspected_abiotic_nutrient_stress"
            if suspected
            else "unknown_visible_stress"
        ),
        suspected=suspected,
        abnormal_coverage_percent=float(abnormal_coverage),
        central_axis_share=float(central_share),
        longitudinal_continuity=float(continuity),
        bilateral_similarity=float(bilateral_similarity),
        off_axis_lesion_coverage_percent=float(off_axis_coverage),
        abnormal_coverage_threshold=ABNORMAL_COVERAGE_THRESHOLD,
        central_axis_share_threshold=CENTRAL_AXIS_SHARE_THRESHOLD,
        longitudinal_continuity_threshold=LONGITUDINAL_CONTINUITY_THRESHOLD,
        bilateral_similarity_threshold=BILATERAL_SIMILARITY_THRESHOLD,
        off_axis_lesion_coverage_threshold=OFF_AXIS_LESION_COVERAGE_THRESHOLD,
        reason=reason,
        evidence_boundary=EVIDENCE_BOUNDARY,
        overlay=overlay,
    )


def _empty_evidence(image: Image.Image, reason: str) -> CornAbioticEvidence:
    shape = (image.height, image.width)
    empty = np.zeros(shape, dtype=bool)
    return _evidence(
        image=image,
        mask=empty,
        abnormal=empty,
        central_band=empty,
        off_axis=empty,
        abnormal_coverage=0.0,
        central_share=0.0,
        continuity=0.0,
        bilateral_similarity=0.0,
        off_axis_coverage=0.0,
        suspected=False,
        reason=reason,
    )


def _overlay(
    image: Image.Image,
    mask: np.ndarray,
    abnormal: np.ndarray,
    central_band: np.ndarray,
    off_axis: np.ndarray,
) -> Image.Image:
    rgb = np.asarray(image.convert("RGB"), dtype=np.uint8).copy()
    tint = rgb.astype(np.float32)
    tint[central_band] = tint[central_band] * 0.72 + np.array((112, 190, 238)) * 0.28
    tint[abnormal] = tint[abnormal] * 0.48 + np.array((247, 181, 64)) * 0.52
    tint[off_axis] = tint[off_axis] * 0.35 + np.array((242, 111, 91)) * 0.65
    contours, _ = cv2.findContours(
        mask.astype(np.uint8),
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE,
    )
    output = np.clip(tint, 0, 255).astype(np.uint8)
    cv2.drawContours(output, contours, -1, (50, 171, 112), thickness=2)
    return Image.fromarray(output, mode="RGB")


def _odd(value: int) -> int:
    return value if value % 2 else value + 1


__all__ = [
    "CORN_ABIOTIC_METHOD",
    "CornAbioticEvidence",
    "analyze_corn_abiotic_pattern",
]
