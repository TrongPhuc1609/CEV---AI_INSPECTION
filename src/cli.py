"""Single command-line entry point for validation, simulation and replay."""
from __future__ import annotations

import argparse
import json

from .integration.commissioning import PhysicalCommissioningGate
from .integration.release_gate import ProductionReleaseGate
from .models.result import Status
from .production_pipeline import ProductionInspectionPipeline
from .replay import ObservationReplay
from .rules.engine import RuleEngine
from .rules.parser import parse_rule_file


class DemoDetector:
    def predict(self, image):
        return {"detections": [{"class": "BOLT_M6", "confidence": .95}] * 4}


class DemoClassifier:
    def predict(self, image):
        return {"class": "BOLT_M8", "confidence": .96, "quantity": 2}


class DemoSegmenter:
    def predict(self, image):
        return {"class": "grease", "confidence": .92, "coverage_percent": 75,
                "target_zone_coverage_percent": 75, "forbidden_zone_violation": False}


def demo_models():
    return {"M01": DemoDetector(), "M02": DemoClassifier(), "M03": DemoSegmenter(), "M04": DemoSegmenter()}


def main(argv=None):
    parser = argparse.ArgumentParser(prog="ai-inspection")
    parser.add_argument("--rule", default="config/Rule.cmd")
    parser.add_argument("--model-root", default=".")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate-rule")
    sub.add_parser("release-gate")
    sub.add_parser("commissioning-report")
    sub.add_parser("simulate")
    replay = sub.add_parser("replay")
    replay.add_argument("observations")
    args = parser.parse_args(argv)

    config = parse_rule_file(args.rule)
    plan = config.to_plan()

    if args.command == "validate-rule":
        print(json.dumps({"valid": True, "version": plan.version, "required_regions": plan.required_regions()}, indent=2))
        return 0
    if args.command == "release-gate":
        result = ProductionReleaseGate().validate(plan, real_hardware=True, require_models=True)
        print(json.dumps({"ready": result.ready, "errors": list(result.errors)}, indent=2))
        return 0 if result.ready else 2
    if args.command == "commissioning-report":
        report = PhysicalCommissioningGate().evaluate(plan, model_root=args.model_root, require_real_hardware=True)
        print(json.dumps(report.as_dict(), indent=2))
        return 0 if report.ready else 2
    if args.command == "simulate":
        pipeline = ProductionInspectionPipeline.from_rule_file(args.rule, demo_models())
        inspection = pipeline.run_product()
        payload = {
            "product_id": inspection.product_id,
            "inspection_id": inspection.inspection_id,
            "status": inspection.final_status().value,
            "metadata": inspection.metadata,
            "timing": pipeline.timing.summary(),
        }
        print(json.dumps(payload, indent=2))
        pipeline.stop()
        return 0 if inspection.final_status() == Status.PASS else 1
    if args.command == "replay":
        observations = ObservationReplay.load(args.observations)
        outcomes = ObservationReplay(RuleEngine(config)).evaluate(observations)
        print(json.dumps([{"index": o.index, "status": o.status.value, "error_code": o.error_code} for o in outcomes], indent=2))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
