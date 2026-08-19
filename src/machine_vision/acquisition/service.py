"""Image acquisition service: trigger -> lighting -> camera -> frame."""
from dataclasses import dataclass
from time import monotonic
from typing import Callable, Optional
from ..camera.base import Camera, Frame
from ..trigger.base import TriggerSource, TriggerEvent
from ..lighting.controller import LightingController, LightingProfile


@dataclass
class AcquisitionResult:
    trigger: TriggerEvent
    frame: Frame
    acquisition_ms: float = 0.0


class ImageAcquisition:
    def __init__(self, camera: Camera, trigger: TriggerSource, lighting: Optional[LightingController] = None,
                 lighting_profile: Optional[LightingProfile] = None,
                 on_timing: Optional[Callable[[str, float], None]] = None):
        self.camera = camera
        self.trigger = trigger
        self.lighting = lighting
        self.lighting_profile = lighting_profile
        self.on_timing = on_timing
        self.started = False

    def start(self):
        if self.started:
            return
        self.camera.open()
        if self.lighting and self.lighting_profile:
            self.lighting.apply(self.lighting_profile)
        self.started = True

    def stop(self):
        if not self.started:
            return
        self.camera.close()
        self.started = False

    def acquire(self) -> AcquisitionResult:
        if not self.started:
            raise RuntimeError("ImageAcquisition is not started")
        started = monotonic()
        event = self.trigger.wait()
        frame = self.camera.capture()
        elapsed_ms = (monotonic() - started) * 1000.0
        if self.on_timing:
            self.on_timing("acquisition", elapsed_ms)
        return AcquisitionResult(event, frame, elapsed_ms)
