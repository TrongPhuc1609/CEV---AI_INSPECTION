"""Physical commissioning readiness checks.

This module deliberately does not claim that hardware is healthy. It checks
whether the software configuration and supplied artifacts are sufficient to
START a physical commissioning run, and keeps unresolved field items explicit.
"""
from __future__ import annotations

from dataclasses import dataclass
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
    """Gate that must pass before a real line may be enabled."""

    def evaluate(self, plan, model_root: str = ".", require_real_hardware: bool = True) -> CommissioningReport:
        checks: list[CommissioningCheck] = []

        try:
            plan.validate()
            checks.append(CommissioningCheck("RULE_PLAN_VALID", True, details="InspectionPlan validation passed"))
        except ValueError as exc:
            checks.append(CommissioningCheck("RULE_PLAN_VALID", False, details=str(exc)))

        camera_drivers = [str(cfg.driver).upper() for cfg in plan.cameras.values()]
        camera_ok = bool(camera_drivers) and (
            not require_real_hardware or all(driver != "MOCK" for driver in camera_drivers)
        )
        checks.append(CommissioningCheck(
            "CAMERA_DRIVER",
            camera_ok,
            details=(f"drivers={camera_drivers}" if camera_drivers else "no camera configured")
            + ("; real driver required" if require_real_hardware and not camera_ok else ""),
        ))

        trigger_drivers = [str(cfg.settings.get("driver", "")).upper() for cfg in plan.triggers.values()]
        trigger_ok = bool(trigger_drivers) and (
            not require_real_hardware or all(driver and driver != "MOCK" for driver in trigger_drivers)
        )
        checks.append(CommissioningCheck(
            "TRIGGER_DRIVER",
            trigger_ok,
            details=(f"drivers={trigger_drivers}" if trigger_drivers else "no trigger configured")
            + ("; explicit real trigger driver required" if require_real_hardware and not trigger_ok else ""),
        ))

        plc_driver = str(plan.plc.driver).upper()
        plc_ok = bool(plc_driver) and (not require_real_hardware or plc_driver != "MOCK")
        checks.append(CommissioningCheck(
            "PLC_DRIVER",
            plc_ok,
            details=f"driver={plc_driver or '<missing>'}"
            + ("; real driver required" if require_real_hardware and not plc_ok else ""),
        ))

        lighting_ok = bool(plan.lights)
        checks.append(CommissioningCheck(
            "LIGHTING_CONFIG",
            lighting_ok,
            details=f"{len(plan.lights)} lighting profile(s) configured"
            if lighting_ok else "no lighting profile configured",
        ))

        registry = ModelRegistry.from_plan(plan)
        if not registry.manifests:
            model_errors = ["MODEL_CONFIGURATION_MISSING"]
        else:
            model_results = registry.validate(model_root, require_artifact=require_real_hardware)
            model_errors = [
                f"{result.model_id}: {error}"
                for result in model_results
                for error in result.errors
            ]
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
        recheck_ok = bool(plan.recheck.enabled and plan.recheck.max_attempts >= 2 and plan.recheck.multi_frame)
        checks.append(CommissioningCheck(
            "RECHECK_POLICY",
            recheck_ok,
            details="multi-frame recheck configured" if recheck_ok else "multi-frame recheck is required",
        ))
        checks.append(CommissioningCheck(
            "PLC_REJECT",
            bool(plan.plc.reject_enabled),
            details="reject output enabled" if plan.plc.reject_enabled else "PLC reject must be enabled",
        ))

        # Field measurements cannot be inferred from software. Keep them as
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
            ready=not any(check.blocking and not check.passed for check in checks),
            checks=tuple(checks),
        )


def evaluate_physical_commissioning(plan, model_root: str = ".") -> CommissioningReport:
    return PhysicalCommissioningGate().evaluate(plan, model_root=model_root, require_real_hardware=True)
