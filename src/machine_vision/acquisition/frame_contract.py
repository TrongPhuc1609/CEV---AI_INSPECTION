from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AcquiredFrame:
    """Vendor-neutral image acquisition record used by the inspection pipeline."""

    frame_id: str
    product_id: str
    timestamp_ns: int
    image: Any
    camera_id: str
    trigger_id: str | None = None
    exposure_us: int | None = None
    lighting_profile: str | None = None

    def is_valid(self) -> bool:
        return bool(self.frame_id and self.product_id and self.camera_id and self.timestamp_ns > 0)


@dataclass(frozen=True)
class AcquisitionHealth:
    ready: bool
    camera_connected: bool
    trigger_connected: bool
    lighting_ready: bool
    reason: str = ""

    @property
    def commissioning_ready(self) -> bool:
        return self.ready and self.camera_connected and self.trigger_connected and self.lighting_ready
