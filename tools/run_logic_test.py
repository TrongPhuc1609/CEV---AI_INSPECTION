"""Deterministic end-to-end logic test using the current PCB image as evidence context.

This intentionally does not require an AI model or PLC. It validates that observations
representing GOOD / missing / wrong / extra / grease / uncertain cases are routed through
RuleEngine + InspectionOrchestrator to the expected final product decision.
"""
from __future__ import annotations

import json
from pathlib import Path

from src.models.result import Observation, Status
from src.orchestrator.orchestrator import InspectionOrchestrator
from src.rules.engine import RuleEngine
from src.rules.parser import parse_rule_file

ROOT = Path(__file__).resolve().parents[1]
RULE = ROOT / "config" / "Rule.cmd"
EVIDENCE = "data/physical_trial/pcb_good.jpg"


def obs(region: str, method: str, **kwargs) -> Observation:
    return Observation(
        product_id="TEST",
        inspection_id="TEST",
        region_id=region,
        method=method,
        evidence_image=EVIDENCE,
        **kwargs,
    )


def inspect_product(config, observations_by_region):
    orchestrator = InspectionOrchestrator(config, RuleEngine(config))
    product = orchestrator.start_product("PCB-TEST-001")
    for region_id, observations in observations_by_region.items():
        orchestrator.inspect_region(product, region_id, observations=observations)
    orchestrator.complete(product)
    return product, orchestrator.final_decision(product)


def base_good():
    return {
        "R01": [obs("R01", "DETECTION", confidence=.95, quantity=4)],
        "R02": [obs("R02", "DETECTION_CLASSIFICATION", confidence=.96, detected_class="BOLT_M8", quantity=2, position={"x": 200, "y": 150})],
        "R03": [obs("R03", "SEGMENTATION", confidence=.92, coverage_percent=75)],
        "R04": [obs("R04", "SEGMENTATION", confidence=.92, coverage_percent=75, metadata={"target_zone_coverage_percent": 75, "forbidden_zone_violation": False})],
    }


def main() -> int:
    config = parse_rule_file(RULE)
    cases = []

    good = base_good()
    cases.append(("GOOD", good, Status.PASS, None))

    missing = base_good()
    missing["R01"] = [obs("R01", "DETECTION", confidence=.95, quantity=3)]
    cases.append(("MISSING_COMPONENT", missing, Status.FAIL, "MISSING_COMPONENT"))

    wrong = base_good()
    wrong["R02"] = [obs("R02", "DETECTION_CLASSIFICATION", confidence=.96, detected_class="BOLT_M6", quantity=2, position={"x": 200, "y": 150})]
    cases.append(("WRONG_COMPONENT", wrong, Status.FAIL, "WRONG_COMPONENT"))

    extra = base_good()
    extra["R01"] = [obs("R01", "DETECTION", confidence=.95, quantity=5)]
    cases.append(("EXTRA_COMPONENT", extra, Status.FAIL, "EXTRA_COMPONENT"))

    no_grease = base_good()
    no_grease["R03"] = [obs("R03", "SEGMENTATION", confidence=.92, coverage_percent=0)]
    cases.append(("NO_GREASE", no_grease, Status.FAIL, "NO_GREASE"))

    wrong_zone = base_good()
    wrong_zone["R04"] = [obs("R04", "SEGMENTATION", confidence=.92, coverage_percent=75, metadata={"target_zone_coverage_percent": 20, "forbidden_zone_violation": False})]
    cases.append(("GREASE_WRONG_ZONE", wrong_zone, Status.FAIL, "GREASE_WRONG_ZONE"))

    recheck = base_good()
    recheck["R01"] = [
        obs("R01", "DETECTION", confidence=.50, quantity=4),
        obs("R01", "DETECTION", confidence=.95, quantity=4),
    ]
    cases.append(("RECHECK_UNCERTAIN_THEN_PASS", recheck, Status.PASS, {"region": "R01", "attempts": 2}))

    missing_region = base_good()
    del missing_region["R04"]
    cases.append(("MISSING_REGION", missing_region, Status.FAIL, {"missing": ["R04"]}))

    results = []
    for name, payload, expected, expected_extra in cases:
        product, actual = inspect_product(config, payload)
        region_errors = {
            rid: rr.final_observation.error_code
            for rid, rr in product.regions.items()
            if rr.final_observation and rr.final_observation.error_code
        }
        passed = actual == expected
        if isinstance(expected_extra, str):
            passed = passed and expected_extra in region_errors.values()
        elif isinstance(expected_extra, dict) and "region" in expected_extra:
            rr = product.regions[expected_extra["region"]]
            passed = passed and rr.attempts == expected_extra["attempts"] and rr.status == Status.PASS
        elif isinstance(expected_extra, dict) and "missing" in expected_extra:
            passed = passed and product.missing_regions == expected_extra["missing"]
        results.append({
            "case": name,
            "pass": passed,
            "final_status": actual.value,
            "region_errors": region_errors,
            "missing_regions": product.missing_regions,
        })

    for result in results:
        print(json.dumps(result, ensure_ascii=False))

    all_pass = all(item["pass"] for item in results)
    print(json.dumps({"logic_test": "PASS" if all_pass else "FAIL", "cases": len(results)}, ensure_ascii=False, indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
