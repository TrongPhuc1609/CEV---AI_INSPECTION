from types import SimpleNamespace

from src.integration.commissioning import (
    CommissioningAcceptanceProfile,
    RealHardwareCommissioning,
    guarded_reject_test,
)
from src.integration.plc import Decision, PLCCommand


class RealCamera:
    pass


class RealTrigger:
    pass


class RecordingPLC:
    def __init__(self):
        self.commands = []

    def send(self, command):
        self.commands.append(command)


class FakePipeline:
    def __init__(self, product_ids=None):
        self.acquisition = SimpleNamespace(camera=RealCamera(), trigger=RealTrigger())
        self.plc = RecordingPLC()
        self.product_ids = iter(product_ids or ["P-001"])
        self.started = False
        self.stopped = False

    def start(self):
        self.started = True

    def stop(self):
        self.stopped = True

    def run_product(self):
        product_id = next(self.product_ids, "P-001")
        inspection = SimpleNamespace(product_id=product_id, inspection_id=f"I-{product_id}")
        self.plc.send(PLCCommand(Decision.PASS, product_id, inspection.inspection_id, []))
        return inspection


def test_preflight_rejects_mock_pipeline():
    pipeline = SimpleNamespace(
        acquisition=SimpleNamespace(camera=SimpleNamespace(__class__=type("MockCamera", (), {})), trigger=None),
        plc=SimpleNamespace(commands=[]),
    )
    # Use the actual class names used by the production adapters.
    pipeline.acquisition.camera.__class__ = type("MockCamera", (), {})
    report = RealHardwareCommissioning(pipeline, CommissioningAcceptanceProfile()).preflight()
    assert "CAMERA_IS_MOCK" in report.blockers


def test_real_commissioning_runs_bounded_samples_and_records_plc():
    pipeline = FakePipeline(["P-001", "P-001", "P-001"])
    profile = CommissioningAcceptanceProfile(sample_count=3, expected_product_id="P-001", require_pass_count=3)
    report = RealHardwareCommissioning(pipeline, profile).run()
    assert report.ready
    assert report.pass_count == 3
    assert len(pipeline.plc.commands) == 3
    assert pipeline.started and pipeline.stopped


def test_real_commissioning_blocks_unexpected_product():
    pipeline = FakePipeline(["P-001", "P-999"])
    profile = CommissioningAcceptanceProfile(sample_count=2, expected_product_id="P-001", require_pass_count=1)
    report = RealHardwareCommissioning(pipeline, profile).run()
    assert not report.ready
    assert "UNEXPECTED_PRODUCT_ID:P-999" in report.blockers


def test_guarded_reject_test_sends_ng():
    plc = RecordingPLC()
    command = guarded_reject_test(plc, "P-001", "I-001")
    assert command.decision == Decision.NG
    assert plc.commands[-1] is command
    assert command.reasons == ["COMMISSIONING_REJECT_TEST"]
