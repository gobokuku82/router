from . import Base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

class EmployeeInfo(Base):
    """직원 인사 정보를 관리하는 테이블 (문서 업로드 대상)"""
    __tablename__ = "employee_info"
    
    # 기본 식별 정보
    employee_info_id = Column(Integer, primary_key=True, autoincrement=True)  # 인사 정보 고유 ID
    employee_id = Column(Integer, ForeignKey("employees.employee_id"), nullable=True)  # 계정 정보 연결 (NULL 가능)
    
    # 직원 기본 정보 (문서에서 업데이트 가능)
    name = Column(String, nullable=False)  # 직원 실명 (필수)
    employee_number = Column(String, unique=True)  # 사번 (고유값, 동명이인 구분용)
    
    # 조직 정보
    team = Column(String)  # 소속 팀명 (예: 영업팀, 마케팅팀)
    position = Column(String)  # 직급 (예: 대리, 과장, 차장)
    business_unit = Column(String)  # 사업부 (예: 제약사업부, 의료사업부)
    branch = Column(String)  # 지점/지사명
    
    # 연락처 정보
    contact_number = Column(String)  # 연락처 전화번호
    
    # 급여 및 예산 정보
    base_salary = Column(Integer)  # 기본급 (원 단위)
    incentive_pay = Column(Integer)  # 인센티브/성과급 (원 단위)
    avg_monthly_budget = Column(Integer)  # 월 평균 업무 예산 (원 단위)
    
    # 평가 정보
    latest_evaluation = Column(String)  # 최근 평가 결과 (예: A, B, C 등급)
    
    # 업무 정보
    responsibilities = Column(String)  # 책임업무/담당업무
    
    # 시스템 정보
    created_at = Column(DateTime, default=func.now())  # 인사 정보 생성 일시
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())  # 인사 정보 수정 일시
    
    # 관계 설정 (선택적)
    employee = relationship("Employee", back_populates="employee_info")
    
    def __repr__(self):
        return f"<EmployeeInfo(name='{self.name}', team='{self.team}', position='{self.position}')>" 