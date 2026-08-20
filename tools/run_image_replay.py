"""Run the inspection pipeline against a real image plus deterministic observations.

This is the bridge between physical camera evidence and the current Rule Engine.
It deliberately does not pretend to perform AI inference: the JSON sidecar supplies
observations while the image is loaded and attached as evidence. Later a real Vision
Adapter can replace the sidecar without changing the Orchestrator/Rule Engine.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import cv2

from src.models.result import Observation, Status
from src.orchestrator.orchestrator import InspectionOrchestrator
from src.rules.engine import RuleEngine
from src.rules.parser import parse_rule_file

ROOT = Path(__file__).resolve().parents[1]
RULE = ROOT / "config" / "Rule.cmd"


def load_case(path: Path, image_path: Path) -> dict[str, list[Observation]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    product_id = payload.get("product_id", "PCB-REAL-001")
    inspection_id = payload.get("inspection_id", "PCB-REAL-001-REPLAY")
    result: dict[str, list[Observation]] = {}
    for item in payload.get("observations", []):
        data: dict[str, Any] = dict(item)
        data["product_id"] = product_id
        data["inspection_id"] = inspection_id
        data["evidence_image"] = str(image_path)
        data["status"] = Status(data.get("status", "UNCERTAIN"))
        result.setdefault(data["region_id"], []).append(Observation(**data))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Replay a real PCB image through Rule Engine/Orchestrator")
    parser.add_argument("image", type=Path)
    parser.add_argument("sidecar", type=Path)
    args = parser.parse_args()

    image_path = args.image.resolve()
    sidecar_path = args.sidecar.resolve()
    if not image_path.is_file():
        print(json.dumps({"status": "ERROR", "error": "IMAGE_NOT_FOUND", "path": str(image_path)}, indent=2))
        return 2
    if not sidecar_path.is_file():
        print(json.dumps({"status": "ERROR", "error": "SIDECAR_NOT_FOUND", "path": str(sidecar_path)}, indent=2))
        return 2

    frame = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
    if frame is None:
        print(json.dumps({"status": "ERROR", "error": "IMAGE_DECODE_FAILED", "path": str(image_path)}, indent=2))
        return 2

    observations = load_case(sidecar_path, image_path)
    config = parse_rule_file(RULE)
    orchestrator = InspectionOrchestrator(config, RuleEngine(config))
    product_id = json.loads(sidecar_path.read_text(encoding="utf-8")).get("product_id", "PCB-REAL-001")
    product = orchestrator.start_product(product_id)

    for region_id, region_observations in observations.items():
        orchestrator.inspect_region(product, region_id, observations=region_observations)
    orchestrator.complete(product)
    decision = orchestrator.final_decision(product)

    evidence_regions = sorted({o.region_id for values in observations.values() for o in values})
    output = {
        "status": decision.value,
        "image": str(image_path),
        "image_shape": {"height": int(frame.shape[0]), "width": int(frame.shape[1]), "channels": int(frame.shape[2])},
        "evidence_regions": evidence_regions,
        "missing_regions": product.missing_regions,
        "regions": {
            rid: {
                "status": rr.status.value,
                "attempts": rr.attempts,
                "error_code": rr.final_observation.error_code if rr.final_observation else None,
            }
            for rid, rr in product.regions.items()
        },
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0 if decision == Status.PASS else 1


if __name__ == "__main__":
    raise SystemExit(main())
