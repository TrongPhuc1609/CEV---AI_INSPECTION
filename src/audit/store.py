"""Minimal durable audit writer for inspection decisions."""
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
import json

class InspectionAuditStore:
    def __init__(self,output_path="artifacts/audit"): self.output_path=Path(output_path)
    def write(self,inspection,plc_command:Optional[Any]=None):
        self.output_path.mkdir(parents=True,exist_ok=True); payload=self._serialize(inspection)
        if plc_command is not None: payload["plc_command"]=self._serialize(plc_command)
        payload["audit_written_at"]=datetime.now(timezone.utc).isoformat(); path=self.output_path/f"{inspection.inspection_id}.json"; path.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8"); return path
    @staticmethod
    def _serialize(value):
        if is_dataclass(value): return InspectionAuditStore._serialize(asdict(value))
        if isinstance(value,dict): return {str(k):InspectionAuditStore._serialize(v) for k,v in value.items()}
        if isinstance(value,(list,tuple)): return [InspectionAuditStore._serialize(v) for v in value]
        if hasattr(value,"value"): return value.value
        return value
