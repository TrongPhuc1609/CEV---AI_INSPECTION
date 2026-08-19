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
v1.1 Physical Commissioning Gate: COMPLETE in software scope.
v1.2 Motion/Timing/Frame Correlation: COMPLETE and merged after CI verification.
v1.3 Velocity/Reject-window/HIL: COMPLETE and merged after CI verification.
v1.4 Real Hardware Commissioning Harness: COMPLETE in software scope.
v1.5 Device Health/Capability Contract: COMPLETE in software scope.
v1.6 Image Acquisition/Lighting Contract: COMPLETE in software scope.
v1.7 PLC/Physical Reject Handshake: COMPLETE in software scope; real PLC is not installed for the current trial.
v1.8 Fail-Closed AI Runtime Boundary: COMPLETE in software scope; model artifact/version/checksum and latency gates are enforced.
v1.9 Physical Vision Trial preparation: ACTIVE.

## Current physical test setup
- Camera: Sanwa Supply CMS-V30SETBK USB webcam.
- PLC: not installed; PLC remains simulated.
- Product: real PCB.
- Current objective: capture and characterize real PCB images before product-specific AI model commissioning.
- Capture tool: `CAPTURE_CAMERA.bat` -> `tools/capture_camera.py`.
- Captured evidence directory: `data/physical_trial/`.
- A real camera frame is acquisition evidence only; it is not production inspection evidence.

## Current V1.9 acceptance path
1. Capture real GOOD PCB frames with the real USB camera.
2. Characterize resolution, exposure/brightness, blur/focus and saturation.
3. Define product-specific Regions/ROIs and inspection targets from real images.
4. Decide per-region technology: deterministic Machine Vision, object detection, classification, or segmentation/anomaly.
5. Collect GOOD/NG datasets and calibrate thresholds.
6. Run offline/replay validation.
7. Only then commission real motion timing, real PLC and physical reject.

## V1.9 implementation rule
Do not invent product-specific ROI coordinates, component classes, AI thresholds, motion values or lighting values without physical evidence. Configuration placeholders are allowed, but must be marked as commissioning parameters.

## V1.0 software acceptance
- Single CLI supports `validate-rule`, `simulate`, `replay` and `release-gate`.
- Configuration and typed inspection-plan hashes are deterministic and attached to each inspection.
- Continuous inspection service has explicit start/stop and graceful bounded-loop behavior for tests.
- CI performs compile checks, Rule.cmd validation and pytest.
- Software release boundary is documented in SOFTWARE_RELEASE.md.
- Production mode is fail-closed until real camera/PLC adapters, model artifacts and commissioning evidence are present.

## Handoff rule
Before changing code, read this file, inspect the current branch/PR state, and continue from `Current physical test setup` and `Current V1.9 acceptance path`. Do not redesign completed architecture without a concrete defect or test requirement.
