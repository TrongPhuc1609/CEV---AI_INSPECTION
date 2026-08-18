"""Deterministic Rule Engine. AI provides observations; this module decides status."""

from typing import List
from .parser import RuleConfig
from ..models.result import Observation, Status


class RuleEngine:
    def __init__(self, config: RuleConfig):
        self.config = config

    def evaluate(self, obs: Observation) -> Observation:
        rule = self.config.region(obs.region_id)
        if not rule or not rule.get("enabled", True):
            obs.status = Status.UNCERTAIN
            obs.error_code = "REGION_NOT_CONFIGURED"
            return obs

        method = str(rule.get("method", obs.method))
        obs.method = method

        min_conf = rule.get("min_confidence")
        if obs.confidence is not None and min_conf is not None and obs.confidence < min_conf:
            obs.status = Status.UNCERTAIN
            obs.error_code = "LOW_CONFIDENCE"
            return obs

        if method in {"DETECTION", "DETECTION_CLASSIFICATION"}:
            return self._evaluate_component(obs, rule)

        if method == "SEGMENTATION":
            return self._evaluate_grease(obs, rule)

        obs.status = Status.UNCERTAIN
        obs.error_code = "UNSUPPORTED_METHOD"
        return obs

    def _evaluate_component(self, obs: Observation, rule: dict) -> Observation:
        expected = rule.get("expected_component")
        expected_qty = rule.get("expected_quantity")
        obs.expected_class = expected
        obs.expected_quantity = expected_qty

        if obs.quantity is not None and expected_qty is not None:
            if obs.quantity < expected_qty:
                obs.status = Status.FAIL
                obs.error_code = "MISSING_COMPONENT"
                return obs
            if obs.quantity > expected_qty:
                obs.status = Status.FAIL
                obs.error_code = "EXTRA_COMPONENT"
                return obs

        if expected and obs.detected_class and obs.detected_class != expected:
            obs.status = Status.FAIL
            obs.error_code = "WRONG_COMPONENT"
            return obs

        obs.status = Status.PASS
        obs.error_code = None
        return obs

    def _evaluate_grease(self, obs: Observation, rule: dict) -> Observation:
        required = rule.get("grease_required", False)
        min_cov = rule.get("min_coverage_percent")
        max_cov = rule.get("max_coverage_percent")

        if required and (obs.coverage_percent is None or obs.coverage_percent <= 0):
            obs.status = Status.FAIL
            obs.error_code = "NO_GREASE"
            return obs

        if obs.coverage_percent is not None:
            if min_cov is not None and obs.coverage_percent < min_cov:
                obs.status = Status.FAIL
                obs.error_code = "INSUFFICIENT_GREASE"
                return obs
            if max_cov is not None and obs.coverage_percent > max_cov:
                obs.status = Status.FAIL
                obs.error_code = "EXCESS_GREASE"
                return obs

        obs.status = Status.PASS
        obs.error_code = None
        return obs

    def evaluate_all(self, observations: List[Observation]) -> Status:
        if not observations:
            return Status.UNCERTAIN
        if any(o.status == Status.FAIL for o in observations):
            return Status.FAIL
        if any(o.status == Status.UNCERTAIN for o in observations):
            return Status.UNCERTAIN
        return Status.PASS
