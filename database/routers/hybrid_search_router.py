from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from services.hybrid_search_service import hybrid_search_service
from routers.user_router import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class HybridSearchRequest(BaseModel):
    """하이브리드 검색 요청 모델"""
    query: str
    limit: Optional[int] = 20

class TableSearchResult(BaseModel):
    """테이블 검색 결과 모델"""
    id: int
    doc_id: int
    table_type: str
    content: Dict[str, Any]
    created_at: Optional[str] = None
    similarity_score: Optional[float] = None
    source: str = "text2sql_search"

class TextSearchResult(BaseModel):
    """텍스트 검색 결과 모델"""
    id: Optional[str] = None
    doc_id: Optional[int] = None
    doc_title: Optional[str] = None
    content: Optional[str] = None
    created_at: Optional[str] = None
    similarity_score: Optional[float] = None
    source: str = "opensearch"

class HybridSearchResponse(BaseModel):
    """하이브리드 검색 응답 모델"""
    success: bool
    message: str
    query: str
    search_type: str
    analysis: Optional[Dict] = None
    table_results: List[TableSearchResult]
    text_results: List[TextSearchResult]
    total_count: int
    search_time: float

@router.post("/search/hybrid", response_model=HybridSearchResponse)
def hybrid_search(
    request: HybridSearchRequest,
    user=Depends(get_current_user)
):
    """
    하이브리드 검색을 수행합니다 (테이블 + 텍스트 문서).
    
    Args:
        request: 검색 요청 정보
        user: 현재 인증된 사용자
        
    Returns:
        HybridSearchResponse: 검색 결과 (테이블과 텍스트 분리)
    """
    try:
        logger.info(f"하이브리드 검색 시작: '{request.query}'")
        
        # 하이브리드 검색 수행
        search_result = hybrid_search_service.search(
            query=request.query,
            limit=request.limit
        )
        
        if not search_result['success']:
            raise HTTPException(status_code=500, detail=search_result['message'])
        
        # 결과를 테이블과 텍스트로 분리
        table_results = []
        text_results = []
        
        for result in search_result['results']:
            if result['type'] == 'table':
                table_result = TableSearchResult(
                    id=result['id'],
                    doc_id=result['doc_id'],
                    table_type=result['table_type'],
                    content=result['content'],
                    created_at=result['created_at'].isoformat() if result['created_at'] else None,
                    similarity_score=result['similarity_score'],
                    source=result['source']
                )
                table_results.append(table_result)
            else:  # text
                text_result = TextSearchResult(
                    id=result['id'],
                    doc_id=result['doc_id'],
                    doc_title=result.get('doc_title'),
                    content=result['content'],
                    created_at=result['created_at'].isoformat() if result['created_at'] else None,
                    similarity_score=result['similarity_score'],
                    source=result['source']
                )
                text_results.append(text_result)
        
        logger.info(f"하이브리드 검색 완료: 테이블 {len(table_results)}개, 텍스트 {len(text_results)}개")
        
        return HybridSearchResponse(
            success=True,
            message=search_result['message'],
            query=search_result['query'],
            search_type=search_result['search_type'],
            analysis=search_result.get('analysis'),
            table_results=table_results,
            text_results=text_results,
            total_count=search_result['total_count'],
            search_time=search_result['search_time']
        )
        
    except Exception as e:
        logger.error(f"하이브리드 검색 중 오류: {e}")
        raise HTTPException(status_code=500, detail=f"검색 중 오류가 발생했습니다: {str(e)}")

@router.get("/search/hybrid", response_model=HybridSearchResponse)
def hybrid_search_get(
    query: str = Query(..., description="검색 쿼리"),
    limit: Optional[int] = Query(20, description="결과 개수 제한"),
    user=Depends(get_current_user)
):
    """
    GET 방식으로 하이브리드 검색을 수행합니다.
    
    Args:
        query: 검색 쿼리
        limit: 결과 개수 제한
        user: 현재 인증된 사용자
        
    Returns:
        HybridSearchResponse: 검색 결과 (테이블과 텍스트 분리)
    """
    try:
        logger.info(f"하이브리드 검색 시작 (GET): '{query}'")
        
        # 하이브리드 검색 수행
        search_result = hybrid_search_service.search(
            query=query,
            limit=limit
        )
        
        if not search_result['success']:
            raise HTTPException(status_code=500, detail=search_result['message'])
        
        # 결과를 테이블과 텍스트로 분리
        table_results = []
        text_results = []
        
        for result in search_result['results']:
            if result['type'] == 'table':
                table_result = TableSearchResult(
                    id=result['id'],
                    doc_id=result['doc_id'],
                    table_type=result['table_type'],
                    content=result['content'],
                    created_at=result['created_at'].isoformat() if result['created_at'] else None,
                    similarity_score=result['similarity_score'],
                    source=result['source']
                )
                table_results.append(table_result)
            else:  # text
                text_result = TextSearchResult(
                    id=result['id'],
                    doc_id=result['doc_id'],
                    doc_title=result.get('doc_title'),
                    content=result['content'],
                    created_at=result['created_at'].isoformat() if result['created_at'] else None,
                    similarity_score=result['similarity_score'],
                    source=result['source']
                )
                text_results.append(text_result)
        
        logger.info(f"하이브리드 검색 완료 (GET): 테이블 {len(table_results)}개, 텍스트 {len(text_results)}개")
        
        return HybridSearchResponse(
            success=True,
            message=search_result['message'],
            query=search_result['query'],
            search_type=search_result['search_type'],
            analysis=search_result.get('analysis'),
            table_results=table_results,
            text_results=text_results,
            total_count=search_result['total_count'],
            search_time=search_result['search_time']
        )
        
    except Exception as e:
        logger.error(f"하이브리드 검색 중 오류 (GET): {e}")
        raise HTTPException(status_code=500, detail=f"검색 중 오류가 발생했습니다: {str(e)}")

@router.get("/search/hybrid/stats")
def get_hybrid_search_stats(user=Depends(get_current_user)):
    """
    하이브리드 검색 통계 정보를 조회합니다.
    
    Args:
        user: 현재 인증된 사용자
        
    Returns:
        Dict: 통계 정보
    """
    try:
        # OpenSearch 통계 (구현 필요)
        opensearch_stats = {
            'total_documents': 0,  # OpenSearch에서 조회 필요
            'indexed_documents': 0
        }
        
        return {
            'success': True,
            'message': '하이브리드 검색 통계 조회 완료',
            'stats': {
                'opensearch': opensearch_stats
            }
        }
        
    except Exception as e:
        logger.error(f"하이브리드 검색 통계 조회 중 오류: {e}")
        raise HTTPException(status_code=500, detail=f"통계 조회 중 오류가 발생했습니다: {str(e)}") 