from pydantic import BaseModel

class DocumentRelationBase(BaseModel):
    doc_id: int
    related_doc_id: int
    relation_type: str  # 'reference', 'similar', etc.

class DocumentRelationInfo(DocumentRelationBase):
    class Config:
        from_attributes = True 