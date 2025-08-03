"""
질문 분류기 모듈
사용자의 질문을 분석하여 적절한 에이전트로 라우팅합니다.
"""
from typing import Dict, Any, Tuple, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import json
import re


class AgentClassifier:
    """
    사용자 질문을 분석하여 적절한 에이전트를 선택하는 분류기
    """
    
    def __init__(self, model_name: str = "gpt-4o-mini", temperature: float = 0.1):
        """
        분류기 초기화
        
        Args:
            model_name: 사용할 LLM 모델명
            temperature: LLM 온도 설정 (낮을수록 일관성 높음)
        """
        self.llm = ChatOpenAI(model=model_name, temperature=temperature)
        
        # 에이전트별 키워드 및 패턴 정의
        self.agent_patterns = {
            "docs_agent": {
                "keywords": [
                    "문서", "보고서", "신청서", "작성", "만들어", "준비",
                    "영업방문", "제품설명회", "결과보고서", "시행신청서",
                    "템플릿", "양식", "서류"
                ],
                "patterns": [
                    r".*(?:문서|보고서|신청서).*(?:작성|만들|준비)",
                    r".*영업방문.*보고서",
                    r".*제품설명회.*(?:신청서|보고서)",
                    r".*(?:작성해|만들어|준비해).*(?:줘|주세요)"
                ],
                "description": "문서 작성, 보고서 생성, 신청서 작성 등 문서 관련 작업"
            },
            "employee_agent": {
                "keywords": [
                    "직원", "실적", "성과", "분석", "평가", "목표", "달성",
                    "매출", "판매", "영업실적", "KPI", "트렌드", "추세"
                ],
                "patterns": [
                    r".*직원.*(?:실적|성과|분석)",
                    r".*실적.*(?:분석|평가|조회)",
                    r".*(?:목표|달성).*(?:률|율)",
                    r".*(?:매출|판매).*분석"
                ],
                "description": "직원 실적 분석, 성과 평가, 목표 달성률 분석 등"
            }
        }
        
    def classify(self, user_query: str) -> Tuple[str, float, Dict[str, Any]]:
        """
        사용자 질문을 분류하여 적절한 에이전트를 선택합니다.
        
        Args:
            user_query: 사용자 입력 질문
            
        Returns:
            Tuple[str, float, Dict]: (선택된 에이전트, 신뢰도, 분석 정보)
        """
        # 1단계: 키워드 기반 빠른 분류 시도
        keyword_result = self._keyword_classification(user_query)
        
        # 2단계: LLM을 통한 정밀 분류
        llm_result = self._llm_classification(user_query)
        
        # 3단계: 결과 통합 및 최종 결정
        final_agent, confidence, analysis = self._combine_results(
            keyword_result, llm_result, user_query
        )
        
        return final_agent, confidence, analysis
    
    def _keyword_classification(self, query: str) -> Dict[str, Any]:
        """
        키워드와 패턴 매칭을 통한 빠른 분류
        
        Args:
            query: 사용자 질문
            
        Returns:
            Dict: 분류 결과 (agent, confidence, matched_keywords)
        """
        query_lower = query.lower()
        scores = {}
        matched_keywords = {}
        
        for agent, config in self.agent_patterns.items():
            score = 0
            matches = []
            
            # 키워드 매칭
            for keyword in config["keywords"]:
                if keyword in query_lower:
                    score += 1
                    matches.append(keyword)
            
            # 패턴 매칭
            for pattern in config["patterns"]:
                if re.search(pattern, query_lower):
                    score += 2  # 패턴 매칭에 더 높은 가중치
                    matches.append(f"pattern: {pattern}")
            
            scores[agent] = score
            matched_keywords[agent] = matches
        
        # 가장 높은 점수의 에이전트 선택
        if max(scores.values()) > 0:
            best_agent = max(scores.items(), key=lambda x: x[1])[0]
            max_score = scores[best_agent]
            
            # 신뢰도 계산 (0~1)
            confidence = min(max_score / 5.0, 1.0)  # 5점 이상이면 100% 신뢰
            
            return {
                "agent": best_agent,
                "confidence": confidence,
                "matched_keywords": matched_keywords[best_agent],
                "scores": scores
            }
        
        return {
            "agent": None,
            "confidence": 0.0,
            "matched_keywords": [],
            "scores": scores
        }
    
    def _llm_classification(self, query: str) -> Dict[str, Any]:
        """
        LLM을 사용한 정밀 분류
        
        Args:
            query: 사용자 질문
            
        Returns:
            Dict: LLM 분류 결과
        """
        classification_prompt = ChatPromptTemplate.from_messages([
            ("system", """
당신은 사용자의 질문을 분석하여 적절한 에이전트로 분류하는 전문가입니다.

사용 가능한 에이전트:
1. docs_agent: 문서 작성, 보고서 생성, 신청서 작성
   - 영업방문 결과보고서
   - 제품설명회 시행 신청서
   - 제품설명회 시행 결과보고서
   
2. employee_agent: 직원 실적 분석, 성과 평가
   - 직원별 실적 조회 및 분석
   - 목표 달성률 분석
   - 실적 트렌드 분석

반드시 다음 JSON 형식으로만 응답하세요. 다른 설명이나 텍스트 없이 JSON만 출력하세요:
{"agent": "docs_agent 또는 employee_agent", "confidence": 0.0~1.0, "reasoning": "분류 이유", "extracted_intent": "사용자 의도", "key_entities": ["주요 개체들"]}

예시:
{"agent": "docs_agent", "confidence": 0.9, "reasoning": "영업방문 보고서 작성 요청", "extracted_intent": "문서 작성", "key_entities": ["영업방문", "보고서"]}

명확하지 않은 경우:
{"agent": null, "confidence": 0.2, "reasoning": "불명확한 요청", "extracted_intent": "", "key_entities": []}
            """),
            ("human", "{query}")
        ])
        
        try:
            response = self.llm.invoke(classification_prompt.format_messages(query=query))
            content = response.content.strip()
            
            # JSON 파싱 - 여러 형태 처리
            if content.startswith('```json'):
                content = content.replace('```json', '').replace('```', '').strip()
            elif content.startswith('```'):
                content = content.replace('```', '').strip()
            
            # JSON 추출 (중괄호 찾기)
            start_idx = content.find('{')
            end_idx = content.rfind('}')
            
            if start_idx != -1 and end_idx != -1:
                json_str = content[start_idx:end_idx + 1]
                result = json.loads(json_str)
            else:
                # JSON 형식이 없으면 기본값 반환
                print(f"[WARNING] JSON 형식을 찾을 수 없음: {content[:100]}")
                return {
                    "agent": None,
                    "confidence": 0.0,
                    "reasoning": "JSON 파싱 실패",
                    "extracted_intent": "",
                    "key_entities": []
                }
            
            # 유효성 검증
            if result.get("agent") not in ["docs_agent", "employee_agent", None]:
                result["agent"] = None
                result["confidence"] = 0.0
            
            return result
            
        except Exception as e:
            print(f"[WARNING] LLM 분류 오류: {e}")
            return {
                "agent": None,
                "confidence": 0.0,
                "reasoning": f"분류 오류: {str(e)}",
                "extracted_intent": "",
                "key_entities": []
            }
    
    def _combine_results(
        self, 
        keyword_result: Dict[str, Any], 
        llm_result: Dict[str, Any],
        original_query: str
    ) -> Tuple[str, float, Dict[str, Any]]:
        """
        키워드 분류와 LLM 분류 결과를 통합하여 최종 결정
        
        Args:
            keyword_result: 키워드 기반 분류 결과
            llm_result: LLM 기반 분류 결과
            original_query: 원본 질문
            
        Returns:
            Tuple[str, float, Dict]: (최종 에이전트, 통합 신뢰도, 분석 정보)
        """
        keyword_agent = keyword_result.get("agent")
        keyword_confidence = keyword_result.get("confidence", 0.0)
        
        llm_agent = llm_result.get("agent")
        llm_confidence = llm_result.get("confidence", 0.0)
        
        # 두 결과가 일치하는 경우
        if keyword_agent == llm_agent and keyword_agent is not None:
            final_confidence = (keyword_confidence + llm_confidence) / 2
            if keyword_confidence > 0.5 and llm_confidence > 0.5:
                final_confidence = min(final_confidence * 1.2, 1.0)  # 보너스
            
            return keyword_agent, final_confidence, {
                "keyword_analysis": keyword_result,
                "llm_analysis": llm_result,
                "agreement": True,
                "original_query": original_query
            }
        
        # LLM 결과를 우선시하되, 키워드 결과도 고려
        if llm_confidence > 0.7:
            return llm_agent, llm_confidence, {
                "keyword_analysis": keyword_result,
                "llm_analysis": llm_result,
                "agreement": False,
                "original_query": original_query
            }
        
        # 키워드 결과가 강한 경우
        if keyword_confidence > 0.6 and keyword_agent is not None:
            return keyword_agent, keyword_confidence * 0.8, {
                "keyword_analysis": keyword_result,
                "llm_analysis": llm_result,
                "agreement": False,
                "original_query": original_query
            }
        
        # 둘 다 확실하지 않은 경우 - 기본값으로 docs_agent 선택
        # (사용자에게 물어볼 수도 있음)
        return "docs_agent", 0.3, {
            "keyword_analysis": keyword_result,
            "llm_analysis": llm_result,
            "agreement": False,
            "original_query": original_query,
            "fallback": True
        }
    
    def get_agent_description(self, agent_name: str) -> str:
        """
        에이전트 설명 반환
        
        Args:
            agent_name: 에이전트 이름
            
        Returns:
            str: 에이전트 설명
        """
        return self.agent_patterns.get(agent_name, {}).get(
            "description", 
            "알 수 없는 에이전트"
        )