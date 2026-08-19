# V1.2 Motion / Timing / Frame Correlation

## Purpose
V1.2 closes the software gap between a trigger event and the image actually evaluated when the product is moving on a conveyor.

## New configuration
`Rule.cmd` now supports:

- `[MOTION]` — nominal/min/max product velocity, sensor-to-camera distance, camera-to-reject distance, and processing budgets.
- `[CORRELATION]` — maximum trigger/frame timestamp delta and optional position tolerance.

These values are commissioning inputs. They are not inferred from mock execution.

## Runtime primitives

`MotionTimingPlanner` calculates:

1. trigger -> camera travel time;
2. acquisition + AI + decision + PLC processing budget;
3. camera -> reject travel window;
4. total trigger -> reject budget.

`TriggerFrameCorrelator` verifies that a frame belongs to the triggering product using:

- product ID when available;
- trigger/frame timestamp tolerance;
- position tolerance when configured.

A failed correlation must not be treated as a valid inspection frame. The application/orchestrator must route it to the configured fail-safe error path before production use.

## Acceptance criteria

- Slow-product velocity is explicitly represented in the typed `InspectionPlan`.
- Timing calculations are deterministic and unit tested.
- Wrong-product frames are rejected.
- Stale frames are rejected.
- Position mismatch can be rejected.
- No vendor SDK is required for the timing/correlation layer.

## Physical commissioning boundary

The software can calculate the timing budget, but only the real line can establish:

- actual conveyor velocity range;
- sensor-to-camera distance;
- trigger jitter;
- camera exposure/readout latency;
- AI latency P50/P95/P99;
- PLC output latency;
- reject actuator latency.

Production mode remains blocked until these measurements are recorded and the HIL/line-trial gates pass.
