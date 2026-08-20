"""CLI for offline real-image machine-vision replay."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.models.result import Status
from src.vision.image_inspection_runner import RealImageInspectionRunner


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("image", help="Path to a real PCB image")
    parser.add_argument("--product-id", default="REAL-PCB-001")
    parser.add_argument(
        "--rule",
        default="config/Rule.machine_vision_test.cmd",
        help="Replay Rule.cmd path",
    )
    args = parser.parse_args()

    runner = RealImageInspectionRunner(args.rule)
    inspection, decision = runner.inspect(args.image, args.product_id)
    region = inspection.regions[runner.region_id]
    observation = region.final_observation
    payload = {
        "product_id": inspection.product_id,
        "inspection_id": inspection.inspection_id,
        "status": decision.value,
        "region_id": runner.region_id,
        "attempts": region.attempts,
        "observation": observation.to_dict() if observation else None,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if decision == Status.PASS else 2


if __name__ == "__main__":
    raise SystemExit(main())
