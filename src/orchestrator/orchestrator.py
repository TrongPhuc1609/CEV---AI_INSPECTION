"""Inspection Orchestrator coordinating one product across multiple regions/frames."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Callable, Dict, Iterable, List, Optional
import uuid

from ..models.result import Observation, Status
from ..rules.engine import RuleEngine
from ..rules.parser import RuleConfig


class InspectionState(str, Enum):
    CREATED = "CREATED"
    INSPECTING = "INSPECTING"
    RECHECKING = "RECHECKING"
    COMPLETED = "COMPLETED"


@dataclass
class RegionResult:
    region_id: str
    attempts: int = 0
    observations: List[Observation] = field(default_factory=list)
    final_observation: Optional[Observation] = None

    @property
    def status(self) -> Status:
        if self.final_observation is None:
            return Status.UNCERTAIN
        return self.final_observation.status


@dataclass
class ProductInspection:
    product_id: str
    inspection_id: str
    created_at: str
    state: InspectionState = InspectionState.CREATED
    regions: Dict[str, RegionResult] = field(default_factory=dict)

    def final_status(self) -> Status:
        if not self.regions:
            return Status.UNCERTAIN
        statuses = [r.status for r in self.regions.values()]
        if any(s == Status.FAIL for s in statuses):
            return Status.FAIL
        if any(s == Status.UNCERTAIN for s in statuses):
            return Status.UNCERTAIN
        return Status.PASS


class InspectionOrchestrator:
    def __init__(self, config: RuleConfig, rule_engine: RuleEngine,
                 observation_provider: Optional[Callable[[str, str, int, ProductInspection], Observation]] = None):
        self.config = config
        self.rule_engine = rule_engine
        self.observation_provider = observation_provider
        self.active: Dict[str, ProductInspection] = {}

    def start_product(self, product_id: str) -> ProductInspection:
        inspection_id = f"{product_id}-{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc).isoformat()
        item = ProductInspection(product_id, inspection_id, now)
        item.state = InspectionState.INSPECTING
        self.active[inspection_id] = item
        return item

    def required_regions(self) -> List[str]:
        regions = []
        for section in self.config.sections:
            if section.startswith("REGION:"):
                region_id = section.split(":", 1)[1]
                if self.config.region(region_id).get("enabled", True):
                    regions.append(region_id)
        return regions

    def inspect_region(self, inspection: ProductInspection, region_id: str,
                       observations: Optional[Iterable[Observation]] = None) -> RegionResult:
        rule = self.config.region(region_id)
        if not rule:
            raise ValueError(f"Region not configured: {region_id}")

        max_attempts = int(self.config.get("RECHECK", "max_attempts", 1))
        recheck_enabled = bool(self.config.get("RECHECK", "enabled", False))
        rr = inspection.regions.setdefault(region_id, RegionResult(region_id))
        provided = list(observations) if observations is not None else None

        while rr.attempts < max_attempts:
            rr.attempts += 1
            if provided is not None:
                obs = provided[min(rr.attempts - 1, len(provided) - 1)]
            elif self.observation_provider is not None:
                obs = self.observation_provider(inspection.product_id, region_id, rr.attempts, inspection)
            else:
                raise ValueError("No observations or observation_provider supplied")

            obs.product_id = inspection.product_id
            obs.inspection_id = inspection.inspection_id
            obs.region_id = region_id
            evaluated = self.rule_engine.evaluate(obs)
            rr.observations.append(evaluated)
            rr.final_observation = evaluated
            if evaluated.status != Status.UNCERTAIN:
                break
            if not recheck_enabled or rr.attempts >= max_attempts:
                break
            inspection.state = InspectionState.RECHECKING

        inspection.state = InspectionState.INSPECTING
        return rr

    def complete(self, inspection: ProductInspection) -> ProductInspection:
        required = self.required_regions()
        missing = [r for r in required if r not in inspection.regions]
        if missing:
            raise ValueError(f"Cannot complete; missing regions: {missing}")
        inspection.state = InspectionState.COMPLETED
        self.active.pop(inspection.inspection_id, None)
        return inspection

    def final_decision(self, inspection: ProductInspection) -> Status:
        return inspection.final_status()
