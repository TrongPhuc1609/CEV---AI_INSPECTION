"""Lighting configuration abstraction."""
from dataclasses import dataclass, field
from typing import Dict

@dataclass
class LightingProfile:
    profile_id: str
    mode: str = "STROBE"
    intensity: int = 100
    exposure_us: int = 5000
    gain: float = 1.0
    parameters: Dict[str, float] = field(default_factory=dict)

class LightingController:
    def __init__(self): self.active_profile = None
    def apply(self, profile: LightingProfile): self.active_profile = profile
    def current(self): return self.active_profile
