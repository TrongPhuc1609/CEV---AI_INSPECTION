# V1.1 Physical Commissioning Gate

## Purpose

V1.0 is the verified software/simulation baseline. V1.1 defines the controlled transition from mock/simulation to real line commissioning without weakening the fail-closed safety boundary.

## Gate order

1. **Rule plan** — `Rule.cmd` parses and `InspectionPlan.validate()` passes.
2. **Camera** — a real vendor adapter is selected and captures frames with stable frame IDs/timestamps.
3. **Trigger/encoder** — product identity and trigger position are stable; product/frame correlation is verified.
4. **Lighting** — exposure, gain, strobe mode and illumination repeatability are measured.
5. **AI models** — real model artifacts are installed; version, SHA-256, class map and thresholds are recorded.
6. **ROI/calibration** — camera-to-product geometry and all configured ROIs are calibrated.
7. **Inspection logic** — representative PASS/NG samples cover missing, extra, wrong type, wrong position, grease missing/insufficient/wrong zone and uncertain/recheck cases.
8. **Timing** — acquisition, AI, decision, PLC and reject-actuator latency are measured against the line speed and sensor-to-camera distance.
9. **PLC/reject** — the reject command and physical actuator are validated as separate events; fail-safe behavior is tested.
10. **Audit** — normalized inspection, configuration/model identity, recheck history and PLC command are persisted.
11. **HIL** — deterministic scenarios pass before line trial.
12. **Line trial** — false-pass and false-reject rates are recorded on representative production samples.

## Fail-closed rules

`production_mode` must remain disabled while a real camera, PLC, required model artifact, audit persistence, or calibrated threshold is missing. Software/mock tests cannot satisfy a physical commissioning gate.

## CLI

```bash
python -m src.cli commissioning-report --rule config/Rule.cmd --model-root .
```

Exit code `0` means the software configuration/artifacts are sufficient to start physical commissioning. Exit code `2` means at least one blocking gate remains open.

The report intentionally lists field measurements as warnings until recorded: sensor-to-camera distance, conveyor velocity, acquisition latency, AI latency, PLC latency and reject-actuator latency.

## Acceptance record

Do not mark V1.1 complete from a software test alone. Record hardware model/firmware, calibration values, measured timings, sample counts, false-pass/false-reject results and PLC/reject evidence before enabling production mode.
