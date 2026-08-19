# GPT_AI Inspection - Test Package

## Purpose
This package runs the current software/simulation baseline before physical commissioning.

## Requirements
- Windows 10/11
- Python 3.10+ available as `py -3`
- Internet access for the first dependency installation if `requirements.txt` is present

## Quick test
1. Extract the ZIP package.
2. Double-click `RUN_TEST.bat`.
3. The script validates `config/Rule.cmd`, runs the simulation and evaluates the release gate.

## Important
A release-gate failure for the repository example configuration is expected. It means the software is correctly refusing production release until real camera/PLC adapters and commissioned AI model artifacts are supplied.

## Physical trial is not yet implied
The current package is software/simulation validated. A physical trial additionally requires:
- real camera and trigger/encoder;
- real lighting;
- real PLC/reject actuator;
- commissioned product-specific `Rule.cmd`;
- real AI model artifact with version/SHA-256/class map;
- real product images and calibrated thresholds;
- measured camera-to-reject timing.

## Source of truth
Read `PROJECT_CONTEXT.md` before changing code or configuration.
