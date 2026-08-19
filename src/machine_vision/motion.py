"""Motion-aware timing calculations for slowly moving products.

This module is deliberately vendor-neutral. It converts conveyor/product motion
and measured processing delays into deterministic timing budgets that can later
be consumed by a real trigger/camera/PLC adapter.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class MotionProfile:
    """Physical motion assumptions expressed in project units and milliseconds."""

    nominal_velocity: float
    min_velocity: float
    max_velocity: float
    trigger_to_camera_distance: float = 0.0
    camera_to_reject_distance: float = 0.0
    acquisition_budget_ms: float = 100.0
    ai_budget_ms: float = 200.0
    decision_budget_ms: float = 20.0
    plc_budget_ms: float = 50.0

    def validate(self) -> None:
        errors = []
        if self.nominal_velocity <= 0:
            errors.append("nominal_velocity must be > 0")
        if self.min_velocity <= 0:
            errors.append("min_velocity must be > 0")
        if self.max_velocity < self.min_velocity:
            errors.append("max_velocity must be >= min_velocity")
        if not self.min_velocity <= self.nominal_velocity <= self.max_velocity:
            errors.append("nominal_velocity must be within min/max velocity")
        for name, value in (
            ("trigger_to_camera_distance", self.trigger_to_camera_distance),
            ("camera_to_reject_distance", self.camera_to_reject_distance),
            ("acquisition_budget_ms", self.acquisition_budget_ms),
            ("ai_budget_ms", self.ai_budget_ms),
            ("decision_budget_ms", self.decision_budget_ms),
            ("plc_budget_ms", self.plc_budget_ms),
        ):
            if value < 0:
                errors.append(f"{name} must be >= 0")
        if errors:
            raise ValueError("Invalid MotionProfile: " + "; ".join(errors))


@dataclass(frozen=True)
class TimingBudget:
    trigger_to_frame_ms: float
    inspection_processing_ms: float
    total_decision_ms: float
    frame_to_reject_ms: float
    total_trigger_to_reject_ms: float


class MotionTimingPlanner:
    """Calculate travel and decision timing at a given product velocity."""

    def __init__(self, profile: MotionProfile):
        profile.validate()
        self.profile = profile

    @staticmethod
    def travel_time_ms(distance: float, velocity: float) -> float:
        if velocity <= 0:
            raise ValueError("velocity must be > 0")
        if distance < 0:
            raise ValueError("distance must be >= 0")
        return distance / velocity * 1000.0

    def budget(self, velocity: float | None = None) -> TimingBudget:
        velocity = self.profile.nominal_velocity if velocity is None else velocity
        trigger_to_frame = self.travel_time_ms(
            self.profile.trigger_to_camera_distance, velocity
        )
        processing = (
            self.profile.acquisition_budget_ms
            + self.profile.ai_budget_ms
            + self.profile.decision_budget_ms
            + self.profile.plc_budget_ms
        )
        frame_to_reject = self.travel_time_ms(
            self.profile.camera_to_reject_distance, velocity
        )
        return TimingBudget(
            trigger_to_frame_ms=trigger_to_frame,
            inspection_processing_ms=processing,
            total_decision_ms=trigger_to_frame + processing,
            frame_to_reject_ms=frame_to_reject,
            total_trigger_to_reject_ms=trigger_to_frame + processing + frame_to_reject,
        )

    def processing_fits_before_reject(self, velocity: float | None = None) -> bool:
        velocity = self.profile.nominal_velocity if velocity is None else velocity
        return self.budget(velocity).inspection_processing_ms <= self.budget(
            velocity
        ).frame_to_reject_ms
