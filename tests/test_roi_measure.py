import numpy as np

from src.vision.roi_measure import RoiBox, detect_green_board_roi, measure_roi


def test_measure_roi_returns_bounded_metrics():
    image = np.zeros((100, 120, 3), dtype=np.uint8)
    image[20:80, 30:90] = (80, 140, 80)
    result = measure_roi(image, RoiBox(20, 10, 80, 80))
    assert 0 <= result.edge_density <= 1
    assert 0 <= result.foreground_ratio <= 1
    assert result.roi.width == 80
    assert result.roi.height == 80


def test_green_board_bootstrap_detector_finds_large_green_region():
    image = np.zeros((200, 300, 3), dtype=np.uint8)
    image[40:160, 60:240] = (60, 130, 60)
    roi = detect_green_board_roi(image)
    assert roi is not None
    assert roi.width >= 150
    assert roi.height >= 100
