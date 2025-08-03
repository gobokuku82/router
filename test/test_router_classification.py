"""
RouterAgent 분류 테스트
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.services.router_agent.router_agent import RouterAgent

async def test_router():
    router = RouterAgent()
    
    test_queries = [
        "영업방문결과보고서 작성해줘",
        "영업방문 결과보고서 작성해줘",
        "제품설명회 결과보고서 작성해줘",
        "안녕하세요",
        "날씨가 좋네요"
    ]
    
    print("=== RouterAgent 분류 테스트 ===\n")
    
    for query in test_queries:
        result = await router.classify(query)
        print(f"질문: {query}")
        print(f"분류 결과: {result}")
        print("-" * 50)

if __name__ == "__main__":
    asyncio.run(test_router())