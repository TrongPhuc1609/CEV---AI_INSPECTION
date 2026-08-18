# CEV — AI INSPECTION

Production-oriented AI inspection project for detecting missing, extra, wrong-type components and oil/grease application defects on slowly moving products.

## Architecture
AI Computer Vision + Machine Vision + Rule Engine + Inspection Orchestrator.

## Current baseline
v0.5.0. Read `PROJECT_CONTEXT.md` before making any code or architecture changes.

## Pipeline
Camera -> Trigger -> Lighting -> Image Acquisition -> Product Tracking -> ROI -> Vision Adapter -> Observation -> Rule Engine -> Region Result -> Inspection Orchestrator -> Product PASS/NG -> PLC/Reject.

## Multi-AI development
All AI contributors (GPT, Claude, Gemini, Copilot, etc.) use the same Git repository and follow `PROJECT_CONTEXT.md`, `AI_AGENT_START.md`, `CONTRIBUTING.md` and `BRANCHING_STRATEGY.md`.

Do not edit `main` directly. Work on a feature branch, test, push and open a Pull Request.

## Next task
Complete v0.6.0: Rule.cmd v1.0 parser, typed InspectionPlan, cross-reference validation, and Orchestrator integration.
