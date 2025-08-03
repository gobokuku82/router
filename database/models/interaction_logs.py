from . import Base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey

class InteractionLog(Base):
    """직원과 고객 간의 상호작용 기록을 관리하는 테이블"""
    __tablename__ = "interaction_logs"
    
    # 기본 식별 정보
    log_id = Column(Integer, primary_key=True, autoincrement=True)  # 상호작용 로그 고유 ID (자동 증가)
    
    # 관계 정보 (역사적 기록이므로 NULL 불가)
    employee_id = Column(Integer, ForeignKey("employee_info.employee_info_id"), nullable=False)  # 상호작용한 직원 ID (외래키, 필수)
    customer_id = Column(Integer, ForeignKey("customers.customer_id"), nullable=False)  # 상호작용한 고객 ID (외래키, 필수)
    
    # 상호작용 내용
    interaction_type = Column(String)  # 상호작용 유형 (예: 방문, 전화, 이메일, 미팅)
    summary = Column(String)  # 상호작용 요약 및 주요 내용
    
    # 분석 결과
    sentiment = Column(String)  # 감정 분석 결과 (예: positive, negative, neutral)
    compliance_risk = Column(String)  # 준법 위험도 평가 (예: low, medium, high)
    
    # 시간 정보
    interacted_at = Column(DateTime)  # 상호작용 발생 일시 
