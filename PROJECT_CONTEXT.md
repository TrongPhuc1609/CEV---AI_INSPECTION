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
12. Real commissioning must use a bounded, fail-safe acceptance procedure; mock adapters are never physical evidence.
13. A physical NG reject is not considered successful until the configured PLC acknowledgement contract is satisfied.

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
v1.1 Physical Commissioning Gate: COMPLETE in software scope; merged after CI verification.
v1.2 Motion/Timing/Frame Correlation: COMPLETE and merged after CI verification.
v1.3 Velocity/Reject-window/HIL: COMPLETE and merged after CI verification.
v1.4 Real Hardware Commissioning Harness: COMPLETE in software scope; merged after CI verification.
v1.5 Device Health/Capability Contract: COMPLETE in software scope; merged after CI verification.
v1.6 Image Acquisition/Lighting Contract: COMPLETE in software scope; merged after CI verification.
v1.7 PLC/Physical Reject Handshake: ACTIVE; implementation is on feature/v1.7-plc-reject and awaits CI/PR merge.

## V1.0 software acceptance
- Single CLI supports `validate-rule`, `simulate`, `replay` and `release-gate`.
- Configuration and typed inspection-plan hashes are deterministic and attached to each inspection.
- Continuous inspection service has explicit start/stop and graceful bounded-loop behavior for tests.
- CI performs compile checks, Rule.cmd validation and pytest.
- Software release boundary is documented in SOFTWARE_RELEASE.md.
- Production mode is fail-closed until real camera/PLC adapters, model artifacts and commissioning evidence are present.

## V1.1 commissioning acceptance
- `PhysicalCommissioningGate` reports blocking configuration/artifact gates and non-blocking field measurements.
- `commissioning-report` exits 0 only when software/configuration/artifact gates are sufficient to start physical commissioning; otherwise exits 2.
- Real camera, trigger, PLC and required model artifacts are mandatory for physical readiness.
- Audit, multi-frame recheck and PLC reject must be enabled.
- Sensor-to-camera distance, conveyor velocity, acquisition/AI/PLC/reject latency remain explicit field measurements.
- HIL and line-trial evidence remain mandatory before production mode.

## V1.2 motion/timing acceptance
- `[MOTION]` and `[CORRELATION]` are parsed into typed configuration.
- `MotionTimingPlanner` calculates trigger-to-camera travel, processing budget and camera-to-reject window.
- `TriggerFrameCorrelator` rejects wrong-product, stale-frame and configured position-mismatch cases.
- `ProductionInspectionPipeline` invokes correlation before Vision/Rule processing and converts correlation failure to fail-safe NG.
- Timing and correlation are vendor-neutral and CI tested.

## V1.3 velocity/reject-window/HIL acceptance
- Velocity envelope validation is applied before inspection.
- Measured velocity can come from trigger metadata/encoder handoff; nominal velocity is only a simulation fallback.
- Camera-to-reject window is calculated from distance and velocity.
- Trigger-to-PLC cycle timing is captured.
- Reject-window exhaustion forces NG.
- HIL scenarios cover slow/fast velocity and reject-window behavior.
- CI was green before merge.

## V1.4 real hardware commissioning
Goal: make the software directly testable on a real inspection cell without changing the inspection core.

Implemented:
- `RealHardwareCommissioning` bounded acceptance runner.
- Fail-closed preflight rejects MockCamera/MockTrigger/MockPLC.
- PLC command recording is required so PASS/NG delivery is observable.
- Product ID expectation can be enforced across a finite sample set.
- Controlled guarded reject command helper exists.
- `docs/V1.4_REAL_HARDWARE_TEST.md` defines safety, acceptance, fault-injection and evidence requirements.

## V1.5 device contract acceptance
- Camera/trigger/PLC/lighting vendor adapters expose health/capability/self-test through the vendor-neutral device contract.
- Only READY devices are eligible for physical commissioning.
- DISCONNECTED/DEGRADED/FAULT states block commissioning.
- Vendor SDK details remain outside the inspection core.

## V1.6 acquisition/lighting acceptance
- `AcquiredFrame` carries frame ID, product ID, timestamp, camera ID and optional trigger/exposure/lighting metadata.
- Invalid frame identity/timestamp is rejected before Vision/Rule processing.
- Acquisition commissioning requires camera, trigger and lighting READY.
- Vendor image objects remain outside the inspection core.
- Physical evidence must include camera/trigger timestamps, exposure/strobe state and measured image-to-decision latency.

## V1.7 PLC / physical reject acceptance
Goal: make the final NG-to-physical-reject boundary deterministic and observable.

Implemented on feature branch:
- `RejectController` translates final `PLCCommand` into a vendor-neutral physical reject operation.
- PASS never emits a reject command.
- NG emits one command for the inspection.
- Missing product/inspection identity blocks the command.
- PLC send exceptions become `FAILED`.
- When an acknowledgement callback is configured, NG is accepted only after acknowledgement within `ack_timeout_ms`.
- ACK timeout is not considered successful physical reject execution.
- `docs/V1.7_PLC_REJECT.md` defines physical evidence requirements.

Required before physical trial:
1. Implement/select vendor camera adapter.
2. Implement/select trigger/encoder adapter producing `TriggerEvent` with product_id/timestamp/position/velocity metadata.
3. Implement lighting adapter and validate strobe/exposure/gain timing.
4. Implement vendor PLC adapter using the command/acknowledgement contract during commissioning.
5. Supply real AI model artifacts and SHA-256/model metadata.
6. Populate production Rule.cmd with real camera/trigger/lighting/PLC drivers and calibrated values.
7. Record physical camera-to-reject distance and conveyor min/nominal/max velocity.
8. Measure acquisition, AI, PLC and reject actuator latency.
9. Run bounded known-good samples, then guarded NG/reject tests, then fault injection.
10. Only after evidence passes may production_mode be enabled.

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
Reject-window exceeded -> NG.
PLC reject send/ack failure -> commissioning/physical reject failure; never report successful physical reject.

## PLC/reject
Keep inspection result, PLC command and physical reject result distinct. Reject timing must be validated against sensor-to-camera distance, conveyor speed, processing latency, PLC latency and actuator latency. A PLC `NG sent` event is not equivalent to a physically confirmed reject unless the configured acknowledgement/actuator evidence is present.

## Session protocol
START: read this file, inspect source tree, confirm baseline/completed/next task.
END: update CURRENT BASELINE, COMPLETED, CURRENT NEXT TASK, KNOWN ISSUES, TEST STATUS, LAST CHANGE.

## Git workflow
Feature branch -> inspect -> implement -> test -> update context -> commit -> PR -> review -> merge. Do not edit main directly for feature work. Merge only after CI verification.

## Git baseline
Repository: TrongPhuc1609/Loc
Baseline branch: main
Latest main V1.6 merge commit: d3272100fce8546dfcf4a1b434c627317a44ca41
V1.3 merge baseline: 3241fa84d26da03562907ce7a54c0d1c36ee1ae1
V1.2 merge baseline: 41b0b81441ae23db031bdcf01fb00568a52af397
V1.0 software baseline: f6c6b03dc1f8d9f4a1246507bd5ddc07c2db4a28

## Current handoff status
V1.6 is merged and CI-verified. V1.7 is the active PLC/reject branch. Physical hardware, vendor SDK behavior, real AI models, threshold calibration and reject timing are not yet validated.

## Known issues / production gates
- Mock drivers are not production drivers.
- Model files are placeholders and must be supplied separately.
- Rule thresholds are examples until calibrated on the production line.
- PLC reject timing and fail-safe electrical behavior require hardware validation.
- Evidence currently persists normalized audit JSON; raw image persistence is adapter/application dependent.
- Physical timing measurements are commissioning inputs and cannot be inferred from mock execution.
- No claim of production readiness is allowed until physical commissioning gates pass.

## Architecture change record
DATE: 2026-08-19
DECISION: Add motion-aware timing, trigger/frame correlation, velocity safety, bounded real-hardware commissioning, device capability contracts, acquisition/lighting contracts and PLC reject acknowledgement.
REASON: Slowly moving products require deterministic proof that the evaluated frame belongs to the correct product, processing completes before the reject window closes, and physical acceptance can be performed safely and observably through the full Camera -> AI -> Rule -> PLC/Reject chain.
ALTERNATIVES: Trust trigger order alone; rejected because buffering, latency, trigger jitter and multiple products can create stale/wrong-frame decisions. Use mock-only acceptance; rejected because it cannot prove physical timing or reject behavior.
IMPACT: Rule.cmd/InspectionPlan carry motion/correlation parameters; pipeline rejects uncorrelated/unsafe frames; commissioning gates verify device readiness; acquisition frames are vendor-neutral; physical NG has an explicit PLC acknowledgement contract.
MIGRATION: Implement vendor adapters, supply real model artifacts, calibrate thresholds, collect line timing, run guarded physical trials and only then enable production mode.
