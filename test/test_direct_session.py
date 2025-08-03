"""
직접 세션 테스트
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.services.docs_agent.web_interface import WebDocumentAgent

def test_direct_session():
    web_agent = WebDocumentAgent()
    session_id = 'test_direct'
    
    # 직접 세션 생성 및 테스트
    content = '''영업방문결과서 작성해줘. 향후계획은 7월 27일에 다시 방문하여 자사 판촉물 전달과 로얄티 협상을 할 예정이야'''
    
    print("=== 직접 세션 테스트 ===\n")
    print(f"테스트 내용: {content}\n")
    
    result = web_agent.create_session(session_id, content)
    print('첫 번째 결과:', result.get('message', ''))
    
    # 예 응답
    if result.get('waiting_for_input'):
        result2 = web_agent.process_user_input(session_id, '예')
        print('\n두 번째 결과:')
        print('- 성공:', result2.get('success'))
        print('- 단계:', result2.get('step'))
        print('- 메시지:', result2.get('message', '')[:200] if result2.get('message') else 'None')
        if result2.get('violation'):
            print('- 위반:', result2.get('violation'))
        if result2.get('error'):
            print('- 에러:', result2.get('error'))

if __name__ == "__main__":
    test_direct_session()