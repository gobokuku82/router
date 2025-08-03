from pydantic import BaseModel
from typing import Optional

class CustomerMonthlyPerformanceBase(BaseModel):
    customer_id: int
    year_month: str  # 'YYYY-MM' 형식
    monthly_sales: int
    budget_used: Optional[int] = None
    visit_count: Optional[int] = None

class CustomerMonthlyPerformanceInfo(CustomerMonthlyPerformanceBase):
    performance_id: int

    class Config:
        from_attributes = True 