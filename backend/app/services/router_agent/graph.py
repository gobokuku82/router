"""
Router Agent Graph 및 State 정의
"""
from typing import Dict, Any, List, TypedDict, Optional
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
import logging
import json

logger = logging.getLogger(__name__)


class RouterState(TypedDict):
    """Router Agent State"""
    # 기본 필드
    messages: List[BaseMessage]
    user_input: str
    session_id: str
    
    # 세션 관리
    active_agent: Optional[str]
    is_continuation: bool
    
    # 동적 컨텍스트
    context: Dict[str, Any]
    
    # 결과
    result: Optional[Dict[str, Any]]
    error: Optional[str]
    requires_interrupt: bool
    agent_type: Optional[str]
    thread_id: Optional[str]
    
    # 추가 정보 (docs_agent용)
    next_node: Optional[str]
    doc_type: Optional[str]
    state_info: Optional[Dict[str, Any]]
    
    # 에이전트 선택
    agent_selection_required: Optional[bool]


def create_graph(router_agent):
    """LangGraph 워크플로우 생성"""
    workflow = StateGraph(RouterState)
    
    # Tool Node 생성
    tool_node = ToolNode(router_agent.tools)
    
    # 노드 추가
    workflow.add_node("check_session", lambda state: check_session_node(router_agent, state))
    workflow.add_node("route", lambda state: route_node(router_agent, state))
    workflow.add_node("continue", lambda state: continue_conversation_node(router_agent, state))
    workflow.add_node("tools", tool_node)
    workflow.add_node("final", lambda state: final_node(router_agent, state))
    
    # 시작점 설정
    workflow.set_entry_point("check_session")
    
    # 조건부 엣지
    workflow.add_conditional_edges(
        "check_session",
        lambda state: session_router(router_agent, state),
        {
            "has_session": "continue",
            "new_conversation": "route"
        }
    )
    
    workflow.add_conditional_edges(
        "route",
        lambda state: route_decision(router_agent, state),
        {
            "tools": "tools",
            "final": "final",
            "error": "final"
        }
    )
    
    workflow.add_edge("continue", "final")
    workflow.add_edge("tools", "final")
    workflow.add_edge("final", END)
    
    return workflow.compile()


def check_session_node(router_agent, state: RouterState) -> RouterState:
    """세션 확인 노드"""
    session_id = state.get("session_id")
    
    if session_id and session_id in router_agent.sessions:
        session = router_agent.sessions[session_id]
        if session.get("active"):
            state["is_continuation"] = True
            state["active_agent"] = session["agent"]
            state["thread_id"] = session.get("thread_id")
            state["context"].update(session.get("context", {}))
        else:
            state["is_continuation"] = False
    else:
        state["is_continuation"] = False
    
    return state


def session_router(router_agent, state: RouterState) -> str:
    """세션 라우팅 결정"""
    if state.get("is_continuation"):
        return "has_session"
    return "new_conversation"


def route_node(router_agent, state: RouterState) -> RouterState:
    """LLM 라우팅 노드"""
    try:
        # 현재 상태 저장 (tool에서 접근용)
        router_agent.current_state = state
        logger.info(f"[ROUTE_NODE] Setting current_state with session_id: {state.get('session_id')}")
        
        # 메시지 생성
        messages = state.get("messages", [])
        if not messages and state.get("user_input"):
            messages = [HumanMessage(content=state["user_input"])]
            state["messages"] = messages
        
        # LLM 호출
        response = router_agent.llm.invoke(messages)
        
        # 응답 추가
        state["messages"].append(response)
        
        # Tool call이 없는 경우 안내 메시지 생성
        if not response.tool_calls:
            logger.info("[ROUTE_NODE] No tool calls found. Showing help message")
            help_message = router_agent._generate_help_message()
            state["result"] = {
                "success": True,
                "help_message": help_message
            }
            # 디버그 로깅
            logger.info(f"[ROUTE_NODE] Help message generated: {help_message[:100]}...")
            logger.info(f"[ROUTE_NODE] State result: {state['result']}")
        
        return state
        
    except Exception as e:
        logger.error(f"Route node error: {e}")
        state["error"] = str(e)
        return state


def route_decision(router_agent, state: RouterState) -> str:
    """라우팅 결정"""
    messages = state.get("messages", [])
    if not messages:
        return "error"
    
    last_message = messages[-1]
    
    if state.get("error"):
        return "error"
    
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tools"
    
    return "final"


def continue_conversation_node(router_agent, state: RouterState) -> RouterState:
    """활성 세션의 대화 계속"""
    try:
        session_id = state["session_id"]
        session = router_agent.sessions[session_id]
        agent_name = session["agent"]
        
        # 에이전트별 처리
        if agent_name == "docs_agent":
            agent = router_agent.agents_config[agent_name]["instance"]
            result = agent.run(user_input=state["user_input"])
            
            # 결과 처리
            if result.get("interrupted"):
                # 계속 대화 필요
                state["requires_interrupt"] = True
                state["result"] = result
            elif result.get("success"):
                # 대화 완료
                session["active"] = False
                state["result"] = result
            else:
                state["error"] = result.get("error", "Unknown error")
                
        elif agent_name == "employee_agent":
            agent = router_agent.agents_config[agent_name]["instance"]
            if hasattr(agent, 'analyze_employee_performance'):
                result = agent.analyze_employee_performance(state["user_input"])
            else:
                result = agent.run(state["user_input"])
            
            state["result"] = result
            session["active"] = False  # employee는 단발성
            
        else:
            state["error"] = f"Unknown agent: {agent_name}"
        
        state["agent_type"] = agent_name
        return state
        
    except Exception as e:
        logger.error(f"Continue conversation error: {e}")
        state["error"] = str(e)
        return state


def final_node(router_agent, state: RouterState) -> RouterState:
    """최종 처리 노드"""
    logger.info(f"[FINAL_NODE] Processing final node with requires_interrupt: {state.get('requires_interrupt')}")
    logger.info(f"[FINAL_NODE] Current state keys: {list(state.keys())}")
    logger.info(f"[FINAL_NODE] Current result: {state.get('result')}")
    
    # 이미 result가 설정되어 있으면 (help_message 등) 그대로 유지
    if state.get("result"):
        logger.info(f"[FINAL_NODE] Result already set, preserving it: {state['result']}")
        # result가 이미 있으면 다른 처리 없이 바로 반환
        return state
    
    # Tool 실행 결과 추출
    messages = state.get("messages", [])
    
    # ToolMessage 찾기 (마지막 메시지가 ToolMessage일 가능성이 높음)
    for i in range(len(messages) - 1, -1, -1):
        msg = messages[i]
        
        # ToolMessage 처리
        if hasattr(msg, 'name') and hasattr(msg, 'content'):  # ToolMessage의 특징
            try:
                # Tool 반환값 처리
                if isinstance(msg.content, str):
                    result = json.loads(msg.content)
                else:
                    result = msg.content
                
                state["result"] = result
                
                # Tool name에서 agent_type 추출
                if msg.name and msg.name.startswith('call_'):
                    state["agent_type"] = msg.name.replace('call_', '')
                
                # 인터럽트 발생 시 추가 정보를 state에 병합
                if isinstance(result, dict) and result.get("interrupted"):
                    logger.info(f"[FINAL_NODE] Interrupt in result - next_node: {result.get('next_node')}, doc_type: {result.get('doc_type')}")
                    if result.get("thread_id"):
                        state["thread_id"] = result["thread_id"]
                    if result.get("next_node"):
                        state["next_node"] = result["next_node"]
                    if result.get("doc_type"):
                        state["doc_type"] = result["doc_type"]
                    if result.get("state_info"):
                        state["state_info"] = result["state_info"]
                    state["requires_interrupt"] = True
                
                break  # 첫 번째 ToolMessage를 찾으면 중단
                
            except json.JSONDecodeError:
                state["result"] = {"content": msg.content}
            except Exception as e:
                logger.error(f"Tool message processing error: {e}")
    
    # 최종 상태 로깅
    logger.info(f"[FINAL_NODE] Final state - requires_interrupt: {state.get('requires_interrupt')}, next_node: {state.get('next_node')}, doc_type: {state.get('doc_type')}")
    
    return state