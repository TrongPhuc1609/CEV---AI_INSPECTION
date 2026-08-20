"""Machine-vision adapter that converts deterministic ROI measurements to Observation.

This adapter intentionally does not decide PASS/FAIL. It exposes pixel measurements
as normalized evidence so Rule.cmd remains the source of inspection policy.
"""
from __future__ import annotations

from dataclasses import asdict
from typing import Any

from ..models.result import Observation, Status
from ..vision.adapters.base import VisionAdapter, VisionInput
from ..vision.roi_measure import RoiBox, measure_roi


class MeasurementAdapter(VisionAdapter):
    """Adapter for deterministic OpenCV measurements inside a configured ROI."""

    method = "MACHINE_VISION_MEASUREMENT"

    def __init__(self, roi: RoiBox | None = None):
        self.roi = roi

    def inspect(self, data: VisionInput) -> Observation:
        roi = self.roi
        if roi is None:
            metadata = data.metadata or {}
            configured = metadata.get("roi")
            if not isinstance(configured, dict):
                raise ValueError("MACHINE_VISION_ROI_REQUIRED")
            roi = RoiBox(
                int(configured["x"]),
                int(configured["y"]),
                int(configured["width"]),
                int(configured["height"]),
            )

        measurement = measure_roi(data.image, roi)
        return Observation(
            product_id=data.product_id,
            inspection_id=data.inspection_id,
            region_id=data.region_id,
            method=self.method,
            status=Status.UNCERTAIN,
            evidence_image=data.metadata.get("evidence_image") if data.metadata else None,
            metadata={
                "frame_id": data.frame_id,
                "measurement": measurement.to_dict(),
                "source": "real_image_pixels",
                "decision_owner": "RuleEngine",
            },
        )
