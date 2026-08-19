from src.models.result import Observation, Status
from src.rules.engine import RuleEngine
from src.rules.parser import parse_rule_file
from src.orchestrator.orchestrator import InspectionOrchestrator
from src.production_pipeline import ProductionInspectionPipeline
from src.integration.plc import MockPLC, Decision

def _cfg(): return parse_rule_file("config/Rule.cmd")
def _det_obs(region="R01",confidence=.95,counts=None,cls="BOLT_M6",qty=4):
    counts=counts or {cls:qty}; return Observation("P","I",region,"DETECTION",detected_class=cls,confidence=confidence,quantity=qty,metadata={"class_counts":counts})
def test_rule_cmd_compiles_to_valid_typed_plan():
    plan=_cfg().to_plan(); assert plan.version=="1.0.0"; assert set(plan.required_regions())=={"R01","R02","R03","R04"}; assert plan.regions["R01"].model_id=="M01"; assert plan.regions["R02"].expected_position_x==200; assert plan.rois["R04"].camera_id=="CAM01"
def test_extra_component_is_ng_even_when_expected_count_is_correct():
    result=RuleEngine(_cfg()).evaluate(_det_obs(counts={"BOLT_M6":4,"BOLT_M8":1})); assert result.status==Status.FAIL; assert result.error_code=="EXTRA_COMPONENT"
def test_missing_component_is_ng():
    result=RuleEngine(_cfg()).evaluate(_det_obs(qty=3,counts={"BOLT_M6":3})); assert result.status==Status.FAIL; assert result.error_code=="MISSING_COMPONENT"
def test_wrong_component_is_ng():
    result=RuleEngine(_cfg()).evaluate(_det_obs(cls="BOLT_M8",qty=4,counts={"BOLT_M8":4})); assert result.status==Status.FAIL; assert result.error_code=="WRONG_COMPONENT"
def test_wrong_position_is_ng():
    obs=Observation("P","I","R02","DETECTION_CLASSIFICATION",detected_class="BOLT_M8",confidence=.96,quantity=2,position={"x":300,"y":150}); result=RuleEngine(_cfg()).evaluate(obs); assert result.status==Status.FAIL; assert result.error_code=="WRONG_POSITION"
def test_low_confidence_rechecks_with_a_new_observation():
    cfg=_cfg(); orch=InspectionOrchestrator(cfg,RuleEngine(cfg)); inspection=orch.start_product("P"); observations=[_det_obs(confidence=.50),_det_obs(confidence=.96)]; rr=orch.inspect_region(inspection,"R01",observation_provider=lambda attempt:observations[attempt-1]); assert rr.attempts==2; assert rr.status==Status.PASS; assert [o.error_code for o in rr.observations]==["LOW_CONFIDENCE",None]
def test_recheck_exhaustion_becomes_product_ng():
    cfg=_cfg(); orch=InspectionOrchestrator(cfg,RuleEngine(cfg)); inspection=orch.start_product("P"); rr=orch.inspect_region(inspection,"R01",observation_provider=lambda attempt:_det_obs(confidence=.50)); assert rr.attempts==2; assert rr.status==Status.UNCERTAIN; assert orch.final_decision(orch.complete(inspection))==Status.FAIL
def test_missing_required_region_cannot_pass():
    cfg=_cfg(); orch=InspectionOrchestrator(cfg,RuleEngine(cfg)); inspection=orch.start_product("P"); orch.inspect_region(inspection,"R01",[_det_obs()]); orch.complete(inspection); assert inspection.missing_regions; assert orch.final_decision(inspection)==Status.FAIL
def test_grease_forbidden_zone_is_ng():
    cfg=_cfg(); obs=Observation("P","I","R04","SEGMENTATION",confidence=.95,coverage_percent=80,metadata={"forbidden_zone_violation":True,"target_zone_coverage_percent":80}); result=RuleEngine(cfg).evaluate(obs); assert result.status==Status.FAIL; assert result.error_code=="GREASE_FORBIDDEN_ZONE"
def test_anomaly_threshold_is_deterministic():
    cfg=_cfg(); cfg.sections["REGION:RA"]={"enabled":True,"method":"ANOMALY_DETECTION","anomaly_threshold":.5}; result=RuleEngine(cfg).evaluate(Observation("P","I","RA","ANOMALY_DETECTION",confidence=.95,metadata={"anomaly_score":.8})); assert result.status==Status.FAIL; assert result.error_code=="ANOMALY_DETECTED"
class FullDetector:
    def predict(self,image): return {"detections":[{"class":"BOLT_M6","confidence":.95},{"class":"BOLT_M6","confidence":.94},{"class":"BOLT_M6","confidence":.93},{"class":"BOLT_M6","confidence":.92}]}
class FullClassifier:
    def predict(self,image): return {"class":"BOLT_M8","confidence":.96,"quantity":2}
class FullSegmenter:
    def predict(self,image): return {"class":"grease","confidence":.92,"coverage_percent":75,"target_zone_coverage_percent":75,"forbidden_zone_violation":False}
def test_config_driven_factory_runs_end_to_end(tmp_path):
    plc=MockPLC(); pipeline=ProductionInspectionPipeline.from_rule_file("config/Rule.cmd",{"M01":FullDetector(),"M02":FullClassifier(),"M03":FullSegmenter(),"M04":FullSegmenter()},plc=plc); pipeline.audit_store.output_path=tmp_path/"audit"; pipeline.acquisition.start()
    try: inspection=pipeline.run_product()
    finally: pipeline.acquisition.stop()
    assert inspection.final_status()==Status.PASS; assert plc.commands[-1].decision==Decision.PASS; assert list((tmp_path/"audit").glob("*.json"))
