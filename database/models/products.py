from . import Base
from sqlalchemy import Column, Integer, String, Boolean

class Product(Base):
    """제품 정보를 관리하는 테이블"""
    __tablename__ = "products"
    
    # 기본 식별 정보
    product_id = Column(Integer, primary_key=True, autoincrement=True)  # 제품 고유 ID (자동 증가)
    product_name = Column(String, nullable=False)  # 제품명 (필수)
    
    # 제품 상세 정보
    description = Column(String)  # 제품 설명 및 상세 정보
    
    # 분류 정보
    category = Column(String)  # 제품 카테고리 (예: 의약품, 의료기기, 건강기능식품)
    
    # 상태 정보
    is_active = Column(Boolean, default=True)  # 제품 활성화 상태 (기본값: 활성) 
