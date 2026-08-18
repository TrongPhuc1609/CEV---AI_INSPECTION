"""Image acquisition service: trigger -> lighting -> camera -> frame."""
from dataclasses import dataclass
from typing import Optional
from ..camera.base import Camera, Frame
from ..trigger.base import TriggerSource, TriggerEvent
from ..lighting.controller import LightingController, LightingProfile

@dataclass
class AcquisitionResult:
    trigger: TriggerEvent
    frame: Frame

class ImageAcquisition:
    def __init__(self, camera: Camera, trigger: TriggerSource, lighting: Optional[LightingController]=None, lighting_profile: Optional[LightingProfile]=None):
        self.camera=camera; self.trigger=trigger; self.lighting=lighting; self.lighting_profile=lighting_profile
    def start(self):
        self.camera.open()
        if self.lighting and self.lighting_profile: self.lighting.apply(self.lighting_profile)
    def stop(self): self.camera.close()
    def acquire(self) -> AcquisitionResult:
        event=self.trigger.wait(); frame=self.camera.capture()
        return AcquisitionResult(event, frame)
