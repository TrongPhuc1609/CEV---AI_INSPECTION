# Physical Vision Trial V1

## Current hardware
- Camera: Sanwa Supply CMS-V30SETBK (USB webcam)
- PLC: not installed; PLC remains simulated
- Product: real PCB

## Trial objective
Prove the real-camera acquisition path before commissioning AI models or PLC.

```text
CMS-V30SETBK
    -> USB acquisition
    -> captured frame + metadata
    -> ROI / machine vision
    -> AI adapter
    -> Observation
    -> Rule Engine
    -> PASS / NG
    -> PLC Simulator
```

## Capture procedure
1. Connect the CMS-V30SETBK to the Windows test PC.
2. Extract the latest repository ZIP from `main` after the V1.9 branch is merged, or use the V1.9 branch during development.
3. Run `CAPTURE_CAMERA.bat`.
4. Press SPACE to save a frame and Q/ESC to exit.
5. Collect at least one GOOD PCB frame under the intended inspection lighting.
6. Keep the `.jpg` and matching `.json` sidecar together.

## Acceptance evidence
For each frame record:
- camera index;
- actual resolution;
- timestamp;
- frame ID;
- source = `real_usb_camera`.

## Important limitation
A USB webcam frame proves acquisition only. It does not establish production inspection accuracy. Product-specific ROI, lighting, exposure, AI model, thresholds, calibration, motion timing and reject behavior must still be commissioned.
