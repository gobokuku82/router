"""
LangGraph 기반 멀티 에이전트 라우터 API
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging
import uuid
from datetime import datetime

# 라우터 에이전트 임포트
from app.services.router_agent import RouterAgent

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 라우터 생성
router = APIRouter(prefix="/v1", tags=["langgraph"])

# 전역 라우터 에이전트 인스턴스
router_agent = RouterAgent()


# Request/Response 모델
class ChatRequest(BaseModel):
    """채팅 요청 모델"""
    message: str
    session_id: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "영업방문 결과보고서 작성해줘",
                "session_id": "optional-session-id"
            }
        }


class ResumeRequest(BaseModel):
    """세션 재개 요청 모델"""
    user_reply: str
    reply_type: str = "user_reply"
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_reply": "네, 맞습니다",
                "reply_type": "verification_reply"
            }
        }


class ChatResponse(BaseModel):
    """채팅 응답 모델"""
    success: bool
    session_id: str
    target_agent: Optional[str] = None
    requires_interrupt: bool = False
    response: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class SessionStatusResponse(BaseModel):
    """세션 상태 응답 모델"""
    exists: bool
    session_id: Optional[str] = None
    agent: Optional[str] = None
    status: Optional[str] = None
    thread_id: Optional[str] = None
    message: Optional[str] = None


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    사용자 메시지를 처리하고 적절한 에이전트로 라우팅합니다.
    
    Args:
        request: 채팅 요청
        
    Returns:
        ChatResponse: 처리 결과
    """
    try:
        logger.info(f"[CHAT] 요청 수신: {request.message[:50]}...")
        
        # 라우터 에이전트 실행
        result = router_agent.run(
            user_query=request.message,
            session_id=request.session_id
        )
        
        # 응답 구성
        response = ChatResponse(
            success=result.get("success", False),
            session_id=result.get("session_id"),
            target_agent=result.get("target_agent"),
            requires_interrupt=result.get("requires_interrupt", False),
            error=result.get("error")
        )
        
        # 하위 에이전트 결과 처리
        sub_result = result.get("result", {})
        
        if sub_result.get("success"):
            # 성공적인 결과
            if sub_result.get("agent") == "docs_agent":
                response.response = "문서가 성공적으로 생성되었습니다."
                response.data = {
                    "document_path": sub_result.get("result", {}).get("final_doc"),
                    "document_type": sub_result.get("result", {}).get("doc_type"),
                    "filled_data": sub_result.get("result", {}).get("filled_data")
                }
            elif sub_result.get("agent") == "employee_agent":
                response.response = sub_result.get("response", "")
                response.data = sub_result.get("data", {})
        
        elif sub_result.get("interrupted"):
            # 인터럽트 발생
            response.requires_interrupt = True
            response.response = "추가 정보가 필요합니다. /resume 엔드포인트를 사용하여 응답해주세요."
            response.data = {
                "thread_id": sub_result.get("thread_id"),
                "interrupt_type": "verification"  # 또는 다른 타입
            }
        
        else:
            # 오류 발생
            response.error = sub_result.get("error", "알 수 없는 오류")
        
        # 메타데이터 추가
        response.metadata = {
            "classification_confidence": result.get("classification_confidence"),
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"[CHAT] 응답 완료: success={response.success}, agent={response.target_agent}")
        return response
        
    except Exception as e:
        logger.error(f"[CHAT] 오류 발생: {str(e)}")
        return ChatResponse(
            success=False,
            session_id=request.session_id or str(uuid.uuid4()),
            error=f"처리 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/resume/{session_id}", response_model=ChatResponse)
async def resume_session(session_id: str, request: ResumeRequest) -> ChatResponse:
    """
    인터럽트된 세션을 재개합니다.
    
    Args:
        session_id: 세션 ID
        request: 재개 요청
        
    Returns:
        ChatResponse: 처리 결과
    """
    try:
        logger.info(f"[RESUME] 세션 재개: {session_id}")
        
        # 세션 재개
        result = router_agent.resume_session(
            session_id=session_id,
            user_reply=request.user_reply,
            reply_type=request.reply_type
        )
        
        # 응답 구성
        response = ChatResponse(
            success=result.get("success", False),
            session_id=session_id,
            error=result.get("error")
        )
        
        if result.get("success"):
            # 성공적으로 완료
            response.response = "처리가 완료되었습니다."
            response.data = {
                "final_doc": result.get("result", {}).get("final_doc"),
                "filled_data": result.get("result", {}).get("filled_data")
            }
        
        elif result.get("interrupted"):
            # 여전히 인터럽트 상태
            response.requires_interrupt = True
            response.response = "추가 정보가 필요합니다."
            response.data = {
                "thread_id": result.get("thread_id"),
                "next_node": result.get("next_node")
            }
        
        logger.info(f"[RESUME] 응답 완료: success={response.success}")
        return response
        
    except Exception as e:
        logger.error(f"[RESUME] 오류 발생: {str(e)}")
        return ChatResponse(
            success=False,
            session_id=session_id,
            error=f"세션 재개 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/status/{session_id}", response_model=SessionStatusResponse)
async def get_session_status(session_id: str) -> SessionStatusResponse:
    """
    세션 상태를 조회합니다.
    
    Args:
        session_id: 세션 ID
        
    Returns:
        SessionStatusResponse: 세션 상태
    """
    try:
        logger.info(f"[STATUS] 세션 상태 조회: {session_id}")
        
        # 세션 상태 조회
        status = router_agent.get_session_status(session_id)
        
        return SessionStatusResponse(**status)
        
    except Exception as e:
        logger.error(f"[STATUS] 오류 발생: {str(e)}")
        return SessionStatusResponse(
            exists=False,
            message=f"상태 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """
    헬스 체크 엔드포인트
    
    Returns:
        Dict: 서비스 상태
    """
    return {
        "status": "healthy",
        "service": "langgraph-router",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


@router.get("/agents")
async def list_agents():
    """
    사용 가능한 에이전트 목록을 반환합니다.
    
    Returns:
        Dict: 에이전트 목록 및 설명
    """
    return {
        "agents": [
            {
                "name": "docs_agent",
                "description": "문서 작성 에이전트 - 영업방문 결과보고서, 제품설명회 신청서/결과보고서 작성",
                "features": [
                    "템플릿 기반 문서 생성",
                    "규정 준수 검사",
                    "대화형 입력 지원"
                ]
            },
            {
                "name": "employee_agent",
                "description": "직원 실적 분석 에이전트 - 실적 조회, 목표 달성률 분석, 트렌드 분석",
                "features": [
                    "실적 데이터 분석",
                    "목표 대비 달성률 계산",
                    "성과 트렌드 분석",
                    "종합 평가 보고서 생성"
                ]
            }
        ]
    }


# 개발용 테스트 엔드포인트
if __name__ == "__main__":
    # 테스트를 위한 간단한 예제
    @router.post("/test")
    async def test_endpoint(message: str):
        """테스트 엔드포인트"""
        return {"message": f"Received: {message}"}