"""
Client Analysis Agent
거래처 분석 에이전트 - 간소화된 버전
"""
import pandas as pd
import os
from typing import Dict, Any, Optional, List
from pathlib import Path
import asyncio

# 상대 경로로 tools 임포트
from ..tools.client_analysis_tools import (
    parse_query_params,
    calculate_company_grade,
    generate_analysis_report
)


class ClientAgent:
    """거래처 분석 에이전트"""
    
    def __init__(self):
        """초기화"""
        self.data_path = Path(__file__).parent / "좋은제약_거래처정보.xlsx"
        self.df = None
        self._load_data()
    
    def _load_data(self):
        """데이터 로드 및 전처리"""
        try:
            self.df = pd.read_excel(self.data_path)
            # 월 컬럼을 datetime으로 변환
            self.df['월'] = pd.to_datetime(self.df['월'].astype(str), format='%Y%m', errors='coerce')
            print(f"[OK] 데이터 로드 완료: {len(self.df)}건")
        except Exception as e:
            print(f"[ERROR] 데이터 로드 실패: {e}")
            self.df = pd.DataFrame()
    
    async def analyze_company(self, query: str) -> Dict[str, Any]:
        """거래처 분석 실행"""
        try:
            # 1. 쿼리 파싱
            params = await parse_query_params(query)
            if not params.get("success"):
                return {
                    "success": False,
                    "error": "쿼리 파싱 실패",
                    "message": params.get("error", "거래처명을 확인할 수 없습니다.")
                }
            
            company_name = params["company_name"]
            start_month = params.get("start_month")
            end_month = params.get("end_month")
            
            # 2. 거래처 존재 확인
            if company_name not in self.df["거래처ID"].values:
                # 유사한 이름 찾기
                similar = self._find_similar_companies(company_name)
                
                # 유사한 거래처가 1개만 있으면 자동 선택
                if len(similar) == 1:
                    company_name = similar[0]
                    print(f"[OK] 자동 선택: {company_name}")
                else:
                    return {
                        "success": False,
                        "error": "거래처를 찾을 수 없습니다",
                        "message": f"'{company_name}'을(를) 찾을 수 없습니다.",
                        "suggestions": similar[:5] if similar else []
                    }
            
            # 3. 등급 계산
            grade_result = calculate_company_grade(
                company_name, 
                self.df, 
                start_month, 
                end_month
            )
            
            # 4. 분석 레포트 생성
            report = await generate_analysis_report(
                company_name,
                grade_result,
                self.df,
                start_month,
                end_month
            )
            
            return {
                "success": True,
                "company_name": company_name,
                "period": f"{start_month}~{end_month}" if start_month else "전체기간",
                "grade_result": grade_result,
                "report": report
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"분석 중 오류가 발생했습니다: {str(e)}"
            }
    
    def _find_similar_companies(self, query: str) -> list:
        """유사한 거래처명 찾기"""
        all_companies = self.df["거래처ID"].unique().tolist()
        similar = []
        
        query_lower = query.lower()
        for company in all_companies:
            if query_lower in company.lower():
                similar.append(company)
        
        return similar
    
    def get_company_list(self) -> list:
        """전체 거래처 목록 반환"""
        if self.df is not None and not self.df.empty:
            return sorted(self.df["거래처ID"].unique().tolist())
        return []
    
    def get_company_summary(self, company_name: str) -> Dict[str, Any]:
        """거래처 간단 정보 반환"""
        company_data = self.df[self.df["거래처ID"] == company_name]
        
        if company_data.empty:
            return {"error": "거래처를 찾을 수 없습니다"}
        
        latest = company_data.iloc[-1]  # 최신 데이터
        
        return {
            "거래처명": company_name,
            "최근월": str(latest["월"]),
            "최근매출": int(latest["매출"]),
            "월방문횟수": int(latest["월방문횟수"]),
            "총환자수": int(latest["총환자수"])
        }


# 전역 에이전트 인스턴스
agent = ClientAgent()


async def run(query: str, session_id: str, messages: List[Dict] = None) -> Dict[str, Any]:
    """
    Client Agent 실행 함수 (멀티턴 대화 지원)
    
    Args:
        query: 사용자 쿼리
        session_id: 세션 ID
        messages: 이전 대화 기록
        
    Returns:
        Dict: 실행 결과
    """
    try:
        # 참조 해결 없이 원본 쿼리 사용
        enhanced_query = query
        
        # 거래처 분석 실행
        result = await agent.analyze_company(enhanced_query)
        
        if result["success"]:
            return {
                "success": True,
                "response": result["report"],
                "report": result["report"],
                "agent": "client_agent",
                "session_id": session_id,
                "grade_result": result.get("grade_result", {}),
                "company_name": result.get("company_name", "")
            }
        else:
            # 오류 메시지 생성
            error_msg = result.get("message", "분석에 실패했습니다.")
            
            # 추천 거래처가 있으면 추가
            if result.get("suggestions"):
                error_msg += "\n\n[TIP] 혹시 이 거래처를 찾으셨나요?"
                for i, suggestion in enumerate(result["suggestions"][:5], 1):
                    error_msg += f"\n{i}. {suggestion}"
            
            return {
                "success": False,
                "response": error_msg,
                "error": result.get("error", "Unknown error"),
                "agent": "client_agent",
                "session_id": session_id
            }
            
    except Exception as e:
        return {
            "success": False,
            "response": f"거래처 분석 중 오류가 발생했습니다: {str(e)}",
            "error": str(e),
            "agent": "client_agent",
            "session_id": session_id
        }