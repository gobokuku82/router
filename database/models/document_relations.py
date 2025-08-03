from . import Base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func, UniqueConstraint

class DocumentRelation(Base):
    """문서와 다른 엔티티들 간의 관계를 관리하는 테이블"""
    __tablename__ = "document_relations"
    
    # 기본 식별 정보
    relation_id = Column(Integer, primary_key=True, autoincrement=True)  # 관계 고유 ID (자동 증가)
    
    # 관계 정보
    doc_id = Column(Integer, ForeignKey("documents.doc_id"), nullable=False)  # 문서 ID (외래키, 필수)
    related_entity_type = Column(String, nullable=False)  # 관련 엔티티 타입 (customer, product, employee, document)
    related_entity_id = Column(Integer, nullable=False)  # 관련 엔티티 ID
    confidence_score = Column(Integer, default=100)  # 신뢰도 점수 (0-100)
    created_at = Column(DateTime, default=func.now())  # 생성 시간
    
    # 제약 조건
    __table_args__ = (
        UniqueConstraint('doc_id', 'related_entity_type', 'related_entity_id', name='uq_doc_relation_unique'),  # 문서-엔티티 조합 유니크 제약
    ) 
