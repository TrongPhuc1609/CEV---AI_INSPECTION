"""Config-driven end-to-end inspection pipeline."""
from time import monotonic

from .machine_vision.lighting.controller import LightingProfile
from .machine_vision.acquisition.service import ImageAcquisition
from .machine_vision.correlation import TriggerFrameCorrelator
from .machine_vision.roi.manager import ROI, ROIManager
from .machine_vision.tracking.tracker import ProductTracker
from .vision.pipeline.pipeline import VisionPipeline
from .vision.adapters.detection import DetectionAdapter
from .vision.adapters.classification import ClassificationAdapter
from .vision.adapters.segmentation import SegmentationAdapter
from .vision.adapters.anomaly import AnomalyDetectionAdapter
from .rules.engine import RuleEngine
from .rules.parser import parse_rule_file
from .orchestrator.orchestrator import InspectionOrchestrator
from .models.result import Status, Observation
from .integration.plc import PLCCommand, Decision
from .integration.hardware_adapters import HardwareFactory, MockHardwareFactory
from .integration.timing import TimingBudget, TimingCollector
from .integration.release_gate import ProductionReleaseGate
from .audit.store import InspectionAuditStore


class ProductionInspectionPipeline:
    def __init__(self, acquisition, roi_manager, tracker, vision, rule_engine,
                 orchestrator, plc, config=None, audit_store=None, timing=None,
                 correlator=None):
        self.acquisition = acquisition
        self.roi_manager = roi_manager
        self.tracker = tracker
        self.vision = vision
        self.rule_engine = rule_engine
        self.orchestrator = orchestrator
        self.plc = plc
        self.config = config or orchestrator.config
        self.audit_store = audit_store
        self.timing = timing or TimingCollector()
        self.correlator = correlator

    @classmethod
    def from_rule_file(cls, rule_path, model_registry, plc=None,
                       hardware_factory: HardwareFactory | None = None,
                       timing_budget: TimingBudget | None = None,
                       production_mode: bool = False, model_root: str = "."):
        config = parse_rule_file(rule_path)
        plan = config.to_plan()
        if not plan.cameras or not plan.triggers:
            raise ValueError("Rule.cmd must define at least one camera and trigger")
        if production_mode:
            gate = ProductionReleaseGate().validate(plan, model_root=model_root, real_hardware=True, require_models=True)
            if not gate.ready:
                raise RuntimeError("Production release gate failed: " + "; ".join(gate.errors))

        hardware = hardware_factory or MockHardwareFactory()
        camera_cfg = next(iter(plan.cameras.values()))
        trigger_cfg = next(iter(plan.triggers.values()))
        camera = hardware.camera(camera_cfg)
        camera.configure(**camera_cfg.settings)
        trigger = hardware.trigger(trigger_cfg)
        light = None
        profile = None
        if plan.lights:
            light_cfg = next(iter(plan.lights.values()))
            light = hardware.lighting(light_cfg)
            if light:
                profile = LightingProfile(light_cfg.light_id, light_cfg.mode, light_cfg.intensity,
                                          light_cfg.exposure_us, light_cfg.gain, light_cfg.parameters)

        acquisition = ImageAcquisition(camera, trigger, light, profile)
        rois = ROIManager([ROI(r.roi_id, r.x, r.y, r.width, r.height, r.camera_id, r.settings)
                           for r in plan.rois.values()])
        adapters = {}
        adapter_types = {
            "DETECTION": DetectionAdapter,
            "DETECTION_CLASSIFICATION": ClassificationAdapter,
            "SEGMENTATION": SegmentationAdapter,
            "ANOMALY_DETECTION": AnomalyDetectionAdapter,
        }
        for region in plan.regions.values():
            model = model_registry.get(region.model_id)
            if model is None:
                raise ValueError(f"No model supplied for {region.model_id} ({region.region_id})")
            model_cfg = plan.models[region.model_id]
            adapter_cls = adapter_types.get(model_cfg.adapter)
            if adapter_cls is None:
                raise ValueError(f"Unsupported adapter: {model_cfg.adapter}")
            adapters[region.region_id] = (adapter_cls(model, float(model_cfg.threshold or .5))
                                          if adapter_cls is AnomalyDetectionAdapter else adapter_cls(model))

        engine = RuleEngine(config)
        orchestrator = InspectionOrchestrator(config, engine)
        plc_driver = plc or hardware.plc(plan.plc)
        audit = InspectionAuditStore(plan.audit.output_path) if plan.audit.enabled else None
        correlator = TriggerFrameCorrelator(plan.correlation.max_timestamp_delta_ms,
                                            plan.correlation.max_position_delta)
        return cls(acquisition, rois, ProductTracker(), VisionPipeline(adapters), engine,
                   orchestrator, plc_driver, config, audit, TimingCollector(timing_budget),
                   correlator)

    def start(self):
        self.acquisition.start()

    def stop(self):
        self.acquisition.stop()

    def run_product(self):
        if not self.acquisition.started:
            self.start()
        try:
            acquisition_start = monotonic()
            acquired = self.acquisition.acquire()
            self.timing.measure("acquisition", acquisition_start, metadata={"frame_id": acquired.frame.frame_id})
            if self.correlator:
                correlation = self.correlator.correlate(acquired.trigger, acquired.frame)
                if not correlation.matched:
                    raise RuntimeError("FRAME_CORRELATION_ERROR:" + correlation.reason)
        except Exception as exc:
            self.plc.send(PLCCommand(Decision.NG, "UNKNOWN", "NO_INSPECTION", ["ACQUISITION_ERROR", str(exc)]))
            return None

        product_id = acquired.trigger.product_id
        if not product_id:
            self.plc.send(PLCCommand(Decision.NG, "UNKNOWN", "NO_INSPECTION", ["TRIGGER_NO_PRODUCT_ID"]))
            return None

        inspection = self.orchestrator.start_product(product_id)
        self.tracker.start(product_id, inspection.inspection_id, acquired.trigger.position, acquired.trigger.timestamp)
        for region_id in self.orchestrator.required_regions():
            try:
                self._inspect_region(inspection, product_id, region_id, acquired)
                self.tracker.mark_region(product_id, region_id)
            except Exception as exc:
                self.orchestrator.inspect_region(
                    inspection, region_id,
                    observations=[Observation(product_id, inspection.inspection_id, region_id, "SYSTEM",
                                               status=Status.FAIL, error_code="INSPECTION_ERROR",
                                               metadata={"exception": str(exc)})])

        decision_start = monotonic()
        self.orchestrator.complete(inspection)
        status = self.orchestrator.final_decision(inspection)
        self.timing.measure("decision", decision_start)
        decision = Decision.PASS if status == Status.PASS else Decision.NG
        reasons = [r.final_observation.error_code for r in inspection.regions.values()
                   if r.final_observation and r.final_observation.error_code]
        if inspection.missing_regions:
            reasons.extend("MISSING_REGION:" + r for r in inspection.missing_regions)

        command = PLCCommand(decision, product_id, inspection.inspection_id, reasons)
        plc_start = monotonic()
        self.plc.send(command)
        self.timing.measure("plc", plc_start)
        if self.audit_store:
            self.audit_store.write(inspection, command)
        return inspection

    def _inspect_region(self, inspection, product_id, region_id, first_acquired):
        def provider(attempt):
            acquired = first_acquired if attempt == 1 else self.acquisition.acquire()
            if acquired.trigger.product_id and acquired.trigger.product_id != product_id:
                raise RuntimeError("TRIGGER_PRODUCT_MISMATCH")
            if self.correlator:
                correlation = self.correlator.correlate(acquired.trigger, acquired.frame)
                if not correlation.matched:
                    raise RuntimeError("FRAME_CORRELATION_ERROR:" + correlation.reason)
            frame = acquired.frame
            self.tracker.update(product_id, acquired.trigger.position, acquired.trigger.timestamp)
            roi = self.roi_manager.get(region_id)
            ai_start = monotonic()
            result = self.vision.inspect(product_id, inspection.inspection_id, region_id,
                                         roi.crop(frame.image), frame.frame_id)
            self.timing.measure("ai", ai_start, metadata={"region_id": region_id, "attempt": attempt})
            return result
        return self.orchestrator.inspect_region(inspection, region_id, observation_provider=provider)
