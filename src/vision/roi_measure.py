"""Deterministic pixel measurements for physical-image inspection.

This module intentionally does not classify components. It converts a configured
ROI into measurable evidence that can later be mapped to Observation fields.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

import cv2
import numpy as np


@dataclass(frozen=True)
class RoiBox:
    x: int
    y: int
    width: int
    height: int


@dataclass(frozen=True)
class RoiMeasurement:
    roi: RoiBox
    mean_gray: float
    std_gray: float
    min_gray: int
    max_gray: int
    edge_density: float
    foreground_ratio: float
    contour_count: int

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["roi"] = asdict(self.roi)
        return value


def _clip_roi(image: np.ndarray, roi: RoiBox) -> tuple[np.ndarray, RoiBox]:
    height, width = image.shape[:2]
    x1 = max(0, min(width, roi.x))
    y1 = max(0, min(height, roi.y))
    x2 = max(x1, min(width, roi.x + roi.width))
    y2 = max(y1, min(height, roi.y + roi.height))
    if x2 <= x1 or y2 <= y1:
        raise ValueError("ROI_OUT_OF_BOUNDS")
    clipped = RoiBox(x1, y1, x2 - x1, y2 - y1)
    return image[y1:y2, x1:x2], clipped


def measure_roi(image: np.ndarray, roi: RoiBox) -> RoiMeasurement:
    if image is None or image.size == 0:
        raise ValueError("IMAGE_EMPTY")
    crop, clipped = _clip_roi(image, roi)
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)

    edges = cv2.Canny(gray, 50, 150)
    edge_density = float(np.count_nonzero(edges)) / float(edges.size)

    # A deterministic, intentionally generic foreground estimate. Product-specific
    # thresholds belong in Rule.cmd and commissioning, not in this adapter.
    _, mask = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    foreground_ratio = float(np.count_nonzero(mask)) / float(mask.size)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contour_count = len(contours)

    return RoiMeasurement(
        roi=clipped,
        mean_gray=float(np.mean(gray)),
        std_gray=float(np.std(gray)),
        min_gray=int(np.min(gray)),
        max_gray=int(np.max(gray)),
        edge_density=edge_density,
        foreground_ratio=foreground_ratio,
        contour_count=contour_count,
    )


def detect_green_board_roi(image: np.ndarray) -> RoiBox | None:
    """Return a conservative board candidate for the current PCB image.

    This is only a bootstrap locator. It must not be treated as a commissioned
    production ROI until validated against multiple real GOOD/NG frames.
    """
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lower = np.array([30, 35, 25], dtype=np.uint8)
    upper = np.array([95, 255, 255], dtype=np.uint8)
    mask = cv2.inRange(hsv, lower, upper)
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    contour = max(contours, key=cv2.contourArea)
    x, y, width, height = cv2.boundingRect(contour)
    if width * height < image.shape[0] * image.shape[1] * 0.02:
        return None
    return RoiBox(x, y, width, height)
