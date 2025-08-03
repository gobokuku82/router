from pydantic import BaseModel

class DocumentSalesMapBase(BaseModel):
    doc_id: int
    record_id: int

class DocumentSalesMapInfo(DocumentSalesMapBase):
    class Config:
        from_attributes = True 