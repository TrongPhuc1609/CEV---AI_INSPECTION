"""PLC / reject abstraction."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import List

class Decision(str, Enum):
    PASS = "PASS"
    NG = "NG"
    UNCERTAIN = "UNCERTAIN"

@dataclass
class PLCCommand:
    decision: Decision
    product_id: str
    inspection_id: str
    reasons: List[str]

class PLCInterface(ABC):
    @abstractmethod
    def send(self, command: PLCCommand) -> None: ...

class MockPLC(PLCInterface):
    def __init__(self):
        self.commands = []
    def send(self, command: PLCCommand):
        self.commands.append(command)
