import time

from src.integration.plc import Decision, MockPLC
from src.machine_vision.acquisition.service import ImageAcquisition
from src.machine_vision.camera.base import Camera, Frame
from src.machine_vision.correlation import TriggerFrameCorrelator
from src.machine_vision.trigger.base import TriggerEvent, TriggerSource, TriggerType
from src.production_pipeline import ProductionInspectionPipeline


class WrongProductCamera(Camera):
    def open(self): pass
    def close(self): pass
    def configure(self, **settings): pass
    def capture(self):
        return Frame("F1", "image", time.time(), "CAM01", {"product_id": "P2"})


class ProductTrigger(TriggerSource):
    def wait(self):
        return TriggerEvent("T1", TriggerType.SENSOR, time.time(), "P1", 1.0, {})


def test_pipeline_rejects_uncorrelated_frame_before_vision():
    acquisition = ImageAcquisition(WrongProductCamera(), ProductTrigger())
    plc = MockPLC()
    pipeline = ProductionInspectionPipeline(
        acquisition, None, None, None, None, None, plc,
        correlator=TriggerFrameCorrelator(100.0),
    )
    assert pipeline.run_product() is None
    assert plc.commands[-1].decision == Decision.NG
    assert any("FRAME_CORRELATION_ERROR" in reason for reason in plc.commands[-1].reasons)
