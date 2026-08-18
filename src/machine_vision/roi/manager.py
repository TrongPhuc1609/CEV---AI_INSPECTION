"""ROI definitions and cropping."""
from dataclasses import dataclass
from typing import Any, Dict

@dataclass(frozen=True)
class ROI:
    region_id: str; x: int; y: int; width: int; height: int; camera_id: str="CAM01"; metadata: Dict[str,Any]|None=None
    def crop(self, image):
        if isinstance(image,(str,bytes,dict)):
            return {"source":image,"roi":(self.x,self.y,self.width,self.height)}
        try: return image[self.y:self.y+self.height,self.x:self.x+self.width]
        except (TypeError,IndexError): return {"source":image,"roi":(self.x,self.y,self.width,self.height)}

class ROIManager:
    def __init__(self, rois=None): self.rois={r.region_id:r for r in (rois or [])}
    def add(self, roi: ROI): self.rois[roi.region_id]=roi
    def get(self, region_id: str) -> ROI:
        if region_id not in self.rois: raise KeyError(f"ROI not configured: {region_id}")
        return self.rois[region_id]
