"""Product tracking for slowly moving products."""
from dataclasses import dataclass, field
from typing import Dict

@dataclass
class ProductTrack:
    product_id: str
    inspection_id: str
    first_position: float|None
    last_position: float|None
    frames_seen: int=0
    region_frames: Dict[str,int]=field(default_factory=dict)

class ProductTracker:
    def __init__(self): self.tracks={}
    def start(self, product_id, inspection_id, position=None):
        t=ProductTrack(product_id,inspection_id,position,position); self.tracks[product_id]=t; return t
    def update(self, product_id, position=None):
        if product_id not in self.tracks: raise KeyError(f"Unknown product: {product_id}")
        t=self.tracks[product_id]; t.last_position=position; t.frames_seen+=1; return t
    def mark_region(self, product_id, region_id):
        t=self.tracks[product_id]; t.region_frames[region_id]=t.region_frames.get(region_id,0)+1; return t
