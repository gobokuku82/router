"""
간단한 규정 위반 검사 테스트
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.services.docs_agent.web_interface import WebDocumentAgent

def test_simple_violation():
    """간단한 규정 위반 테스트"""
    
    # 테스트용 문서 내용
    test_content = """방문 및 협의 내용은 자사 약품 소개와 로얄티 및 자사 약품 사용시 메리트를 소개하였음 
    향후계획및일정은 7월 27일에 다시 방문하여 자사 판촉물 전달과 로얄티 협상을 할 예정이야 
    협조사항으로 자사 판촉물 1개 지급 요망"""
    
    print("=== 규정 위반 검사 테스트 ===\n")
    
    # WebDocumentAgent 생성
    web_agent = WebDocumentAgent()
    
    print("테스트 내용:")
    print(test_content)
    print("\n검사 중...")
    
    # DB 기반 규정 검사 실행
    try:
        result = web_agent._check_additional_violations(test_content)
        
        print("\n검사 결과:")
        if result:
            print(result)
        else:
            print("위반 사항이 발견되지 않았습니다.")
            
    except Exception as e:
        print(f"\n[ERROR] 검사 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple_violation()