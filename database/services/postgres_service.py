from models.documents import Document
from services.db import SessionLocal
from schemas.document import DocumentBase
from sqlalchemy.orm import Session
from typing import List, Optional

def save_document(doc_meta: DocumentBase) -> Document:
    db = SessionLocal()
    try:
        db_doc = Document(**doc_meta.dict())
        db.add(db_doc)
        db.commit()
        db.refresh(db_doc)
        return db_doc
    finally:
        db.close()

def get_documents() -> List[Document]:
    db = SessionLocal()
    try:
        return db.query(Document).all()
    finally:
        db.close()

def get_document_by_id(doc_id: int) -> Optional[Document]:
    db = SessionLocal()
    try:
        return db.query(Document).filter(Document.doc_id == doc_id).first()
    finally:
        db.close()

def delete_document_from_postgres(doc_id: int) -> Optional[Document]:
    db = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.doc_id == doc_id).first()
        if doc:
            db.delete(doc)
            db.commit()
        return doc
    finally:
        db.close()
