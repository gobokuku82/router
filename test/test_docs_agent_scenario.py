"""
시나리오 기반 docs_agent 상호작용 테스트
실제 사용 케이스를 시뮬레이션하여 전체 워크플로우를 테스트합니다.
"""
import sys
from pathlib import Path
import json

# 경로 설정
current_file = Path(__file__).resolve()
test_dir = current_file.parent
project_root = test_dir.parent
backend_dir = project_root / "backend"

# backend를 Python 경로에 추가
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

print(f"[PATH] Added to sys.path: {backend_dir}")

# 필요한 모듈 import
from app.services.router_agent import RouterAgent
from app.services.docs_agent.create_document_agent import CreateDocumentAgent


def print_step(step_num, title):
    """단계별 구분선 출력"""
    print(f"\n{'='*60}")
    print(f"STEP {step_num}: {title}")
    print('='*60)


def test_full_scenario_with_router():
    """Router를 통한 전체 시나리오 테스트"""
    print("\n" + "#"*70)
    print("# 시나리오: Router를 통한 영업방문 결과보고서 작성 (규정 위반 포함)")
    print("#"*70)
    
    # RouterAgent 초기화
    router = RouterAgent()
    session_id = "test-scenario-001"
    
    # STEP 1: 초기 요청
    print_step(1, "초기 요청 - '영업방문결과서 작성해줘'")
    
    initial_query = "영업방문결과서 작성해줘."
    print(f"[USER] {initial_query}")
    
    try:
        result = router.run(
            user_query=initial_query,
            session_id=session_id
        )
        
        print(f"\n[ROUTER RESPONSE]")
        print(f"  - Success: {result.get('success')}")
        print(f"  - Target Agent: {result.get('target_agent')}")
        print(f"  - Session ID: {result.get('session_id')}")
        
        # 하위 결과 확인
        sub_result = result.get('result', {})
        if sub_result:
            print(f"  - Sub Agent Success: {sub_result.get('success')}")
            print(f"  - Thread ID: {sub_result.get('thread_id')}")
            
            # 분류 결과 확인
            inner_result = sub_result.get('result', {})
            if inner_result:
                print(f"  - Classified Doc Type: {inner_result.get('doc_type')}")
                
        if not result.get('success') and sub_result.get('thread_id'):
            thread_id = sub_result['thread_id']
            print(f"\n[STATUS] 사용자 입력 대기 중... (Thread ID: {thread_id})")
            
            # STEP 2: 문서 타입 확인에 "예" 응답
            print_step(2, "문서 타입 확인 - '예' 응답")
            
            user_reply = "예"
            print(f"[USER] {user_reply}")
            
            result = router.resume_session(
                session_id=session_id,
                user_reply=user_reply,
                reply_type="verification_reply"
            )
            
            print(f"\n[ROUTER RESPONSE]")
            print(f"  - Success: {result.get('success')}")
            
            sub_result = result.get('result', {})
            if sub_result.get('interrupted'):
                print(f"[STATUS] 추가 정보 입력 대기 중...")
                
                # STEP 3: 상세 정보 입력
                print_step(3, "상세 정보 입력 (로얄티/메리트 포함)")
                
                detailed_info = """방문 제목: 유미가정의학과 신약 홍보
방문일: 2025-07-25
Client: 유미가정의학과
방문사이트: www.yumibanplz.com
담당자성명: 손현성
담당자소속: 영업팀
담당자연락처: 010-1234-5678
영업제공자성명: 김도윤
영업제공자연락처: 010-8765-4321
방문자성명: 허한결
방문자소속: 영업팀
고객사개요: 이번에 새로 오픈한 가정의학과로 사용 약품에 대해 많은 논의가 필요해보이는 잠재력이 있는 고객
프로젝트개요: 신규고객 유치로 자사 약품홍보 후 로얄티 및 메리트 소개
방문및협의내용: 자사 약품 소개와 로얄티 및 자사 약품 사용시 메리트를 소개하였음
향후계획및일정: 7월 27일에 다시 방문하여 자사 판촉물 전달과 로얄티 협상을 할 예정
협조사항및기타내용: 자사 판촉물 1개 지급 요망"""
                
                print("[USER] (상세 정보 입력)")
                # 입력 내용의 일부만 표시
                print(detailed_info.split('\n')[:5])
                print("... (중략) ...")
                print("특히 '로얄티 및 메리트 소개' 부분 포함")
                
                result = router.resume_session(
                    session_id=session_id,
                    user_reply=detailed_info,
                    reply_type="user_reply"
                )
                
                print(f"\n[FINAL RESULT]")
                print(f"  - Success: {result.get('success')}")
                
                sub_result = result.get('result', {})
                if sub_result:
                    inner_result = sub_result.get('result', {})
                    
                    # 규정 위반 확인
                    if inner_result.get('violation') and inner_result['violation'] != "OK":
                        print(f"\n[VIOLATION DETECTED]")
                        print(f"  - Violation: {inner_result['violation']}")
                        print("\n[EXPECTED] 로얄티/메리트 언급으로 인한 규정 위반이 감지되어야 합니다.")
                    elif inner_result.get('final_doc'):
                        print(f"\n[DOCUMENT CREATED]")
                        print(f"  - Document Path: {inner_result['final_doc']}")
                        print(f"  - Doc Type: {inner_result['doc_type']}")
                        print("\n[WARNING] 규정 위반이 감지되지 않았습니다!")
                    else:
                        print("\n[ERROR] 예상치 못한 결과")
                        print(f"Result: {json.dumps(inner_result, ensure_ascii=False, indent=2)}")
        
    except Exception as e:
        print(f"\n[ERROR] 테스트 실패: {e}")
        import traceback
        traceback.print_exc()


def test_direct_docs_agent_scenario():
    """CreateDocumentAgent 직접 호출 시나리오 테스트"""
    print("\n" + "#"*70)
    print("# 시나리오: CreateDocumentAgent 직접 호출 테스트")
    print("#"*70)
    
    agent = CreateDocumentAgent()
    
    # STEP 1: 초기 실행
    print_step(1, "초기 실행")
    
    try:
        # 초기 입력과 함께 실행
        initial_input = "영업방문결과서 작성해줘."
        print(f"[USER] {initial_input}")
        
        result = agent.run(user_input=initial_input)
        
        if not result.get('success') and result.get('thread_id'):
            thread_id = result['thread_id']
            print(f"[AGENT] 문서 타입 확인이 필요합니다. (Thread ID: {thread_id})")
            
            # STEP 2: 확인 응답
            print_step(2, "문서 타입 확인")
            
            result = agent.resume(thread_id, "예", "verification_reply")
            
            if result.get('interrupted'):
                print("[AGENT] 필요한 정보를 입력해주세요.")
                
                # STEP 3: 상세 정보 입력
                print_step(3, "상세 정보 입력")
                
                # 정리된 형식으로 입력
                detailed_info = """방문일자: 2025-07-25
방문자: 허한결
방문기관: 유미가정의학과
면담자: 손현성
방문목적: 신약 홍보
면담내용: 자사 약품 소개와 로얄티 및 자사 약품 사용시 메리트를 소개하였음
건의사항: 자사 판촉물 1개 지급 요망"""
                
                print("[USER] (필수 정보 입력)")
                print(detailed_info)
                
                result = agent.resume(thread_id, detailed_info, "user_reply")
                
                # 결과 확인
                if result.get('success'):
                    inner_result = result.get('result', {})
                    if inner_result.get('violation') and inner_result['violation'] != "OK":
                        print(f"\n[VIOLATION DETECTED] {inner_result['violation']}")
                    elif inner_result.get('final_doc'):
                        print(f"\n[SUCCESS] 문서 생성 완료: {inner_result['final_doc']}")
                    
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()


def test_violation_detection_only():
    """규정 위반 감지 기능만 단독 테스트"""
    print("\n" + "#"*70)
    print("# 규정 위반 감지 단독 테스트")
    print("#"*70)
    
    from app.services.tools.common_tools import check_policy_violation
    
    test_cases = [
        {
            "name": "로얄티 언급",
            "content": "자사 약품 사용시 로얄티를 제공하겠다고 약속함"
        },
        {
            "name": "메리트 언급",
            "content": "약품 구매시 특별한 메리트를 제공할 예정"
        },
        {
            "name": "정상 내용",
            "content": "약품의 효능과 안전성에 대해 설명함"
        }
    ]
    
    for test in test_cases:
        print(f"\n[TEST] {test['name']}")
        print(f"Content: {test['content']}")
        
        violation = check_policy_violation(test['content'])
        
        if violation == "OK":
            print("[RESULT] 규정 위반 없음")
        else:
            print(f"[RESULT] 규정 위반 감지: {violation}")


def main():
    """메인 테스트 실행"""
    print("="*70)
    print("시나리오 기반 상호작용 테스트 시작")
    print("="*70)
    
    # 1. Router를 통한 전체 시나리오 테스트
    test_full_scenario_with_router()
    
    # 2. CreateDocumentAgent 직접 호출 테스트
    test_direct_docs_agent_scenario()
    
    # 3. 규정 위반 감지 단독 테스트
    test_violation_detection_only()
    
    print("\n" + "="*70)
    print("시나리오 기반 상호작용 테스트 완료")
    print("="*70)
    
    print("\n[참고사항]")
    print("- 로얄티/메리트 언급 시 규정 위반이 감지되어야 합니다")
    print("- 위반 감지 시 문서 생성이 중단되어야 합니다")
    print("- 정상적인 내용은 문서가 생성되어야 합니다")


if __name__ == "__main__":
    main()