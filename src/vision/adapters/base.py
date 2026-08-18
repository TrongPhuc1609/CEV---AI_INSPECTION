"""Common AI Vision Adapter interface."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional
from ...models.result import Observation

@dataclass
class VisionInput:
    product_id: str
    inspection_id: str
    region_id: str
    image: Any
    frame_id: Optional[str]=None
    metadata: Dict[str,Any]|None=None

class VisionAdapter(ABC):
    method: str
    @abstractmethod
    def inspect(self, data: VisionInput) -> Observation: raise NotImplementedError
