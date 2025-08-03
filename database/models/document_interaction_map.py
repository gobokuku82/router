from . import Base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func, UniqueConstraint

class DocumentInteractionMap(Base):
    """문서와 상호작용 로그 간의 연결을 관리하는 테이블"""
    __tablename__ = "document_interaction_map"
    
    # 기본 식별 정보
    link_id = Column(Integer, primary_key=True, autoincrement=True)  # 연결 고유 ID (자동 증가)
    
    # 관계 정보
    doc_id = Column(Integer, ForeignKey("documents.doc_id"), nullable=False)  # 문서 ID (외래키, 필수)
    interaction_id = Column(Integer, ForeignKey("interaction_logs.log_id"), nullable=False)  # 상호작용 로그 ID (외래키, 필수)
    
    # 제약 조건
    __table_args__ = (
        UniqueConstraint('doc_id', 'interaction_id', name='uq_doc_interaction_doc_interaction'),  # 문서-상호작용 조합 유니크 제약
    ) 
