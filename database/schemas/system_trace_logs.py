from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class SystemTraceLogBase(BaseModel):
    message_id: int
    event_type: str
    log_data: dict
    latency_ms: Optional[int] = None
    created_at: Optional[datetime] = None

class SystemTraceLogInfo(SystemTraceLogBase):
    trace_id: int

    class Config:
        from_attributes = True 