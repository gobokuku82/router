"""
최종 통합 테스트
라우터 시스템의 모든 기능을 종합적으로 테스트합니다.
"""
import sys
from pathlib import Path
import time

# 경로 설정
project_root = Path(__file__).parent.parent
backend_path = project_root / "backend"
sys.path.insert(0, str(backend_path))

from app.services.router_agent import RouterAgent

def print_separator(title=""):
    """구분선 출력"""
    if title:
        print(f"\n{'='*20} {title} {'='*20}")
    else:
        print("="*60)

def test_complete_flow():
    """전체 플로우 테스트"""
    print_separator("전체 통합 테스트 시작")
    
    router = RouterAgent()
    
    # 테스트 케이스
    test_cases = [
        {
            "name": "Employee Agent 테스트 (인터럽트 없음)",
            "query": "최수아 직원의 2024년 상반기 실적을 분석해줘",
            "expected_agent": "employee_agent"
        },
        {
            "name": "Docs Agent 기본 테스트",
            "query": "영업방문 결과보고서 작성 템플릿을 보여줘",
            "expected_agent": "docs_agent"
        },
        {
            "name": "분류 애매한 케이스",
            "query": "실적 보고서를 작성해야 하는데 어떻게 해야 할까?",
            "expected_agent": None  # 애매한 케이스
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print_separator(f"테스트 {i}: {test_case['name']}")
        
        query = test_case["query"]
        expected = test_case["expected_agent"]
        
        print(f"질문: {query}")
        print(f"예상 에이전트: {expected}")
        
        try:
            # 라우터 실행
            start_time = time.time()
            result = router.run(query)
            elapsed_time = time.time() - start_time
            
            # 결과 출력
            print(f"\n실행 시간: {elapsed_time:.2f}초")
            print(f"성공 여부: {result.get('success')}")
            print(f"대상 에이전트: {result.get('target_agent')}")
            print(f"분류 신뢰도: {result.get('classification_confidence', 0):.2f}")
            
            # 에러 확인
            if result.get('error'):
                print(f"에러: {result.get('error')}")
            
            # 인터럽트 확인
            if result.get('requires_interrupt'):
                print("\n[인터럽트 발생]")
                sub_result = result.get('result', {})
                print(f"스레드 ID: {sub_result.get('thread_id')}")
                print("사용자 입력이 필요합니다.")
            
            # 성공적인 결과 확인
            sub_result = result.get('result', {})
            if sub_result.get('success'):
                agent = sub_result.get('agent')
                
                if agent == 'employee_agent':
                    print("\n[Employee Agent 결과]")
                    data = sub_result.get('data', {})
                    print(f"직원명: {data.get('employee_name')}")
                    print(f"분석 기간: {data.get('period')}")
                    print(f"총 실적: {data.get('total_performance', 0):,}원")
                    print(f"달성률: {data.get('achievement_rate', 0):.1f}%")
                    
                    # 보고서 일부 출력
                    report = sub_result.get('response', '')
                    if report:
                        print("\n[보고서 미리보기]")
                        print(report[:200] + "..." if len(report) > 200 else report)
                
                elif agent == 'docs_agent':
                    print("\n[Docs Agent 결과]")
                    print("문서 작성 프로세스가 시작되었습니다.")
            
        except Exception as e:
            print(f"\n[오류 발생] {str(e)}")
            import traceback
            traceback.print_exc()
        
        # 테스트 간 간격
        if i < len(test_cases):
            time.sleep(1)

def test_classification_accuracy():
    """분류 정확도 집중 테스트"""
    print_separator("분류 정확도 테스트")
    
    from app.services.router_agent.classifier import AgentClassifier
    
    classifier = AgentClassifier()
    
    # 다양한 테스트 케이스
    test_queries = [
        # 명확한 docs_agent 케이스
        ("영업방문 결과보고서 작성", "docs_agent"),
        ("제품설명회 신청서 만들기", "docs_agent"),
        ("방문 보고서 템플릿", "docs_agent"),
        
        # 명확한 employee_agent 케이스  
        ("김도윤 실적 분석", "employee_agent"),
        ("직원 성과 평가", "employee_agent"),
        ("매출 트렌드 분석", "employee_agent"),
        
        # 애매한 케이스
        ("실적 보고서 작성", None),  # 실적(employee) + 보고서(docs)
        ("방문 실적 분석", None),    # 방문(docs) + 실적(employee)
    ]
    
    correct = 0
    total = len(test_queries)
    
    for query, expected in test_queries:
        agent, confidence, _ = classifier.classify(query)
        
        # 애매한 케이스는 신뢰도가 낮아야 함
        if expected is None:
            is_correct = confidence < 0.5
        else:
            is_correct = agent == expected
        
        if is_correct:
            correct += 1
        
        status = "O" if is_correct else "X"
        print(f"[{status}] '{query}' -> {agent} ({confidence:.2f})")
    
    accuracy = (correct / total) * 100
    print(f"\n정확도: {correct}/{total} ({accuracy:.1f}%)")

def test_error_handling():
    """에러 처리 테스트"""
    print_separator("에러 처리 테스트")
    
    router = RouterAgent()
    
    # 에러 유발 케이스
    error_cases = [
        "",  # 빈 쿼리
        "a" * 1000,  # 너무 긴 쿼리
        "!@#$%^&*()",  # 특수문자만
    ]
    
    for query in error_cases:
        print(f"\n테스트: '{query[:50]}...' (길이: {len(query)})")
        
        try:
            result = router.run(query)
            print(f"처리됨: success={result.get('success')}, agent={result.get('target_agent')}")
        except Exception as e:
            print(f"예외 발생: {type(e).__name__}: {str(e)}")

if __name__ == "__main__":
    # 메인 테스트 실행
    print("\n" + "="*60)
    print("라우터 시스템 최종 통합 테스트")
    print("="*60)
    
    # 1. 분류 정확도 테스트
    test_classification_accuracy()
    
    # 2. 전체 플로우 테스트
    test_complete_flow()
    
    # 3. 에러 처리 테스트
    test_error_handling()
    
    print_separator("테스트 완료")