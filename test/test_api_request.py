"""
API 테스트 스크립트
"""
import requests
import json

# API 엔드포인트
BASE_URL = "http://localhost:8000"

def test_health_check():
    """헬스 체크 테스트"""
    print("=== 헬스 체크 테스트 ===")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_chat_api():
    """Chat API 테스트"""
    print("=== Chat API 테스트 ===")
    
    # 요청 데이터
    payload = {
        "message": "영업방문 결과보고서 작성해줘",
        "session_id": "test-123"
    }
    
    # API 호출
    url = f"{BASE_URL}/api/v1/chat"
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, ensure_ascii=False)}")
    
    try:
        response = requests.post(url, json=payload)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Success: {result.get('success')}")
            print(f"Session ID: {result.get('session_id')}")
            print(f"Target Agent: {result.get('target_agent')}")
            print(f"Requires Interrupt: {result.get('requires_interrupt')}")
            
            if result.get('response'):
                print(f"Response: {result['response']}")
            
            if result.get('error'):
                print(f"Error: {result['error']}")
                
            return result
        else:
            print(f"Error Response: {response.text}")
            
    except Exception as e:
        print(f"Request failed: {e}")
    
    print()

def test_resume_api(session_id, user_reply="예"):
    """Resume API 테스트"""
    print("=== Resume API 테스트 ===")
    
    payload = {
        "user_reply": user_reply,
        "reply_type": "verification_reply"
    }
    
    url = f"{BASE_URL}/api/v1/resume/{session_id}"
    print(f"URL: {url}")
    print(f"User Reply: {user_reply}")
    
    try:
        response = requests.post(url, json=payload)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Success: {result.get('success')}")
            
            if result.get('response'):
                print(f"Response: {result['response'][:100]}...")
                
            return result
        else:
            print(f"Error Response: {response.text}")
            
    except Exception as e:
        print(f"Request failed: {e}")
    
    print()

def test_full_workflow():
    """전체 워크플로우 테스트"""
    print("\n" + "="*60)
    print("전체 워크플로우 테스트 시작")
    print("="*60 + "\n")
    
    # 1. 헬스 체크
    test_health_check()
    
    # 2. 초기 채팅 요청
    chat_result = test_chat_api()
    
    if chat_result and chat_result.get('requires_interrupt'):
        session_id = chat_result.get('session_id')
        
        # 3. 세션 재개 - "예" 응답
        resume_result = test_resume_api(session_id, "예")
        
        if resume_result and resume_result.get('requires_interrupt'):
            # 4. 상세 정보 입력
            print("=== 상세 정보 입력 ===")
            detailed_info = """방문일자: 2025-07-25
방문자: 허한결
방문기관: 유미가정의학과
면담자: 손현성
방문목적: 신약 홍보
면담내용: 자사 약품 소개와 로얄티 및 자사 약품 사용시 메리트를 소개하였음
건의사항: 자사 판촉물 1개 지급 요망"""
            
            final_result = test_resume_api(session_id, detailed_info)
            
            if final_result:
                print("\n=== 최종 결과 ===")
                print(f"Success: {final_result.get('success')}")
                if final_result.get('response'):
                    print(f"Response: {final_result['response']}")

if __name__ == "__main__":
    test_full_workflow()