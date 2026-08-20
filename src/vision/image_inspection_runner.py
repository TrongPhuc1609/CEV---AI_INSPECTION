"""Offline real-image inspection runner for the V1.9 machine-vision boundary.

This runner deliberately avoids camera/PLC hardware. It proves that a real image can
flow through ROI measurement -> Observation -> RuleEngine -> InspectionOrchestrator.
Product-specific component/grease AI remains a later commissioning step.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import cv2

from ..machine_vision.measurement_adapter import MeasurementAdapter
from ..orchestrator.orchestrator import InspectionOrchestrator
from ..rules.engine import RuleEngine
from ..rules.parser import parse_rule_file
from .adapters.base import VisionInput
from .roi_measure import RoiBox


class RealImageInspectionRunner:
    """Run one configured machine-vision region against a real image."""

    def __init__(self, rule_path: str | Path):
        self.config = parse_rule_file(rule_path)
        plan = self.config.to_plan()
        required = plan.required_regions()
        if len(required) != 1:
            raise ValueError(
                "RealImageInspectionRunner requires exactly one enabled region; "
                f"got {required}"
            )
        self.region_id = required[0]
        region = plan.regions[self.region_id]
        roi = plan.rois[region.roi_id]
        self.adapter = MeasurementAdapter(
            RoiBox(roi.x, roi.y, roi.width, roi.height)
        )
        self.engine = RuleEngine(self.config)
        self.orchestrator = InspectionOrchestrator(self.config, self.engine)

    def inspect(self, image_path: str | Path, product_id: str = "REAL-PCB-001") -> Any:
        path = Path(image_path)
        image = cv2.imread(str(path), cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError(f"IMAGE_READ_ERROR:{path}")

        inspection = self.orchestrator.start_product(product_id)
        frame_id = path.stem

        def provider(_attempt: int):
            return self.adapter.inspect(
                VisionInput(
                    product_id=product_id,
                    inspection_id=inspection.inspection_id,
                    region_id=self.region_id,
                    image=image,
                    frame_id=frame_id,
                    metadata={"evidence_image": str(path)},
                )
            )

        self.orchestrator.inspect_region(
            inspection,
            self.region_id,
            observation_provider=provider,
        )
        self.orchestrator.complete(inspection)
        decision = self.orchestrator.final_decision(inspection)
        return inspection, decision
