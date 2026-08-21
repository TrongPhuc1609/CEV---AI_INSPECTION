# V1.9 Real-World Validation Plan

## Purpose

This plan closes the gap between software/CI verification and physical evidence. A green CI run proves software behavior for the tested inputs; it does not prove inspection accuracy on a real production line.

## Current boundary

The current V1.9 path is:

`real image -> OpenCV measurement -> MeasurementAdapter -> Observation -> RuleEngine -> InspectionOrchestrator`

The current bootstrap green-board locator and measurement rule are commissioning scaffolding. They must not be presented as a commissioned component/grease inspection model.

## Evidence classes

| Class | Evidence | Can support |
|---|---|---|
| S | Unit/integration/CI tests | Software correctness for covered cases |
| R | Real-image offline replay with labelled ground truth | Image-to-decision behavior on the sampled dataset |
| C | Live camera characterization | Acquisition/lighting/focus/ROI stability |
| M | Motion/timing correlation on the actual conveyor | Trigger/frame/product correlation |
| P | Real PLC handshake and physical reject | End-to-end reject actuation |

A production acceptance claim must list the evidence classes actually completed. Never promote S evidence into R/C/M/P evidence.

## Phase 1 — Dataset and ground truth

**Input:** real PCB images from the actual camera/optics/lighting setup.

Minimum dataset categories:

- GOOD reference boards.
- NG missing component.
- NG extra component.
- NG wrong component/type.
- NG grease/oil missing.
- NG grease/oil insufficient.
- NG grease/oil wrong zone.
- Borderline/uncertain samples.
- Acquisition edge cases: exposure, saturation, blur, focus and position variation.

Every image receives a stable `sample_id` and human-verified `ground_truth`. Defect type is recorded when known. The manifest must be frozen before acceptance scoring.

**Exit gate:** no unknown ground truth for the samples used to claim accuracy; dataset composition and acceptance thresholds are documented.

## Phase 2 — Offline replay

Run:

```text
python tools/run_real_trial_batch.py data/physical_trial/manifest.jsonl
python tools/evaluate_real_trial.py data/physical_trial/manifest.jsonl --predictions data/physical_trial/results/predictions.jsonl
```

Required evidence:

- `evaluation.json`
- `evaluation.html`
- frozen manifest
- exact Rule.cmd/config revision
- software commit SHA

Report separately:

- false accepts: NG -> PASS
- false rejects: GOOD -> NG
- UNCERTAIN rate
- coverage rate
- performance by defect type

Do not use a single accuracy percentage as the only acceptance criterion.

**Exit gate:** thresholds for false accepts/rejects/uncertain/coverage are approved for the specific product and dataset. If the product requirement is not yet known, the result is calibration evidence, not acceptance.

## Phase 3 — Live camera characterization

Use `CAPTURE_CAMERA.bat` and `tools/capture_camera.py` with the actual camera.

Record:

- resolution and frame rate;
- exposure/brightness;
- saturation/clipping;
- focus/blur;
- board pose and position variation;
- lighting repeatability;
- ROI localization success/failure.

The same labelled samples should be captured through the live acquisition path where practical. A captured frame is acquisition evidence until it is linked to a ground-truth sample and replayed/scored.

**Exit gate:** acquisition quality is stable enough that image-level false decisions are attributable to inspection logic rather than uncontrolled capture conditions.

## Phase 4 — Motion and frame correlation

Only after offline and acquisition gates pass, test the real conveyor/trigger.

Verify:

- trigger-to-frame latency;
- product identity/frame correlation;
- multi-frame/recheck timing;
- timeout behavior;
- no stale-frame acceptance;
- no duplicate or skipped product decisions.

Use commissioning documents and measured values; never substitute assumed motion values.

**Exit gate:** every accepted production frame is demonstrably correlated to the triggering product within the configured timing bounds.

## Phase 5 — PLC/reject

PLC is currently simulated. Real PLC testing must verify the actual acknowledgement contract.

Required cases:

1. GOOD product -> no reject.
2. NG product -> reject command and acknowledgement.
3. Reject timeout -> fail closed.
4. PLC unavailable -> no silent PASS.
5. Duplicate/late acknowledgement -> handled deterministically.
6. Physical reject position/timing verified against the conveyor.

**Exit gate:** physical NG reject is successful only when the configured PLC acknowledgement contract and physical actuation evidence are both satisfied.

## Acceptance record

For every release candidate, record:

- commit SHA;
- Rule.cmd/config checksum;
- model artifact/version/checksum when AI is introduced;
- camera/lighting configuration;
- dataset manifest/checksum;
- sample counts by class;
- false-accept rate;
- false-reject rate;
- uncertain rate;
- coverage rate;
- motion/timing measurements;
- PLC/reject evidence;
- operator/reviewer sign-off.

## Explicit non-claims

Until the corresponding evidence exists, the project must not claim:

- component detection accuracy from the current measurement-only rule;
- grease/oil detection accuracy;
- production camera stability;
- real conveyor timing correctness;
- physical PLC reject success.
