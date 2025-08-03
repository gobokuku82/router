from pydantic import BaseModel

class DocumentInteractionMapBase(BaseModel):
    doc_id: int
    log_id: int

class DocumentInteractionMapInfo(DocumentInteractionMapBase):
    class Config:
        from_attributes = True 