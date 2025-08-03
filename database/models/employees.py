from . import Base
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

class Employee(Base):
    """직원 계정 정보를 관리하는 테이블"""
    __tablename__ = "employees"
    
    # 기본 식별 정보
    employee_id = Column(Integer, primary_key=True, autoincrement=True)  # 직원 고유 ID (자동 증가)
    email = Column(String, unique=True, nullable=False)  # 직원 이메일 주소 (고유값, 필수)
    username = Column(String, unique=True, nullable=False)  # 로그인용 사용자명 (고유값, 필수)
    password = Column(String, nullable=False)  # 로그인 비밀번호 (해시화된 값, 필수)
    name = Column(String, nullable=False)  # 직원 실명 (필수)
    
    # 시스템 역할
    role = Column(String, nullable=False)  # 시스템 내 역할 (예: admin, user, manager, 필수)
    is_active = Column(Boolean, default=True)  # 계정 활성화 상태 (기본값: 활성)
    
    # Soft Delete 관련 필드
    is_deleted = Column(Boolean, default=False)  # 논리적 삭제 상태 (기본값: 삭제되지 않음)
    deleted_at = Column(DateTime)  # 논리적 삭제 일시
    
    # 시스템 정보
    created_at = Column(DateTime, default=func.now())  # 계정 생성 일시 (자동 설정)
    
    # 관계 설정
    employee_info = relationship("EmployeeInfo", back_populates="employee", uselist=False)
