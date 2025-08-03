"""
DB 기반 규정 위반 검사 테스트
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from backend.app.services.docs_agent.web_interface import WebDocumentAgent

async def test_db_violation_check():
    """DB 기반 규정 위반 검사 테스트"""
    
    # 테스트용 문서 내용 (규정 위반 포함)
    test_content = """영업방문결과서 작성해줘. 내용은 방문 제목은 유미가정의학과 신약 홍보이고 
    방문일은 250725이고 client는 유미가정의학과 방문사이트는 www.yumibanplz.com 
    담담자는 손현성이고 소속은 영업팀 연락처는 010-1234-5678이야 
    영업제공자는 김도윤이고 연락처는 010-8765-4321이야 
    방문자는 허한결이고 소속은 영업팀이야 
    고객사 개요는 이번에 새로 오픈한 가정의학과로 사용 약품에 대해 많은 논의가 필요해보이는 잠재력이 있는 고객이야 
    프로젝트 개요는 신규고객 유치로 자사 약품홍보 후 로얄티 및 메리트 소개를 할거야 
    방문 및 협의 내용은 자사 약품 소개와 로얄티 및 자사 약품 사용시 메리트를 소개하였음 
    향후계획및일정은 7월 27일에 다시 방문하여 자사 판촉물 전달과 로얄티 협상을 할 예정이야 
    협조사항으로 자사 판촉물 1개 지급 요망"""
    
    print("=== DB 기반 규정 위반 검사 테스트 ===\n")
    
    # WebDocumentAgent 생성
    web_agent = WebDocumentAgent()
    
    print("테스트 내용:")
    print(test_content[:100] + "...\n")
    
    # DB 기반 규정 검사 실행
    print("DB에서 규정을 조회하여 검사 중...")
    result = web_agent._check_additional_violations(test_content)
    
    print("\n검사 결과:")
    print(result if result else "위반 사항 없음")
    
    # FastAPI 연결 테스트
    import requests
    try:
        response = requests.get("http://localhost:8010/health")
        if response.status_code == 200:
            print("\n[OK] FastAPI 연결 성공")
            print(f"API 상태: {response.json()}")
        else:
            print(f"\n[ERROR] FastAPI 연결 실패: {response.status_code}")
    except Exception as e:
        print(f"\n[ERROR] FastAPI 연결 오류: {e}")

if __name__ == "__main__":
    asyncio.run(test_db_violation_check())