"""Bridge between Vision Adapter and Inspection Orchestrator."""
from typing import Any, Dict
from ..adapters.base import VisionInput, VisionAdapter
from ...models.result import Observation

class VisionPipeline:
    def __init__(self, adapters:Dict[str,VisionAdapter]): self.adapters=adapters
    def inspect(self,product_id:str,inspection_id:str,region_id:str,image:Any,frame_id:str=None)->Observation:
        adapter=self.adapters.get(region_id)
        if adapter is None: raise ValueError(f"No vision adapter configured for region {region_id}")
        return adapter.inspect(VisionInput(product_id,inspection_id,region_id,image,frame_id))
