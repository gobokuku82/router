import logging
from typing import Dict, Any, List, Optional
import json
from services.openai_service import openai_service

logger = logging.getLogger(__name__)

class QueryAnalyzer:
    """AI 기반 질의 분석 서비스"""
    
    def __init__(self):
        """질의 분석기 초기화"""
        pass
    
    def analyze_query(self, query: str) -> Dict[str, Any]:
        """
        질의를 분석하여 검색 유형과 타겟을 결정
        
        Args:
            query: 사용자 질의
            
        Returns:
            Dict: 분석 결과
        """
        try:
            # AI 기반 질의 분석
            analysis_prompt = self._create_analysis_prompt(query)
            
            messages = [
                {"role": "system", "content": "당신은 사용자의 검색 질의를 분석하여 적절한 검색 방식을 결정하는 전문가입니다."},
                {"role": "user", "content": analysis_prompt}
            ]
            
            analysis_result = openai_service.create_json_completion(
                messages=messages,
                model="gpt-3.5-turbo",
                max_tokens=500,
                temperature=0.1
            )
            
            if not analysis_result:
                raise Exception("LLM 응답을 받지 못했습니다.")
            
            logger.info(f"질의 분석 완료: {query} -> {analysis_result['search_type']}")
            
            return {
                'success': True,
                'query': query,
                'analysis': analysis_result
            }
            
        except Exception as e:
            logger.error(f"질의 분석 중 오류: {e}")
            return {
                'success': False,
                'query': query,
                'error': str(e),
                'analysis': {
                    'search_type': 'hybrid',
                    'table_targets': [],
                    'text_targets': [],
                    'confidence': 0.0,
                    'reasoning': '분석 실패로 인한 기본값'
                }
            }
    
    def _create_analysis_prompt(self, query: str) -> str:
        """질의 분석을 위한 프롬프트 생성"""
        return f"""
다음 질의를 분석하여 검색 유형을 분류해주세요:

질의: "{query}"

분류 기준:
1. 테이블 데이터 검색: 고객, 직원, 매출, 제품, 상호작용 관련 질의
   - 고객: 병원, 의원, 고객명, 주소, 환자수, 담당의사, 고객등급
   - 직원: 직원명, 팀, 직급, 사업부, 지점, 급여, 성과급, 예산
   - 매출: 매출액, 판매일, 거래내역
   - 제품: 제품명, 카테고리, 의료기기, 의약품
   - 상호작용: 방문, 전화, 이메일, 미팅, 감정분석, 준법위험도

2. 텍스트 문서 검색: 규정, 매뉴얼, 보고서, 가이드 관련 질의
   - 규정: 휴가, 출장, 보안, 정책
   - 매뉴얼: 설치, 사용법, 가이드, 방법
   - 보고서: 실적, 분석, 조사, 결과

3. 복합 검색: 테이블과 텍스트를 모두 포함하는 질의

응답 형식 (JSON):
{{
  "search_type": "table|text|hybrid",
  "table_targets": ["customers", "employees", "sales", "products", "interactions"],
  "text_targets": ["regulations", "manuals", "reports", "guides"],
  "confidence": 0.0-1.0,
  "reasoning": "분석 근거"
}}
"""

# 전역 인스턴스
query_analyzer = QueryAnalyzer() 