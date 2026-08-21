"""Run the current real-image inspection path over a labelled JSONL manifest.

Usage:
  python tools/run_real_trial_batch.py data/physical_trial/manifest.jsonl
  python tools/run_real_trial_batch.py data/physical_trial/manifest.jsonl --rule config/Rule.machine_vision_test.cmd

The command records the actual RuleEngine decision for every image. It does not
change thresholds or infer ground truth from the image.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.vision.image_inspection_runner import RealImageInspectionRunner


def load_manifest(path: Path) -> list[dict]:
    rows: list[dict] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON on line {line_no}: {exc}") from exc
        for key in ("sample_id", "image", "ground_truth"):
            if key not in row:
                raise ValueError(f"Missing '{key}' on line {line_no}")
        if row["ground_truth"] not in {"GOOD", "NG"}:
            raise ValueError(f"ground_truth must be GOOD or NG on line {line_no}")
        rows.append(row)
    if not rows:
        raise ValueError("Manifest contains no samples")
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Replay a labelled real-image trial set")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--rule", default="config/Rule.machine_vision_test.cmd")
    parser.add_argument("--output", type=Path, default=Path("data/physical_trial/results/predictions.jsonl"))
    args = parser.parse_args()

    rows = load_manifest(args.manifest)
    runner = RealImageInspectionRunner(args.rule)
    args.output.parent.mkdir(parents=True, exist_ok=True)

    with args.output.open("w", encoding="utf-8") as handle:
        for row in rows:
            image = Path(row["image"])
            if not image.is_file():
                image = args.manifest.parent.parent.parent / row["image"]
            if not image.is_file():
                raise FileNotFoundError(f"Image not found for {row['sample_id']}: {row['image']}")

            inspection, decision = runner.inspect(str(image), row["sample_id"])
            region = inspection.regions[runner.region_id]
            observation = region.final_observation
            result = {
                "sample_id": row["sample_id"],
                "image": row["image"],
                "ground_truth": row["ground_truth"],
                "defect_type": row.get("defect_type", ""),
                "prediction": decision.value,
                "observation": observation.to_dict() if observation else None,
                "inspection_id": inspection.inspection_id,
                "attempts": region.attempts,
            }
            handle.write(json.dumps(result, ensure_ascii=False) + "\n")

    print(f"Wrote {len(rows)} predictions to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
