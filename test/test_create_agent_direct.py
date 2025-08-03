"""
CreateDocumentAgent 직접 테스트
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.services.docs_agent.create_document_agent import CreateDocumentAgent

def test_create_agent():
    """CreateDocumentAgent 직접 테스트"""
    
    # 테스트 내용
    test_content = """영업방문결과서 작성해줘. 향후계획은 7월 27일에 다시 방문하여 자사 판촉물 전달과 로얄티 협상을 할 예정이야"""
    
    print("=== CreateDocumentAgent 직접 테스트 ===\n")
    
    # 에이전트 생성
    agent = CreateDocumentAgent()
    
    # run 메서드 실행
    result = agent.run(test_content)
    
    print("\n실행 결과:")
    print(f"- 성공: {result.get('success')}")
    print(f"- 결과: {result.get('result')}")
    
    if result.get('result'):
        state = result['result']
        print(f"\n상태 정보:")
        print(f"- doc_type: {state.get('doc_type')}")
        print(f"- user_content: {state.get('user_content', '')[:50]}...")
        print(f"- skip_ask_fields: {state.get('skip_ask_fields')}")
        print(f"- violation: {state.get('violation')}")
        print(f"- final_doc: {state.get('final_doc')}")

if __name__ == "__main__":
    test_create_agent()