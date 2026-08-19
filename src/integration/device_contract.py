"""Common device capability and health contracts for physical commissioning.

Vendor SDKs must implement these semantics through adapters. The inspection
core can use this contract to decide whether a device is usable without
knowing the vendor SDK or transport protocol.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, FrozenSet


class DeviceState(str, Enum):
    DISCONNECTED = "DISCONNECTED"
    READY = "READY"
    DEGRADED = "DEGRADED"
    FAULT = "FAULT"


@dataclass(frozen=True)
class DeviceHealth:
    device_id: str
    state: DeviceState
    message: str = ""
    timestamp_s: float = 0.0
    metrics: Dict[str, float] = field(default_factory=dict)

    @property
    def usable(self) -> bool:
        return self.state == DeviceState.READY


@dataclass(frozen=True)
class DeviceCapabilities:
    device_id: str
    device_type: str
    vendor: str = "UNKNOWN"
    model: str = "UNKNOWN"
    serial: str = "UNKNOWN"
    capabilities: FrozenSet[str] = frozenset()
    metadata: Dict[str, Any] = field(default_factory=dict)

    def supports(self, capability: str) -> bool:
        return capability in self.capabilities


class CommissioningDevice:
    """Minimal runtime contract expected from a real hardware adapter."""

    def health(self) -> DeviceHealth:
        raise NotImplementedError

    def capabilities(self) -> DeviceCapabilities:
        raise NotImplementedError

    def self_test(self) -> DeviceHealth:
        """Run a non-destructive device diagnostic before commissioning."""
        return self.health()
