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
            user_input=request.message,
            session_id=request.session_id
        )
        
        # 응답 구성
        response = ChatResponse(
            success=result.get("success", False),
            session_id=result.get("session_id"),
            target_agent=result.get("agent_type"),  # agent_type으로 변경
            requires_interrupt=result.get("requires_interrupt", False),
            error=result.get("error"),
            data={}  # 초기화
        )
        
        # 하위 에이전트 결과 처리
        sub_result = result.get("result", {})
        
        logger.info(f"[CHAT] Router result: {result}")
        logger.info(f"[CHAT] Sub-agent result: {sub_result}")
        logger.info(f"[CHAT] Router requires_interrupt: {result.get('requires_interrupt')}, next_node: {result.get('next_node')}, doc_type: {result.get('doc_type')}")
        logger.info(f"[CHAT] Router has response: {result.get('response') is not None}")
        
        # help_message 처리 (router에서 직접 반환하는 경우)
        if result.get("response"):
            logger.info(f"[CHAT] Returning help message from router")
            response.response = result["response"]
            return response
        
        # 인터럽트 처리를 먼저 확인
        if result.get("requires_interrupt"):
            # router 레벨의 인터럽트 정보 사용
            response.requires_interrupt = True
            
            # 상태 정보 추출 (router 레벨 우선, 없으면 sub_result 확인)
            next_node = result.get("next_node") or (sub_result.get("next_node") if sub_result else None)
            doc_type = result.get("doc_type") or (sub_result.get("doc_type") if sub_result else None)
            state_info = result.get("state_info") or (sub_result.get("state_info", {}) if sub_result else {})
            
            logger.info(f"[INTERRUPT] next_node: {next_node}, doc_type: {doc_type}")
            
            response.data = {
                "thread_id": result.get("thread_id") or (sub_result.get("thread_id") if sub_result else None),
                "next_node": next_node,
                "doc_type": doc_type,
                "state_info": state_info
            }
            
            # next_node로 정확한 상황 판단
            if next_node == "receive_verification_input":
                # 분류 검증 단계
                response.response = f"분류된 문서 타입: {doc_type}\n\n위 분류 결과가 올바른가요?"
                response.data["interrupt_type"] = "verification"
                response.data["prompt_type"] = "verification"
                
            elif next_node == "receive_manual_doc_type_input":
                # 수동 선택 단계
                response.response = "문서 타입을 선택해주세요."
                response.data["prompt_type"] = "manual_doc_selection"
                response.data["options"] = [
                    {"value": "1", "label": "영업방문 결과보고서"},
                    {"value": "2", "label": "제품설명회 시행 신청서"},
                    {"value": "3", "label": "제품설명회 시행 결과보고서"},
                    {"value": "4", "label": "종료"}
                ]
                response.data["message"] = "올바른 문서 타입을 선택해주세요. 번호(1-4) 또는 문서명을 직접 입력할 수 있습니다."
                
            elif next_node == "receive_user_input":
                # 필드 입력 단계
                response.response = "필요한 정보를 입력해주세요."
                response.data["interrupt_type"] = "data_input"
                
            else:
                # 기본값
                response.response = sub_result.get("prompt") if sub_result else "추가 정보가 필요합니다."
                response.data["interrupt_type"] = "verification"
                
        elif sub_result and sub_result.get("success"):
            # 성공적인 결과
            agent_type = result.get("agent_type")
            
            if agent_type == "docs_agent":
                response.response = "문서가 성공적으로 생성되었습니다."
                response.data = {
                    "document_path": sub_result.get("result", {}).get("final_doc"),
                    "document_type": sub_result.get("result", {}).get("doc_type"),
                    "filled_data": sub_result.get("result", {}).get("filled_data")
                }
            elif agent_type == "employee_agent":
                response.response = sub_result.get("report", "")
                response.data = {
                    "employee_name": sub_result.get("employee_name"),
                    "period": sub_result.get("period"),
                    "total_performance": sub_result.get("total_performance"),
                    "achievement_rate": sub_result.get("achievement_rate")
                }
            elif agent_type == "client_agent":
                # client_agent 결과 처리
                response.response = sub_result.get("response", "") or sub_result.get("report", "") or sub_result.get("analysis_result", "") or sub_result.get("result", "") or str(sub_result)
                response.data = sub_result if isinstance(sub_result, dict) else {"result": sub_result}
            elif agent_type == "search_agent":
                # search_agent 결과 처리
                response.response = sub_result.get("search_result", "") or sub_result.get("result", "") or str(sub_result)
                response.data = sub_result if isinstance(sub_result, dict) else {"result": sub_result}
        
        
        else:
            # 오류 발생 또는 결과 없음
            if sub_result:
                response.error = sub_result.get("error", "알 수 없는 오류")
            else:
                response.error = result.get("error", "결과를 가져올 수 없습니다.")
        
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
            requires_interrupt=False,
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
        result = router_agent.resume(
            session_id=session_id,
            user_reply=request.user_reply,
            reply_type=request.reply_type
        )
        
        # result가 None인 경우 처리
        if result is None:
            logger.error(f"[RESUME] None 반환: session_id={session_id}")
            result = {
                "success": False,
                "error": "세션 처리 중 오류가 발생했습니다."
            }
        
        # 응답 구성
        response = ChatResponse(
            success=result.get("success", False),
            session_id=session_id,
            error=result.get("error")
        )
        
        if result.get("success"):
            # 성공적으로 완료
            response.response = "처리가 완료되었습니다."
            result_data = result.get("result") or {}
            response.data = {
                "final_doc": result_data.get("final_doc") if isinstance(result_data, dict) else None,
                "filled_data": result_data.get("filled_data") if isinstance(result_data, dict) else None
            }
        
        elif result.get("interrupted"):
            # 여전히 인터럽트 상태
            response.requires_interrupt = True
            response.response = "추가 정보가 필요합니다."
            response.data = {
                "thread_id": result.get("thread_id"),
                "next_node": result.get("next_node")
            }
            
            # next_node로 정확한 상황 판단
            next_node = result.get("next_node")
            doc_type = result.get("doc_type")
            
            if next_node == "receive_verification_input":
                # 분류 검증 단계
                response.response = f"분류된 문서 타입: {doc_type}\n\n위 분류 결과가 올바른가요?"
                response.data["interrupt_type"] = "verification"
                response.data["prompt_type"] = "verification"
                response.data["doc_type"] = doc_type
                
            elif next_node == "receive_manual_doc_type_input":
                # 수동 선택 단계
                response.response = "문서 타입을 선택해주세요."
                response.data["prompt_type"] = "manual_doc_selection"
                response.data["options"] = [
                    {"value": "1", "label": "영업방문 결과보고서"},
                    {"value": "2", "label": "제품설명회 시행 신청서"},
                    {"value": "3", "label": "제품설명회 시행 결과보고서"},
                    {"value": "4", "label": "종료"}
                ]
                response.data["message"] = "올바른 문서 타입을 선택해주세요. 번호(1-4) 또는 문서명을 직접 입력할 수 있습니다."
                
            elif next_node == "receive_user_input":
                # 필드 입력 단계
                response.response = "필요한 정보를 입력해주세요."
                response.data["interrupt_type"] = "data_input"
                response.data["doc_type"] = doc_type
        else:
            # 실패 케이스 (규정 위반 등)
            response.requires_interrupt = False
            
            # 에러 메시지 구성
            error_msg = "처리 중 오류가 발생했습니다."
            if result.get("error"):
                error_msg = f"오류 발생: {result['error']}"
            elif result.get("violation"):
                error_msg = "규정 위반으로 문서 생성이 중단되었습니다."
            elif result.get("result") is None:
                error_msg = "문서 생성 실패: 결과가 없습니다."
            
            response.response = error_msg
            
            # result가 dict인지 확인하고 안전하게 처리
            if isinstance(result, dict):
                # result.result에서 violation 정보 확인
                inner_result = result.get("result", {})
                violation = None
                
                if result.get("violation"):
                    violation = result["violation"]
                elif isinstance(inner_result, dict) and inner_result.get("violation"):
                    violation = inner_result["violation"]
                
                response.data = {
                    "error_type": "policy_violation" if violation else "processing_error",
                    "violation": violation,
                    "details": result.get("details", result.get("error"))
                }
            else:
                response.data = {"error_type": "unknown_error"}
        
        logger.info(f"[RESUME] 응답 완료: success={response.success}")
        return response
        
    except Exception as e:
        logger.error(f"[RESUME] 오류 발생: {str(e)}")
        return ChatResponse(
            success=False,
            session_id=session_id,
            requires_interrupt=False,
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