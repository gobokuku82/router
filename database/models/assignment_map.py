from . import Base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func, UniqueConstraint

class AssignmentMap(Base):
    """직원과 고객 간의 배정 관계를 관리하는 테이블"""
    __tablename__ = "assignment_map"
    
    # 기본 식별 정보
    assignment_id = Column(Integer, primary_key=True, autoincrement=True)  # 배정 관계 고유 ID (자동 증가)
    
    # 관계 정보 (역사적 기록이므로 NULL 불가)
    employee_id = Column(Integer, ForeignKey("employee_info.employee_info_id"), nullable=False)  # 배정된 직원 ID (외래키, 필수)
    customer_id = Column(Integer, ForeignKey("customers.customer_id"), nullable=False)  # 배정된 고객 ID (외래키, 필수)
    
    # 제약 조건
    __table_args__ = (
        UniqueConstraint('employee_id', 'customer_id', name='uq_assignment_employee_customer'),  # 직원-고객 조합 유니크 제약
    ) 
