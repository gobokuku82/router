from typing import Dict, List, Any, Optional, TypedDict
from datetime import datetime
import openai
import os
from langgraph.graph import StateGraph, END
from .db_manager import EmployeeDBManager
from .query_analyzer import EmployeeQueryAnalyzer
from ..tools.calculation_tools import PerformanceCalculationTools

# 상태 정의
class AnalysisState(TypedDict):
    query: str
    query_analysis: Optional[Dict[str, Any]]
    employee_name: Optional[str]
    start_period: Optional[str]
    end_period: Optional[str]
    analysis_type: Optional[str]
    performance_data: Optional[Dict[str, Any]]
    target_data: Optional[Dict[str, Any]]
    analysis_results: Optional[Dict[str, Any]]
    report: Optional[str]
    error: Optional[str]

class EnhancedEmployeeAgent:
    """개선된 직원 실적 분석 에이전트"""
    
    def __init__(self):
        self.db_manager = EmployeeDBManager()
        self.query_analyzer = EmployeeQueryAnalyzer()
        self.calc_tools = PerformanceCalculationTools()
        self.graph = self._create_graph()
    
    def _create_graph(self):
        """LangGraph StateGraph를 생성합니다."""
        workflow = StateGraph(AnalysisState)
        
        # 노드 추가
        workflow.add_node("analyze_query", self._analyze_query_node)
        workflow.add_node("load_data", self._load_data_node)
        workflow.add_node("perform_analysis", self._perform_analysis_node)
        workflow.add_node("generate_report", self._generate_report_node)
        
        # 엣지 연결
        workflow.set_entry_point("analyze_query")
        workflow.add_edge("analyze_query", "load_data")
        workflow.add_edge("load_data", "perform_analysis")
        workflow.add_edge("perform_analysis", "generate_report")
        workflow.add_edge("generate_report", END)
        
        return workflow.compile()
    
    def _analyze_query_node(self, state: AnalysisState) -> AnalysisState:
        """사용자 쿼리를 분석하는 노드"""
        try:
            query = state["query"]
            
            # 쿼리 분석 수행
            query_analysis = self.query_analyzer.get_enhanced_analysis(query)
            
            # 쿼리 분석 결과 검증
            if not query_analysis:
                state["error"] = "쿼리 분석에 실패했습니다."
                return state
            
            # 필수 정보 확인 및 기본값 설정
            employee_name = query_analysis.get("employee_name")
            start_period = query_analysis.get("start_period") 
            end_period = query_analysis.get("end_period")
            
            if not employee_name:
                print("[WARNING] 직원명이 추출되지 않아 기본값(최수아)을 사용합니다.")
                employee_name = "최수아"
            
            if not start_period or not end_period:
                print("[WARNING] 기간이 추출되지 않아 기본값(202312~202403)을 사용합니다.")
                start_period = "202312"
                end_period = "202403"
            
            state["query_analysis"] = query_analysis
            state["employee_name"] = employee_name
            state["start_period"] = start_period
            state["end_period"] = end_period
            state["analysis_type"] = query_analysis.get("analysis_type", "종합분석")
            
            print(f"[OK] 쿼리 분석 완료: 직원={employee_name}, 기간={start_period}~{end_period}")
            
        except Exception as e:
            state["error"] = f"쿼리 분석 오류: {str(e)}"
            print(f"[ERROR] 쿼리 분석 오류: {e}")
            
            # 오류 발생시 기본값으로 설정
            print("[RETRY] 기본값으로 분석을 계속 진행합니다.")
            state["employee_name"] = "최수아"
            state["start_period"] = "202312" 
            state["end_period"] = "202403"
            state["analysis_type"] = "종합분석"
            state["error"] = None  # 오류 상태 초기화
        
        return state
    
    def _load_data_node(self, state: AnalysisState) -> AnalysisState:
        """데이터를 로드하는 노드"""
        try:
            if state.get("error"):
                return state
            
            employee_name = state["employee_name"]
            start_period = state["start_period"]
            end_period = state["end_period"]
            
            print(f"[DATA] 데이터 로드 시작: {employee_name}, {start_period}~{end_period}")
            
            # 실적 데이터 로드
            performance_summary = self.db_manager.get_performance_summary(
                employee_name, start_period, end_period
            )
            
            # 실적 데이터가 없는 경우 확인
            if performance_summary["total_performance"] <= 0:
                print(f"[WARNING] '{employee_name}' 직원의 {start_period}~{end_period} 기간 실적 데이터가 없습니다.")
                # 사용 가능한 직원 목록 확인
                available_employees = self.db_manager.get_available_employees()
                if available_employees:
                    print(f"[INFO] 사용 가능한 직원: {', '.join(available_employees)}")
                    # 첫 번째 사용 가능한 직원으로 재시도
                    alternative_employee = available_employees[0]
                    print(f"[RETRY] '{alternative_employee}' 직원 데이터로 분석을 진행합니다.")
                    
                    performance_summary = self.db_manager.get_performance_summary(
                        alternative_employee, start_period, end_period
                    )
                    state["employee_name"] = alternative_employee
            
            # 목표 대비 실적 데이터 로드
            target_vs_performance = self.db_manager.get_target_vs_performance(
                state["employee_name"], start_period, end_period
            )
            
            # 트렌드 분석 데이터 로드
            trend_analysis = self.db_manager.analyze_performance_trend(
                state["employee_name"], start_period, end_period
            )
            
            state["performance_data"] = performance_summary
            state["target_data"] = target_vs_performance
            
            # 추가 분석 데이터를 analysis_results에 임시 저장
            state["analysis_results"] = {
                "trend_analysis": trend_analysis
            }
            
            print(f"[OK] 데이터 로드 완료: 실적 {performance_summary['total_performance']:,.0f}원")
            
        except Exception as e:
            state["error"] = f"데이터 로드 오류: {str(e)}"
            print(f"[ERROR] 데이터 로드 오류: {e}")
            
            # 오류 발생시 더미 데이터로 설정하여 분석 계속 진행
            print("🔄 기본 데이터로 분석을 계속 진행합니다.")
            state["performance_data"] = {
                "employee_name": state["employee_name"],
                "period": f"{state['start_period']}~{state['end_period']}",
                "total_performance": 0,
                "monthly_breakdown": [],
                "product_breakdown": [],
                "client_breakdown": []
            }
            # 더미 데이터 반환 (오류 방지)
            state["target_data"] = {
                "total_performance": 0,
                "total_target": 0,
                "achievement_rate": 0,
                "evaluation": "데이터 없음",
                "grade": "N/A",  # recommendation → grade로 변경
                "gap_amount": 0
            }
            state["analysis_results"] = {
                "trend_analysis": {"trend": "데이터 없음", "analysis": "분석할 데이터가 없습니다."}
            }
            state["error"] = None  # 오류 상태 초기화
        
        return state
    
    def _perform_analysis_node(self, state: AnalysisState) -> AnalysisState:
        """실적 분석을 수행하는 노드"""
        try:
            if state.get("error"):
                return state
            
            performance_data = state["performance_data"]
            target_data = state["target_data"]
            analysis_type = state["analysis_type"]
            
            analysis_results = state["analysis_results"] or {}
            
            # 1. 기본 성과 분석
            total_performance = performance_data["total_performance"]
            monthly_data = performance_data["monthly_breakdown"]
            
            # 2. 계산 도구를 사용한 고급 분석
            if len(monthly_data) >= 2:
                monthly_amounts = [data["amount"] for data in monthly_data]
                
                # 트렌드 분석
                trend_calc = self.calc_tools.calculate_trend_analysis(monthly_amounts)
                analysis_results["detailed_trend"] = trend_calc
                
                # 분산 분석
                variance_analysis = self.calc_tools.calculate_variance_analysis(monthly_amounts)
                analysis_results["variance_analysis"] = variance_analysis
                
                # 계절성 분석
                seasonal_analysis = self.calc_tools.calculate_seasonal_analysis(monthly_data)
                analysis_results["seasonal_analysis"] = seasonal_analysis
                
                # 예측 분석
                forecast = self.calc_tools.calculate_forecast(monthly_amounts, periods=3)
                analysis_results["forecast"] = forecast
            
            # 3. 제품 분석
            if performance_data["product_breakdown"]:
                product_pareto = self.calc_tools.calculate_pareto_analysis(
                    performance_data["product_breakdown"], "amount"
                )
                analysis_results["product_pareto"] = product_pareto
            
            # 4. 거래처 분석
            if performance_data["client_breakdown"]:
                client_pareto = self.calc_tools.calculate_pareto_analysis(
                    performance_data["client_breakdown"], "amount"
                )
                analysis_results["client_pareto"] = client_pareto
            
            # 5. 달성 분석
            achievement_analysis = {
                "total_performance": target_data["total_performance"],
                "total_target": target_data["total_target"],
                "achievement_rate": target_data["achievement_rate"],
                "evaluation": target_data["evaluation"],
                "grade": target_data.get("grade", "N/A"),  # recommendation → grade로 변경
                "gap_amount": target_data["gap_amount"]
            }
            analysis_results["achievement_analysis"] = achievement_analysis
            
            # 6. 종합 평가
            comprehensive_evaluation = self._generate_comprehensive_evaluation(
                analysis_results, performance_data, target_data
            )
            analysis_results["comprehensive_evaluation"] = comprehensive_evaluation
            
            state["analysis_results"] = analysis_results
            
            print("[OK] 실적 분석 완료")
            
        except Exception as e:
            state["error"] = f"분석 수행 오류: {str(e)}"
            print(f"[ERROR] 분석 수행 오류: {e}")
        
        return state
    
    def _generate_comprehensive_evaluation(self, analysis_results: Dict[str, Any], 
                                         performance_data: Dict[str, Any], 
                                         target_data: Dict[str, Any]) -> Dict[str, Any]:
        """종합 평가를 생성합니다."""
        
        # 성과 점수 계산 (100점 만점)
        score_components = {}
        
        # 1. 목표 달성률 점수 (40점)
        achievement_rate = target_data.get("achievement_rate", 0)
        if achievement_rate >= 120:
            achievement_score = 40
        elif achievement_rate >= 100:
            achievement_score = 35
        elif achievement_rate >= 80:
            achievement_score = 25
        elif achievement_rate >= 60:
            achievement_score = 15
        else:
            achievement_score = 5
        score_components["achievement"] = achievement_score
        
        # 2. 트렌드 점수 (30점)
        trend_data = analysis_results.get("detailed_trend", {})
        trend = trend_data.get("trend", "안정")
        if trend in ["강한 상승", "상승"]:
            trend_score = 30
        elif trend == "안정":
            trend_score = 20
        else:
            trend_score = 10
        score_components["trend"] = trend_score
        
        # 3. 안정성 점수 (20점)
        variance_data = analysis_results.get("variance_analysis", {})
        stability = variance_data.get("stability", "보통")
        stability_score_map = {
            "매우 안정": 20, "안정": 16, "보통": 12, 
            "불안정": 8, "매우 불안정": 4
        }
        stability_score = stability_score_map.get(stability, 10)
        score_components["stability"] = stability_score
        
        # 4. 집중도 점수 (10점) - 파레토 분석 기반
        product_pareto = analysis_results.get("product_pareto", {})
        if product_pareto.get("pareto_point"):
            # 파레토 효율성이 좋을수록 높은 점수
            pareto_ratio = product_pareto["pareto_point"] / product_pareto["total_items"]
            if pareto_ratio <= 0.2:  # 20% 이하가 80% 차지
                concentration_score = 10
            elif pareto_ratio <= 0.3:
                concentration_score = 8
            else:
                concentration_score = 6
        else:
            concentration_score = 5
        score_components["concentration"] = concentration_score
        
        # 총점 계산
        total_score = sum(score_components.values())
        
        # 등급 결정
        if total_score >= 90:
            grade = "S"
            grade_desc = "탁월"
        elif total_score >= 80:
            grade = "A"
            grade_desc = "우수"
        elif total_score >= 70:
            grade = "B"
            grade_desc = "양호"
        elif total_score >= 60:
            grade = "C"
            grade_desc = "보통"
        else:
            grade = "D"
            grade_desc = "개선 필요"
        
        # 개선 우선순위 결정
        improvement_priorities = []
        sorted_components = sorted(score_components.items(), key=lambda x: x[1])
        
        for component, score in sorted_components[:2]:  # 가장 낮은 2개 영역
            if component == "achievement" and score < 30:
                improvement_priorities.append("목표 달성률 개선")
            elif component == "trend" and score < 25:
                improvement_priorities.append("실적 증가 추세 확보")
            elif component == "stability" and score < 15:
                improvement_priorities.append("실적 안정성 확보")
            elif component == "concentration" and score < 8:
                improvement_priorities.append("핵심 제품 집중도 향상")
        
        return {
            "total_score": int(total_score),  # numpy 타입 방지
            "grade": grade,
            "grade_description": grade_desc,
            "score_breakdown": {k: int(v) for k, v in score_components.items()},  # numpy 타입 방지
            "improvement_priorities": improvement_priorities,
            "strengths": self._identify_strengths(score_components),
            "weaknesses": self._identify_weaknesses(score_components)
        }
    
    def _identify_strengths(self, score_components: Dict[str, int]) -> List[str]:
        """강점을 식별합니다."""
        strengths = []
        if score_components.get("achievement", 0) >= 35:
            strengths.append("목표 달성률 우수")
        if score_components.get("trend", 0) >= 25:
            strengths.append("성장 추세 양호")
        if score_components.get("stability", 0) >= 16:
            strengths.append("실적 안정성 확보")
        if score_components.get("concentration", 0) >= 8:
            strengths.append("제품 집중도 효율적")
        
        return strengths if strengths else ["기본 실적 유지"]
    
    def _identify_weaknesses(self, score_components: Dict[str, int]) -> List[str]:
        """약점을 식별합니다."""
        weaknesses = []
        if score_components.get("achievement", 0) < 25:
            weaknesses.append("목표 달성률 부족")
        if score_components.get("trend", 0) < 20:
            weaknesses.append("성장 추세 부진")
        if score_components.get("stability", 0) < 12:
            weaknesses.append("실적 변동성 과대")
        if score_components.get("concentration", 0) < 6:
            weaknesses.append("제품 포트폴리오 분산 과다")
        
        return weaknesses if weaknesses else ["특별한 약점 없음"]
    
    def _generate_report_node(self, state: AnalysisState) -> AnalysisState:
        """보고서를 생성하는 노드"""
        try:
            if state.get("error"):
                return state
            
            analysis_results = state["analysis_results"]
            performance_data = state["performance_data"]
            target_data = state["target_data"]
            query_analysis = state["query_analysis"]
            
            # LLM을 사용한 지능형 보고서 생성
            report = self._generate_intelligent_report(
                analysis_results, performance_data, target_data, query_analysis
            )
            
            state["report"] = report
            
            print("[OK] 보고서 생성 완료")
            
        except Exception as e:
            state["error"] = f"보고서 생성 오류: {str(e)}"
            print(f"[ERROR] 보고서 생성 오류: {e}")
        
        return state
    
    def _generate_intelligent_report(self, analysis_results: Dict[str, Any], 
                                   performance_data: Dict[str, Any], 
                                   target_data: Dict[str, Any],
                                   query_analysis: Dict[str, Any]) -> str:
        """LLM을 활용한 지능형 보고서 생성"""
        
        try:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                return self._generate_basic_report(analysis_results, performance_data, target_data)
            
            # 데이터 요약 준비
            employee_name = query_analysis.get("employee_name", "직원")
            period = f"{query_analysis.get('start_period')}~{query_analysis.get('end_period')}"
            
            comprehensive_eval = analysis_results.get("comprehensive_evaluation", {})
            trend_analysis = analysis_results.get("detailed_trend", {})
            achievement_analysis = analysis_results.get("achievement_analysis", {})
            
            # LLM 프롬프트 생성
            prompt = f"""
다음 직원 실적 분석 데이터를 바탕으로 전문적이고 실행 가능한 인사이트가 담긴 보고서를 작성해주세요.

## 기본 정보
- 직원명: {employee_name}
- 분석 기간: {period}
- 총 실적: {performance_data.get('total_performance', 0):,.0f}원
- 목표 달성률: {achievement_analysis.get('achievement_rate', 0):.1f}%

## 종합 평가
- 총점: {comprehensive_eval.get('total_score', 0)}점/100점
- 등급: {comprehensive_eval.get('grade', 'N/A')} ({comprehensive_eval.get('grade_description', '')})
- 강점: {', '.join(comprehensive_eval.get('strengths', []))}
- 약점: {', '.join(comprehensive_eval.get('weaknesses', []))}

## 트렌드 분석
- 추세: {trend_analysis.get('trend', '정보 없음')}
- 예측 신뢰도: {trend_analysis.get('trend_strength', '정보 없음')}

## 개선 우선순위
{chr(10).join([f"- {priority}" for priority in comprehensive_eval.get('improvement_priorities', [])])}

다음 형식으로 작성해주세요:

[직원 실적 분석 보고서]

1. 실행 요약
[전체적인 성과를 3-4줄로 요약]

2. 주요 성과 분석
[구체적인 수치와 함께 성과 분석]

3. 트렌드 및 예측
[실적 추세와 향후 전망]

4. 강점과 개선점
[명확한 강점과 개선이 필요한 영역]

5. 실행 권고사항
[구체적이고 실행 가능한 3-5개 권고사항]

주의사항:
- 전문적이지만 이해하기 쉬운 언어 사용
- 구체적인 수치와 데이터 기반 분석
- 실행 가능한 개선 방안 제시
- 긍정적 톤 유지하되 개선점 명확히 지적
- 마크다운 형식 사용하지 말고 일반 텍스트로 작성
"""
            
            client = openai.OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "당신은 전문적인 인사 성과 분석가입니다. 데이터 기반의 정확하고 실행 가능한 인사이트를 제공합니다."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"LLM 보고서 생성 실패: {e}")
            return self._generate_basic_report(analysis_results, performance_data, target_data)
    
    def _generate_basic_report(self, analysis_results: Dict[str, Any], 
                             performance_data: Dict[str, Any], 
                             target_data: Dict[str, Any]) -> str:
        """기본 보고서 생성 (LLM 실패시 폴백)"""
        
        comprehensive_eval = analysis_results.get("comprehensive_evaluation", {})
        achievement_analysis = analysis_results.get("achievement_analysis", {})
        trend_analysis = analysis_results.get("detailed_trend", {})
        
        report = f"""[직원 실적 분석 보고서]

1. 실행 요약

분석 결과 총 {performance_data.get('total_performance', 0):,.0f}원의 실적을 달성하였으며, 
목표 달성률은 {achievement_analysis.get('achievement_rate', 0):.1f}%입니다. 
종합 평가 점수는 {comprehensive_eval.get('total_score', 0)}점으로 {comprehensive_eval.get('grade_description', '평가 불가')} 수준입니다.

2. 주요 성과 분석

월별 실적 추이를 분석한 결과 {trend_analysis.get('trend', '안정적인')} 패턴을 보이고 있습니다. 
{achievement_analysis.get('evaluation', '목표 달성 상황')}이며, 
{achievement_analysis.get('grade', 'N/A')} 등급을 받았습니다.

3. 트렌드 및 예측

실적 트렌드는 {trend_analysis.get('trend', '안정')} 상태이며, 
예측 신뢰도는 {trend_analysis.get('trend_strength', '보통')} 수준입니다.

4. 강점과 개선점

주요 강점: {', '.join(comprehensive_eval.get('strengths', ['기본 실적 유지']))}
개선 필요 영역: {', '.join(comprehensive_eval.get('weaknesses', ['특별한 약점 없음']))}

5. 실행 권고사항

{chr(10).join([f"• {priority}" for priority in comprehensive_eval.get('improvement_priorities', ['현재 수준 유지'])])}

보고서 작성일시: {datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')}
"""
        
        return report
    
    def analyze_employee_performance(self, query: str) -> Dict[str, Any]:
        """직원 실적 분석을 실행합니다."""
        initial_state = {
            "query": query,
            "query_analysis": None,
            "employee_name": None,
            "start_period": None,
            "end_period": None,
            "analysis_type": None,
            "performance_data": None,
            "target_data": None,
            "analysis_results": None,
            "report": None,
            "error": None
        }
        
        try:
            # LangGraph 워크플로우 실행
            result = self.graph.invoke(initial_state)
            
            if result.get("error"):
                return {
                    "success": False,
                    "error": result["error"],
                    "message": "분석 처리 중 오류가 발생했습니다."
                }
            
            # 성공적인 결과 반환
            return {
                "success": True,
                "employee_name": result.get("employee_name"),
                "period": f"{result.get('start_period')}~{result.get('end_period')}",
                "total_performance": int(result.get("performance_data", {}).get("total_performance", 0)),  # numpy 타입 방지
                "achievement_rate": float(result.get("target_data", {}).get("achievement_rate", 0)),  # numpy 타입 방지
                "evaluation": result.get("analysis_results", {}).get("comprehensive_evaluation", {}).get("grade_description", "평가 불가"),
                "report": result.get("report", "보고서 생성 실패"),
                "analysis_details": result.get("analysis_results", {}),
                "message": "실적 분석이 완료되었습니다."
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "분석 실행 중 오류가 발생했습니다."
            }
    
    def run(self, user_input: str = None) -> Dict[str, Any]:
        """
        라우터와 통합하기 위한 표준 run() 인터페이스
        
        Args:
            user_input: 사용자 입력 쿼리
            
        Returns:
            Dict: 실행 결과 (success, result 등)
        """
        if not user_input:
            return {
                "success": False,
                "error": "입력이 필요합니다."
            }
        
        try:
            # analyze_employee_performance 메서드 호출
            result = self.analyze_employee_performance(user_input)
            
            # 표준 형식으로 변환
            if result.get("success", False):
                return {
                    "success": True,
                    "result": {
                        "report": result.get("report", ""),
                        "employee_name": result.get("employee_name"),
                        "period": result.get("period"),
                        "total_performance": result.get("total_performance"),
                        "achievement_rate": result.get("achievement_rate"),
                        "evaluation": result.get("evaluation"),
                        "analysis_details": result.get("analysis_details", {})
                    }
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "분석 실패")
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"실행 중 오류: {str(e)}"
            }

# 전역 에이전트 인스턴스
enhanced_agent = EnhancedEmployeeAgent()

async def analyze_employee_query(query: str) -> Dict[str, Any]:
    """비동기 쿼리 분석 함수 (API에서 호출)"""
    return enhanced_agent.analyze_employee_performance(query)

async def run(query: str, session_id: str) -> Dict[str, Any]:
    """router_api.py에서 호출하는 표준 인터페이스 (기존 유지)"""
    try:
        # EnhancedEmployeeAgent를 사용하여 쿼리 분석
        result = enhanced_agent.analyze_employee_performance(query)
        
        # 결과가 성공적으로 반환된 경우
        if result.get("success", False):
            return {
                "success": True,
                "response": result.get("report", "분석 결과를 생성할 수 없습니다."),
                "report": result.get("report", ""),
                "agent": "employee_agent",
                "session_id": session_id,
                "employee_name": result.get("employee_name"),
                "period": result.get("period"),
                "total_performance": result.get("total_performance"),
                "achievement_rate": result.get("achievement_rate"),
                "evaluation": result.get("evaluation"),
                "analysis_details": result.get("analysis_details", {})
            }
        else:
            # 오류가 발생한 경우
            error_message = result.get("error", "알 수 없는 오류")
            return {
                "success": False,
                "response": f"분석 중 오류가 발생했습니다: {error_message}",
                "error": error_message,
                "agent": "employee_agent",
                "session_id": session_id
            }
            
    except Exception as e:
        # 예외 처리
        error_message = str(e)
        print(f"[ERROR] Employee Agent 실행 오류: {error_message}")
        
        return {
            "success": False,
            "response": f"직원 실적 분석 중 오류가 발생했습니다: {error_message}",
            "error": error_message,
            "agent": "employee_agent",
            "session_id": session_id
        } 
                  