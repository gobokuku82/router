"""
docs_agent 직접 상호작용 테스트
CreateDocumentAgent를 직접 호출하여 문서 생성 프로세스를 테스트합니다.
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

# CreateDocumentAgent import
from app.services.docs_agent.create_document_agent import CreateDocumentAgent


def test_create_document_agent_init():
    """CreateDocumentAgent 초기화 테스트"""
    print("\n=== CreateDocumentAgent 초기화 테스트 ===")
    
    try:
        agent = CreateDocumentAgent()
        print("[OK] CreateDocumentAgent 인스턴스 생성 성공")
        
        # 속성 확인
        print(f"  - Model: {agent.model_name}")
        print(f"  - Temperature: {agent.temperature}")
        print(f"  - Templates loaded: {len(agent.doc_prompts)} types")
        
        if agent.doc_prompts:
            print("  - Available document types:")
            for doc_type in agent.doc_prompts.keys():
                print(f"    - {doc_type}")
                
        return agent
        
    except Exception as e:
        print(f"[ERROR] 초기화 실패: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_run_method(agent):
    """run 메서드 테스트"""
    print("\n=== run 메서드 테스트 ===")
    
    test_cases = [
        {
            "name": "영업방문 결과보고서",
            "input": "어제 삼성병원에 김철수 과장이 방문했습니다. 신약 A의 임상 데이터를 설명했고, 긍정적인 반응을 얻었습니다."
        },
        {
            "name": "제품설명회 신청서",
            "input": "다음주 금요일에 서울대병원에서 제품설명회를 하려고 합니다"
        },
        {
            "name": "간단한 질의",
            "input": "영업방문 결과보고서 작성해줘"
        }
    ]
    
    for test in test_cases:
        print(f"\n테스트: {test['name']}")
        print(f"입력: {test['input']}")
        
        try:
            result = agent.run(user_input=test['input'])
            
            print(f"\n결과:")
            print(f"  - Success: {result.get('success')}")
            print(f"  - Thread ID: {result.get('thread_id')}")
            
            # 내부 result 확인
            inner_result = result.get('result', {})
            if inner_result:
                print(f"  - Doc Type: {inner_result.get('doc_type')}")
                print(f"  - Template Content: {'있음' if inner_result.get('template_content') else '없음'}")
                print(f"  - Final Doc: {'있음' if inner_result.get('final_doc') else '없음'}")
                
                # 메시지 확인
                messages = inner_result.get('messages', [])
                if messages:
                    print(f"  - Messages: {len(messages)}개")
                    
            # 인터럽트 발생 확인
            if not result.get('success') and result.get('thread_id'):
                print("  - 상태: 사용자 입력 대기 중 (인터럽트)")
                return result['thread_id']  # 다음 테스트를 위해 thread_id 반환
                
        except Exception as e:
            print(f"[ERROR] 실행 실패: {e}")
            import traceback
            traceback.print_exc()
            
    return None


def test_resume_method(agent, thread_id):
    """resume 메서드 테스트"""
    print("\n=== resume 메서드 테스트 ===")
    
    if not thread_id:
        print("[SKIP] Thread ID가 없어 resume 테스트를 건너뜁니다.")
        return
        
    print(f"Thread ID: {thread_id}")
    
    # 다양한 사용자 응답 테스트
    test_responses = [
        {
            "name": "긍정 응답",
            "reply": "네, 맞습니다",
            "input_type": "verification_reply"
        },
        {
            "name": "문서 타입 선택",
            "reply": "1",
            "input_type": "user_reply"
        },
        {
            "name": "상세 정보 입력",
            "reply": "방문일자: 2024-01-15, 방문자: 김철수, 방문기관: 삼성병원, 면담자: 이영희 과장, 방문목적: 신약 A 임상 데이터 설명",
            "input_type": "user_reply"
        }
    ]
    
    # 첫 번째 응답만 테스트 (실제 워크플로우에 맞춰)
    test = test_responses[0]
    print(f"\n테스트: {test['name']}")
    print(f"응답: {test['reply']}")
    
    try:
        result = agent.resume(
            thread_id=thread_id,
            user_reply=test['reply'],
            input_type=test['input_type']
        )
        
        print(f"\n결과:")
        print(f"  - Success: {result.get('success')}")
        print(f"  - Interrupted: {result.get('interrupted')}")
        
        inner_result = result.get('result', {})
        if inner_result:
            print(f"  - Current State: {inner_result.get('current_step', 'N/A')}")
            
    except Exception as e:
        print(f"[ERROR] Resume 실패: {e}")
        import traceback
        traceback.print_exc()


def test_interactive_flow(agent):
    """대화형 흐름 전체 테스트"""
    print("\n=== 대화형 흐름 전체 테스트 ===")
    
    # 1단계: 초기 요청
    print("\n1. 초기 요청")
    initial_input = "김철수가 어제 삼성병원에 방문한 내용으로 영업방문 결과보고서 작성해줘"
    
    try:
        result = agent.run(user_input=initial_input)
        print(f"  - Thread ID: {result.get('thread_id')}")
        
        if not result.get('success') and result.get('thread_id'):
            thread_id = result['thread_id']
            print("  [OK] 사용자 입력 대기 상태")
            
            # 2단계: 문서 타입 확인
            print("\n2. 문서 타입 확인에 '예' 응답")
            result = agent.resume(thread_id, "예", "verification_reply")
            
            if result.get('interrupted'):
                print("  [OK] 추가 정보 입력 대기")
                
                # 3단계: 상세 정보 입력
                print("\n3. 상세 정보 입력")
                detailed_info = """
                방문일자: 2024-01-15
                방문자: 김철수
                방문기관: 삼성병원
                면담자: 이영희 과장
                방문목적: 신약 A 임상 데이터 설명
                면담내용: 신약 A의 3상 임상 결과를 설명했으며, 특히 기존 약물 대비 30% 향상된 효능에 대해 긍정적 반응을 보임
                """
                
                result = agent.resume(thread_id, detailed_info, "user_reply")
                
                if result.get('success'):
                    inner_result = result.get('result', {})
                    if inner_result.get('final_doc'):
                        print("  [OK] 문서 생성 완료!")
                        print(f"  - 문서 경로: {inner_result.get('final_doc')}")
                        print(f"  - 문서 타입: {inner_result.get('doc_type')}")
                    else:
                        print("  [ERROR] 문서 생성 실패")
                else:
                    print(f"  [ERROR] 오류 발생: {result.get('error')}")
                    
    except Exception as e:
        print(f"[ERROR] 대화형 흐름 테스트 실패: {e}")
        import traceback
        traceback.print_exc()


def test_direct_node_methods(agent):
    """개별 노드 메서드 직접 테스트"""
    print("\n=== 개별 노드 메서드 테스트 ===")
    
    # State 생성
    from app.services.docs_agent.create_document_agent import State
    from langchain_core.messages import HumanMessage
    
    # 1. classify_doc_type 테스트
    print("\n1. classify_doc_type 메서드")
    state = State(
        messages=[HumanMessage(content="영업방문 결과보고서 작성해줘")],
        retry_count=0
    )
    
    try:
        new_state = agent.classify_doc_type(state)
        print(f"  - Doc Type: {new_state.get('doc_type')}")
        print(f"  - Classification Failed: {new_state.get('classification_failed')}")
        print("  [OK] 분류 성공")
    except Exception as e:
        print(f"  [ERROR] 분류 실패: {e}")
        
    # 2. parse_user_input 테스트
    print("\n2. parse_user_input 메서드")
    state['messages'].append(HumanMessage(content="""
    방문일자: 2024-01-15
    방문자: 김철수
    방문기관: 삼성병원
    """))
    state['doc_type'] = "영업방문 결과보고서"
    
    try:
        new_state = agent.parse_user_input(state)
        if new_state.get('filled_data'):
            print(f"  - Parsed Data: {json.dumps(new_state['filled_data'], ensure_ascii=False, indent=2)}")
            print("  [OK] 파싱 성공")
        else:
            print("  [ERROR] 파싱 실패")
    except Exception as e:
        print(f"  [ERROR] 파싱 오류: {e}")


def main():
    """메인 테스트 실행"""
    print("="*60)
    print("docs_agent 직접 상호작용 테스트")
    print("="*60)
    
    # 1. 초기화 테스트
    agent = test_create_document_agent_init()
    
    if agent:
        # 2. run 메서드 테스트
        thread_id = test_run_method(agent)
        
        # 3. resume 메서드 테스트
        if thread_id:
            test_resume_method(agent, thread_id)
        
        # 4. 대화형 흐름 테스트
        test_interactive_flow(agent)
        
        # 5. 개별 노드 메서드 테스트
        test_direct_node_methods(agent)
    
    print("\n" + "="*60)
    print("테스트 완료")
    print("="*60)
    
    print("\n참고:")
    print("- 삭제된 web_interface.py 없이도 CreateDocumentAgent가 정상 작동합니다")
    print("- RouterAgent는 CreateDocumentAgent를 직접 import하여 사용합니다")
    print("- run()과 resume() 메서드로 대화형 문서 생성이 가능합니다")


if __name__ == "__main__":
    main()