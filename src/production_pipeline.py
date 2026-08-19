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
from .integration.motion import MotionSafetyMonitor
from .integration.release_gate import ProductionReleaseGate
from .audit.store import InspectionAuditStore


class ProductionInspectionPipeline:
    def __init__(self, acquisition, roi_manager, tracker, vision, rule_engine,
                 orchestrator, plc, config=None, audit_store=None, timing=None,
                 correlator=None, motion_monitor=None):
        self.acquisition = acquisition
        self.roi_manager = roi_manager
        self.tracker = tracker
        self.vision = vision
        self.rule_engine = rule_engine
        self.orchestrator = orchestrator
        self.plc = plc
        self.config = config or (orchestrator.config if orchestrator is not None else None)
        self.audit_store = audit_store
        self.timing = timing or TimingCollector()
        self.correlator = correlator
        self.motion_monitor = motion_monitor

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
        motion = MotionSafetyMonitor(plan.motion.nominal_velocity, plan.motion.min_velocity,
                                     plan.motion.max_velocity, plan.motion.camera_to_reject_distance)
        return cls(acquisition, rois, ProductTracker(), VisionPipeline(adapters), engine,
                   orchestrator, plc_driver, config, audit, TimingCollector(timing_budget),
                   correlator, motion)

    def start(self):
        self.acquisition.start()

    def stop(self):
        self.acquisition.stop()

    def _velocity_for_trigger(self, trigger, product_id):
        metadata = trigger.metadata or {}
        measured = metadata.get("velocity_units_per_s", metadata.get("velocity"))
        if measured is not None:
            try:
                track = self.tracker.tracks.get(product_id)
                if track:
                    track.velocity_units_per_s = float(measured)
                return float(measured), True
            except (TypeError, ValueError):
                return None, True
        track = self.tracker.tracks.get(product_id)
        measured = track.velocity_units_per_s if track else None
        if self.motion_monitor:
            return self.motion_monitor.effective_velocity(measured), False
        return measured, False

    def _motion_check(self, trigger, product_id):
        if not self.motion_monitor:
            return None
        velocity, measured = self._velocity_for_trigger(trigger, product_id)
        assessment = self.motion_monitor.assess(velocity)
        if not assessment.velocity_ok:
            return [*assessment.errors]
        return assessment

    def run_product(self):
        if not self.acquisition.started:
            self.start()
        cycle_start = monotonic()
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

        motion = self._motion_check(acquired.trigger, product_id)
        if isinstance(motion, list):
            self.plc.send(PLCCommand(Decision.NG, product_id, "NO_INSPECTION", motion))
            return None

        inspection = self.orchestrator.start_product(product_id)
        self.tracker.start(product_id, inspection.inspection_id, acquired.trigger.position, acquired.trigger.timestamp)
        if motion is not None and motion.velocity is not None:
            self.tracker.tracks[product_id].velocity_units_per_s = motion.velocity
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

        elapsed_ms = (monotonic() - cycle_start) * 1000.0
        reject_window_ms = motion.reject_window_ms if motion is not None else None
        if not MotionSafetyMonitor.within_reject_window(elapsed_ms, reject_window_ms):
            decision = Decision.NG
            reasons.append("REJECT_WINDOW_EXCEEDED")
        self.timing.measure("cycle", cycle_start, metadata={
            "product_id": product_id,
            "reject_window_ms": reject_window_ms,
            "elapsed_ms": elapsed_ms,
        })

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
