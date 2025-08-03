from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class InteractionLogBase(BaseModel):
    employee_id: int
    customer_id: int
    interaction_type: str
    summary: Optional[str] = None
    sentiment: Optional[str] = None
    compliance_risk: Optional[str] = None
    interacted_at: datetime

class InteractionLogInfo(InteractionLogBase):
    log_id: int

    class Config:
        from_attributes = True 