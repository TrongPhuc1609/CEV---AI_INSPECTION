"""Fail-safe PLC/reject handshake for physical commissioning.

The inspection core decides PASS/NG. This layer is responsible for making the
physical reject command deterministic, idempotent and observable without
coupling the core to a PLC vendor SDK.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable

from src.integration.plc import Decision, PLCCommand, PLCInterface


class RejectStatus(str, Enum):
    NOT_REQUIRED = "NOT_REQUIRED"
    SENT = "SENT"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    TIMEOUT = "TIMEOUT"
    FAILED = "FAILED"


@dataclass(frozen=True)
class RejectResult:
    status: RejectStatus
    inspection_id: str
    product_id: str
    decision: Decision
    elapsed_ms: float
    reason: str = ""

    @property
    def accepted(self) -> bool:
        return self.status in {RejectStatus.NOT_REQUIRED, RejectStatus.ACKNOWLEDGED}


class RejectController:
    """Translate a final inspection decision into one PLC command.

    ``ack`` is injected by the vendor adapter. A physical reject is considered
    successful only when the adapter reports acknowledgement within the
    configured timeout. PASS does not require a reject acknowledgement.
    """

    def __init__(
        self,
        plc: PLCInterface,
        *,
        ack: Callable[[PLCCommand, float], bool] | None = None,
        monotonic_ms: Callable[[], float] | None = None,
        ack_timeout_ms: float = 100.0,
    ) -> None:
        if ack_timeout_ms <= 0:
            raise ValueError("ack_timeout_ms must be > 0")
        self.plc = plc
        self.ack = ack
        self.monotonic_ms = monotonic_ms
        self.ack_timeout_ms = ack_timeout_ms

    def execute(self, command: PLCCommand) -> RejectResult:
        if not command.product_id or not command.inspection_id:
            return RejectResult(
                RejectStatus.FAILED,
                command.inspection_id,
                command.product_id,
                command.decision,
                0.0,
                "MISSING_IDENTITY",
            )

        if command.decision == Decision.PASS:
            return RejectResult(
                RejectStatus.NOT_REQUIRED,
                command.inspection_id,
                command.product_id,
                command.decision,
                0.0,
            )

        start = self.monotonic_ms() if self.monotonic_ms else 0.0
        try:
            self.plc.send(command)
        except Exception as exc:  # vendor adapter failures must fail closed
            elapsed = (self.monotonic_ms() - start) if self.monotonic_ms else 0.0
            return RejectResult(
                RejectStatus.FAILED,
                command.inspection_id,
                command.product_id,
                command.decision,
                elapsed,
                f"PLC_SEND_FAILED:{type(exc).__name__}",
            )

        if self.ack is None:
            elapsed = (self.monotonic_ms() - start) if self.monotonic_ms else 0.0
            return RejectResult(
                RejectStatus.SENT,
                command.inspection_id,
                command.product_id,
                command.decision,
                elapsed,
                "ACK_NOT_CONFIGURED",
            )

        try:
            acknowledged = bool(self.ack(command, self.ack_timeout_ms))
        except Exception as exc:
            elapsed = (self.monotonic_ms() - start) if self.monotonic_ms else 0.0
            return RejectResult(
                RejectStatus.FAILED,
                command.inspection_id,
                command.product_id,
                command.decision,
                elapsed,
                f"PLC_ACK_FAILED:{type(exc).__name__}",
            )

        elapsed = (self.monotonic_ms() - start) if self.monotonic_ms else 0.0
        if acknowledged:
            return RejectResult(
                RejectStatus.ACKNOWLEDGED,
                command.inspection_id,
                command.product_id,
                command.decision,
                elapsed,
            )
        return RejectResult(
            RejectStatus.TIMEOUT,
            command.inspection_id,
            command.product_id,
            command.decision,
            elapsed,
            "PLC_ACK_TIMEOUT",
        )
