"""Camera abstraction for industrial/image acquisition."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict

@dataclass
class Frame:
    frame_id: str
    image: Any
    timestamp: float
    camera_id: str
    metadata: Dict[str, Any]

class Camera(ABC):
    @abstractmethod
    def open(self) -> None: ...
    @abstractmethod
    def close(self) -> None: ...
    @abstractmethod
    def configure(self, **settings) -> None: ...
    @abstractmethod
    def capture(self) -> Frame: ...

class MockCamera(Camera):
    def __init__(self, camera_id="CAM01"):
        self.camera_id = camera_id
        self.opened = False
        self.counter = 0
        self.settings = {}
    def open(self): self.opened = True
    def close(self): self.opened = False
    def configure(self, **settings): self.settings.update(settings)
    def capture(self):
        if not self.opened:
            raise RuntimeError("Camera is not open")
        import time
        self.counter += 1
        return Frame(f"{self.camera_id}-F{self.counter}", f"mock-image-{self.counter}", time.time(), self.camera_id, {"settings": dict(self.settings)})
