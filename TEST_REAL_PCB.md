# GPT AI Inspection — Real PCB Trial Quick Start

## Scope

This trial verifies the real-image offline software path. It does **not** claim production inspection accuracy, live conveyor timing, or physical PLC reject success.

## Before testing

- Product: real PCB.
- Camera: Sanwa Supply CMS-V30SETBK USB webcam.
- PLC: not installed; PLC remains simulated.
- Python environment must have the same dependencies used by CI (`pytest`, `numpy`, `opencv-python-headless`).

## Single-image smoke test

```bat
RUN_MACHINE_VISION_REPLAY.bat path\to\real_pcb.jpg
```

or:

```bash
python tools/run_machine_vision_replay.py path/to/real_pcb.jpg
```

Review the `observation` and final `status`. The current Rule.cmd is a measurement-boundary recipe, not a component/grease classifier.

## Labelled dataset test

1. Put real images under `data/physical_trial/images/`.
2. Copy `data/physical_trial/manifest.example.jsonl` to `manifest.jsonl` and replace entries with human-verified ground truth.
3. Run:

```bash
python tools/run_real_trial_batch.py data/physical_trial/manifest.jsonl
python tools/evaluate_real_trial.py data/physical_trial/manifest.jsonl --predictions data/physical_trial/results/predictions.jsonl
```

4. Review:
   - `data/physical_trial/results/evaluation.json`
   - `data/physical_trial/results/evaluation.html`

## Acceptance rule

Do not accept the trial from accuracy alone. Record false accepts (NG -> PASS), false rejects (GOOD -> NG), UNCERTAIN rate and coverage. Product-specific limits must be approved before the run.

See `docs/REAL_WORLD_VALIDATION_PLAN.md` for the complete physical validation sequence.
