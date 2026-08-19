"""Capture a real USB camera frame for Physical Vision Trial V1.

Usage:
    python tools/capture_camera.py --camera 0 --output data/physical_trial

Press SPACE to save a frame, Q/ESC to quit. The capture is intentionally
camera-only: no AI decision is made here. Each saved frame gets a JSON sidecar
with camera index, resolution and timestamp for later replay/inspection.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import cv2


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--camera", type=int, default=0)
    parser.add_argument("--output", default="data/physical_trial")
    parser.add_argument("--width", type=int, default=0)
    parser.add_argument("--height", type=int, default=0)
    args = parser.parse_args()

    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(args.camera, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap.release()
        cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        print(f"ERROR: cannot open camera index {args.camera}")
        return 2

    if args.width:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    if args.height:
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)

    actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"Camera {args.camera}: {actual_width}x{actual_height}")
    print("SPACE = save frame | Q/ESC = quit")

    saved = 0
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                print("ERROR: camera frame acquisition failed")
                return 3
            cv2.imshow("AI Inspection - Physical Vision Trial V1", frame)
            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), 27):
                break
            if key == 32:
                ts_ns = time.time_ns()
                stem = f"frame_{ts_ns}"
                image_path = output / f"{stem}.jpg"
                meta_path = output / f"{stem}.json"
                if not cv2.imwrite(str(image_path), frame):
                    print(f"ERROR: failed to save {image_path}")
                    continue
                metadata = {
                    "frame_id": stem,
                    "timestamp_ns": ts_ns,
                    "camera_index": args.camera,
                    "width": actual_width,
                    "height": actual_height,
                    "source": "real_usb_camera",
                }
                meta_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
                saved += 1
                print(f"SAVED: {image_path}")
    finally:
        cap.release()
        cv2.destroyAllWindows()

    print(f"Capture complete. Saved frames: {saved}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
