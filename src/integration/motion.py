"""Motion/latency safety checks for a slowly moving inspection line."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class MotionAssessment:
    velocity: Optional[float]
    velocity_ok: bool
    reject_window_ms: Optional[float]
    errors: tuple[str, ...] = ()


class MotionSafetyMonitor:
    """Validates product velocity and the time available before reject."""
    def __init__(self, nominal_velocity: float, min_velocity: float, max_velocity: float,
                 camera_to_reject_distance: float):
        self.nominal_velocity = float(nominal_velocity)
        self.min_velocity = float(min_velocity)
        self.max_velocity = float(max_velocity)
        self.camera_to_reject_distance = float(camera_to_reject_distance)

    def assess(self, velocity: Optional[float]) -> MotionAssessment:
        errors: list[str] = []
        if velocity is None:
            return MotionAssessment(None, False, None, ("VELOCITY_UNAVAILABLE",))
        velocity = float(velocity)
        velocity_ok = self.min_velocity <= abs(velocity) <= self.max_velocity
        if not velocity_ok:
            errors.append("VELOCITY_OUT_OF_RANGE")
        window_ms = None
        if self.camera_to_reject_distance > 0 and abs(velocity) > 0:
            window_ms = self.camera_to_reject_distance / abs(velocity) * 1000.0
        return MotionAssessment(velocity, velocity_ok, window_ms, tuple(errors))

    @staticmethod
    def within_reject_window(elapsed_ms: float, reject_window_ms: Optional[float]) -> bool:
        return reject_window_ms is None or elapsed_ms <= reject_window_ms

    def effective_velocity(self, measured: Optional[float]) -> float:
        return abs(float(measured)) if measured is not None and abs(float(measured)) > 0 else abs(self.nominal_velocity)
