"""Component classification adapter."""
from typing import Any
from .base import VisionAdapter, VisionInput
from ...models.result import Observation

class ClassificationAdapter(VisionAdapter):
    method="DETECTION_CLASSIFICATION"
    def __init__(self, model:Any=None): self.model=model
    def inspect(self,data:VisionInput)->Observation:
        if self.model is None: raise RuntimeError("ClassificationAdapter requires a classifier model")
        raw=self.model.predict(data.image)
        return Observation(data.product_id,data.inspection_id,data.region_id,self.method,detected_class=raw.get("class"),confidence=raw.get("confidence"),quantity=raw.get("quantity",1),position=raw.get("position"),metadata={"frame_id":data.frame_id,"raw":raw})
