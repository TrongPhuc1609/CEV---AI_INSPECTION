"""Commissioning calibration profiles compiled from Rule.cmd model/region settings."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass(frozen=True)
class CalibrationProfile:
    region_id: str
    confidence_threshold: Optional[float]
    min_coverage_percent: Optional[float]
    max_coverage_percent: Optional[float]
    anomaly_threshold: Optional[float]
    source: str = "RULE_CMD"


class CalibrationRegistry:
    def __init__(self, profiles: Dict[str, CalibrationProfile]):
        self.profiles = profiles

    @classmethod
    def from_plan(cls, plan):
        profiles = {}
        for region_id, region in plan.regions.items():
            model = plan.models[region.model_id]
            settings = model.settings
            profiles[region_id] = CalibrationProfile(
                region_id,
                region.min_confidence if region.min_confidence is not None else model.threshold,
                region.min_coverage_percent,
                region.max_coverage_percent,
                settings.get("anomaly_threshold"),
            )
        return cls(profiles)

    def for_region(self, region_id: str) -> CalibrationProfile:
        return self.profiles[region_id]
