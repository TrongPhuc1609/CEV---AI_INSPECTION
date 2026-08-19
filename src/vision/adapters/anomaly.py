"""Anomaly detection adapter."""
from typing import Any
from .base import VisionAdapter, VisionInput
from ...models.result import Observation
class AnomalyDetectionAdapter(VisionAdapter):
    method="ANOMALY_DETECTION"
    def __init__(self,model:Any=None,anomaly_threshold:float=0.5): self.model=model; self.anomaly_threshold=anomaly_threshold
    def inspect(self,data:VisionInput)->Observation:
        if self.model is None: raise RuntimeError("AnomalyDetectionAdapter requires an anomaly model")
        raw=self.model.predict(data.image); score=float(raw.get("anomaly_score",0.0))
        return Observation(data.product_id,data.inspection_id,data.region_id,self.method,confidence=raw.get("confidence",1.0),metadata={"frame_id":data.frame_id,"anomaly_score":score,"anomaly_threshold":self.anomaly_threshold,"raw":raw})
