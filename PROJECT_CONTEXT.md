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
10. A frame must be correlated to its triggering product before it is accepted for production inspection.
11. Motion/timing values are configuration and commissioning measurements, never assumptions hidden in code.

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
v1.0 Software Release: VERIFIED in software/simulation scope; GitHub Actions CI is green on the main baseline.
v1.1 Physical Commissioning Gate: COMPLETE in software/mock scope; merged after CI verification.
v1.2 Motion/Timing/Frame Correlation: IN PROGRESS.

## V1.0 software acceptance
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
- HIL and line-trial evidence remain mandatory before production mode.

## V1.2 motion/timing acceptance
- `[MOTION]` is parsed into typed `MotionConfig`.
- `[CORRELATION]` is parsed into typed `CorrelationConfig`.
- `MotionTimingPlanner` calculates trigger-to-camera travel, processing budget and camera-to-reject window.
- `TriggerFrameCorrelator` rejects wrong-product, stale-frame and configured position-mismatch cases.
- Timing and correlation are vendor-neutral and independently unit tested.
- The correlation result must be integrated into the production acquisition/orchestrator error path before physical production use.

## Current next task
V1.2 CONTINUE:
1. Integrate `TriggerFrameCorrelator` into `ImageAcquisition`/`ProductionInspectionPipeline` so an uncorrelated frame cannot enter Vision/Rule processing.
2. Add motion-aware ProductTracker constraints and velocity range monitoring.
3. Add acquisition timing records to the normalized inspection/audit result.
4. Add HIL scenarios for trigger jitter, stale frame, wrong product frame, slow/fast velocity and reject-window exhaustion.
5. Keep real camera/trigger/encoder/lighting/PLC vendor adapters behind interfaces.

After V1.2 software acceptance:
6. Select and implement vendor camera adapter(s).
7. Select trigger/encoder interface and implement real product-ID handoff.
8. Select lighting controller and validate exposure/gain/strobe timing.
9. Implement vendor PLC adapter and reject output handshake.
10. Supply real AI model artifacts and record model version/SHA-256/class map in Rule.cmd.
11. Calibrate confidence, quantity, position, grease coverage/zone and anomaly thresholds on representative good/NG samples.
12. Record actual line timing and run deterministic HIL followed by line trials.
13. Only after all gates pass, remove MOCK drivers and enable `production_mode`.

## Inspection logic
Missing/extra: YOLO or RT-DETR detection + expected class/quantity/tolerance.
Wrong type: detection + classification or constrained classification.
Position: configured expected position + tolerance when required.
Oil/grease: segmentation for coverage + target/forbidden zone checks; anomaly detection may cross-check.
Thresholds require real-line calibration; Rule.cmd example values are not production validated.

## Product decision default
All required regions PASS -> PASS.
Any final region FAIL -> NG.
Missing region/timeout/camera error/trigger error/AI error/correlation error -> NG.
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
Current development branch: feature/v1.2-motion-timing-correlation
Latest main v1.1 merge commit: 564798afdbb138f045b012e8b4a51aff44bb7b68
Latest main v1.0 software baseline commit: f6c6b03dc1f8d9f4a1246507bd5ddc07c2db4a28
Latest v0.98 baseline commit: 6a1f7e4b03af2390df68d0c79dc3bb9c3ec5129a
Latest v0.95 baseline commit: 7c602410761b462468beb20b31a1be327e4edcf1

## Current handoff status
V1.1 physical commissioning gate is merged and CI-verified in software scope. V1.2 adds motion-aware timing and trigger/frame correlation. Physical hardware, vendor SDK behavior, real AI models, threshold calibration and reject timing are not validated.

## Known issues / production gates
- Mock drivers are not production drivers.
- Model files are placeholders and must be supplied separately.
- Rule thresholds are examples until calibrated on the production line.
- PLC reject timing and fail-safe electrical behavior require hardware validation.
- Evidence currently persists normalized audit JSON; raw image persistence is adapter/application dependent.
- Correlation is currently a standalone validated primitive and must be wired into the live production pipeline before production use.
- Field timing measurements are commissioning inputs and cannot be inferred from mock execution.
- No claim of production readiness is allowed until physical commissioning gates pass.

## Architecture change record
DATE: 2026-08-19
DECISION: Add V1.2 motion-aware timing and trigger/frame product correlation.
REASON: A slowly moving product requires deterministic proof that the evaluated frame belongs to the correct product and that processing completes before the reject window closes.
ALTERNATIVES: Trust trigger order alone; rejected because buffering, latency, trigger jitter and multiple products can create stale/wrong-frame decisions.
IMPACT: Rule.cmd and InspectionPlan now carry motion/correlation parameters; timing/correlation are independently testable and vendor-neutral.
MIGRATION: Integrate the correlator into acquisition/orchestrator, then collect real line timing measurements and validate HIL/line trials.
