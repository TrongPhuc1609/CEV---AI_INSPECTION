import json

import pytest

from src.integration.release_gate import ProductionReleaseGate
from src.models.calibration import CalibrationRegistry
from src.models.registry import ModelRegistry
from src.performance import PerformanceMetrics
from src.replay import ObservationReplay
from src.models.result import Observation, Status
from src.rules.parser import parse_rule_file
from src.rules.engine import RuleEngine
from src.production_pipeline import ProductionInspectionPipeline


def test_model_registry_reads_rule_metadata_and_fails_closed_for_real_release():
    plan = parse_rule_file("config/Rule.cmd").to_plan()
    registry = ModelRegistry.from_plan(plan)
    results = registry.validate(require_artifact=True)
    assert results
    assert all(not result.ok for result in results)
    gate = ProductionReleaseGate().validate(plan, real_hardware=True, require_models=True)
    assert not gate.ready
    assert any("MODEL_ARTIFACT_MISSING" in error for error in gate.errors)


def test_calibration_registry_uses_rule_cmd_thresholds():
    plan = parse_rule_file("config/Rule.cmd").to_plan()
    registry = CalibrationRegistry.from_plan(plan)
    assert registry.for_region("R01").confidence_threshold == .85
    assert registry.for_region("R03").min_coverage_percent == 60


def test_observation_replay_is_deterministic(tmp_path):
    payload = [{
        "product_id": "P", "inspection_id": "I", "region_id": "R01", "method": "DETECTION",
        "detected_class": "BOLT_M6", "confidence": .95, "quantity": 4,
        "metadata": {"class_counts": {"BOLT_M6": 4}}
    }]
    path = tmp_path / "observations.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    observations = ObservationReplay.load(path)
    outcomes = ObservationReplay(RuleEngine(parse_rule_file("config/Rule.cmd"))).evaluate(observations)
    assert outcomes[0].status == Status.PASS


def test_performance_metrics_percentiles():
    metrics = PerformanceMetrics()
    for value in [10, 20, 30, 40, 50]:
        metrics.add_latency(value)
    for value in [.5, .8, .9]:
        metrics.add_confidence(value)
    metrics.add_coverage(75)
    summary = metrics.summary()
    assert summary["latency_ms"]["p50"] == 30
    assert summary["latency_ms"]["p95"] == 50
    assert summary["confidence"]["count"] == 3
    assert summary["coverage_percent"]["mean"] == 75


def test_production_pipeline_refuses_uncommissioned_models():
    with pytest.raises(RuntimeError, match="Production release gate failed"):
        ProductionInspectionPipeline.from_rule_file(
            "config/Rule.cmd", {"M01": object(), "M02": object(), "M03": object(), "M04": object()},
            production_mode=True,
        )
