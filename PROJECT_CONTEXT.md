# PROJECT_CONTEXT.md

## MANDATORY
Every new AI/coding session MUST read this file before coding. It is the single source of project memory. Git is the source of code/history/branches/PRs.

## Mission
Production-oriented inspection for slowly moving products: missing components, extra components, wrong component/type, and oil/grease missing, insufficient, or in the wrong zone.

## Core architecture
AI Computer Vision + Machine Vision + Rule Engine + Inspection Orchestrator.

Pipeline: Camera -> Trigger -> Lighting -> Image Acquisition -> Product Tracking -> ROI -> Vision Adapter -> Observation -> Rule Engine -> Region Result -> Inspection Orchestrator -> Product PASS/NG -> PLC/Reject.

## Non-negotiable decisions
1. AI never directly decides product PASS/NG; AI produces Observation.
2. Rule Engine owns deterministic inspection decisions.
3. Orchestrator owns Product ID, Inspection ID, regions, multi-frame/recheck, timeout and product aggregation.
4. Rule.cmd is the human-readable source for product-specific configuration; do not hard-code product rules.
5. Camera/AI/PLC vendors remain behind replaceable adapters.
6. Hardware/AI errors and missing required regions must never silently become PASS.
7. UNCERTAIN follows explicit recheck/final policy.
8. Production decisions must be auditable.
9. Real hardware/model thresholds remain commissioning parameters; mock validation is not physical validation.

## Baseline status
v0.1 Foundation: COMPLETE.
v0.2 Rule Parser + Rule Engine + Normalized Result: COMPLETE.
v0.3 Inspection Orchestrator: COMPLETE.
v0.4 AI Vision Adapter Layer: COMPLETE / architecture baseline.
v0.5 Machine Vision Layer: COMPLETE / architecture baseline; real hardware is not physically validated.
v0.6 Rule.cmd v1.0 + typed InspectionPlan: COMPLETE in software/mock scope.
v0.9 Runtime stabilization: COMPLETE in software/mock scope.
v0.95 Commissioning framework: COMPLETE in software/mock scope.
v0.98 Model/config commissioning framework: COMPLETE in software/mock scope.
v1.0 Software Release: VERIFIED in software/simulation scope; GitHub Actions CI is green on the current main baseline.
v1.1 Physical Commissioning Gate: IN PROGRESS on feature/v1.1-commissioning-framework.

## v1.0 software acceptance
- Single CLI supports `validate-rule`, `simulate`, `replay` and `release-gate`.
- Configuration and typed inspection-plan hashes are deterministic and attached to each inspection.
- Continuous inspection service has explicit start/stop and graceful bounded-loop behavior for tests.
- CI performs compile checks, Rule.cmd validation and pytest.
- Software release boundary is documented in SOFTWARE_RELEASE.md.
- Production mode is fail-closed until real camera/PLC adapters, model artifacts and commissioning evidence are present.

## V1.1 commissioning acceptance
- `PhysicalCommissioningGate` explicitly reports blocking configuration/artifact gates and non-blocking field measurements.
- `commissioning-report` CLI exits 0 only when software/configuration/artifact gates are sufficient to start physical commissioning; otherwise exits 2.
- Real camera, trigger, PLC and required model artifacts are mandatory for physical readiness.
- Audit, multi-frame recheck and PLC reject must be enabled.
- Sensor-to-camera distance, conveyor velocity, acquisition/AI/PLC/reject latency remain explicit field measurements and cannot be inferred from software.
- V1.1 is not complete until HIL and line-trial evidence is recorded.

## Current next task
V1.1 PHYSICAL COMMISSIONING:
1. Select and implement vendor camera adapter(s) behind `Camera`/`CallbackCamera`.
2. Select trigger/encoder interface and implement real product-ID handoff.
3. Select lighting controller and validate exposure/gain/strobe timing.
4. Implement vendor PLC adapter and reject output handshake.
5. Supply real AI model artifacts and record model version/SHA-256/class map in Rule.cmd.
6. Calibrate confidence, quantity, position, grease coverage/zone and anomaly thresholds on representative good/NG samples.
7. Record sensor-to-camera distance, conveyor velocity, acquisition/AI/decision/PLC/actuator latency.
8. Run deterministic HIL scenarios, then line trials; document false-pass/false-reject and recheck behavior.
9. Only after all gates pass, remove MOCK drivers and enable `production_mode`.

## Inspection logic
Missing/extra: YOLO or RT-DETR detection + expected class/quantity/tolerance.
Wrong type: detection + classification or constrained classification.
Position: configured expected position + tolerance when required.
Oil/grease: segmentation for coverage + target/forbidden zone checks; anomaly detection may cross-check.
Thresholds require real-line calibration; Rule.cmd example values are not production validated.

## Product decision default
All required regions PASS -> PASS.
Any final region FAIL -> NG.
Missing region/timeout/camera error/trigger error/AI error -> NG.
UNCERTAIN -> recheck -> NG unless explicitly configured otherwise.

## PLC/reject
Keep inspection result, PLC command and physical reject result distinct. Reject timing must be validated against sensor-to-camera distance, conveyor speed, processing latency, PLC latency and actuator latency.

## Session protocol
START: read this file, inspect source tree, confirm baseline/completed/next task.
END: update CURRENT BASELINE, COMPLETED, CURRENT NEXT TASK, KNOWN ISSUES, TEST STATUS, LAST CHANGE.

## Git workflow
Feature branch -> inspect -> implement -> test -> update context -> commit -> PR -> review -> merge. Do not edit main directly for feature work. If the GitHub integration cannot create a PR, a fast-forward of a reviewed feature branch is allowed only after code/CI verification is documented.

## Git baseline
Repository: TrongPhuc1609/Loc
Baseline branch: main
Current development branch: feature/v1.1-commissioning-framework
Latest main v1.0 software baseline commit: f6c6b03dc1f8d9f4a1246507bd5ddc07c2db4a28
Latest v0.98 baseline commit: 6a1f7e4b03af2390df68d0c79dc3bb9c3ec5129a
Latest v0.95 baseline commit: 7c602410761b462468beb20b31a1be327e4edcf1
Latest verified v0.9 merge commit: b422b9336b863811c1487eeeef5137337845db45

## Current handoff status
V1.0 software release is verified in software/simulation scope. V1.1 adds an explicit physical commissioning gate and CLI report. The architecture, configuration, simulation, replay, release gating, operational service loop and commissioning checklist are software-defined. Physical hardware, vendor SDK behavior, real AI models, threshold calibration and reject timing are not validated.

## Known issues / production gates
- Mock drivers are not production drivers.
- Model files are placeholders and must be supplied separately.
- Rule thresholds are examples until calibrated on the production line.
- PLC reject timing and fail-safe electrical behavior require hardware validation.
- Evidence currently persists normalized audit JSON; raw image persistence is adapter/application dependent.
- No claim of production readiness is allowed until physical commissioning gates pass.
- Field timing measurements are intentionally warnings in the commissioning report until recorded.

## Architecture change record
DATE: 2026-08-19
DECISION: Add an explicit PhysicalCommissioningGate and commissioning-report CLI while preserving the fail-closed production boundary.
REASON: Make the transition from verified software to real hardware auditable and prevent mock/simulation success from being mistaken for physical readiness.
ALTERNATIVES: Treat V1.0 software CI as production acceptance; rejected because camera, lighting, conveyor, PLC, AI calibration and reject timing require physical evidence.
IMPACT: V1.1 now has a machine-readable readiness report and explicit field-measurement checklist.
MIGRATION: Implement vendor adapters through HardwareFactory, install real model artifacts, record calibration/timing evidence, pass HIL and line trial, then enable production_mode.
