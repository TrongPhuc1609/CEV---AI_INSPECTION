"""Production AI runtime boundary.

Keeps vendor/model SDKs outside the inspection core. A runtime validates the
registered model manifest before inference and converts adapter output into
normalized Observation objects. No model artifact or backend is silently
substituted with a mock in production mode.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from time import perf_counter_ns
from typing import Any, Callable, Dict

from .adapters.base import VisionInput
from .adapters.factory import create_adapter
from ..models.registry import ModelRegistry
from ..models.result import Observation, Status


@dataclass(frozen=True)
class RuntimeConfig:
    model_root: str = "."
    production_mode: bool = False
    max_latency_ms: float | None = None


class AIRuntimeError(RuntimeError):
    """Raised when an AI runtime cannot safely execute inference."""


class AIRuntime:
    """Loads one configured adapter and exposes a normalized inference API."""

    def __init__(self, manifest, registry: ModelRegistry, config: RuntimeConfig | None = None,
                 model_loader: Callable[[Any], Any] | None = None):
        self.manifest = manifest
        self.registry = registry
        self.config = config or RuntimeConfig()
        self.model_loader = model_loader or self._default_loader
        self._adapter = None
        self._loaded = False
        self._load_error: str | None = None

    @staticmethod
    def _default_loader(manifest):
        raise AIRuntimeError("MODEL_BACKEND_NOT_CONFIGURED")

    def load(self) -> None:
        root = Path(self.config.model_root)
        validation = {r.model_id: r for r in self.registry.validate(root, require_artifact=self.config.production_mode)}
        result = validation.get(self.manifest.model_id)
        if result is None:
            raise AIRuntimeError("MODEL_NOT_REGISTERED")
        if not result.ok:
            raise AIRuntimeError("MODEL_VALIDATION_FAILED:" + ",".join(result.errors))
        try:
            model = self.model_loader(self.manifest)
            self._adapter = create_adapter(self.manifest.adapter, model=model)
            self._loaded = True
            self._load_error = None
        except Exception as exc:
            self._loaded = False
            self._load_error = str(exc)
            raise AIRuntimeError("MODEL_LOAD_FAILED") from exc

    @property
    def ready(self) -> bool:
        return self._loaded and self._adapter is not None

    def inspect(self, data: VisionInput) -> Observation:
        started = perf_counter_ns()
        if not self.ready:
            return Observation(
                data.product_id, data.inspection_id, data.region_id,
                self.manifest.adapter, status=Status.FAIL,
                error_code=self._load_error or "MODEL_NOT_READY",
                metadata={"frame_id": data.frame_id},
            )
        try:
            observation = self._adapter.inspect(data)
        except Exception as exc:
            return Observation(
                data.product_id, data.inspection_id, data.region_id,
                self.manifest.adapter, status=Status.FAIL,
                error_code="INFERENCE_FAILED",
                metadata={"frame_id": data.frame_id, "error": str(exc)},
            )
        latency_ms = (perf_counter_ns() - started) / 1_000_000.0
        observation.metadata = dict(observation.metadata or {})
        observation.metadata["model_id"] = self.manifest.model_id
        observation.metadata["model_version"] = self.manifest.version
        observation.metadata["inference_latency_ms"] = latency_ms
        if self.config.max_latency_ms is not None and latency_ms > self.config.max_latency_ms:
            observation.status = Status.FAIL
            observation.error_code = "AI_LATENCY_EXCEEDED"
        return observation


class AIRuntimeRegistry:
    """Caches runtimes by model id without coupling core code to model vendors."""

    def __init__(self, registry: ModelRegistry, config: RuntimeConfig | None = None,
                 model_loader: Callable[[Any], Any] | None = None):
        self.registry = registry
        self.config = config or RuntimeConfig()
        self.model_loader = model_loader
        self._runtimes: Dict[str, AIRuntime] = {}

    def get(self, model_id: str) -> AIRuntime:
        if model_id not in self._runtimes:
            manifest = self.registry.manifests.get(model_id)
            if manifest is None:
                raise AIRuntimeError("MODEL_NOT_REGISTERED")
            self._runtimes[model_id] = AIRuntime(manifest, self.registry, self.config, self.model_loader)
        return self._runtimes[model_id]
