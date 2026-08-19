"""Physical commissioning readiness checks.

This module deliberately does not claim that hardware is healthy.  It checks
whether the software configuration and supplied artifacts are sufficient to
START a physical commissioning run, and keeps unresolved field items explicit.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from .release_gate import ProductionReleaseGate
from ..models.registry import ModelRegistry


@dataclass(frozen=True)
class CommissioningCheck:
    name: str
    passed: bool
    blocking: bool = True
    details: str = ""


@dataclass(frozen=True)
class CommissioningReport:
    ready: bool
    checks: tuple[CommissioningCheck, ...] = ()

    @property
    def blockers(self) -> tuple[CommissioningCheck, ...]:
        return tuple(c for c in self.checks if c.blocking and not c.passed)

    @property
    def warnings(self) -> tuple[CommissioningCheck, ...]:
        return tuple(c for c in self.checks if not c.blocking and not c.passed)

    def as_dict(self) -> dict:
        return {
            "ready": self.ready,
            "checks": [
                {
                    "name": c.name,
                    "passed": c.passed,
                    "blocking": c.blocking,
                    "details": c.details,
                }
                for c in self.checks
            ],
            "blockers": [c.name for c in self.blockers],
            "warnings": [c.name for c in self.warnings],
        }


class PhysicalCommissioningGate:
    """Gate that must pass before a real line may be enabled.

    ``real_hardware`` and ``model_root`` are explicit inputs so this check can
    be executed in CI and on a commissioning laptop without hidden state.
    """

    REQUIRED_DRIVERS = {"camera", "trigger", "plc"}

    def evaluate(self, plan, model_root: str = ".", require_real_hardware: bool = True) -> CommissioningReport:
        checks: list[CommissioningCheck] = []

        try:
            plan.validate()
            checks.append(CommissioningCheck("RULE_PLAN_VALID", True, details="InspectionPlan validation passed"))
        except ValueError as exc:
            checks.append(CommissioningCheck("RULE_PLAN_VALID", False, details=str(exc)))

        for name, configs in (
            ("camera", plan.cameras),
            ("trigger", plan.triggers),
        ):
            if configs:
                driver = str(next(iter(configs.values())).driver).upper()
                passed = not require_real_hardware or driver != "MOCK"
                checks.append(CommissioningCheck(
                    f"{name.upper()}_DRIVER",
                    passed,
                    details=f"driver={driver}" + ("" if passed else "; real driver required"),
                ))
            else:
                checks.append(CommissioningCheck(f"{name.upper()}_DRIVER", False, details="no configuration"))

        plc_driver = str(plan.plc.driver).upper()
        checks.append(CommissioningCheck(
            "PLC_DRIVER",
            not require_real_hardware or plc_driver != "MOCK",
            details=f"driver={plc_driver}" + ("" if not require_real_hardware or plc_driver != "MOCK" else "; real driver required"),
        ))

        if plan.lights:
            checks.append(CommissioningCheck("LIGHTING_CONFIG", True, details=f"{len(plan.lights)} lighting profile(s) configured"))
        else:
            checks.append(CommissioningCheck("LIGHTING_CONFIG", False, details="no lighting profile configured"))

        registry = ModelRegistry.from_plan(plan)
        model_results = registry.validate(model_root, require_artifact=require_real_hardware)
        model_errors = [f"{r.model_id}: {error}" for r in model_results for error in r.errors]
        checks.append(CommissioningCheck(
            "MODEL_ARTIFACTS",
            not model_errors,
            details="all model artifacts validated" if not model_errors else "; ".join(model_errors),
        ))

        checks.append(CommissioningCheck(
            "AUDIT_ENABLED",
            bool(plan.audit.enabled),
            details="audit persistence enabled" if plan.audit.enabled else "physical commissioning requires audit persistence",
        ))
        checks.append(CommissioningCheck(
            "RECHECK_POLICY",
            bool(plan.recheck.enabled and plan.recheck.max_attempts >= 2 and plan.recheck.multi_frame),
            details="multi-frame recheck configured" if plan.recheck.enabled and plan.recheck.max_attempts >= 2 and plan.recheck.multi_frame else "multi-frame recheck is required",
        ))
        checks.append(CommissioningCheck(
            "PLC_REJECT",
            bool(plan.plc.reject_enabled),
            details="reject output enabled" if plan.plc.reject_enabled else "PLC reject must be enabled",
        ))

        # Field measurements cannot be inferred from software.  Keep them as
        # explicit non-blocking checklist entries until commissioning values
        # are recorded in a future calibration/line profile.
        for name in (
            "SENSOR_TO_CAMERA_DISTANCE",
            "CONVEYOR_VELOCITY",
            "ACQUISITION_LATENCY",
            "AI_LATENCY",
            "PLC_LATENCY",
            "REJECT_ACTUATOR_LATENCY",
        ):
            checks.append(CommissioningCheck(name, False, blocking=False, details="field measurement not recorded"))

        return CommissioningReport(
            ready=not any(c.blocking and not c.passed for c in checks),
            checks=tuple(checks),
        )


def evaluate_physical_commissioning(plan, model_root: str = ".") -> CommissioningReport:
    return PhysicalCommissioningGate().evaluate(plan, model_root=model_root, require_real_hardware=True)
