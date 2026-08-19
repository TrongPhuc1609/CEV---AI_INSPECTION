"""Deterministic hardware-in-the-loop harness for commissioning tests."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterable, Optional

from .plc import Decision, PLCCommand
from .timing import TimingCollector


@dataclass(frozen=True)
class HILScenario:
    name: str
    expected_decision: Decision
    expected_reason: Optional[str] = None


@dataclass
class HILResult:
    scenario: HILScenario
    actual_decision: Optional[Decision]
    commands: list[PLCCommand] = field(default_factory=list)
    passed: bool = False
    timing: dict = field(default_factory=dict)


class HILRunner:
    """Runs a pipeline against injected hardware/model doubles.

    The runner deliberately does not know camera, AI or PLC vendor APIs.  A
    scenario factory creates a fully wired pipeline, which makes the same
    scenarios reusable when real adapters are introduced.
    """
    def __init__(self, pipeline_factory: Callable[[HILScenario], object]):
        self.pipeline_factory = pipeline_factory

    def run(self, scenario: HILScenario) -> HILResult:
        pipeline = self.pipeline_factory(scenario)
        timer = getattr(pipeline, "timing", TimingCollector())
        inspection = pipeline.run_product()
        plc = pipeline.plc
        commands = list(getattr(plc, "commands", []))
        actual = commands[-1].decision if commands else None
        reason_ok = True
        if scenario.expected_reason:
            reason_ok = any(scenario.expected_reason in reason for reason in commands[-1].reasons) if commands else False
        passed = actual == scenario.expected_decision and reason_ok
        return HILResult(scenario, actual, commands, passed, timer.summary())

    def run_all(self, scenarios: Iterable[HILScenario]) -> list[HILResult]:
        return [self.run(scenario) for scenario in scenarios]
