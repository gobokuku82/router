from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DocumentBase(BaseModel):
    doc_title: str
    doc_type: Optional[str] = None
    file_path: str
    uploader_id: int
    version: Optional[str] = None
    created_at: Optional[datetime] = None

class DocumentInfo(DocumentBase):
    doc_id: int

    class Config:
        from_attributes = True 