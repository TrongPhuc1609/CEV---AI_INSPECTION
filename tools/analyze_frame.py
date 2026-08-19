"""Basic real-camera image quality characterization for Physical Vision Trial V1."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np


def analyze(path: Path) -> dict:
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"cannot read image: {path}")
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    brightness = float(np.mean(gray))
    contrast = float(np.std(gray))
    laplacian_variance = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    saturation_mean = float(np.mean(hsv[:, :, 1]))
    saturation_high_fraction = float(np.mean(hsv[:, :, 1] >= 245))
    return {
        "image": str(path),
        "width": int(image.shape[1]),
        "height": int(image.shape[0]),
        "brightness_mean_0_255": round(brightness, 2),
        "contrast_stddev": round(contrast, 2),
        "focus_laplacian_variance": round(laplacian_variance, 2),
        "saturation_mean_0_255": round(saturation_mean, 2),
        "high_saturation_fraction": round(saturation_high_fraction, 5),
        "note": "Metrics are diagnostic only; acceptance thresholds must be commissioned from real PCB images.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("image")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = analyze(Path(args.image))
    print(json.dumps(result, indent=2) if args.json else "\n".join(f"{k}: {v}" for k, v in result.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
