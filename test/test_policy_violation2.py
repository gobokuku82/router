"""
정책 위반 테스트 2 - 로얄티 관련
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.services.docs_agent.web_interface import WebDocumentAgent

def test_policy_violation2():
    web_agent = WebDocumentAgent()
    session_id = 'test_violation2'
    
    # 로얄티 관련 위반 내용
    content = '''영업방문결과서 작성해줘. 
    방문일은 250725이고 client는 유미가정의학과야.
    방문 내용은 자사 약품 사용시 현금 50만원을 지급하기로 협의했어.
    향후 계획은 다음주에 현금을 전달할 예정이야.'''
    
    print("=== 정책 위반 테스트 2 (로얄티) ===\n")
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
    test_policy_violation2()