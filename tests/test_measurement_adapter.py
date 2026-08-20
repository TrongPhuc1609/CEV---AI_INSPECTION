import numpy as np

from src.machine_vision.measurement_adapter import MeasurementAdapter
from src.models.result import Status
from src.vision.adapters.base import VisionInput
from src.vision.roi_measure import RoiBox


def test_measurement_adapter_returns_normalized_observation():
    image = np.zeros((100, 120, 3), dtype=np.uint8)
    image[20:80, 30:90] = (0, 180, 0)

    adapter = MeasurementAdapter(RoiBox(30, 20, 60, 60))
    observation = adapter.inspect(
        VisionInput("P1", "I1", "R01", image, "F1")
    )

    assert observation.method == "MACHINE_VISION_MEASUREMENT"
    assert observation.status == Status.UNCERTAIN
    assert observation.metadata["source"] == "real_image_pixels"
    measurement = observation.metadata["measurement"]
    assert measurement["roi"] == {"x": 30, "y": 20, "width": 60, "height": 60}
    assert 0.0 <= measurement["edge_density"] <= 1.0
    assert 0.0 <= measurement["foreground_ratio"] <= 1.0


def test_measurement_adapter_requires_roi():
    image = np.zeros((20, 20, 3), dtype=np.uint8)
    adapter = MeasurementAdapter()

    try:
        adapter.inspect(VisionInput("P1", "I1", "R01", image, "F1"))
    except ValueError as exc:
        assert str(exc) == "MACHINE_VISION_ROI_REQUIRED"
    else:
        raise AssertionError("Expected missing ROI to be rejected")
