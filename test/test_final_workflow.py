"""
최종 워크플로우 테스트
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from backend.app.services.docs_agent.web_interface import WebDocumentAgent

async def test_complete_workflow():
    """전체 워크플로우 테스트"""
    print("=== 전체 워크플로우 테스트 ===\n")
    
    # 테스트 케이스들
    test_cases = [
        {
            "name": "규정 위반이 있는 경우",
            "content": """영업방문결과서 작성해줘. 내용은 방문 제목은 유미가정의학과 신약 홍보이고 
            방문일은 250725이고 client는 유미가정의학과 
            담담자는 손현성이고 소속은 영업팀 
            방문자는 허한결이고 소속은 영업팀이야 
            고객사 개요는 새로 오픈한 가정의학과야 
            프로젝트 개요는 신규고객 유치로 자사 약품홍보 후 로얄티 및 메리트 소개를 할거야 
            방문 및 협의 내용은 자사 약품 소개와 로얄티 및 자사 약품 사용시 메리트를 소개하였음 
            향후계획은 7월 27일에 다시 방문하여 자사 판촉물 전달과 로얄티 협상을 할 예정이야 
            협조사항으로 자사 판촉물 1개 지급 요망"""
        },
        {
            "name": "규정 위반이 없는 경우",
            "content": """영업방문결과서 작성해줘. 내용은 방문 제목은 유미가정의학과 제품 설명이고 
            방문일은 250725이고 client는 유미가정의학과 
            담담자는 손현성이고 소속은 영업팀 
            방문자는 허한결이고 소속은 영업팀이야 
            고객사 개요는 새로 오픈한 가정의학과야 
            방문 및 협의 내용은 자사 의약품의 효능과 사용법에 대해 설명하였음 
            향후계획은 7월 27일에 다시 방문하여 추가 질문사항에 답변할 예정"""
        }
    ]
    
    web_agent = WebDocumentAgent()
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*50}")
        print(f"테스트 {i}: {test_case['name']}")
        print(f"{'='*50}\n")
        
        # 세션 생성
        session_id = f"test_session_{i}"
        
        # 문서 생성 시작
        result = web_agent.create_session(session_id, test_case['content'])
        
        # 분류 확인
        if result.get('waiting_for_input') and result.get('input_type') == 'verification':
            print(f"문서 분류: {result.get('doc_type')}")
            print("분류 확인 응답: 예")
            
            # 검증 응답
            result = web_agent.process_user_input(session_id, "예")
            
            if result.get('success'):
                print(f"\n결과: {result.get('message', '성공')}")
                if result.get('document'):
                    print(f"생성된 문서: {result.get('file_path')}")
            else:
                print(f"\n결과: 실패")
                print(f"메시지: {result.get('message')}")
                if result.get('violation'):
                    print(f"위반 내용: {result.get('violation')}")

if __name__ == "__main__":
    # 로깅 설정
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s'
    )
    
    asyncio.run(test_complete_workflow())