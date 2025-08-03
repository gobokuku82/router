from . import Base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func, BigInteger, Text

class ChatHistory(Base):
    """채팅 대화 기록을 관리하는 테이블"""
    __tablename__ = "chat_history"
    
    # 기본 식별 정보
    message_id = Column(BigInteger, primary_key=True, autoincrement=True)  # 메시지 고유 ID (자동 증가, 큰 정수)
    
    # 세션 정보
    session_id = Column(String, nullable=False)  # 채팅 세션 ID (필수)
    
    # 사용자 정보 (역사적 기록이므로 NULL 불가)
    employee_id = Column(Integer, ForeignKey("employees.employee_id"), nullable=False)  # 채팅한 직원 ID (외래키, 필수)
    
    # 대화 내용
    user_query = Column(Text)  # 사용자 질문 내용 (긴 텍스트)
    system_response = Column(Text)  # 시스템 응답 내용 (긴 텍스트)
    
    # TTL (Time To Live) 관련 필드
    expires_at = Column(DateTime)  # 자동 삭제 예정 일시 (예: 1년 후)
    
    # 시스템 정보
    created_at = Column(DateTime, nullable=False, default=func.now())  # 메시지 생성 일시 (필수, 자동 설정) 
