from src.integration.hardware_adapters import CallbackCamera, CallbackTrigger, CallbackPLC, MockHardwareFactory
from src.integration.hil import HILRunner, HILScenario
from src.integration.plc import Decision, PLCCommand
from src.integration.timing import TimingBudget, TimingCollector
from src.machine_vision.camera.base import Frame
from src.machine_vision.trigger.base import TriggerEvent, TriggerType
from src.production_pipeline import ProductionInspectionPipeline


class FullDetector:
    def predict(self, image):
        return {"detections": [
            {"class": "BOLT_M6", "confidence": .95},
            {"class": "BOLT_M6", "confidence": .94},
            {"class": "BOLT_M6", "confidence": .93},
            {"class": "BOLT_M6", "confidence": .92},
        ]}


class FullClassifier:
    def predict(self, image):
        return {"class": "BOLT_M8", "confidence": .96, "quantity": 2}


class FullSegmenter:
    def predict(self, image):
        return {"class": "grease", "confidence": .92, "coverage_percent": 75,
                "target_zone_coverage_percent": 75, "forbidden_zone_violation": False}


def models():
    return {"M01": FullDetector(), "M02": FullClassifier(),
            "M03": FullSegmenter(), "M04": FullSegmenter()}


def test_pipeline_auto_starts_and_records_timing(tmp_path):
    pipeline = ProductionInspectionPipeline.from_rule_file("config/Rule.cmd", models())
    pipeline.audit_store.output_path = tmp_path / "audit"
    inspection = pipeline.run_product()
    assert inspection is not None
    assert pipeline.plc.commands[-1].decision == Decision.PASS
    assert pipeline.timing.last("acquisition") is not None
    assert pipeline.timing.last("ai") is not None
    assert pipeline.timing.last("decision") is not None
    assert pipeline.timing.last("plc") is not None
    pipeline.stop()


def test_timing_budget_is_deterministic():
    collector = TimingCollector(TimingBudget(acquisition_max_ms=1))
    start = collector.start()
    collector.measure("acquisition", start, start + .002)
    assert collector.exceeds("acquisition")
    assert collector.summary()["budget_ms"]["inspection_max"] > 0


def test_callback_hardware_adapters_preserve_contracts():
    calls = []
    camera = CallbackCamera(
        "CAM01", lambda: calls.append("open"), lambda: calls.append("close"),
        lambda frame_id, settings: {"frame_id": frame_id, "settings": settings})
    camera.configure(exposure_us=5000)
    camera.open()
    frame = camera.capture()
    camera.close()
    assert isinstance(frame, Frame)
    assert frame.frame_id == "CAM01-F1"
    assert calls == ["open", "close"]

    trigger = CallbackTrigger(lambda: TriggerEvent("T1", TriggerType.SENSOR, 1.0, "P1", 10.0, {}))
    assert trigger.wait().product_id == "P1"

    sent = []
    plc = CallbackPLC(sent.append)
    command = PLCCommand(Decision.NG, "P1", "I1", ["TEST"])
    plc.send(command)
    assert sent == [command]
    assert plc.commands == [command]


def test_mock_hardware_factory_is_replaceable():
    factory = MockHardwareFactory()
    config = __import__("src.rules.parser", fromlist=["parse_rule_file"]).parse_rule_file("config/Rule.cmd").to_plan()
    assert factory.camera(next(iter(config.cameras.values()))).__class__.__name__ == "MockCamera"
    assert factory.trigger(next(iter(config.triggers.values()))).__class__.__name__ == "MockTrigger"


def test_hil_runner_passes_reference_scenario(tmp_path):
    def make_pipeline(scenario):
        pipeline = ProductionInspectionPipeline.from_rule_file("config/Rule.cmd", models())
        pipeline.audit_store.output_path = tmp_path / scenario.name
        return pipeline

    result = HILRunner(make_pipeline).run(HILScenario("nominal-pass", Decision.PASS))
    assert result.passed
    assert result.actual_decision == Decision.PASS
    assert result.timing["samples"]
