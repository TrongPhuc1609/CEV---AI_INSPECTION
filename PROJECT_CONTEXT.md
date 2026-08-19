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
v0.9 Runtime stabilization: COMPLETE in software/mock scope; physical hardware and real AI models remain unvalidated.

## v0.9 verified acceptance
- Rule.cmd v1.0 exists and is human-readable.
- Parser compiles typed Camera/Trigger/Encoder/Lighting/Model/ROI/Recheck/Region/ProductDecision/PLC/Evidence/Audit config.
- InspectionPlan validates cross-references and configured component positions.
- Production pipeline can be constructed from Rule.cmd.
- Detection preserves class counts so extra/wrong components cannot be hidden by a dominant class.
- Recheck requests a new acquisition/observation for each attempt.
- Missing required regions and final UNCERTAIN are fail-safe NG.
- Camera/trigger startup errors fail safe to PLC NG when no product identity is available.
- Grease coverage and forbidden/target-zone checks are deterministic when model evidence is supplied.
- Anomaly method is supported by Rule Engine.
- Final product decision is sent to PLC and audit JSON is written when enabled.
- Automated tests pass: 15 passed in the development environment.

## Current next task
V0.95 Hardware Integration:
1. Replace MockCamera/MockTrigger/MockPLC with validated vendor adapters.
2. Implement real product-ID handoff and encoder tracking.
3. Validate lighting profiles and camera exposure/gain on the line.
4. Measure sensor-to-camera distance, conveyor speed, processing latency, PLC latency and reject-actuator latency.
5. Commission real AI models and calibrate confidence/coverage/anomaly thresholds.
6. Add hardware-in-the-loop tests before production release.

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
Feature branch -> inspect -> implement -> test -> update context -> commit -> PR -> review -> merge. Do not edit main directly for feature work.

## Git baseline
Repository: TrongPhuc1609/Loc
Baseline branch: main
Current development branch: feature/v0.9-completion

## Current handoff status
v0.9 software stabilization is implemented on feature/v0.9-completion. Local verification in the development environment: 15 tests passed. The implementation is mock/simulation validated; physical hardware, vendor SDKs, real AI models, threshold calibration and reject timing are not yet validated.

## Known issues / production gates
- Mock drivers are not production drivers.
- Model files are placeholders and must be supplied separately.
- Rule thresholds are examples until calibrated on the production line.
- PLC reject timing and fail-safe electrical behavior require hardware validation.
- Evidence currently persists normalized audit JSON; raw image persistence is adapter/application dependent.
- No claim of production readiness is allowed until V0.95/V0.98 gates pass.

## Architecture change record
DATE: 2026-08-19
DECISION: Make Rule.cmd compile into a typed InspectionPlan and drive the reference runtime; make recheck acquire a new frame; make errors/missing regions fail-safe; make component position checks fully configurable.
REASON: Close the v0.9 gaps between configuration, runtime, deterministic decision logic and auditability.
ALTERNATIVES: Keep hard-coded runtime wiring; rejected because product-specific changes would require code changes and could drift from Rule.cmd.
IMPACT: Adds typed plan models, config-driven factory, durable audit JSON, expanded rule handling and runtime tests.
MIGRATION: Existing RuleConfig API remains compatible; use RuleConfig.to_plan()/build_inspection_plan() for new integrations.
