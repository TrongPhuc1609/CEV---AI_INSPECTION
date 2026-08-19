"""Typed, validated inspection configuration built from Rule.cmd."""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

@dataclass(frozen=True)
class CameraConfig: camera_id:str; driver:str="MOCK"; settings:Dict[str,Any]=field(default_factory=dict)
@dataclass(frozen=True)
class TriggerConfig: trigger_id:str; trigger_type:str="SENSOR"; settings:Dict[str,Any]=field(default_factory=dict)
@dataclass(frozen=True)
class EncoderConfig: encoder_id:str; enabled:bool=False; units_per_pulse:float=1.0; settings:Dict[str,Any]=field(default_factory=dict)
@dataclass(frozen=True)
class LightingConfig: light_id:str; mode:str="STROBE"; intensity:int=100; exposure_us:int=5000; gain:float=1.0; parameters:Dict[str,Any]=field(default_factory=dict)
@dataclass(frozen=True)
class ModelConfig: model_id:str; method:str; adapter:str; model_path:Optional[str]=None; threshold:Optional[float]=None; settings:Dict[str,Any]=field(default_factory=dict)
@dataclass(frozen=True)
class ROIConfig: roi_id:str; camera_id:str; x:int; y:int; width:int; height:int; settings:Dict[str,Any]=field(default_factory=dict)
@dataclass(frozen=True)
class RecheckConfig: enabled:bool=True; max_attempts:int=2; min_confidence:float=.70; multi_frame:bool=True
@dataclass(frozen=True)
class MotionConfig:
    nominal_velocity:float=1.0; min_velocity:float=.1; max_velocity:float=2.0
    trigger_to_camera_distance:float=0.0; camera_to_reject_distance:float=0.0
    acquisition_budget_ms:float=100.0; ai_budget_ms:float=200.0; decision_budget_ms:float=20.0; plc_budget_ms:float=50.0
@dataclass(frozen=True)
class CorrelationConfig:
    max_timestamp_delta_ms:float=100.0; max_position_delta:Optional[float]=None
@dataclass(frozen=True)
class RegionConfig:
    region_id:str; name:str; method:str; enabled:bool; camera_id:str; trigger_id:str; light_id:Optional[str]; model_id:str; roi_id:str
    expected_component:Optional[str]=None; expected_quantity:Optional[int]=None; min_confidence:Optional[float]=None
    position_check:bool=False; position_tolerance_px:Optional[float]=None; expected_position_x:Optional[float]=None; expected_position_y:Optional[float]=None
    grease_required:bool=False; min_coverage_percent:Optional[float]=None; max_coverage_percent:Optional[float]=None; forbidden_zone_check:bool=False; target_zone_min_percent:Optional[float]=None
@dataclass(frozen=True)
class ProductDecisionConfig: final_decision:str="ALL_REQUIRED_REGIONS_PASS"; uncertain_policy:str="RECHECK_THEN_NG"; missing_region_policy:str="NG"
@dataclass(frozen=True)
class PLCConfig: plc_id:str; driver:str="MOCK"; reject_enabled:bool=True; reject_output:str="REJECT"
@dataclass(frozen=True)
class EvidenceConfig: save_evidence_image:bool=True; save_raw_result:bool=True; save_final_result:bool=True
@dataclass(frozen=True)
class AuditConfig: enabled:bool=True; output_path:str="artifacts/audit"
@dataclass(frozen=True)
class InspectionPlan:
    project_name:str; version:str; product_id:str; cameras:Dict[str,CameraConfig]; triggers:Dict[str,TriggerConfig]; encoders:Dict[str,EncoderConfig]; lights:Dict[str,LightingConfig]; models:Dict[str,ModelConfig]; rois:Dict[str,ROIConfig]; regions:Dict[str,RegionConfig]; recheck:RecheckConfig; product_decision:ProductDecisionConfig; plc:PLCConfig; evidence:EvidenceConfig; audit:AuditConfig; motion:MotionConfig=field(default_factory=MotionConfig); correlation:CorrelationConfig=field(default_factory=CorrelationConfig)
    def required_regions(self)->List[str]: return [r.region_id for r in self.regions.values() if r.enabled]
    def validate(self)->None:
        errors=[]
        if not self.cameras:errors.append("No cameras configured")
        if not self.triggers:errors.append("No triggers configured")
        if not self.regions:errors.append("No regions configured")
        if self.motion.nominal_velocity<=0:errors.append("MOTION nominal_velocity must be > 0")
        if self.motion.min_velocity<=0:errors.append("MOTION min_velocity must be > 0")
        if self.motion.max_velocity<self.motion.min_velocity:errors.append("MOTION max_velocity must be >= min_velocity")
        if not self.motion.min_velocity<=self.motion.nominal_velocity<=self.motion.max_velocity:errors.append("MOTION nominal_velocity must be within min/max velocity")
        if self.correlation.max_timestamp_delta_ms<0:errors.append("CORRELATION max_timestamp_delta_ms must be >= 0")
        if self.correlation.max_position_delta is not None and self.correlation.max_position_delta<0:errors.append("CORRELATION max_position_delta must be >= 0")
        for region in self.regions.values():
            if region.camera_id not in self.cameras:errors.append(f"{region.region_id}: unknown camera {region.camera_id}")
            if region.trigger_id not in self.triggers:errors.append(f"{region.region_id}: unknown trigger {region.trigger_id}")
            if region.light_id and region.light_id not in self.lights:errors.append(f"{region.region_id}: unknown light {region.light_id}")
            if region.model_id not in self.models:errors.append(f"{region.region_id}: unknown model {region.model_id}")
            if region.roi_id not in self.rois:errors.append(f"{region.region_id}: unknown ROI {region.roi_id}")
            elif self.rois[region.roi_id].camera_id!=region.camera_id:errors.append(f"{region.region_id}: ROI camera mismatch")
            if region.model_id in self.models and region.method!=self.models[region.model_id].method:errors.append(f"{region.region_id}: method/model mismatch")
            if region.position_check and region.position_tolerance_px is not None and (region.expected_position_x is None or region.expected_position_y is None):errors.append(f"{region.region_id}: expected position required when position_check=true")
        if self.recheck.max_attempts<1:errors.append("RECHECK max_attempts must be >= 1")
        if self.product_decision.uncertain_policy not in {"RECHECK_THEN_NG","NG","PASS"}:errors.append("Unsupported uncertain_policy")
        if self.product_decision.missing_region_policy not in {"NG","UNCERTAIN"}:errors.append("Unsupported missing_region_policy")
        if errors:raise ValueError("Invalid InspectionPlan: "+"; ".join(errors))
