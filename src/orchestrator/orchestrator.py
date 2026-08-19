"""Inspection Orchestrator: product identity, regions, recheck and aggregation."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Callable, Dict, Iterable, List, Optional
import uuid
from ..models.result import Observation, Status
from ..rules.engine import RuleEngine
from ..rules.parser import RuleConfig
from ..config_hash import inspection_plan_hash, rule_config_hash

class InspectionState(str,Enum):
    CREATED="CREATED"; INSPECTING="INSPECTING"; RECHECKING="RECHECKING"; COMPLETED="COMPLETED"; ERROR="ERROR"
@dataclass
class RegionResult:
    region_id:str; attempts:int=0; observations:List[Observation]=field(default_factory=list); final_observation:Optional[Observation]=None; error_code:Optional[str]=None
    @property
    def status(self): return self.final_observation.status if self.final_observation else Status.UNCERTAIN
@dataclass
class ProductInspection:
    product_id:str; inspection_id:str; created_at:str; state:InspectionState=InspectionState.CREATED; regions:Dict[str,RegionResult]=field(default_factory=dict); missing_regions:List[str]=field(default_factory=list); metadata:Dict[str,str]=field(default_factory=dict)
    def final_status(self):
        if self.missing_regions:return Status.FAIL
        if not self.regions:return Status.UNCERTAIN
        statuses=[r.status for r in self.regions.values()]
        if any(s==Status.FAIL for s in statuses):return Status.FAIL
        if any(s==Status.UNCERTAIN for s in statuses):return Status.UNCERTAIN
        return Status.PASS
class InspectionOrchestrator:
    def __init__(self,config:RuleConfig,rule_engine:RuleEngine,observation_provider:Optional[Callable]=None): self.config=config; self.rule_engine=rule_engine; self.observation_provider=observation_provider; self.active={}
    def start_product(self,product_id):
        if not product_id: raise ValueError("product_id is required")
        inspection_id=f"{product_id}-{uuid.uuid4().hex[:8]}"; plan=self.config.to_plan(); item=ProductInspection(product_id,inspection_id,datetime.now(timezone.utc).isoformat()); item.state=InspectionState.INSPECTING; item.metadata.update({"rule_config_hash":rule_config_hash(self.config),"inspection_plan_hash":inspection_plan_hash(plan),"plan_version":plan.version}); self.active[inspection_id]=item; return item
    def required_regions(self): return self.config.to_plan().required_regions()
    def inspect_region(self,inspection,region_id,observations:Optional[Iterable[Observation]]=None,observation_provider:Optional[Callable[[int],Observation]]=None):
        rule=self.config.region(region_id); rr=inspection.regions.setdefault(region_id,RegionResult(region_id))
        if not rule:
            rr.error_code="REGION_NOT_CONFIGURED"; rr.final_observation=Observation(inspection.product_id,inspection.inspection_id,region_id,"UNKNOWN",status=Status.FAIL,error_code=rr.error_code); return rr
        max_attempts=int(self.config.get("RECHECK","max_attempts",1)); recheck_enabled=bool(self.config.get("RECHECK","enabled",False)); provided=list(observations) if observations is not None else None
        while rr.attempts<max_attempts:
            rr.attempts+=1
            try:
                if observation_provider is not None: obs=observation_provider(rr.attempts)
                elif provided is not None: obs=provided[min(rr.attempts-1,len(provided)-1)]
                elif self.observation_provider is not None: obs=self.observation_provider(inspection.product_id,region_id,rr.attempts,inspection)
                else: raise ValueError("No observations or observation_provider supplied")
                obs.product_id=inspection.product_id; obs.inspection_id=inspection.inspection_id; obs.region_id=region_id; evaluated=self.rule_engine.evaluate(obs)
            except Exception as exc:
                evaluated=Observation(inspection.product_id,inspection.inspection_id,region_id,"SYSTEM",status=Status.FAIL,error_code=self._error_code(exc))
            rr.observations.append(evaluated); rr.final_observation=evaluated
            if evaluated.status!=Status.UNCERTAIN: break
            if not recheck_enabled or rr.attempts>=max_attempts: break
            inspection.state=InspectionState.RECHECKING
        inspection.state=InspectionState.INSPECTING; return rr
    @staticmethod
    def _error_code(exc):
        name=exc.__class__.__name__.upper()
        if "CAMERA" in name:return "CAMERA_ERROR"
        if "TRIGGER" in name:return "TRIGGER_ERROR"
        if "TIMEOUT" in name:return "TIMEOUT"
        return "INSPECTION_ERROR"
    def complete(self,inspection):
        required=self.required_regions(); inspection.missing_regions=[r for r in required if r not in inspection.regions]; inspection.state=InspectionState.COMPLETED; self.active.pop(inspection.inspection_id,None); return inspection
    def final_decision(self,inspection):
        status=inspection.final_status()
        if status==Status.UNCERTAIN:
            policy=str(self.config.get("PRODUCT_DECISION","uncertain_policy",self.config.get("INSPECTION","uncertain_policy","RECHECK_THEN_NG")))
            if policy in {"NG","RECHECK_THEN_NG"}:return Status.FAIL
            if policy=="PASS":return Status.PASS
        return status
