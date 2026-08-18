"""Adapter factory."""
from typing import Any
from .base import VisionAdapter
from .detection import DetectionAdapter
from .classification import ClassificationAdapter
from .segmentation import SegmentationAdapter
from .anomaly import AnomalyDetectionAdapter

def create_adapter(method:str, model:Any=None, **kwargs)->VisionAdapter:
    mapping={"DETECTION":DetectionAdapter,"DETECTION_CLASSIFICATION":ClassificationAdapter,"SEGMENTATION":SegmentationAdapter,"ANOMALY_DETECTION":AnomalyDetectionAdapter}
    if method not in mapping: raise ValueError(f"Unsupported vision method: {method}")
    return mapping[method](model=model, **kwargs)
