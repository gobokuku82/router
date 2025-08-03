import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import openai
import os

class EmployeeQueryAnalyzer:
    """직원 실적 분석 쿼리 분석 클래스"""
    
    def __init__(self):
        self.common_employee_names = ["최수아", "조시현"]  # 알려진 직원명들
        self.period_patterns = {
            r'(\d{4})년\s*(\d{1,2})월': 'YYYYMM',
            r'(\d{4})\s*년': 'YYYY',
            r'(\d{6})': 'YYYYMM',
            r'(\d{4})': 'YYYY',
            r'지난\s*(\d+)\s*개월': 'LAST_N_MONTHS',
            r'최근\s*(\d+)\s*개월': 'LAST_N_MONTHS',
            r'작년': 'LAST_YEAR',
            r'올해': 'THIS_YEAR',
            r'이번\s*달': 'THIS_MONTH',
            r'지난\s*달': 'LAST_MONTH'
        }
    
    def analyze_query(self, query: str) -> Dict[str, Any]:
        """사용자 쿼리를 분석하여 필요한 정보를 추출합니다."""
        analysis_result = {
            "employee_name": None,
            "start_period": None,
            "end_period": None,
            "analysis_type": "종합분석",
            "specific_requests": [],
            "confidence": 0.0
        }
        
        # 1. 직원명 추출
        employee_name = self._extract_employee_name(query)
        if employee_name:
            analysis_result["employee_name"] = employee_name
            analysis_result["confidence"] += 0.3
        
        # 2. 기간 추출
        start_period, end_period = self._extract_period(query)
        if start_period:
            analysis_result["start_period"] = start_period
            analysis_result["confidence"] += 0.2
        if end_period:
            analysis_result["end_period"] = end_period
            analysis_result["confidence"] += 0.2
        
        # 3. 분석 유형 추출
        analysis_type = self._extract_analysis_type(query)
        analysis_result["analysis_type"] = analysis_type
        analysis_result["confidence"] += 0.2
        
        # 4. 특정 요청사항 추출
        specific_requests = self._extract_specific_requests(query)
        analysis_result["specific_requests"] = specific_requests
        if specific_requests:
            analysis_result["confidence"] += 0.1
        
        # 5. 기본값 설정 (추출되지 않은 경우)
        analysis_result = self._set_defaults(analysis_result)
        
        return analysis_result
    
    def _extract_employee_name(self, query: str) -> Optional[str]:
        """쿼리에서 직원명을 추출합니다."""
        # 직접 명시된 직원명 찾기
        for name in self.common_employee_names:
            if name in query:
                return name
        
        # 패턴으로 직원명 찾기
        name_patterns = [
            r'(\w+)\s*(?:씨|님|직원|담당자)의?\s*실적',
            r'(\w+)\s*(?:씨|님|직원|담당자)\s*분석',
            r'직원\s*(\w+)',
            r'담당자\s*(\w+)'
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, query)
            if match:
                potential_name = match.group(1)
                if len(potential_name) >= 2:  # 최소 2글자 이상
                    return potential_name
        
        return None
    
    def _extract_period(self, query: str) -> Tuple[Optional[str], Optional[str]]:
        """쿼리에서 기간을 추출합니다."""
        current_date = datetime.now()
        
        # 구체적인 기간 패턴 찾기
        for pattern, format_type in self.period_patterns.items():
            matches = re.findall(pattern, query)
            if matches:
                if format_type == 'YYYYMM':
                    if isinstance(matches[0], tuple):
                        year, month = matches[0]
                        period = f"{year}{month.zfill(2)}"
                    else:
                        period = matches[0]
                    return period, period
                elif format_type == 'YYYY':
                    year = matches[0] if isinstance(matches[0], str) else matches[0][0]
                    return f"{year}01", f"{year}12"
                elif format_type == 'LAST_N_MONTHS':
                    months_back = int(matches[0])
                    end_date = current_date
                    start_date = end_date - timedelta(days=30 * months_back)
                    return start_date.strftime("%Y%m"), end_date.strftime("%Y%m")
        
        # 상대적 기간 처리
        if "작년" in query:
            last_year = current_date.year - 1
            return f"{last_year}01", f"{last_year}12"
        elif "올해" in query:
            return f"{current_date.year}01", f"{current_date.year}12"
        elif "이번 달" in query:
            return current_date.strftime("%Y%m"), current_date.strftime("%Y%m")
        elif "지난 달" in query:
            last_month = current_date - timedelta(days=30)
            return last_month.strftime("%Y%m"), last_month.strftime("%Y%m")
        
        # 범위 기간 추출 (예: 2023년 12월부터 2024년 3월까지)
        range_pattern = r'(\d{4})년?\s*(\d{1,2})월?[부터|에서]*\s*[~|-|부터|까지]*\s*(\d{4})년?\s*(\d{1,2})월?'
        range_match = re.search(range_pattern, query)
        if range_match:
            start_year, start_month, end_year, end_month = range_match.groups()
            start_period = f"{start_year}{start_month.zfill(2)}"
            end_period = f"{end_year}{end_month.zfill(2)}"
            return start_period, end_period
        
        return None, None
    
    def _extract_analysis_type(self, query: str) -> str:
        """쿼리에서 분석 유형을 추출합니다."""
        analysis_keywords = {
            "트렌드": ["트렌드", "추세", "변화", "흐름"],
            "목표달성": ["목표", "달성", "성과", "평가"],
            "제품분석": ["제품", "품목", "상품", "아이템"],
            "거래처분석": ["거래처", "고객", "병원", "클라이언트"],
            "월별분석": ["월별", "매월", "월간"],
            "종합분석": ["종합", "전체", "전반", "overall"]
        }
        
        for analysis_type, keywords in analysis_keywords.items():
            for keyword in keywords:
                if keyword in query:
                    return analysis_type
        
        return "종합분석"
    
    def _extract_specific_requests(self, query: str) -> List[str]:
        """쿼리에서 특정 요청사항을 추출합니다."""
        requests = []
        
        request_patterns = {
            "보고서 생성": ["보고서", "리포트", "문서"],
            "차트 분석": ["차트", "그래프", "시각화"],
            "비교 분석": ["비교", "대비", "vs"],
            "개선 방안": ["개선", "방안", "제안", "권고"],
            "예측 분석": ["예측", "전망", "미래"]
        }
        
        for request_type, keywords in request_patterns.items():
            for keyword in keywords:
                if keyword in query:
                    requests.append(request_type)
                    break
        
        return list(set(requests))  # 중복 제거
    
    def _set_defaults(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """기본값을 설정합니다."""
        current_date = datetime.now()
        
        # 직원명이 없으면 기본 직원으로 설정
        if not analysis_result["employee_name"]:
            analysis_result["employee_name"] = "최수아"  # 기본 직원
        
        # 기간이 없으면 최근 4개월로 설정 (하드코딩된 데이터 기간)
        if not analysis_result["start_period"]:
            analysis_result["start_period"] = "202312"  # 실제 데이터가 있는 기간
            analysis_result["end_period"] = "202403"    # 실제 데이터가 있는 기간
        elif not analysis_result["end_period"]:
            # 시작 기간만 있는 경우 3개월 범위로 설정
            start_period = analysis_result["start_period"]
            if len(start_period) == 6:  # YYYYMM 형식
                try:
                    year = int(start_period[:4])
                    month = int(start_period[4:])
                    # 3개월 후 계산
                    if month <= 9:
                        end_month = month + 3
                        end_year = year
                    else:
                        end_month = month + 3 - 12
                        end_year = year + 1
                    analysis_result["end_period"] = f"{end_year}{end_month:02d}"
                except:
                    analysis_result["end_period"] = "202403"
            else:
                analysis_result["end_period"] = "202403"
        
        return analysis_result
    
    def analyze_with_llm(self, query: str) -> Optional[Dict[str, Any]]:
        """LLM을 사용하여 쿼리를 더 정확히 분석합니다."""
        try:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                return None
            
            client = openai.OpenAI(api_key=api_key)
            
            prompt = f"""
다음 직원 실적 분석 요청을 분석하여 JSON 형태로 정보를 추출해주세요:

요청: "{query}"

추출해야 할 정보:
1. employee_name: 직원명 (최수아, 조시현 중 하나, 없으면 "최수아")
2. start_period: 시작 기간 (YYYYMM 형식, 예: "202312")
3. end_period: 종료 기간 (YYYYMM 형식, 예: "202403")
4. analysis_type: 분석 유형 ("종합분석", "트렌드분석", "목표달성분석", "제품분석", "거래처분석" 중 하나)
5. specific_requests: 특정 요청사항 배열 (예: ["보고서 생성", "차트 분석"])

응답은 다음 JSON 형식으로만 해주세요:
{{
    "employee_name": "최수아",
    "start_period": "202312",
    "end_period": "202403",
    "analysis_type": "종합분석",
    "specific_requests": ["보고서 생성"]
}}
"""
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "당신은 직원 실적 분석 요청을 정확히 파싱하는 전문가입니다."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.1
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            result["confidence"] = 0.9  # LLM 분석의 신뢰도는 높게 설정
            
            return result
            
        except Exception as e:
            print(f"LLM 쿼리 분석 오류: {e}")
            return None
    
    def get_enhanced_analysis(self, query: str) -> Dict[str, Any]:
        """기본 분석과 LLM 분석을 결합하여 최적의 결과를 반환합니다."""
        # 기본 분석 수행
        basic_analysis = self.analyze_query(query)
        
        # LLM 분석 시도
        llm_analysis = self.analyze_with_llm(query)
        
        if llm_analysis and llm_analysis.get("confidence", 0) > basic_analysis.get("confidence", 0):
            return llm_analysis
        else:
            return basic_analysis 