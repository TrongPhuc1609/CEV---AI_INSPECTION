# PROJECT_CONTEXT.md

## MANDATORY
Every new AI/coding session MUST read this file before coding. It is the single source of project memory. Git is the source of code/history/branches/PRs.

## Mission
Production-oriented inspection for slowly moving products:
- missing components
- extra components
- wrong component/type
- oil/grease missing or insufficient

## Core architecture
AI Computer Vision + Machine Vision + Rule Engine + Inspection Orchestrator.

Pipeline:
Camera -> Trigger -> Lighting -> Image Acquisition -> Product Tracking -> ROI -> Vision Adapter -> Observation -> Rule Engine -> Region Result -> Inspection Orchestrator -> Product PASS/NG -> PLC/Reject.

## Non-negotiable decisions
1. AI never directly decides product PASS/NG; AI produces Observation.
2. Rule Engine owns deterministic inspection decisions.
3. Orchestrator owns Product ID, Inspection ID, regions, multi-frame/recheck, timeout and product aggregation.
4. Rule.cmd is the human-readable source for product-specific configuration; do not hard-code product rules.
5. Camera/AI/PLC vendors remain behind replaceable adapters.
6. Hardware/AI errors and missing required regions must never silently become PASS.
7. UNCERTAIN follows explicit recheck/final policy.
8. Production decisions must be auditable.

## Baseline status
v0.1 Foundation: COMPLETE.
v0.2 Rule Parser + Rule Engine + Normalized Result: COMPLETE.
v0.3 Inspection Orchestrator: COMPLETE.
v0.4 AI Vision Adapter Layer: COMPLETE / architecture baseline.
v0.5 Machine Vision Layer: COMPLETE / architecture baseline; real hardware is not yet physically validated.
v0.6 Rule.cmd v1.0: DESIGN DEFINED, NOT COMPLETE.

## v0.6 acceptance criteria
- Rule.cmd v1.0 exists and is human-readable.
- Parser reads PROJECT/PRODUCT/CAMERA/TRIGGER/ENCODER/LIGHT/MODEL/RECHECK/REGION/PRODUCT_DECISION/PLC/PLC_REJECT/EVIDENCE/AUDIT.
- Typed config objects exist: CameraConfig, TriggerConfig, EncoderConfig, LightingConfig, ModelConfig, ROIConfig, RecheckConfig, RegionConfig, ProductDecisionConfig, PLCConfig, EvidenceConfig.
- Build an InspectionPlan/ProjectConfig.
- Validate region references to camera/trigger/light/model/recheck.
- Orchestrator consumes InspectionPlan.
- Tests pass.
- Package/build is verified.

## Current next task
COMPLETE v0.6: Rule.cmd v1 parser -> typed InspectionPlan -> validation -> Orchestrator integration -> tests -> verified package.

## Inspection logic
Missing/extra: YOLO or RT-DETR detection + expected class/quantity/tolerance.
Wrong type: detection + classification or constrained classification.
Oil/grease: segmentation for coverage, optionally anomaly detection cross-check.
Thresholds require real-line calibration; example values are not production validated.

## Product decision default
All required regions PASS -> PASS.
Any final region NG -> NG.
Missing region/timeout/camera error/trigger error/AI error -> NG.
UNCERTAIN -> recheck -> NG unless explicitly configured otherwise.

## PLC/reject
Keep inspection result, PLC command and physical reject result distinct. Reject timing must be validated against sensor-to-camera distance, conveyor speed, processing latency, PLC latency and actuator latency.

## Session protocol
START: read this file, inspect source tree, confirm baseline/completed/next task.
END: update CURRENT BASELINE, COMPLETED, CURRENT NEXT TASK, KNOWN ISSUES, TEST STATUS, LAST CHANGE.

## Multi-AI Git workflow
READ CONTEXT -> CREATE FEATURE BRANCH -> INSPECT -> IMPLEMENT -> TEST -> UPDATE CONTEXT -> COMMIT -> PUSH -> PULL REQUEST -> REVIEW -> MERGE.
Never have multiple AIs directly edit main.

## Git baseline
Repository: TrongPhuc1609/CEV---AI_INSPECTION
Baseline: v0.5.0
Planned first feature branch: feature/rule-cmd-v1

## Architecture change record
No pending architecture change approved. Major changes must record DATE, DECISION, REASON, ALTERNATIVES, IMPACT and MIGRATION here.
