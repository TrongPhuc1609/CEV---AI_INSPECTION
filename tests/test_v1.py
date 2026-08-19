from src.cli import main
from src.config_hash import inspection_plan_hash, rule_config_hash
from src.rules.parser import parse_rule_file


def test_config_and_plan_hashes_are_deterministic(capsys):
    config = parse_rule_file("config/Rule.cmd")
    plan = config.to_plan()
    assert rule_config_hash(config) == rule_config_hash(config)
    assert inspection_plan_hash(plan) == inspection_plan_hash(plan)
    assert len(rule_config_hash(config)) == 64
    assert len(inspection_plan_hash(plan)) == 64


def test_cli_validate_rule(capsys):
    assert main(["--rule", "config/Rule.cmd", "validate-rule"]) == 0
    output = capsys.readouterr().out
    assert '"valid": true' in output
    assert '"version": "1.0.0"' in output
