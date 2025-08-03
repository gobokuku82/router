"""
RouterAgent 긴 쿼리 테스트
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.services.router_agent.router_agent import RouterAgent

async def test_long_queries():
    router = RouterAgent()
    
    # 실제 문제가 되었던 쿼리들
    test_queries = [
        # 22%% 포함된 쿼리
        "영업방문결과보고서 작성해줘. 거래처방문해서 COSMOS논문에서 아사 소화기용제가 경쟁사 대비 22%% 복약순응도가 높았다는 내용의 논문을 참고해서 제품의 우수한 특장점 디테일 했어.",
        
        # 매우 긴 쿼리
        "영업방문결과서 작성해줘. 내용은 방문 제목은 유미가정의학과 신약 홍보이고 방문일은 250725이고 client는 유미가정의학과 방문사이트는 www.yumibanplz.com 담담자는 손현성이고 소속은 영업팀 연락처는  010-1234-5678이야 영업제공자는  김도윤이고 연락처는 010-8765-4321이야 방문자는 허한결이고 소속은 영업팀이야 고객사 개요는 이번에 새로 오픈한 가정의학과로 사용 약품에 대해 많은 논의가 필요해보이는 잠재력이 있는 고객이야 프로젝트 개요는 신규고객 유치로 자사 약품홍보 후 로얄티 및 메리트 소개를 할거야 방문 및 협의 내용은 자사 약품 소개와 로얄티 및 자사 약품 사용시 메리트를 소개하였음 향후계획및일정은 7월 27일에 다시 방문하여 자사 판촉물 전달과 로얄티 협상을 할 예정이야 협조사항으로 자사 판촉물 1개 지급 요망"
    ]
    
    print("=== RouterAgent 긴 쿼리 테스트 ===\n")
    
    for i, query in enumerate(test_queries):
        print(f"테스트 {i+1}:")
        print(f"쿼리 길이: {len(query)}자")
        print(f"쿼리 시작: {query[:50]}...")
        
        result = await router.classify(query)
        print(f"분류 결과: {result}")
        print("-" * 80)

if __name__ == "__main__":
    asyncio.run(test_long_queries())