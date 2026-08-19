"""Explicit software release gates; production mode must fail closed."""
from __future__ import annotations

from dataclasses import dataclass

from ..models.registry import ModelRegistry


@dataclass(frozen=True)
class ReleaseGateResult:
    ready: bool
    errors: tuple[str, ...] = ()


class ProductionReleaseGate:
    def validate(self, plan, model_root=".", real_hardware=False, require_models=False) -> ReleaseGateResult:
        errors = []
        try:
            plan.validate()
        except ValueError as exc:
            errors.append(str(exc))

        if real_hardware and str(getattr(plan.cameras[next(iter(plan.cameras))], "driver", "MOCK")).upper() == "MOCK":
            errors.append("REAL_HARDWARE_REQUIRES_NON_MOCK_CAMERA")
        if real_hardware and str(plan.plc.driver).upper() == "MOCK":
            errors.append("REAL_HARDWARE_REQUIRES_NON_MOCK_PLC")

        registry = ModelRegistry.from_plan(plan)
        if require_models or real_hardware:
            for result in registry.validate(model_root, require_artifact=True):
                errors.extend(f"{result.model_id}:{error}" for error in result.errors)

        if real_hardware and not plan.audit.enabled:
            errors.append("REAL_HARDWARE_REQUIRES_AUDIT")
        return ReleaseGateResult(not errors, tuple(errors))
