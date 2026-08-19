"""Object detection adapter for YOLO/RT-DETR-like models."""
from typing import Any, Dict, List
from .base import VisionAdapter, VisionInput
from ...models.result import Observation
class DetectionAdapter(VisionAdapter):
    method="DETECTION"
    def __init__(self,model:Any=None): self.model=model
    def inspect(self,data:VisionInput)->Observation:
        if self.model is None: raise RuntimeError("DetectionAdapter requires a detector model")
        raw=self.model.predict(data.image); detections:List[Dict[str,Any]]=raw.get("detections",[])
        if not detections:return Observation(data.product_id,data.inspection_id,data.region_id,self.method,confidence=0.0,quantity=0,metadata={"frame_id":data.frame_id,"raw":raw,"class_counts":{}})
        counts={}
        for d in detections:
            cls=str(d["class"]); counts[cls]=counts.get(cls,0)+1
        confidence=min(float(d.get("confidence",0.0)) for d in detections); dominant=max(counts,key=counts.get)
        return Observation(data.product_id,data.inspection_id,data.region_id,self.method,detected_class=dominant,confidence=confidence,quantity=counts[dominant],position=raw.get("position"),metadata={"frame_id":data.frame_id,"class_counts":counts,"detections":detections,"raw":raw})
