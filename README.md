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
**v0.9 software-verified / mock-validated.**

The v0.9 runtime is configuration-driven from `config/Rule.cmd`, compiles into a typed `InspectionPlan`, supports deterministic region decisions, real multi-frame recheck in the reference pipeline, fail-safe NG aggregation, PLC command output and audit JSON.

Read `PROJECT_CONTEXT.md` before making any code or architecture changes.

## Rule.cmd
`config/Rule.cmd` is the human-readable source for product-specific inspection configuration. It covers Camera, Trigger, Encoder, Lighting, AI model/adapter, ROI, Region rules, Recheck, Product decision, PLC/reject, Evidence and Audit. Do not hard-code product-specific rules in Python.

## Verification
The repository test suite covers the machine-vision pipeline, configuration compilation, missing/extra/wrong components, grease rules, anomaly decisions, recheck, missing-region fail-safe behavior, config-driven construction and audit output.

The current software baseline is mock/simulation validated. Real camera SDKs, PLCs, production AI models, threshold calibration and reject timing remain commissioning work.

## Next milestone: v0.95 Hardware Integration
1. Vendor camera/trigger/PLC adapters.
2. Real product-ID handoff and encoder tracking.
3. Lighting/exposure/gain commissioning.
4. Sensor-to-camera and reject timing validation.
5. Real AI model integration and threshold calibration.
6. Hardware-in-the-loop verification before production release.

## Project ownership
This project is currently maintained as a single implementation stream. External AI assistants are not part of the active development workflow unless explicitly re-enabled by the project owner.
