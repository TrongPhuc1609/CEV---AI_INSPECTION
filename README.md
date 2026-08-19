# Loc

Production-oriented AI inspection software for slowly moving products:
- missing components
- extra components
- wrong component/type
- oil/grease missing, insufficient, or in the wrong zone

## Architecture
AI Computer Vision + Machine Vision + Rule Engine + Inspection Orchestrator.

```text
Camera -> Trigger -> Lighting -> Image Acquisition -> Product Tracking
       -> ROI -> Vision Adapter -> Observation -> Rule Engine
       -> Region Result -> Inspection Orchestrator -> Product PASS/NG -> PLC/Reject
```

## Current baseline
**v1.0 software release / simulation baseline.**

The software is configuration-driven from `config/Rule.cmd`, compiles into a typed `InspectionPlan`, supports deterministic region decisions, real multi-frame recheck in the reference pipeline, fail-safe NG aggregation, PLC command output, audit JSON, model lifecycle validation, deterministic replay, timing metrics, a release gate and a continuous service loop.

Read `PROJECT_CONTEXT.md` before making any code or architecture changes.

## Rule.cmd
`config/Rule.cmd` is the human-readable source for product-specific inspection configuration. It covers Camera, Trigger, Encoder, Lighting, AI model/adapter, ROI, Region rules, Recheck, Product decision, PLC/reject, Evidence and Audit. Model lifecycle fields include version, SHA-256 and class map. Do not hard-code product-specific rules in Python.

## CLI
```bash
python -m src.cli validate-rule
python -m src.cli simulate
python -m src.cli replay path/to/observations.json
python -m src.cli release-gate
```

`release-gate` is intentionally expected to fail for the repository's example configuration until real camera/PLC adapters and commissioned model artifacts are supplied.

## Verification
CI performs Python compile checks, Rule.cmd validation and the pytest suite. The software architecture is simulation/mock validated; physical camera SDKs, PLCs, production AI models, threshold calibration and reject timing remain commissioning work.

## Next milestone: physical commissioning
1. Vendor camera/trigger/PLC adapters behind the existing interfaces.
2. Real product-ID handoff and encoder tracking.
3. Lighting/exposure/gain commissioning.
4. Sensor-to-camera and reject timing validation.
5. Real AI model integration and threshold calibration.
6. Hardware-in-the-loop and controlled line trials before production release.

## Project ownership
This project is currently maintained as a single implementation stream. External AI assistants are not part of the active development workflow unless explicitly re-enabled by the project owner.
