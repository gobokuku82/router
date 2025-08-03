from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ChatHistoryBase(BaseModel):
    session_id: str
    employee_id: int
    user_query: str
    system_response: str
    created_at: Optional[datetime] = None

class ChatHistoryInfo(ChatHistoryBase):
    message_id: int

    class Config:
        from_attributes = True 