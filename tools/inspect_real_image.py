"""Inspect a real image with deterministic pixel measurements.

Usage:
  python tools/inspect_real_image.py path/to/frame.jpg
  python tools/inspect_real_image.py path/to/frame.jpg --roi 100 100 400 300
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2

from src.vision.roi_measure import RoiBox, detect_green_board_roi, measure_roi


def main() -> int:
    parser = argparse.ArgumentParser(description="Measure a real PCB image ROI")
    parser.add_argument("image", type=Path)
    parser.add_argument("--roi", nargs=4, type=int, metavar=("X", "Y", "W", "H"))
    args = parser.parse_args()

    image_path = args.image.resolve()
    if not image_path.is_file():
        print(json.dumps({"status": "ERROR", "error": "IMAGE_NOT_FOUND", "path": str(image_path)}, indent=2))
        return 2

    image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
    if image is None:
        print(json.dumps({"status": "ERROR", "error": "IMAGE_DECODE_FAILED", "path": str(image_path)}, indent=2))
        return 2

    roi = RoiBox(*args.roi) if args.roi else detect_green_board_roi(image)
    if roi is None:
        print(json.dumps({"status": "ERROR", "error": "BOARD_ROI_NOT_FOUND"}, indent=2))
        return 3

    measurement = measure_roi(image, roi)
    output = {
        "status": "OK",
        "image": str(image_path),
        "image_shape": {"height": int(image.shape[0]), "width": int(image.shape[1]), "channels": int(image.shape[2])},
        "roi_source": "manual" if args.roi else "bootstrap_green_board_detector",
        "measurement": measurement.to_dict(),
        "commissioning_note": "Measurements are evidence only; no production threshold is inferred automatically.",
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
