"""Offline deterministic replay for inspection-rule calibration."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .models.result import Observation, Status


@dataclass(frozen=True)
class ReplayOutcome:
    index: int
    status: Status
    error_code: str | None


class ObservationReplay:
    def __init__(self, rule_engine):
        self.rule_engine = rule_engine

    @staticmethod
    def load(path: str | Path) -> list[Observation]:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            payload = payload.get("observations", [payload])
        observations = []
        for item in payload:
            data = dict(item)
            data["status"] = Status(data.get("status", Status.UNCERTAIN))
            observations.append(Observation(**data))
        return observations

    def evaluate(self, observations: Iterable[Observation]) -> list[ReplayOutcome]:
        outcomes = []
        for index, observation in enumerate(observations):
            result = self.rule_engine.evaluate(observation)
            outcomes.append(ReplayOutcome(index, result.status, result.error_code))
        return outcomes

    def assert_expected(self, observations: Iterable[Observation], expected: Iterable[tuple[str, str | None]]) -> list[ReplayOutcome]:
        outcomes = self.evaluate(observations)
        expected = list(expected)
        if len(outcomes) != len(expected):
            raise AssertionError(f"Replay length mismatch: {len(outcomes)} != {len(expected)}")
        for outcome, (status, error_code) in zip(outcomes, expected):
            if outcome.status.value != status or outcome.error_code != error_code:
                raise AssertionError(f"Replay mismatch at {outcome.index}: got {(outcome.status.value, outcome.error_code)}, expected {(status, error_code)}")
        return outcomes
