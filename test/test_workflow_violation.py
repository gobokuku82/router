"""
워크플로우에서 규정 위반 차단 테스트
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.services.docs_agent import run

async def test_violation_blocking():
    """규정 위반 시 문서 생성 차단 테스트"""
    
    # 규정 위반이 포함된 내용
    test_query = """영업방문결과서 작성해줘. 내용은 방문 제목은 유미가정의학과 신약 홍보이고 
    방문일은 250725이고 client는 유미가정의학과 
    담담자는 손현성이고 소속은 영업팀 
    방문자는 허한결이고 소속은 영업팀이야 
    고객사 개요는 새로 오픈한 가정의학과야 
    프로젝트 개요는 신규고객 유치로 자사 약품홍보 후 로얄티 및 메리트 소개를 할거야 
    방문 및 협의 내용은 자사 약품 소개와 로얄티 및 자사 약품 사용시 메리트를 소개하였음 
    향후계획은 7월 27일에 다시 방문하여 자사 판촉물 전달과 로얄티 협상을 할 예정이야 
    협조사항으로 자사 판촉물 1개 지급 요망"""
    
    session_id = "test_violation_session"
    
    print("=== 규정 위반 차단 테스트 ===\n")
    print("테스트 내용: 로얄티, 판촉물 등 규정 위반 내용 포함\n")
    
    # docs_agent 실행
    result = await run(test_query, session_id)
    
    print("\n실행 결과:")
    print(f"- 성공 여부: {result.get('success')}")
    print(f"- 에이전트: {result.get('agent')}")
    print(f"- 응답: {result.get('response', '')[:200]}...")
    
    if result.get('violation'):
        print(f"\n[성공] 규정 위반이 감지되었습니다:")
        print(f"위반 내용: {result.get('violation')}")
    
    if result.get('error'):
        print(f"\n에러: {result.get('error')}")
    
    # 두 번째 응답 처리 (예/아니오)
    if result.get('waiting_for_input'):
        print("\n분류 확인 중...")
        result2 = await run("예", session_id)
        
        print("\n두 번째 응답 결과:")
        print(f"- 성공 여부: {result2.get('success')}")
        print(f"- 응답: {result2.get('response', '')[:200]}...")
        
        if result2.get('violation'):
            print(f"\n[성공] 규정 위반이 감지되었습니다:")
            print(f"위반 내용: {result2.get('violation')}")
        
        if not result2.get('success') and result2.get('step') == 'violation_detected':
            print("\n[성공] 규정 위반으로 인해 문서 생성이 차단되었습니다!")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_violation_blocking())