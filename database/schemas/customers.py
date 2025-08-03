from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class CustomerBase(BaseModel):
    customer_name: str
    address: Optional[str] = None
    doctor_name: Optional[str] = None
    total_patients: Optional[int] = None
    customer_grade: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None

class CustomerInfo(CustomerBase):
    customer_id: int

    class Config:
        from_attributes = True 