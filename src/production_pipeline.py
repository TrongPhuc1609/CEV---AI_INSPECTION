"""End-to-end production-oriented inspection pipeline.
Camera -> Orchestrator -> Vision Adapter -> Rule Engine -> PLC/Reject
"""
from .machine_vision.acquisition.service import ImageAcquisition
from .machine_vision.roi.manager import ROIManager
from .machine_vision.tracking.tracker import ProductTracker
from .vision.pipeline.pipeline import VisionPipeline
from .rules.engine import RuleEngine
from .orchestrator.orchestrator import InspectionOrchestrator
from .models.result import Status
from .integration.plc import PLCCommand, Decision, PLCInterface

class ProductionInspectionPipeline:
    def __init__(self, acquisition:ImageAcquisition, roi_manager:ROIManager, tracker:ProductTracker, vision:VisionPipeline, rule_engine:RuleEngine, orchestrator:InspectionOrchestrator, plc:PLCInterface):
        self.acquisition=acquisition; self.roi_manager=roi_manager; self.tracker=tracker; self.vision=vision; self.rule_engine=rule_engine; self.orchestrator=orchestrator; self.plc=plc
    def run_product(self):
        acquired=self.acquisition.acquire(); product_id=acquired.trigger.product_id
        if not product_id: raise RuntimeError("Trigger did not provide product_id")
        inspection=self.orchestrator.start_product(product_id)
        self.tracker.start(product_id,inspection.inspection_id,acquired.trigger.position)
        for region_id in self.orchestrator.required_regions():
            roi=self.roi_manager.get(region_id); roi_image=roi.crop(acquired.frame.image)
            obs=self.vision.inspect(product_id,inspection.inspection_id,region_id,roi_image,acquired.frame.frame_id)
            self.tracker.mark_region(product_id,region_id)
            self.orchestrator.inspect_region(inspection,region_id,[obs])
        self.orchestrator.complete(inspection); status=self.orchestrator.final_decision(inspection)
        decision=Decision.PASS if status==Status.PASS else Decision.NG if status==Status.FAIL else Decision.UNCERTAIN
        reasons=[r.final_observation.error_code for r in inspection.regions.values() if r.final_observation and r.final_observation.error_code]
        self.plc.send(PLCCommand(decision,product_id,inspection.inspection_id,reasons))
        return inspection
