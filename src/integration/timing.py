"""Timing/latency instrumentation for commissioning a moving inspection line."""
from __future__ import annotations

from dataclasses import dataclass, field
from time import monotonic
from typing import Dict, Optional


@dataclass(frozen=True)
class TimingBudget:
    """Expected upper bounds in milliseconds for one inspection cycle."""
    trigger_timeout_ms: float = 500.0
    acquisition_max_ms: float = 100.0
    ai_max_ms: float = 200.0
    decision_max_ms: float = 50.0
    plc_max_ms: float = 50.0
    reject_max_ms: float = 200.0

    @property
    def inspection_max_ms(self) -> float:
        return self.acquisition_max_ms + self.ai_max_ms + self.decision_max_ms + self.plc_max_ms


@dataclass
class TimingSample:
    name: str
    elapsed_ms: float
    metadata: Dict[str, object] = field(default_factory=dict)


class TimingCollector:
    """Small dependency-free timer suitable for production and HIL tests."""
    def __init__(self, budget: Optional[TimingBudget] = None):
        self.budget = budget or TimingBudget()
        self.samples: list[TimingSample] = []

    def measure(self, name: str, start: float, end: Optional[float] = None, **metadata) -> TimingSample:
        end = monotonic() if end is None else end
        sample = TimingSample(name, (end - start) * 1000.0, metadata)
        self.samples.append(sample)
        return sample

    def start(self) -> float:
        return monotonic()

    def last(self, name: str) -> Optional[TimingSample]:
        for sample in reversed(self.samples):
            if sample.name == name:
                return sample
        return None

    def exceeds(self, name: str) -> bool:
        sample = self.last(name)
        if sample is None:
            return False
        limits = {
            "acquisition": self.budget.acquisition_max_ms,
            "ai": self.budget.ai_max_ms,
            "decision": self.budget.decision_max_ms,
            "plc": self.budget.plc_max_ms,
            "reject": self.budget.reject_max_ms,
        }
        limit = limits.get(name)
        return limit is not None and sample.elapsed_ms > limit

    def summary(self) -> Dict[str, object]:
        return {
            "budget_ms": {
                "inspection_max": self.budget.inspection_max_ms,
                "trigger_timeout": self.budget.trigger_timeout_ms,
                "reject_max": self.budget.reject_max_ms,
            },
            "samples": [
                {"name": s.name, "elapsed_ms": s.elapsed_ms, "metadata": s.metadata}
                for s in self.samples
            ],
        }
