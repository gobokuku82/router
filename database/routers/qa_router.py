"""
자연어 질문-답변 (QA) API 라우터

사용자의 자연어 질문을 받아 관련 문서를 검색하고 요약하여 답변을 생성하는 API를 제공합니다.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import logging
from services.opensearch_service import question_answering, opensearch_client

# 로깅 설정
logger = logging.getLogger(__name__)

# API 라우터 생성
router = APIRouter()

# Pydantic 모델 정의
class QaRequest(BaseModel):
    """자연어 질문 요청 모델"""
    question: str = Field(..., description="자연어 질문", min_length=1, max_length=1000)
    top_k: int = Field(default=5, description="검색할 문서 수", ge=1, le=20)
    include_summary: bool = Field(default=True, description="요약 포함 여부")
    include_sources: bool = Field(default=True, description="원본 문서 정보 포함 여부")

class QaResponse(BaseModel):
    """자연어 질문 응답 모델"""
    success: bool
    question: str
    answer: str
    summary: Optional[str] = None
    sources: list[Dict[str, Any]]
    search_results: list[Dict[str, Any]]
    total_sources: int
    confidence_score: float

class QaHealthResponse(BaseModel):
    """QA 시스템 상태 응답 모델"""
    status: str
    opensearch_connected: bool
    embedding_model_available: bool
    message: str

@router.get("/health", response_model=QaHealthResponse, summary="QA 시스템 상태 확인")
async def qa_health_check():
    """QA 시스템의 상태를 확인합니다."""
    try:
        # OpenSearch 연결 상태 확인
        opensearch_connected = False
        if opensearch_client and opensearch_client.client:
            try:
                opensearch_connected = opensearch_client.client.ping()
            except:
                pass
        
        # 임베딩 모델 상태 확인
        embedding_model_available = False
        if hasattr(opensearch_client, 'model') and opensearch_client.model:
            try:
                # 간단한 테스트 임베딩 생성
                test_embedding = opensearch_client.model.encode("test")
                embedding_model_available = len(test_embedding) > 0
            except:
                pass
        
        # 전체 상태 결정
        if opensearch_connected and embedding_model_available:
            status = "healthy"
            message = "QA 시스템이 정상 작동 중입니다."
        elif opensearch_connected:
            status = "partial"
            message = "OpenSearch는 연결되었지만 임베딩 모델에 문제가 있습니다."
        elif embedding_model_available:
            status = "partial"
            message = "임베딩 모델은 사용 가능하지만 OpenSearch 연결에 문제가 있습니다."
        else:
            status = "unhealthy"
            message = "QA 시스템에 문제가 있습니다."
        
        return QaHealthResponse(
            status=status,
            opensearch_connected=opensearch_connected,
            embedding_model_available=embedding_model_available,
            message=message
        )
        
    except Exception as e:
        logger.error(f"QA 헬스 체크 오류: {e}")
        return QaHealthResponse(
            status="unhealthy",
            opensearch_connected=False,
            embedding_model_available=False,
            message=f"QA 시스템 상태 확인 중 오류 발생: {str(e)}"
        )

@router.post("/question", response_model=QaResponse, summary="자연어 질문-답변")
async def ask_question(request: QaRequest):
    """
    자연어 질문을 받아 관련 문서를 검색하고 요약하여 답변을 생성합니다.
    
    기능:
    1. 질문에서 키워드 추출
    2. 벡터 검색을 사용한 문서 검색
    3. 검색된 문서들을 요약하여 답변 생성
    4. 원본 문서 정보 제공
    """
    try:
        logger.info(f"QA 요청 처리: {request.question[:50]}...")
        
        # QA 처리 실행
        result = question_answering(
            question=request.question,
            top_k=request.top_k,
            include_sources=request.include_sources
        )
        
        # 요약 생성 (선택적)
        if request.include_summary and result.get("success") and len(result.get("search_results", [])) > 1:
            answer = result.get("answer", "")
            result["summary"] = f"총 {result.get('total_sources', 0)}개의 관련 문서를 찾았습니다. 주요 내용은 다음과 같습니다: {answer[:300]}..."
        
        logger.info(f"QA 응답 생성 완료: {result.get('total_sources', 0)}개 문서에서 정보를 찾았습니다.")
        
        return QaResponse(**result)
        
    except Exception as e:
        logger.error(f"QA 처리 오류: {e}")
        raise HTTPException(status_code=500, detail=f"질문 처리 중 오류가 발생했습니다: {str(e)}")

@router.post("/test", response_model=QaResponse, summary="테스트 질문-답변")
async def test_qa():
    """기본 테스트 질문으로 QA 시스템을 확인합니다."""
    try:
        # 테스트 질문
        test_question = "신입사원 교육 기간은 얼마나 되나요?"
        
        logger.info(f"테스트 QA 요청: {test_question}")
        
        # QA 처리 실행
        result = question_answering(
            question=test_question,
            top_k=5,
            include_sources=True
        )
        
        # 요약 생성
        if result.get("success") and len(result.get("search_results", [])) > 1:
            answer = result.get("answer", "")
            result["summary"] = f"총 {result.get('total_sources', 0)}개의 관련 문서를 찾았습니다. 주요 내용은 다음과 같습니다: {answer[:300]}..."
        
        logger.info(f"테스트 QA 응답 생성 완료: {result.get('total_sources', 0)}개 문서에서 정보를 찾았습니다.")
        
        return QaResponse(**result)
        
    except Exception as e:
        logger.error(f"테스트 QA 처리 오류: {e}")
        raise HTTPException(status_code=500, detail=f"테스트 질문 처리 중 오류가 발생했습니다: {str(e)}")