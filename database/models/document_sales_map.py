from . import Base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func, UniqueConstraint

class DocumentSalesMap(Base):
    """문서와 매출 기록 간의 연결을 관리하는 테이블"""
    __tablename__ = "document_sales_map"
    
    # 기본 식별 정보
    link_id = Column(Integer, primary_key=True, autoincrement=True)  # 연결 고유 ID (자동 증가)
    
    # 관계 정보
    doc_id = Column(Integer, ForeignKey("documents.doc_id"), nullable=False)  # 문서 ID (외래키, 필수)
    sales_record_id = Column(Integer, ForeignKey("sales_records.record_id"), nullable=False)  # 매출 기록 ID (외래키, 필수)
    
    # 제약 조건
    __table_args__ = (
        UniqueConstraint('doc_id', 'sales_record_id', name='uq_doc_sales_doc_sales'),  # 문서-매출 조합 유니크 제약
    ) 
