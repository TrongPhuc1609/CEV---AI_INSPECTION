"""Physical commissioning readiness and controlled acceptance helpers.

This module deliberately does not implement vendor SDKs. It provides a
vendor-neutral gate plus a bounded runner around the production pipeline so
real camera/trigger/PLC adapters can be commissioned without changing the
inspection core.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from time import monotonic
from typing import Any, Optional

from ..models.registry import ModelRegistry
from .hardware_adapters import MockHardwareFactory
from .plc import Decision, PLCCommand


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
                {"name": c.name, "passed": c.passed, "blocking": c.blocking, "details": c.details}
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
        camera_ok = bool(camera_drivers) and (not require_real_hardware or all(driver != "MOCK" for driver in camera_drivers))
        checks.append(CommissioningCheck("CAMERA_DRIVER", camera_ok, details=f"drivers={camera_drivers}" if camera_drivers else "no camera configured"))

        trigger_drivers = [str(cfg.settings.get("driver", "")).upper() for cfg in plan.triggers.values()]
        trigger_ok = bool(trigger_drivers) and (not require_real_hardware or all(driver and driver != "MOCK" for driver in trigger_drivers))
        checks.append(CommissioningCheck("TRIGGER_DRIVER", trigger_ok, details=f"drivers={trigger_drivers}" if trigger_drivers else "no trigger configured"))

        plc_driver = str(plan.plc.driver).upper()
        plc_ok = bool(plc_driver) and (not require_real_hardware or plc_driver != "MOCK")
        checks.append(CommissioningCheck("PLC_DRIVER", plc_ok, details=f"driver={plc_driver or '<missing>'}"))

        lighting_ok = bool(plan.lights)
        checks.append(CommissioningCheck("LIGHTING_CONFIG", lighting_ok, details=f"{len(plan.lights)} lighting profile(s) configured" if lighting_ok else "no lighting profile configured"))

        registry = ModelRegistry.from_plan(plan)
        if not registry.manifests:
            model_errors = ["MODEL_CONFIGURATION_MISSING"]
        else:
            model_results = registry.validate(model_root, require_artifact=require_real_hardware)
            model_errors = [f"{result.model_id}: {error}" for result in model_results for error in result.errors]
        checks.append(CommissioningCheck("MODEL_ARTIFACTS", not model_errors, details="all model artifacts validated" if not model_errors else "; ".join(model_errors)))
        checks.append(CommissioningCheck("AUDIT_ENABLED", bool(plan.audit.enabled), details="audit persistence enabled" if plan.audit.enabled else "physical commissioning requires audit persistence"))
        recheck_ok = bool(plan.recheck.enabled and plan.recheck.max_attempts >= 2 and plan.recheck.multi_frame)
        checks.append(CommissioningCheck("RECHECK_POLICY", recheck_ok, details="multi-frame recheck configured" if recheck_ok else "multi-frame recheck is required"))
        checks.append(CommissioningCheck("PLC_REJECT", bool(plan.plc.reject_enabled), details="reject output enabled" if plan.plc.reject_enabled else "PLC reject must be enabled"))

        for name in ("SENSOR_TO_CAMERA_DISTANCE", "CONVEYOR_VELOCITY", "ACQUISITION_LATENCY", "AI_LATENCY", "PLC_LATENCY", "REJECT_ACTUATOR_LATENCY"):
            checks.append(CommissioningCheck(name, False, blocking=False, details="field measurement not recorded"))

        return CommissioningReport(
            ready=not any(check.blocking and not check.passed for check in checks),
            checks=tuple(checks),
        )


def evaluate_physical_commissioning(plan, model_root: str = ".") -> CommissioningReport:
    return PhysicalCommissioningGate().evaluate(plan, model_root=model_root, require_real_hardware=True)


@dataclass(frozen=True)
class CommissioningAcceptanceProfile:
    """Bounded field-test policy."""
    sample_count: int = 10
    expected_product_id: Optional[str] = None
    require_pass_count: int = 1
    require_plc_observation: bool = True
    allow_ng_samples: bool = True
    enable_reject_test: bool = False


@dataclass
class CommissioningSample:
    index: int
    product_id: Optional[str]
    inspection_id: Optional[str]
    decision: Optional[str]
    elapsed_ms: float
    plc_command: Optional[PLCCommand] = None
    error: Optional[str] = None


@dataclass
class CommissioningRunReport:
    ready: bool
    samples: list[CommissioningSample] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def pass_count(self) -> int:
        return sum(1 for sample in self.samples if sample.decision == Decision.PASS.value)

    @property
    def ng_count(self) -> int:
        return sum(1 for sample in self.samples if sample.decision == Decision.NG.value)

    def as_dict(self) -> dict:
        return {
            "ready": self.ready,
            "pass_count": self.pass_count,
            "ng_count": self.ng_count,
            "blockers": list(self.blockers),
            "warnings": list(self.warnings),
            "samples": [
                {"index": s.index, "product_id": s.product_id, "inspection_id": s.inspection_id,
                 "decision": s.decision, "elapsed_ms": s.elapsed_ms, "error": s.error}
                for s in self.samples
            ],
        }


class RealHardwareCommissioning:
    """Run a finite acceptance sequence against a real pipeline.

    A real PLC adapter must expose a ``commands`` list (the same recorder
    contract used by CallbackPLC) so the acceptance test can prove that the
    decision reached the PLC.
    """

    def __init__(self, pipeline, profile: CommissioningAcceptanceProfile):
        self.pipeline = pipeline
        self.profile = profile

    def preflight(self) -> CommissioningRunReport:
        blockers: list[str] = []
        warnings: list[str] = []
        acquisition = getattr(self.pipeline, "acquisition", None)
        plc = getattr(self.pipeline, "plc", None)
        if acquisition is None:
            blockers.append("ACQUISITION_MISSING")
        if plc is None:
            blockers.append("PLC_MISSING")
        camera = getattr(acquisition, "camera", None) if acquisition else None
        trigger = getattr(acquisition, "trigger", None) if acquisition else None
        if camera is not None and camera.__class__.__name__ == "MockCamera":
            blockers.append("CAMERA_IS_MOCK")
        if trigger is not None and trigger.__class__.__name__ == "MockTrigger":
            blockers.append("TRIGGER_IS_MOCK")
        if plc is not None and plc.__class__.__name__ == "MockPLC":
            blockers.append("PLC_IS_MOCK")
        if self.profile.sample_count < 1:
            blockers.append("INVALID_SAMPLE_COUNT")
        if self.profile.require_pass_count > self.profile.sample_count:
            blockers.append("INVALID_PASS_REQUIREMENT")
        if self.profile.require_plc_observation and not isinstance(getattr(plc, "commands", None), list):
            blockers.append("PLC_COMMAND_RECORDING_REQUIRED")
        if not self.profile.enable_reject_test:
            warnings.append("REJECT_TEST_DISABLED: perform guarded reject test separately")
        return CommissioningRunReport(not blockers, blockers=blockers, warnings=warnings)

    def run(self) -> CommissioningRunReport:
        report = self.preflight()
        if not report.ready:
            return report
        plc = self.pipeline.plc
        command_index = len(plc.commands)
        try:
            self.pipeline.start()
            for index in range(1, self.profile.sample_count + 1):
                started = monotonic()
                inspection = self.pipeline.run_product()
                elapsed_ms = (monotonic() - started) * 1000.0
                command = plc.commands[-1] if len(plc.commands) > command_index else None
                command_index = len(plc.commands)
                product_id = getattr(inspection, "product_id", None) if inspection else None
                inspection_id = getattr(inspection, "inspection_id", None) if inspection else None
                decision = command.decision.value if command else None
                error = None if inspection is not None else "INSPECTION_RETURNED_NONE"
                report.samples.append(CommissioningSample(index, product_id, inspection_id, decision, elapsed_ms, command, error))
        except Exception as exc:
            report.blockers.append("COMMISSIONING_RUNTIME_ERROR:" + str(exc))
        finally:
            self.pipeline.stop()

        if self.profile.expected_product_id:
            for sample in report.samples:
                if sample.product_id not in (None, self.profile.expected_product_id):
                    report.blockers.append("UNEXPECTED_PRODUCT_ID:" + str(sample.product_id))
        if report.pass_count < self.profile.require_pass_count:
            report.blockers.append("INSUFFICIENT_PASS_SAMPLES")
        if not self.profile.allow_ng_samples and report.ng_count:
            report.blockers.append("NG_SAMPLE_PRESENT")
        report.ready = not report.blockers
        return report


def assert_real_factory(factory: Any) -> None:
    if isinstance(factory, MockHardwareFactory):
        raise RuntimeError("REAL_HARDWARE_REQUIRED: MockHardwareFactory is not allowed")


def guarded_reject_test(plc, product_id: str, inspection_id: str) -> PLCCommand:
    """Send the deterministic NG command used by a guarded reject test."""
    command = PLCCommand(Decision.NG, product_id, inspection_id, ["COMMISSIONING_REJECT_TEST"])
    plc.send(command)
    return command
