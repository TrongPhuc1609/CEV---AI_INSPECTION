from src.models.result import Observation, Status
from src.rules.engine import RuleEngine
from src.rules.parser import RuleConfig


def test_machine_vision_measurement_passes_when_measurement_is_valid():
    config = RuleConfig(
        {
            "REGION:R01": {
                "enabled": True,
                "method": "MACHINE_VISION_MEASUREMENT",
                "min_edge_density": 0.01,
                "max_edge_density": 0.50,
                "min_foreground_ratio": 0.05,
                "max_foreground_ratio": 0.95,
            }
        }
    )
    obs = Observation(
        "P1",
        "I1",
        "R01",
        "MACHINE_VISION_MEASUREMENT",
        metadata={
            "measurement": {
                "mean_gray": 100.0,
                "std_gray": 30.0,
                "min_gray": 0,
                "max_gray": 255,
                "edge_density": 0.10,
                "foreground_ratio": 0.40,
                "contour_count": 20,
            }
        },
    )
    result = RuleEngine(config).evaluate(obs)
    assert result.status == Status.PASS
    assert result.error_code is None


def test_machine_vision_measurement_fails_when_edge_density_is_outside_rule():
    config = RuleConfig(
        {
            "REGION:R01": {
                "enabled": True,
                "method": "MACHINE_VISION_MEASUREMENT",
                "max_edge_density": 0.05,
            }
        }
    )
    obs = Observation(
        "P1",
        "I1",
        "R01",
        "MACHINE_VISION_MEASUREMENT",
        metadata={
            "measurement": {
                "mean_gray": 100.0,
                "std_gray": 30.0,
                "min_gray": 0,
                "max_gray": 255,
                "edge_density": 0.10,
                "foreground_ratio": 0.40,
                "contour_count": 20,
            }
        },
    )
    result = RuleEngine(config).evaluate(obs)
    assert result.status == Status.FAIL
    assert result.error_code == "MEASUREMENT_ABOVE_EDGE_DENSITY"
