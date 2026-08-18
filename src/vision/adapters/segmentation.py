"""Segmentation adapter for grease/oil or other visible material."""
from typing import Any
from .base import VisionAdapter, VisionInput
from ...models.result import Observation

class SegmentationAdapter(VisionAdapter):
    method="SEGMENTATION"
    def __init__(self, model:Any=None): self.model=model
    def inspect(self,data:VisionInput)->Observation:
        if self.model is None: raise RuntimeError("SegmentationAdapter requires a segmentation model")
        raw=self.model.predict(data.image)
        return Observation(data.product_id,data.inspection_id,data.region_id,self.method,detected_class=raw.get("class","grease"),confidence=raw.get("confidence"),coverage_percent=raw.get("coverage_percent"),metadata={"frame_id":data.frame_id,"raw":raw,"mask":raw.get("mask")})
