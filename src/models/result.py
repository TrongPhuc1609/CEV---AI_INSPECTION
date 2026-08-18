"""Normalized result contract shared by all AI vision modules."""

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, Optional
import json


class Status(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNCERTAIN = "UNCERTAIN"


@dataclass
class Observation:
    product_id: str
    inspection_id: str
    region_id: str
    method: str
    detected_class: Optional[str] = None
    expected_class: Optional[str] = None
    confidence: Optional[float] = None
    quantity: Optional[int] = None
    expected_quantity: Optional[int] = None
    position: Optional[Dict[str, float]] = None
    coverage_percent: Optional[float] = None
    status: Status = Status.UNCERTAIN
    error_code: Optional[str] = None
    evidence_image: Optional[str] = None
    timestamp: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value
        return d

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
