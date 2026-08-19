"""Dependency-free performance and confidence distribution metrics."""
from __future__ import annotations

from dataclasses import dataclass, field
from math import ceil
from statistics import mean
from typing import Iterable, Optional


@dataclass
class PerformanceMetrics:
    latency_ms: list[float] = field(default_factory=list)
    confidences: list[float] = field(default_factory=list)
    coverages: list[float] = field(default_factory=list)

    def add_latency(self, value_ms: float): self.latency_ms.append(float(value_ms))
    def add_confidence(self, value: Optional[float]):
        if value is not None: self.confidences.append(float(value))
    def add_coverage(self, value: Optional[float]):
        if value is not None: self.coverages.append(float(value))

    @staticmethod
    def _percentile(values: Iterable[float], percentile: float) -> Optional[float]:
        data = sorted(values)
        if not data: return None
        index = max(0, min(len(data) - 1, ceil((percentile / 100.0) * len(data)) - 1))
        return data[index]

    def summary(self) -> dict:
        return {
            "latency_ms": {
                "count": len(self.latency_ms),
                "mean": mean(self.latency_ms) if self.latency_ms else None,
                "p50": self._percentile(self.latency_ms, 50),
                "p95": self._percentile(self.latency_ms, 95),
                "p99": self._percentile(self.latency_ms, 99),
            },
            "confidence": {
                "count": len(self.confidences),
                "mean": mean(self.confidences) if self.confidences else None,
                "p05": self._percentile(self.confidences, 5),
                "p50": self._percentile(self.confidences, 50),
            },
            "coverage_percent": {
                "count": len(self.coverages),
                "mean": mean(self.coverages) if self.coverages else None,
                "p05": self._percentile(self.coverages, 5),
                "p50": self._percentile(self.coverages, 50),
            },
        }
