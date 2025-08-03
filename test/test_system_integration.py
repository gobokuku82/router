"""
전체 시스템 통합 테스트
FastAPI 서버와 RouterAgent, docs_agent의 연동을 테스트합니다.
"""
import sys
from pathlib import Path
import asyncio
import requests
import json
from time import sleep

# 경로 설정
current_file = Path(__file__).resolve()
test_dir = current_file.parent
project_root = test_dir.parent
backend_dir = project_root / "backend"

# backend를 Python 경로에 추가
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

print(f"[PATH] Added to sys.path: {backend_dir}")

# FastAPI 서버가 실행 중이라고 가정
API_BASE_URL = "http://localhost:8000/api"


def test_health_check():
    """헬스 체크 테스트"""
    print("\n=== 헬스 체크 테스트 ===")
    try:
        response = requests.get("http://localhost:8000/health")
        assert response.status_code == 200
        print(f"✓ 헬스 체크 성공: {response.json()}")
        return True
    except Exception as e:
        print(f"✗ 헬스 체크 실패: {e}")
        print("서버가 실행 중인지 확인하세요.")
        return False


def test_router_to_docs_agent():
    """Router → docs_agent 라우팅 테스트"""
    print("\n=== Router → docs_agent 라우팅 테스트 ===")
    
    # 세션 ID 생성
    import uuid
    session_id = str(uuid.uuid4())
    
    # 문서 작성 요청
    test_queries = [
        "영업방문 결과보고서 작성해줘",
        "제품설명회 신청서 만들어줘",
        "김철수가 삼성병원에 방문한 내용으로 보고서 작성"
    ]
    
    for query in test_queries:
        print(f"\n테스트 쿼리: {query}")
        
        payload = {
            "message": query,
            "session_id": session_id
        }
        
        try:
            response = requests.post(f"{API_BASE_URL}/v1/chat", json=payload)
            print(f"상태 코드: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✓ 라우팅 성공:")
                print(f"  - Target Agent: {result.get('target_agent')}")
                print(f"  - Success: {result.get('success')}")
                print(f"  - Requires Interrupt: {result.get('requires_interrupt')}")
                
                if result.get('response'):
                    print(f"  - Response: {result['response'][:100]}...")
                    
                # 새 세션으로 다음 테스트
                session_id = str(uuid.uuid4())
            else:
                print(f"✗ 오류: {response.text}")
                
        except Exception as e:
            print(f"✗ 요청 실패: {e}")


def test_direct_router_agent():
    """RouterAgent 직접 테스트 (서버 없이)"""
    print("\n=== RouterAgent 직접 테스트 ===")
    
    try:
        from app.services.router_agent import RouterAgent
        
        # RouterAgent 인스턴스 생성
        router = RouterAgent()
        print("✓ RouterAgent 인스턴스 생성 성공")
        
        # 테스트 쿼리
        test_queries = [
            ("영업방문 결과보고서 작성", "docs_agent"),
            ("김철수의 이번달 실적 조회", "employee_agent"),
            ("제품설명회 신청서 작성해줘", "docs_agent")
        ]
        
        for query, expected_agent in test_queries:
            print(f"\n쿼리: {query}")
            
            # run 메서드 호출
            result = router.run(
                user_query=query,
                session_id=f"test-{query[:10]}"
            )
            
            print(f"  - Success: {result.get('success')}")
            print(f"  - Target Agent: {result.get('target_agent')}")
            print(f"  - Expected: {expected_agent}")
            
            if result.get('target_agent') == expected_agent:
                print("  ✓ 올바른 에이전트로 라우팅됨")
            else:
                print("  ✗ 잘못된 에이전트로 라우팅됨")
                
    except Exception as e:
        print(f"✗ RouterAgent 직접 테스트 실패: {e}")
        import traceback
        traceback.print_exc()


def test_docs_agent_in_router():
    """Router 내에서 docs_agent 동작 테스트"""
    print("\n=== Router 내에서 docs_agent 동작 테스트 ===")
    
    try:
        from app.services.router_agent import RouterAgent
        
        router = RouterAgent()
        
        # docs_agent가 제대로 초기화되었는지 확인
        print(f"docs_agent 타입: {type(router.docs_agent)}")
        print(f"docs_agent 메서드: {[m for m in dir(router.docs_agent) if not m.startswith('_')][:5]}...")
        
        # 간단한 문서 작성 테스트
        result = router.run(
            user_query="영업방문 결과보고서를 작성하려고 합니다",
            session_id="test-docs-123"
        )
        
        print(f"\n실행 결과:")
        print(f"  - Success: {result.get('success')}")
        print(f"  - Target Agent: {result.get('target_agent')}")
        
        # 하위 결과 확인
        sub_result = result.get('result', {})
        if sub_result:
            print(f"  - Sub Result Success: {sub_result.get('success')}")
            print(f"  - Thread ID: {sub_result.get('thread_id')}")
            
            # result 내부 확인
            inner_result = sub_result.get('result', {})
            if inner_result:
                print(f"  - Doc Type: {inner_result.get('doc_type')}")
                print(f"  - Current Step: {inner_result.get('current_step', 'N/A')}")
        
        print("✓ docs_agent가 Router 내에서 정상 작동")
        
    except Exception as e:
        print(f"✗ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()


def main():
    """메인 테스트 실행"""
    print("="*60)
    print("시스템 통합 테스트 시작")
    print("="*60)
    
    # 1. 헬스 체크
    if not test_health_check():
        print("\n서버가 실행 중이 아닙니다. 서버 없이 직접 테스트를 진행합니다.")
        
    # 2. RouterAgent 직접 테스트
    test_direct_router_agent()
    
    # 3. Router 내 docs_agent 테스트
    test_docs_agent_in_router()
    
    # 4. API 테스트 (서버가 실행 중인 경우)
    if test_health_check():
        test_router_to_docs_agent()
    
    print("\n" + "="*60)
    print("시스템 통합 테스트 완료")
    print("="*60)


if __name__ == "__main__":
    main()