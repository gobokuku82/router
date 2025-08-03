"""
로얄티 위반 테스트
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.services.docs_agent.web_interface import WebDocumentAgent

def test_loyalty_violation():
    web_agent = WebDocumentAgent()
    session_id = 'test_loyalty'
    
    # 로얄티가 명확히 포함된 내용
    content = '''영업방문결과서 작성해줘. 
    프로젝트 개요는 신규고객 유치로 자사 약품홍보 후 로얄티 및 메리트 소개를 할거야
    방문 및 협의 내용은 자사 약품 소개와 로얄티 및 자사 약품 사용시 메리트를 소개하였음'''
    
    print("=== 로얄티 위반 테스트 ===\n")
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
    test_loyalty_violation()