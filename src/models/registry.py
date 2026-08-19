"""Model lifecycle metadata and validation for commissioning/release gates."""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Dict, Optional


@dataclass(frozen=True)
class ModelManifest:
    model_id: str
    path: Optional[str]
    version: Optional[str]
    checksum_sha256: Optional[str]
    class_map: Optional[str]
    adapter: str
    threshold: Optional[float]


@dataclass(frozen=True)
class ModelValidation:
    model_id: str
    ok: bool
    errors: tuple[str, ...] = ()


class ModelRegistry:
    """Compiles model metadata from InspectionPlan without loading vendor SDKs."""
    def __init__(self, manifests: Dict[str, ModelManifest]):
        self.manifests = manifests

    @classmethod
    def from_plan(cls, plan):
        manifests = {}
        for model_id, cfg in plan.models.items():
            settings = cfg.settings
            manifests[model_id] = ModelManifest(
                model_id, cfg.model_path,
                settings.get("model_version"),
                settings.get("checksum_sha256"),
                settings.get("class_map"),
                cfg.adapter, cfg.threshold,
            )
        return cls(manifests)

    def validate(self, model_root: str | Path = ".", require_artifact: bool = False) -> list[ModelValidation]:
        root = Path(model_root)
        results = []
        for manifest in self.manifests.values():
            errors = []
            if not manifest.path:
                errors.append("MODEL_PATH_MISSING")
            if require_artifact and manifest.path:
                path = root / manifest.path
                if not path.exists():
                    errors.append("MODEL_ARTIFACT_MISSING")
                elif manifest.checksum_sha256:
                    digest = sha256(path.read_bytes()).hexdigest()
                    if digest.lower() != str(manifest.checksum_sha256).lower():
                        errors.append("MODEL_CHECKSUM_MISMATCH")
                else:
                    errors.append("MODEL_CHECKSUM_MISSING")
            if require_artifact and not manifest.version:
                errors.append("MODEL_VERSION_MISSING")
            if require_artifact and not manifest.class_map:
                errors.append("MODEL_CLASS_MAP_MISSING")
            if manifest.threshold is None:
                errors.append("MODEL_THRESHOLD_MISSING")
            results.append(ModelValidation(manifest.model_id, not errors, tuple(errors)))
        return results

    def production_ready(self, model_root: str | Path = ".") -> bool:
        return all(result.ok for result in self.validate(model_root, require_artifact=True))
