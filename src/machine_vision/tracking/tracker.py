"""Product tracking for slowly moving products."""
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class ProductTrack:
    product_id: str
    inspection_id: str
    first_position: float | None
    last_position: float | None
    first_timestamp: float | None = None
    last_timestamp: float | None = None
    velocity_units_per_s: float | None = None
    frames_seen: int = 0
    region_frames: Dict[str, int] = field(default_factory=dict)


class ProductTracker:
    def __init__(self):
        self.tracks = {}

    def start(self, product_id, inspection_id, position=None, timestamp: Optional[float] = None):
        track = ProductTrack(product_id, inspection_id, position, position, timestamp, timestamp)
        self.tracks[product_id] = track
        return track

    def update(self, product_id, position=None, timestamp: Optional[float] = None):
        if product_id not in self.tracks:
            raise KeyError(f"Unknown product: {product_id}")
        track = self.tracks[product_id]
        if position is not None and track.last_position is not None and timestamp is not None and track.last_timestamp is not None:
            dt = timestamp - track.last_timestamp
            if dt > 0:
                track.velocity_units_per_s = (position - track.last_position) / dt
        track.last_position = position
        if timestamp is not None:
            track.last_timestamp = timestamp
        track.frames_seen += 1
        return track

    def mark_region(self, product_id, region_id):
        track = self.tracks[product_id]
        track.region_frames[region_id] = track.region_frames.get(region_id, 0) + 1
        return track
