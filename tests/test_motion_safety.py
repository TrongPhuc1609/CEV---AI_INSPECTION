from src.integration.motion import MotionSafetyMonitor


def test_velocity_within_configured_range():
    monitor = MotionSafetyMonitor(0.25, 0.10, 0.50, 0.80)
    result = monitor.assess(0.25)
    assert result.velocity_ok
    assert result.errors == ()
    assert result.reject_window_ms == 3200.0


def test_velocity_out_of_range_blocks_inspection():
    monitor = MotionSafetyMonitor(0.25, 0.10, 0.50, 0.80)
    result = monitor.assess(0.75)
    assert not result.velocity_ok
    assert "VELOCITY_OUT_OF_RANGE" in result.errors


def test_reject_window_is_based_on_actual_velocity():
    monitor = MotionSafetyMonitor(0.25, 0.10, 0.50, 0.20)
    result = monitor.assess(0.50)
    assert result.reject_window_ms == 400.0
    assert monitor.within_reject_window(399.9, result.reject_window_ms)
    assert not monitor.within_reject_window(400.1, result.reject_window_ms)


def test_nominal_velocity_fallback_is_available():
    monitor = MotionSafetyMonitor(0.25, 0.10, 0.50, 0.80)
    assert monitor.effective_velocity(None) == 0.25
