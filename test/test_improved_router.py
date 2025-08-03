"""
개선된 라우터 통합 테스트
"""
import sys
from pathlib import Path

# 경로 설정
project_root = Path(__file__).parent.parent
backend_path = project_root / "backend"
sys.path.insert(0, str(backend_path))

print(f"프로젝트 루트: {project_root}")
print(f"sys.path에 추가: {backend_path}")

# 임포트
from app.services.router_agent.classifier import AgentClassifier
from app.services.router_agent.router import RouterAgent

def test_classifier_improved():
    """개선된 분류기 테스트"""
    print("\n=== 분류기 개선 테스트 ===")
    
    classifier = AgentClassifier()
    
    test_cases = [
        ("영업방문 결과보고서 작성해줘", "docs_agent"),
        ("김도윤 직원의 실적을 분석해줘", "employee_agent"),
        ("제품설명회 신청서 만들어줘", "docs_agent"),
        ("이번 분기 매출 트렌드 보여줘", "employee_agent"),
    ]
    
    for query, expected in test_cases:
        agent, confidence, analysis = classifier.classify(query)
        success = agent == expected
        print(f"\n[테스트] {query}")
        print(f"  예상: {expected}, 결과: {agent}")
        print(f"  신뢰도: {confidence:.2f}")
        print(f"  성공: {'O' if success else 'X'}")
        
        # 디버깅 정보
        if not success:
            llm_analysis = analysis.get('llm_analysis', {})
            print(f"  LLM 분석: {llm_analysis.get('agent', 'N/A')}")
            print(f"  LLM 이유: {llm_analysis.get('reasoning', 'N/A')}")

def test_router_without_interrupt():
    """인터럽트 없는 라우터 테스트"""
    print("\n\n=== 라우터 테스트 (인터럽트 회피) ===")
    
    router = RouterAgent()
    
    # employee_agent는 인터럽트가 없으므로 성공해야 함
    test_query = "김도윤 직원의 2024년 실적 분석해줘"
    
    print(f"\n[테스트] {test_query}")
    result = router.run(test_query)
    
    print(f"성공: {result.get('success')}")
    print(f"대상 에이전트: {result.get('target_agent')}")
    print(f"신뢰도: {result.get('classification_confidence', 0):.2f}")
    
    if result.get('error'):
        print(f"오류: {result.get('error')}")
    
    # 결과 확인
    sub_result = result.get('result', {})
    if sub_result.get('success'):
        print(f"\n[결과] 분석 완료")
        if sub_result.get('agent') == 'employee_agent':
            data = sub_result.get('data', {})
            print(f"  직원: {data.get('employee_name')}")
            print(f"  기간: {data.get('period')}")
            print(f"  총 실적: {data.get('total_performance', 0):,}원")

def test_docs_agent_classification():
    """docs_agent 분류만 테스트"""
    print("\n\n=== docs_agent 분류 테스트 ===")
    
    router = RouterAgent()
    
    # 명확한 문서 작성 요청
    test_query = "영업방문 결과보고서를 작성하고 싶어요. 오늘 ABC병원을 방문했습니다."
    
    print(f"\n[테스트] {test_query}")
    
    # 초기 상태만 확인
    from langchain_core.messages import HumanMessage
    
    initial_state = {
        "messages": [HumanMessage(content=test_query)],
        "session_id": "test-session",
        "agent_type": "router",
        "error": None,
        "target_agent": None,
        "sub_agent_state": None,
        "sub_agent_result": None,
        "requires_interrupt": None,
        "classification_confidence": None
    }
    
    # 분류만 실행
    state = router._classify_query_node(initial_state)
    
    print(f"분류 결과: {state.get('target_agent')}")
    print(f"신뢰도: {state.get('classification_confidence', 0):.2f}")

if __name__ == "__main__":
    test_classifier_improved()
    test_router_without_interrupt()
    test_docs_agent_classification()
    
    print("\n\n테스트 완료!")