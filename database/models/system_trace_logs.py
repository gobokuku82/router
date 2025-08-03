from . import Base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func, BigInteger
from sqlalchemy.dialects.postgresql import JSONB

class SystemTraceLog(Base):
    """시스템 추적 로그를 관리하는 테이블"""
    __tablename__ = "system_trace_logs"
    
    # 기본 식별 정보
    trace_id = Column(BigInteger, primary_key=True, autoincrement=True)  # 추적 로그 고유 ID (자동 증가, 큰 정수)
    
    # 관계 정보
    message_id = Column(BigInteger, ForeignKey("chat_history.message_id"), nullable=False)  # 관련 채팅 메시지 ID (외래키, 필수)
    
    # 이벤트 정보
    event_type = Column(String)  # 이벤트 유형 (예: search_request, document_upload, api_call)
    
    # 상세 데이터
    log_data = Column(JSONB)  # 상세 로그 데이터 (JSON 형태로 저장)
    latency_ms = Column(Integer)  # 처리 시간 (밀리초 단위)
    
    # 시스템 정보
    created_at = Column(DateTime, nullable=False, default=func.now())  # 로그 생성 일시 (필수, 자동 설정) 
