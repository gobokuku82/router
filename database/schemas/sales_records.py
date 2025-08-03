from pydantic import BaseModel
from typing import Optional
from datetime import date

class SalesRecordBase(BaseModel):
    employee_id: int
    customer_id: int
    product_id: int
    sale_amount: int
    sale_date: date

class SalesRecordInfo(SalesRecordBase):
    record_id: int

    class Config:
        from_attributes = True 