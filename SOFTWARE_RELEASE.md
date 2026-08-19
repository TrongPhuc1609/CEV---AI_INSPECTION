# Software Release Boundary

## Scope
The repository contains a production-oriented inspection software core plus simulation/commissioning adapters. It is not a declaration that a physical inspection machine is production commissioned.

## Validate configuration
```bash
python -m src.cli validate-rule
```

## Simulate the reference pipeline
```bash
python -m src.cli simulate
```

## Offline replay
```bash
python -m src.cli replay path/to/observations.json
```

## Production release gate
```bash
python -m src.cli release-gate
```
The example Rule.cmd intentionally fails this gate because model artifacts are uncommissioned placeholders and the configured camera/PLC are MOCK.

## Real-mode requirements
Before `production_mode=True` may be used:
1. Camera and PLC drivers must be non-MOCK vendor adapters behind `HardwareFactory`.
2. Every model must have a real artifact, model version, SHA-256 checksum and class map.
3. Rule thresholds must be calibrated on the production line.
4. Lighting/exposure/gain must be validated.
5. Product ID and encoder tracking must be validated at line speed.
6. Acquisition, AI, decision, PLC and reject timing must meet the commissioned budget.
7. Fail-safe electrical reject behavior must be validated.
8. Hardware-in-the-loop scenarios must pass.

## Audit identity
Every inspection carries `rule_config_hash`, `inspection_plan_hash` and `plan_version` so an audit record can be tied to the exact configuration used for the decision.
