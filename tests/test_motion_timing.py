import time

import pytest

from src.machine_vision.camera.base import Frame
from src.machine_vision.correlation import TriggerFrameCorrelator
from src.machine_vision.motion import MotionProfile, MotionTimingPlanner
from src.machine_vision.trigger.base import TriggerEvent, TriggerType
from src.rules.parser import parse_rule_file


def test_motion_plan_parses_from_rule_cmd():
    plan = parse_rule_file("config/Rule.cmd").to_plan()
    assert plan.motion.nominal_velocity == 0.25
    assert plan.motion.camera_to_reject_distance == 0.80
    assert plan.correlation.max_position_delta == 0.05


def test_travel_time_for_slow_product():
    planner = MotionTimingPlanner(MotionProfile(0.25, 0.10, 0.50))
    assert planner.travel_time_ms(0.25, 0.25) == pytest.approx(1000.0)


def test_timing_budget_exposes_reject_window():
    profile = MotionProfile(
        nominal_velocity=0.25,
        min_velocity=0.10,
        max_velocity=0.50,
        trigger_to_camera_distance=0.20,
        camera_to_reject_distance=0.80,
        acquisition_budget_ms=100,
        ai_budget_ms=50,
        decision_budget_ms=10,
        plc_budget_ms=20,
    )
    budget = MotionTimingPlanner(profile).budget()
    assert budget.trigger_to_frame_ms == pytest.approx(800.0)
    assert budget.frame_to_reject_ms == pytest.approx(3200.0)
    assert budget.inspection_processing_ms == pytest.approx(180.0)
    assert MotionTimingPlanner(profile).processing_fits_before_reject()


def test_trigger_frame_correlation_matches_product_and_position():
    now = time.time()
    event = TriggerEvent("T1", TriggerType.SENSOR, now, "P1", 10.0, {})
    frame = Frame("F1", "image", now + 0.010, "CAM01", {"product_id": "P1", "position": 10.02})
    result = TriggerFrameCorrelator(100, 0.05).correlate(event, frame)
    assert result.matched
    assert result.reason == "MATCH"
    assert result.product_id == "P1"


def test_trigger_frame_correlation_rejects_wrong_product():
    now = time.time()
    event = TriggerEvent("T1", TriggerType.SENSOR, now, "P1", 10.0, {})
    frame = Frame("F1", "image", now, "CAM01", {"product_id": "P2", "position": 10.0})
    result = TriggerFrameCorrelator().correlate(event, frame)
    assert not result.matched
    assert result.reason == "PRODUCT_ID_MISMATCH"


def test_trigger_frame_correlation_rejects_stale_frame():
    now = time.time()
    event = TriggerEvent("T1", TriggerType.SENSOR, now, "P1", 10.0, {})
    frame = Frame("F1", "image", now + 0.250, "CAM01", {"product_id": "P1", "position": 10.0})
    result = TriggerFrameCorrelator(100).correlate(event, frame)
    assert not result.matched
    assert result.reason == "TIMESTAMP_OUT_OF_TOLERANCE"
