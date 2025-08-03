"""
상세한 규정 위반 검사 테스트
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import json

def test_fastapi_direct():
    """FastAPI 직접 호출 테스트"""
    print("=== FastAPI 직접 호출 테스트 ===\n")
    
    test_phrases = [
        "자사 판촉물 전달",
        "로얄티 협상",
        "자사 약품 사용시 메리트 소개"
    ]
    
    fastapi_url = "http://localhost:8010/qa/question"
    
    for phrase in test_phrases:
        print(f"\n검색 문구: '{phrase}'")
        
        payload = {
            "question": phrase,
            "top_k": 5,
            "include_summary": True,
            "include_sources": True
        }
        
        try:
            response = requests.post(
                fastapi_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"성공: {result.get('success')}")
                print(f"검색 결과 수: {len(result.get('search_results', []))}")
                
                if result.get('search_results'):
                    for i, res in enumerate(result['search_results'][:2]):
                        print(f"\n  결과 {i+1}:")
                        print(f"  - 점수: {res.get('score', 0):.3f}")
                        content = res.get('source', {}).get('content', '')
                        print(f"  - 내용: {content[:100]}...")
            else:
                print(f"API 호출 실패: {response.status_code}")
                
        except Exception as e:
            print(f"오류 발생: {e}")

def test_web_interface_violation():
    """WebInterface 규정 위반 검사 테스트"""
    print("\n\n=== WebInterface 규정 위반 검사 테스트 ===\n")
    
    from backend.app.services.docs_agent.web_interface import WebDocumentAgent
    
    test_content = """영업방문결과서 작성해줘. 
    방문 및 협의 내용은 자사 약품 소개와 로얄티 및 자사 약품 사용시 메리트를 소개하였음 
    향후계획및일정은 7월 27일에 다시 방문하여 자사 판촉물 전달과 로얄티 협상을 할 예정이야 
    협조사항으로 자사 판촉물 1개 지급 요망"""
    
    web_agent = WebDocumentAgent()
    
    print("테스트 내용:")
    print(test_content[:100] + "...")
    print("\n검사 중...")
    
    try:
        # 디버깅을 위해 로깅 활성화
        import logging
        logging.basicConfig(level=logging.INFO)
        
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
    test_fastapi_direct()
    test_web_interface_violation()