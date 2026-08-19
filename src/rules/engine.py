"""Deterministic Rule Engine. AI produces observations; rules decide status."""
from typing import List
from .parser import RuleConfig
from ..models.result import Observation, Status

class RuleEngine:
    def __init__(self, config: RuleConfig): self.config=config
    def evaluate(self, obs: Observation) -> Observation:
        rule=self.config.region(obs.region_id)
        if not rule or not rule.get("enabled",True): obs.status=Status.FAIL; obs.error_code="REGION_NOT_CONFIGURED"; return obs
        if obs.error_code and obs.error_code not in {"LOW_CONFIDENCE"}: obs.status=Status.FAIL; return obs
        method=str(rule.get("method",obs.method)); obs.method=method
        min_conf=rule.get("min_confidence")
        if obs.confidence is not None and min_conf is not None and obs.confidence < min_conf: obs.status=Status.UNCERTAIN; obs.error_code="LOW_CONFIDENCE"; return obs
        if method in {"DETECTION","DETECTION_CLASSIFICATION"}: return self._evaluate_component(obs,rule)
        if method=="SEGMENTATION": return self._evaluate_grease(obs,rule)
        if method=="ANOMALY_DETECTION": return self._evaluate_anomaly(obs,rule)
        obs.status=Status.UNCERTAIN; obs.error_code="UNSUPPORTED_METHOD"; return obs
    def _evaluate_component(self,obs,rule):
        expected=rule.get("expected_component"); expected_qty=rule.get("expected_quantity"); obs.expected_class=expected; obs.expected_quantity=expected_qty
        counts=obs.metadata.get("class_counts",{})
        if expected is not None and counts and expected not in counts and any(counts.values()): obs.status=Status.FAIL; obs.error_code="WRONG_COMPONENT"; return obs
        if expected is not None and counts:
            actual_expected=int(counts.get(expected,0))
            if actual_expected < int(expected_qty or 0): obs.status=Status.FAIL; obs.error_code="MISSING_COMPONENT"; return obs
            if actual_expected > int(expected_qty or 0): obs.status=Status.FAIL; obs.error_code="EXTRA_COMPONENT"; return obs
            extra={c:n for c,n in counts.items() if c!=expected and n>0}
            if extra: obs.status=Status.FAIL; obs.error_code="EXTRA_COMPONENT"; obs.metadata["extra_classes"]=extra; return obs
            obs.quantity=actual_expected
        elif obs.quantity is not None and expected_qty is not None:
            if obs.quantity < expected_qty: obs.status=Status.FAIL; obs.error_code="MISSING_COMPONENT"; return obs
            if obs.quantity > expected_qty: obs.status=Status.FAIL; obs.error_code="EXTRA_COMPONENT"; return obs
        if expected and obs.detected_class and obs.detected_class!=expected: obs.status=Status.FAIL; obs.error_code="WRONG_COMPONENT"; return obs
        if rule.get("position_check"):
            tolerance=rule.get("position_tolerance_px"); actual=obs.position; expected_pos=rule.get("expected_position")
            if tolerance is not None and expected_pos and actual:
                dx=float(actual.get("x",0))-float(expected_pos.get("x",0)); dy=float(actual.get("y",0))-float(expected_pos.get("y",0)); distance=(dx*dx+dy*dy)**0.5; obs.metadata["position_distance_px"]=distance
                if distance>float(tolerance): obs.status=Status.FAIL; obs.error_code="WRONG_POSITION"; return obs
        obs.status=Status.PASS; obs.error_code=None; return obs
    def _evaluate_grease(self,obs,rule):
        required=bool(rule.get("grease_required",False)); min_cov=rule.get("min_coverage_percent"); max_cov=rule.get("max_coverage_percent"); coverage=obs.coverage_percent
        if required and (coverage is None or coverage<=0): obs.status=Status.FAIL; obs.error_code="NO_GREASE"; return obs
        if coverage is not None:
            if min_cov is not None and coverage<min_cov: obs.status=Status.FAIL; obs.error_code="INSUFFICIENT_GREASE"; return obs
            if max_cov is not None and coverage>max_cov: obs.status=Status.FAIL; obs.error_code="EXCESS_GREASE"; return obs
        if rule.get("forbidden_zone_check") and obs.metadata.get("forbidden_zone_violation",False): obs.status=Status.FAIL; obs.error_code="GREASE_FORBIDDEN_ZONE"; return obs
        target_min=rule.get("target_zone_min_percent")
        if target_min is not None:
            target=obs.metadata.get("target_zone_coverage_percent")
            if target is None: obs.status=Status.UNCERTAIN; obs.error_code="GREASE_ZONE_EVIDENCE_MISSING"; return obs
            if float(target)<float(target_min): obs.status=Status.FAIL; obs.error_code="GREASE_WRONG_ZONE"; return obs
        obs.status=Status.PASS; obs.error_code=None; return obs
    def _evaluate_anomaly(self,obs,rule):
        score=obs.metadata.get("anomaly_score"); threshold=rule.get("anomaly_threshold")
        if score is None or threshold is None: obs.status=Status.UNCERTAIN; obs.error_code="ANOMALY_SCORE_MISSING"; return obs
        obs.status=Status.FAIL if float(score)>=float(threshold) else Status.PASS; obs.error_code="ANOMALY_DETECTED" if obs.status==Status.FAIL else None; return obs
    def evaluate_all(self,observations:List[Observation])->Status:
        if not observations:return Status.UNCERTAIN
        if any(o.status==Status.FAIL for o in observations):return Status.FAIL
        if any(o.status==Status.UNCERTAIN for o in observations):return Status.UNCERTAIN
        return Status.PASS
