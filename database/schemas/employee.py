from pydantic import BaseModel, EmailStr, constr
from typing import Optional
from datetime import datetime

class EmployeeBase(BaseModel):
    """
    email: unique, required
    username: unique, required
    password: required (only for creation)
    name: required
    role: required
    is_active: default True
    created_at: optional
    """
    email: EmailStr
    username: str
    password: Optional[constr(min_length=8)] = None
    name: str
    role: str  # 'admin', 'manager', 'user'
    is_active: Optional[bool] = True
    created_at: Optional[datetime] = None

class EmployeeCreate(EmployeeBase):
    password: constr(min_length=8)

class EmployeeLogin(BaseModel):
    email: EmailStr
    password: str

class EmployeeInfo(EmployeeBase):
    employee_id: int

    class Config:
        from_attributes = True 