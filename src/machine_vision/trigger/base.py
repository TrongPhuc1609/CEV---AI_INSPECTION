"""Trigger abstraction for sensor, PLC, encoder, software or continuous triggering."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict

class TriggerType(str, Enum):
    SENSOR="SENSOR"; PLC="PLC"; ENCODER="ENCODER"; SOFTWARE="SOFTWARE"; CONTINUOUS="CONTINUOUS"

@dataclass
class TriggerEvent:
    event_id: str
    trigger_type: TriggerType
    timestamp: float
    product_id: str | None = None
    position: float | None = None
    metadata: Dict[str, Any] | None = None

class TriggerSource(ABC):
    @abstractmethod
    def wait(self) -> TriggerEvent: ...

class MockTrigger(TriggerSource):
    def __init__(self): self.counter=0
    def wait(self):
        import time
        self.counter += 1
        return TriggerEvent(f"T{self.counter}", TriggerType.SENSOR, time.time(), f"PRODUCT-{self.counter}", float(self.counter), {})
