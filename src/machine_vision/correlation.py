"""Correlation of trigger events and camera frames for moving products."""
from dataclasses import dataclass
from typing import Optional

from .camera.base import Frame
from .trigger.base import TriggerEvent


@dataclass(frozen=True)
class CorrelationResult:
    matched: bool
    product_id: Optional[str]
    event_id: str
    frame_id: str
    timestamp_delta_ms: float
    position_delta: Optional[float]
    reason: str


class TriggerFrameCorrelator:
    """Validate that a captured frame belongs to the triggering product."""

    def __init__(self, max_timestamp_delta_ms: float = 100.0, max_position_delta: float | None = None):
        if max_timestamp_delta_ms < 0:
            raise ValueError("max_timestamp_delta_ms must be >= 0")
        if max_position_delta is not None and max_position_delta < 0:
            raise ValueError("max_position_delta must be >= 0")
        self.max_timestamp_delta_ms = max_timestamp_delta_ms
        self.max_position_delta = max_position_delta

    def correlate(self, event: TriggerEvent, frame: Frame) -> CorrelationResult:
        delta_ms = abs(frame.timestamp - event.timestamp) * 1000.0
        frame_product = frame.metadata.get("product_id") if frame.metadata else None
        product_id = frame_product or event.product_id
        if frame_product and event.product_id and frame_product != event.product_id:
            return CorrelationResult(False, product_id, event.event_id, frame.frame_id, delta_ms, None, "PRODUCT_ID_MISMATCH")
        if delta_ms > self.max_timestamp_delta_ms:
            return CorrelationResult(False, product_id, event.event_id, frame.frame_id, delta_ms, None, "TIMESTAMP_OUT_OF_TOLERANCE")
        position_delta = None
        frame_position = frame.metadata.get("position") if frame.metadata else None
        if event.position is not None and frame_position is not None:
            position_delta = abs(float(frame_position) - float(event.position))
            if self.max_position_delta is not None and position_delta > self.max_position_delta:
                return CorrelationResult(False, product_id, event.event_id, frame.frame_id, delta_ms, position_delta, "POSITION_OUT_OF_TOLERANCE")
        return CorrelationResult(True, product_id, event.event_id, frame.frame_id, delta_ms, position_delta, "MATCH")
