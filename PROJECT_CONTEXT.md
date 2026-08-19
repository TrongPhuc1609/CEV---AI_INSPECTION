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
v0.95 Commissioning framework: COMPLETE in software/mock scope; vendor SDKs and physical line remain unvalidated.

## v0.95 verified software acceptance
- Vendor-neutral CallbackCamera, CallbackTrigger and CallbackPLC adapters exist.
- HardwareFactory is an explicit injection boundary; MockHardwareFactory remains the reference simulator.
- ImageAcquisition has explicit start/stop lifecycle and refuses capture before start.
- Production pipeline can be constructed from Rule.cmd and auto-starts acquisition when run_product() is called.
- Camera settings from Rule.cmd are applied through the hardware abstraction.
- TimingCollector records acquisition, AI, decision and PLC latency and evaluates configurable budgets.
- ProductTracker calculates velocity for slowly moving products when position/timestamp data are available.
- HILRunner executes deterministic commissioning scenarios against injected hardware/model doubles.
- Existing Rule.cmd remains the source of product configuration; no credentials are stored in it.
- Automated v0.95 tests cover lifecycle, adapter contracts, timing budget, slow-line tracking and HIL nominal PASS.

## Current next task
V0.98 AI/model commissioning software:
1. Add model registry metadata and model lifecycle validation (path, checksum, version, class map).
2. Add threshold/calibration profiles without hard-coding product rules.
3. Add deterministic replay from saved frames/observations for offline calibration.
4. Add performance aggregation (latency percentiles, confidence/coverage distributions).
5. Add a production release gate that refuses real mode when model/config validation is incomplete.
6. Expand HIL scenarios for PASS, missing, extra, wrong type, grease failures, recheck and hardware faults.

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
Latest v0.95 baseline commit: 7c602410761b462468beb20b31a1be327e4edcf1
Latest verified v0.9 merge commit: b422b9336b863811c1487eeeef5137337845db45

## Current handoff status
V0.95 commissioning framework is merged into main. Code review completed against the feature branch diff. Physical hardware, vendor SDKs, real AI models, threshold calibration and reject timing are not yet validated.

## Known issues / production gates
- Mock drivers are not production drivers.
- Model files are placeholders and must be supplied separately.
- Rule thresholds are examples until calibrated on the production line.
- PLC reject timing and fail-safe electrical behavior require hardware validation.
- Evidence currently persists normalized audit JSON; raw image persistence is adapter/application dependent.
- CI execution must be confirmed on GitHub Actions before declaring the v0.95 test suite green.
- No claim of production readiness is allowed until V0.98 model/config gates and hardware commissioning pass.

## Architecture change record
DATE: 2026-08-19
DECISION: Add vendor-neutral hardware injection, acquisition lifecycle enforcement, timing instrumentation and deterministic HIL scenarios.
REASON: Establish a software commissioning boundary before physical camera/PLC/lighting integration.
ALTERNATIVES: Bind the core directly to a vendor SDK; rejected because vendor changes would contaminate the inspection core.
IMPACT: Hardware SDKs can be wrapped by Callback* adapters or a HardwareFactory without changing Rule Engine/Orchestrator logic.
MIGRATION: Use ProductionInspectionPipeline.from_rule_file(..., hardware_factory=...) for real adapters; keep MockHardwareFactory for CI.
