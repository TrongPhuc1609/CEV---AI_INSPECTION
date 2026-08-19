from src.cli import main
from src.integration.commissioning import PhysicalCommissioningGate
from src.rules.parser import parse_rule_file


def test_commissioning_gate_fails_closed_for_mock_hardware():
    plan = parse_rule_file("config/Rule.cmd").to_plan()
    report = PhysicalCommissioningGate().evaluate(plan, model_root=".", require_real_hardware=True)

    assert not report.ready
    assert "CAMERA_DRIVER" in report.blockers
    assert "TRIGGER_DRIVER" in report.blockers
    assert "PLC_DRIVER" in report.blockers
    assert "MODEL_ARTIFACTS" in report.blockers
    assert any(check.name == "SENSOR_TO_CAMERA_DISTANCE" and not check.blocking for check in report.checks)


def test_commissioning_gate_can_validate_software_only_profile():
    plan = parse_rule_file("config/Rule.cmd").to_plan()
    report = PhysicalCommissioningGate().evaluate(plan, model_root=".", require_real_hardware=False)

    assert report.ready
    assert not report.blockers
    assert {c.name for c in report.warnings} >= {
        "SENSOR_TO_CAMERA_DISTANCE",
        "CONVEYOR_VELOCITY",
        "ACQUISITION_LATENCY",
        "AI_LATENCY",
        "PLC_LATENCY",
        "REJECT_ACTUATOR_LATENCY",
    }


def test_commissioning_report_cli_fails_closed():
    assert main(["commissioning-report"]) == 2


def test_report_is_serializable():
    plan = parse_rule_file("config/Rule.cmd").to_plan()
    payload = PhysicalCommissioningGate().evaluate(plan, require_real_hardware=True).as_dict()

    assert payload["ready"] is False
    assert isinstance(payload["checks"], list)
    assert payload["blockers"]
