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
v0.98 Model/config commissioning framework: COMPLETE in software/mock scope; real model artifacts and physical line remain unvalidated.

## v0.98 verified software acceptance
- ModelRegistry compiles model lifecycle metadata from Rule.cmd.
- Model validation checks path, checksum, version, class map and threshold when production artifacts are required.
- CalibrationRegistry exposes deterministic region thresholds derived from the typed plan without duplicating product rules.
- ObservationReplay supports deterministic offline rule evaluation from saved observations.
- PerformanceMetrics aggregates latency, confidence and grease coverage percentiles.
- ProductionReleaseGate fails closed for incomplete real-hardware/model commissioning.
- ProductionInspectionPipeline refuses production_mode when the release gate is not satisfied.
- Rule.cmd explicitly records uncommissioned model metadata placeholders and never stores credentials.
- Automated tests cover the new v0.98 software gates.

## Current next task
V1.0 Software Release Hardening:
1. Add a single CLI entry point for validate-rule, simulate, replay, and release-gate commands.
2. Add structured JSON result schema/versioning and compatibility checks.
3. Add end-to-end scenario fixtures for PASS/NG/recheck/hardware-fault paths.
4. Add CI quality gates for tests, compile checks and Rule.cmd validation.
5. Add deterministic configuration hash and inspection-plan hash to every audit/result.
6. Add operational service loop and graceful shutdown for continuous product inspection.
7. Produce a documented software release package; keep hardware commissioning explicitly separate.

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
Current development branch: main
Latest v0.98 software baseline commit: 6a1f7e4b03af2390df68d0c79dc3bb9c3ec5129a
Latest v0.95 baseline commit: 7c602410761b462468beb20b31a1be327e4edcf1
Latest verified v0.9 merge commit: b422b9336b863811c1487eeeef5137337845db45

## Current handoff status
V0.98 model/config commissioning framework is implemented on main. This is software/simulation validation only; real model artifacts, vendor SDKs, hardware timing and physical reject behavior are not validated.

## Known issues / production gates
- Mock drivers are not production drivers.
- Model files are placeholders and must be supplied separately.
- Rule thresholds are examples until calibrated on the production line.
- PLC reject timing and fail-safe electrical behavior require hardware validation.
- Evidence currently persists normalized audit JSON; raw image persistence is adapter/application dependent.
- CI execution must be confirmed on GitHub Actions before declaring the new v0.98 test suite green.
- No claim of production readiness is allowed until V1.0 software release gates and subsequent hardware commissioning pass.

## Architecture change record
DATE: 2026-08-19
DECISION: Add model lifecycle validation, deterministic calibration/replay/performance tooling and a fail-closed production release gate.
REASON: Prevent uncommissioned AI models or incomplete hardware configuration from entering production mode.
ALTERNATIVES: Trust model paths/thresholds at runtime; rejected because configuration drift and unverified model artifacts are production risks.
IMPACT: Adds ModelRegistry, CalibrationRegistry, ObservationReplay, PerformanceMetrics and ProductionReleaseGate.
MIGRATION: Continue using Rule.cmd as the single product configuration source; add model_version/checksum_sha256/class_map when commissioning real models.
