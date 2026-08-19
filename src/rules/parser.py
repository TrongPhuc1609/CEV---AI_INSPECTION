"""Parser and compiler for the human-readable Rule.cmd format."""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict
from .plan import AuditConfig, CameraConfig, CorrelationConfig, EncoderConfig, EvidenceConfig, InspectionPlan, LightingConfig, ModelConfig, MotionConfig, PLCConfig, ProductDecisionConfig, ROIConfig, RecheckConfig, RegionConfig, TriggerConfig

def _parse_value(value: str) -> Any:
    value=value.strip()
    if value.lower() in {"true","false"}: return value.lower()=="true"
    try:
        if "." in value: return float(value)
        return int(value)
    except ValueError: return value
@dataclass
class RuleConfig:
    sections: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    def get(self,section,key,default=None): return self.sections.get(section,{}).get(key,default)
    def region(self,region_id): return self.sections.get(f"REGION:{region_id}",{})
    def to_plan(self): return build_inspection_plan(self)
def parse_rule_file(path: str|Path)->RuleConfig:
    path=Path(path)
    if not path.exists(): raise FileNotFoundError(path)
    sections={}; current=None
    for line_no,raw in enumerate(path.read_text(encoding="utf-8").splitlines(),1):
        line=raw.strip()
        if not line or line.startswith("#"): continue
        if line.startswith("[") and line.endswith("]"):
            current=line[1:-1].strip()
            if current in sections: raise ValueError(f"Duplicate section at line {line_no}: {current}")
            sections[current]={}; continue
        if "=" not in line: raise ValueError(f"Invalid Rule.cmd line {line_no}: {raw}")
        if current is None: raise ValueError(f"Key outside section at line {line_no}")
        key,value=line.split("=",1); key=key.strip()
        if not key: raise ValueError(f"Empty key at line {line_no}")
        sections[current][key]=_parse_value(value)
    return RuleConfig(sections)
def _sections(config,prefix): return {k.split(":",1)[1]:v for k,v in config.sections.items() if k.startswith(prefix+":")}
def build_inspection_plan(config: RuleConfig)->InspectionPlan:
    project=config.sections.get("PROJECT",{}); product=config.sections.get("PRODUCT",{})
    cameras={k:CameraConfig(k,str(v.get("driver","MOCK")),{x:y for x,y in v.items() if x!="driver"}) for k,v in _sections(config,"CAMERA").items()}
    triggers={k:TriggerConfig(k,str(v.get("type","SENSOR")),{x:y for x,y in v.items() if x!="type"}) for k,v in _sections(config,"TRIGGER").items()}
    encoders={k:EncoderConfig(k,bool(v.get("enabled",False)),float(v.get("units_per_pulse",1.0)),{x:y for x,y in v.items() if x not in {"enabled","units_per_pulse"}}) for k,v in _sections(config,"ENCODER").items()}
    lights={k:LightingConfig(k,str(v.get("mode","STROBE")),int(v.get("intensity",100)),int(v.get("exposure_us",5000)),float(v.get("gain",1.0)),{x:y for x,y in v.items() if x not in {"mode","intensity","exposure_us","gain"}}) for k,v in _sections(config,"LIGHT").items()}
    models={k:ModelConfig(k,str(v.get("method","")),str(v.get("adapter",v.get("method",""))),v.get("model_path"),v.get("threshold"),{x:y for x,y in v.items() if x not in {"method","adapter","model_path","threshold"}}) for k,v in _sections(config,"MODEL").items()}
    rois={k:ROIConfig(k,str(v.get("camera_id","")),int(v.get("x",0)),int(v.get("y",0)),int(v.get("width",0)),int(v.get("height",0)),{x:y for x,y in v.items() if x not in {"camera_id","x","y","width","height"}}) for k,v in _sections(config,"ROI").items()}
    regions={}
    for k,v in _sections(config,"REGION").items():
        regions[k]=RegionConfig(k,str(v.get("name",k)),str(v.get("method","")),bool(v.get("enabled",True)),str(v.get("camera_id","")),str(v.get("trigger_id","")),v.get("light_id"),str(v.get("model_id","")),str(v.get("roi_id",k)),v.get("expected_component"),v.get("expected_quantity"),v.get("min_confidence"),bool(v.get("position_check",False)),v.get("position_tolerance_px"),v.get("expected_position_x"),v.get("expected_position_y"),bool(v.get("grease_required",False)),v.get("min_coverage_percent"),v.get("max_coverage_percent"),bool(v.get("forbidden_zone_check",False)),v.get("target_zone_min_percent"))
    recheck=config.sections.get("RECHECK",{}); decision=config.sections.get("PRODUCT_DECISION",config.sections.get("INSPECTION",{})); plc=config.sections.get("PLC",{}); reject=config.sections.get("PLC_REJECT",{}); evidence=config.sections.get("EVIDENCE",config.sections.get("OUTPUT",{})); audit=config.sections.get("AUDIT",{}); motion=config.sections.get("MOTION",{}); correlation=config.sections.get("CORRELATION",{})
    plan=InspectionPlan(str(project.get("name","AI_Inspection")),str(project.get("version","1.0.0")),str(product.get("id","")),cameras,triggers,encoders,lights,models,rois,regions,RecheckConfig(bool(recheck.get("enabled",True)),int(recheck.get("max_attempts",2)),float(recheck.get("min_confidence",.70)),bool(recheck.get("multi_frame",True))),ProductDecisionConfig(str(decision.get("final_decision","ALL_REQUIRED_REGIONS_PASS")),str(decision.get("uncertain_policy","RECHECK_THEN_NG")),str(decision.get("missing_region_policy","NG"))),PLCConfig(str(plc.get("id","PLC01")),str(plc.get("driver","MOCK")),bool(reject.get("enabled",True)),str(reject.get("output","REJECT"))),EvidenceConfig(bool(evidence.get("save_evidence_image",True)),bool(evidence.get("save_raw_result",True)),bool(evidence.get("save_final_result",True))),AuditConfig(bool(audit.get("enabled",True)),str(audit.get("output_path","artifacts/audit"))),MotionConfig(float(motion.get("nominal_velocity",1.0)),float(motion.get("min_velocity",.1)),float(motion.get("max_velocity",2.0)),float(motion.get("trigger_to_camera_distance",0.0)),float(motion.get("camera_to_reject_distance",0.0)),float(motion.get("acquisition_budget_ms",100.0)),float(motion.get("ai_budget_ms",200.0)),float(motion.get("decision_budget_ms",20.0)),float(motion.get("plc_budget_ms",50.0))),CorrelationConfig(float(correlation.get("max_timestamp_delta_ms",100.0)),correlation.get("max_position_delta")))
    plan.validate(); return plan
