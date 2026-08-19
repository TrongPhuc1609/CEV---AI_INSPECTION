from src.machine_vision.camera.base import MockCamera
from src.machine_vision.trigger.base import MockTrigger
from src.machine_vision.lighting.controller import LightingController, LightingProfile
from src.machine_vision.acquisition.service import ImageAcquisition
from src.machine_vision.roi.manager import ROI, ROIManager
from src.machine_vision.tracking.tracker import ProductTracker
from src.integration.plc import MockPLC, Decision
from src.vision.adapters.detection import DetectionAdapter
from src.vision.adapters.classification import ClassificationAdapter
from src.vision.adapters.segmentation import SegmentationAdapter
from src.vision.pipeline.pipeline import VisionPipeline
from src.rules.parser import parse_rule_file
from src.rules.engine import RuleEngine
from src.orchestrator.orchestrator import InspectionOrchestrator
from src.production_pipeline import ProductionInspectionPipeline
class Detector:
    def predict(self,image): return {"detections":[{"class":"BOLT_M6","confidence":.95},{"class":"BOLT_M6","confidence":.94},{"class":"BOLT_M6","confidence":.93},{"class":"BOLT_M6","confidence":.92}]}
class Classifier:
    def predict(self,image): return {"class":"BOLT_M8","confidence":.96,"quantity":2}
class Segmenter:
    def predict(self,image): return {"class":"grease","confidence":.92,"coverage_percent":75,"target_zone_coverage_percent":75,"forbidden_zone_violation":False}
def test_acquisition_trigger_camera():
    cam=MockCamera();trig=MockTrigger();light=LightingController();acq=ImageAcquisition(cam,trig,light,LightingProfile("L1"));acq.start();result=acq.acquire();acq.stop(); assert result.trigger.product_id=="PRODUCT-1"; assert result.frame.frame_id=="CAM01-F1"; assert light.current().profile_id=="L1"
def test_tracker():
    tracker=ProductTracker();t=tracker.start("P1","I1",10.0);tracker.update("P1",10.5);tracker.mark_region("P1","R01"); assert t.last_position==10.5; assert t.frames_seen==1; assert t.region_frames["R01"]==1
def test_roi():
    roi=ROI("R01",1,2,10,10); assert roi.crop("img")["roi"]==(1,2,10,10)
def test_full_pipeline_pass():
    cfg=parse_rule_file("config/Rule.cmd");engine=RuleEngine(cfg);orch=InspectionOrchestrator(cfg,engine);vision=VisionPipeline({"R01":DetectionAdapter(Detector()),"R02":ClassificationAdapter(Classifier()),"R03":SegmentationAdapter(Segmenter()),"R04":SegmentationAdapter(Segmenter())});rois=ROIManager([ROI("R01",0,0,10,10),ROI("R02",0,0,10,10),ROI("R03",0,0,10,10),ROI("R04",0,0,10,10)]);acq=ImageAcquisition(MockCamera(),MockTrigger());acq.start();plc=MockPLC();pipe=ProductionInspectionPipeline(acq,rois,ProductTracker(),vision,engine,orch,plc);inspection=pipe.run_product();acq.stop(); assert inspection.final_status().value=="PASS"; assert plc.commands[-1].decision==Decision.PASS
