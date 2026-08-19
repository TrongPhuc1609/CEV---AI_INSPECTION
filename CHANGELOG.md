# CHANGELOG

## v1.0.0-software
- Single CLI entry point for Rule.cmd validation, simulation, replay and production release gating
- Deterministic rule-config and inspection-plan hashes persisted with every inspection
- Graceful continuous inspection service loop with bounded test mode and shutdown support
- CI now runs Python compile checks, Rule.cmd validation and the complete pytest suite
- Documented software release boundary and explicit hardware commissioning gates
- Production mode is fail-closed until real camera/PLC adapters and commissioned model artifacts are supplied

## v0.98.0
- Model manifest registry with version, checksum, class-map and threshold metadata sourced from Rule.cmd
- Production release gate that fails closed when real hardware/models are uncommissioned
- Deterministic calibration registry derived from typed InspectionPlan
- Offline observation replay for deterministic rule/calibration verification
- Latency/confidence/coverage performance aggregation with percentile metrics
- Rule.cmd now records explicit uncommissioned model metadata placeholders
- Automated tests cover model validation, release gating, replay, calibration and performance metrics
- Scope remains software/commissioning validated; real model artifacts and physical line validation remain required

## v0.95.0
- Vendor-neutral `CallbackCamera`, `CallbackTrigger` and `CallbackPLC` adapters
- Injectable `HardwareFactory` boundary with `MockHardwareFactory` reference implementation
- Explicit acquisition start/stop lifecycle and pre-start capture protection
- Commissioning `TimingBudget` and `TimingCollector` for acquisition, AI, decision and PLC latency
- Deterministic `HILRunner` for reusable hardware/model commissioning scenarios
- Production pipeline supports injected hardware and automatic acquisition startup
- Automated tests for hardware adapter contracts, lifecycle, timing budget and HIL nominal PASS
- Scope remains software/simulation validated; physical vendor SDKs and line timing are commissioning gates

## v0.9.0
- Rule.cmd v1.0 configuration schema
- Typed `InspectionPlan` with cross-reference and position validation
- Config-driven reference runtime factory
- Detection evidence preserves all class counts to prevent hidden extra/wrong components
- Real multi-frame recheck through fresh acquisition attempts
- Fail-safe missing-region, acquisition-error and UNCERTAIN -> NG decisions
- Configurable component position tolerance
- Grease target/forbidden-zone decision support
- Anomaly detection decision support
- Durable normalized audit JSON
- Automated verification: 15 tests passing in the development environment

## v0.5.0
- Machine Vision layer baseline
- Camera, Trigger, Product Tracking, ROI, Lighting, Image Acquisition
- PLC/Reject abstraction
- End-to-end production pipeline

## v0.4.0
- AI Vision Adapter layer baseline
- Normalized Observation

## v0.3.0
- Inspection Orchestrator
- Product ID / Inspection ID
- Multi-region and recheck
- Product PASS/NG aggregation

## v0.2.0
- Rule Parser
- Rule Engine
- Normalized result

## v0.1.0
- Project foundation
