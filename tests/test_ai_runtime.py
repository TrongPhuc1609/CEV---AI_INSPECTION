from pathlib import Path

from src.models.registry import ModelManifest, ModelRegistry
from src.models.result import Observation, Status
from src.vision.adapters.base import VisionInput
from src.vision.runtime import AIRuntime, RuntimeConfig


class FakeModel:
    def predict(self, image):
        return {"detections": [{"class": "bolt", "confidence": 0.95}]}


def registry(tmp_path: Path):
    artifact = tmp_path / "model.bin"
    artifact.write_bytes(b"model")
    import hashlib
    digest = hashlib.sha256(b"model").hexdigest()
    manifest = ModelManifest("m1", "model.bin", "1.0.0", digest, "bolt", "DETECTION", 0.8)
    return ModelRegistry({"m1": manifest})


def data():
    return VisionInput("P1", "I1", "R1", image=b"frame", frame_id="F1")


def test_runtime_blocks_unready_model(tmp_path):
    r = registry(tmp_path)
    runtime = AIRuntime(r.manifests["m1"], r, RuntimeConfig(model_root=str(tmp_path), production_mode=True))
    obs = runtime.inspect(data())
    assert obs.status is Status.FAIL
    assert obs.error_code == "MODEL_NOT_READY"


def test_runtime_loads_and_normalizes_observation(tmp_path):
    r = registry(tmp_path)
    runtime = AIRuntime(r.manifests["m1"], r, RuntimeConfig(model_root=str(tmp_path), production_mode=True), lambda _: FakeModel())
    runtime.load()
    obs = runtime.inspect(data())
    assert obs.status is Status.UNCERTAIN
    assert obs.detected_class == "bolt"
    assert obs.quantity == 1
    assert obs.metadata["model_version"] == "1.0.0"
    assert obs.metadata["inference_latency_ms"] >= 0


def test_runtime_fails_closed_on_inference_error(tmp_path):
    r = registry(tmp_path)
    runtime = AIRuntime(r.manifests["m1"], r, RuntimeConfig(model_root=str(tmp_path), production_mode=True), lambda _: object())
    runtime.load()
    obs = runtime.inspect(data())
    assert obs.status is Status.FAIL
    assert obs.error_code == "INFERENCE_FAILED"


def test_runtime_marks_latency_over_budget(tmp_path):
    r = registry(tmp_path)
    runtime = AIRuntime(r.manifests["m1"], r, RuntimeConfig(model_root=str(tmp_path), production_mode=True, max_latency_ms=0.0), lambda _: FakeModel())
    runtime.load()
    obs = runtime.inspect(data())
    assert obs.status is Status.FAIL
    assert obs.error_code == "AI_LATENCY_EXCEEDED"
