from src.machine_vision.acquisition.frame_contract import AcquiredFrame, AcquisitionHealth


def test_acquired_frame_contract_requires_identity_and_timestamp():
    frame = AcquiredFrame("F1", "P1", 1, object(), "CAM01", "TRG01")
    assert frame.is_valid()


def test_invalid_frame_is_not_pipeline_eligible():
    frame = AcquiredFrame("", "P1", 1, object(), "CAM01")
    assert not frame.is_valid()


def test_acquisition_health_is_fail_closed():
    assert AcquisitionHealth(True, True, True, True).commissioning_ready
    assert not AcquisitionHealth(True, True, False, True).commissioning_ready
    assert not AcquisitionHealth(False, True, True, True).commissioning_ready
