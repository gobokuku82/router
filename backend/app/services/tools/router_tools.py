"""
Router Agent를 위한 동적 도구 생성 모듈
"""
from typing import Dict, Any, List, Annotated
from langchain_core.tools import tool
import logging

logger = logging.getLogger(__name__)


def create_tools_from_config(agents_config: Dict[str, Any], execute_agent_func) -> List:
    """설정에서 도구를 동적으로 생성"""
    tools = []
    
    for agent_name, config in agents_config.items():
        # 메타데이터에서 정보 추출
        metadata = config["metadata"]
        
        # 도구 함수 동적 생성
        def make_tool(name, cfg):
            # 클로저로 agent_name과 config 캡처
            def agent_tool(query: Annotated[str, f"{metadata['description'][:50]}..."]) -> Dict[str, Any]:
                return execute_agent_func(name, query)
            
            # 함수 메타데이터 설정
            agent_tool.__name__ = f"call_{name}"
            agent_tool.__doc__ = generate_tool_docstring(metadata)
            
            return tool(agent_tool)
        
        tools.append(make_tool(agent_name, config))
    
    return tools


def generate_tool_docstring(metadata: Dict[str, Any]) -> str:
    """메타데이터에서 도구 설명 생성"""
    docstring = f"{metadata['description']}\n\n"
    
    if metadata.get("capabilities"):
        docstring += "주요 기능:\n"
        for cap in metadata["capabilities"]:
            docstring += f"- {cap}\n"
    
    if metadata.get("examples"):
        docstring += "\n사용 예시:\n"
        for ex in metadata["examples"]:
            docstring += f"- {ex}\n"
    
    return docstring