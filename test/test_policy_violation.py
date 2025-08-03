"""
정책 위반 테스트
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.services.docs_agent.web_interface import WebDocumentAgent

def test_policy_violation():
    web_agent = WebDocumentAgent()
    session_id = 'test_violation'
    
    # 정책 위반이 포함된 내용
    content = '''제품설명회 결과보고서 작성해줘. 
    행사 후 저녁식사를 가졌고 메뉴는 스테이크였어. 
    사용한 금액은 200만원이고 주류는 와인 10병을 마셨어. 
    인당 금액은 20만원이 나왔어.'''
    
    print("=== 정책 위반 테스트 ===\n")
    print(f"테스트 내용: {content}\n")
    
    result = web_agent.create_session(session_id, content)
    print('첫 번째 결과:', result.get('message', ''))
    
    # 예 응답
    if result.get('waiting_for_input'):
        result2 = web_agent.process_user_input(session_id, '예')
        print('\n두 번째 결과:')
        print('- 성공:', result2.get('success'))
        print('- 단계:', result2.get('step'))
        print('- 메시지:', result2.get('message', ''))
        if result2.get('violation'):
            print('- 위반:', result2.get('violation'))
        if result2.get('error'):
            print('- 에러:', result2.get('error'))

if __name__ == "__main__":
    test_policy_violation()