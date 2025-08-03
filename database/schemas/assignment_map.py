from pydantic import BaseModel

class AssignmentMapBase(BaseModel):
    employee_id: int
    customer_id: int

class AssignmentMapInfo(AssignmentMapBase):
    class Config:
        from_attributes = True 