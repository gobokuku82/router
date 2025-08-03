"""
간단한 라우터 테스트
"""
import sys
from pathlib import Path

# 경로 설정
project_root = Path(__file__).parent.parent
backend_path = project_root / "backend"
sys.path.insert(0, str(backend_path))

print(f"프로젝트 루트: {project_root}")
print(f"sys.path에 추가: {backend_path}")

# 1. 기본 임포트 테스트
print("\n=== 1. 기본 임포트 테스트 ===")
try:
    from app.services.router_agent.classifier import AgentClassifier
    print("[성공] AgentClassifier 임포트")
except Exception as e:
    print(f"[실패] AgentClassifier 임포트: {e}")

try:
    from app.services.router_agent.router import RouterAgent
    print("[성공] RouterAgent 임포트")
except Exception as e:
    print(f"[실패] RouterAgent 임포트: {e}")

# 2. 분류기 테스트
print("\n=== 2. 분류기 단순 테스트 ===")
try:
    classifier = AgentClassifier()
    
    # docs_agent 테스트
    test_query = "영업방문 결과보고서 작성해줘"
    agent, confidence, analysis = classifier.classify(test_query)
    print(f"질문: {test_query}")
    print(f"분류 결과: {agent} (신뢰도: {confidence:.2f})")
    
    # employee_agent 테스트
    test_query2 = "김도윤 직원의 실적을 분석해줘"
    agent2, confidence2, analysis2 = classifier.classify(test_query2)
    print(f"\n질문: {test_query2}")
    print(f"분류 결과: {agent2} (신뢰도: {confidence2:.2f})")
    
except Exception as e:
    print(f"[실패] 분류기 테스트: {e}")
    import traceback
    traceback.print_exc()

# 3. 라우터 에이전트 테스트
print("\n=== 3. 라우터 에이전트 기본 테스트 ===")
try:
    router = RouterAgent()
    print("[성공] RouterAgent 인스턴스 생성")
    
    # 간단한 실행 테스트
    result = router.run("테스트 메시지입니다")
    print(f"실행 결과: success={result.get('success')}")
    print(f"대상 에이전트: {result.get('target_agent')}")
    
except Exception as e:
    print(f"[실패] 라우터 에이전트 테스트: {e}")
    import traceback
    traceback.print_exc()

print("\n테스트 완료!")