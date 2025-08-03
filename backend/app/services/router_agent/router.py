"""
Router Agent - 세션 기반 라우팅 시스템
동적 도구 생성과 대화 연속성을 지원합니다.
"""
from typing import Dict, Any, List, TypedDict, Optional, Annotated
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
import logging
from datetime import datetime
import uuid
import json
import os

from ..employee_agent.employee_agent import EnhancedEmployeeAgent
from ..docs_agent import CreateDocumentAgent
from ..client_agent import client_agent
from ..search_agent import run as search_agent_run
import asyncio

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


class RouterAgent:
    """세션 기반 Router Agent"""
    
    def __init__(self):
        # 에이전트 설정 (메타데이터 포함)
        self.agents_config = {
            "docs_agent": {
                "instance": CreateDocumentAgent(),
                "metadata": {
                    "description": "문서 자동 생성 및 규정 검토를 담당합니다. 문서생성시 규정위반 여부도 검토합니다.",
                    "capabilities": [
                        "영업방문 결과보고서 작성",
                        "제품설명회 시행 신청서 작성",
                        "제품설명회 시행 결과보고서 작성",

                    ],
                    "examples": [
                        "영업방문 보고서 작성해줘",
                        "제품설명회 신청서 만들어줘",
                        "문서 작성 도와줘"
                    ]
                }
            },
            "employee_agent": {
                "instance": EnhancedEmployeeAgent(),
                "metadata": {
                    "description": "사내 직원에 대한 정보 제공을 담당합니다",
                    "capabilities": [
                        "개인 실적 조회 및 분석",
                        "인사 이력, 직책, 소속 부서 확인",
                        "성과 평가 및 목표 달성률 분석",
                        "실적 트렌드 분석"
                    ],
                    "examples": [
                        "최수아 실적 분석해줘",
                        "서부팀 성과 보여줘",
                        "최수아 이번달 달성률이 얼마지?"
                    ]
                }
            },
            "client_agent": {
                "instance": client_agent.agent,
                "metadata": {
                    "description": "고객 및 거래처에 대한 정보를 제공합니다. 테이블데이터에서 요청한 정보를 분석합니다. 사용자 질의를 바탕으로 필요한 tool을 호출합니다.",
                    "capabilities": [
                        "병원명,월별 실적 활동 정보 조회",
                        "매출 추이 분석",
                        "기준점을 제시하면 다른 수치와 비교,분석",
                        "고객 등급 분류",
                        "병원 전체매출과 우리 매출 비교"
                    ],
                    "examples": [
                        "미라클신경과 실적분석해줘",
                        "미라클신경과와 우리가족의원 비교",
                        "최근 3개월 실적 트렌드 분석"
                    ]
                }
            },
            "search_agent": {
                "instance": "search",  # 플래그로 사용
                "metadata": {
                    "description": "내부 데이터베이스에서 정보 검색을 수행합니다",
                    "capabilities": [
                        "문서 검색",
                        "사내 규정 및 정책 조회",
                        "업무 매뉴얼 검색",
                        "제품 정보 조회",
                        "교육 자료 검색"
                    ],
                    "examples": [
                        "영업 규정 찾아줘",
                        "제품 설명서 검색",
                        "교육 자료 조회"
                    ]
                }
            }
        }
        
        # 세션 저장소
        self.sessions: Dict[str, Dict[str, Any]] = {}
        
        # 동적으로 도구 생성
        self.tools = self._create_tools_from_config()
        
        # LLM with tools
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0
        ).bind_tools(self.tools)
        
        # Graph 생성
        self.graph = self._create_graph()
    
    def _create_tools_from_config(self):
        """설정에서 도구를 동적으로 생성"""
        tools = []
        
        for agent_name, config in self.agents_config.items():
            # 메타데이터에서 정보 추출
            metadata = config["metadata"]
            
            # 도구 함수 동적 생성
            def make_tool(name, cfg):
                # 클로저로 agent_name과 config 캡처
                def agent_tool(query: Annotated[str, f"{metadata['description'][:50]}..."]) -> Dict[str, Any]:
                    return self._execute_agent(name, query)
                
                # 함수 메타데이터 설정
                agent_tool.__name__ = f"call_{name}"
                agent_tool.__doc__ = self._generate_tool_docstring(metadata)
                
                return tool(agent_tool)
            
            tools.append(make_tool(agent_name, config))
        
        return tools
    
    def _generate_tool_docstring(self, metadata: Dict[str, Any]) -> str:
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
    
    def _execute_agent(self, agent_name: str, query: str) -> Dict[str, Any]:
        """에이전트 실행"""
        try:
            logger.info(f"[EXECUTE_AGENT] Starting {agent_name} with query: {query[:50]}...")
            
            config = self.agents_config.get(agent_name)
            if not config or not config["instance"]:
                return {
                    "success": False,
                    "error": f"{agent_name}는 아직 구현되지 않았습니다.",
                    "message": "담당자에게 문의해주세요."
                }
            
            agent = config["instance"]
            
            # 현재 state에서 정보 추출
            current_state = getattr(self, 'current_state', {})
            logger.info(f"[EXECUTE_AGENT] Current state keys: {list(current_state.keys()) if current_state else 'None'}")
            session_id = current_state.get("session_id")
            context = current_state.get("context", {})
            
            # 에이전트별 실행
            if agent_name == "docs_agent":
                # API 모드 설정
                os.environ["NO_INPUT_MODE"] = "true"
                logger.info(f"[EXECUTE_AGENT] API mode enabled for docs_agent")
                try:
                    # docs_agent는 thread_id를 지원하지 않음
                    result = agent.run(user_input=query)
                    logger.info(f"[EXECUTE_AGENT] docs_agent result keys: {list(result.keys()) if result else 'None'}")
                finally:
                    # 환경 변수 복원
                    os.environ.pop("NO_INPUT_MODE", None)
                
                # 인터럽트 처리
                if isinstance(result, dict) and result.get("interrupted"):
                    logger.info(f"[EXECUTE_AGENT] Interrupt detected - next_node: {result.get('next_node')}, doc_type: {result.get('doc_type')}")
                    current_state["requires_interrupt"] = True
                    current_state["agent_type"] = agent_name
                    
                    # 추가 정보를 result에 병합
                    if result.get("next_node"):
                        current_state["next_node"] = result["next_node"]
                    if result.get("doc_type"):
                        current_state["doc_type"] = result["doc_type"]
                    if result.get("state_info"):
                        current_state["state_info"] = result["state_info"]
                    
                    # 세션 생성/업데이트
                    if session_id:
                        logger.info(f"[EXECUTE_AGENT] Saving session for {session_id} with thread_id: {result.get('thread_id')}")
                        self.sessions[session_id] = {
                            "agent": agent_name,
                            "thread_id": result.get("thread_id"),
                            "active": True,
                            "context": context,
                            "next_node": result.get("next_node"),
                            "doc_type": result.get("doc_type")
                        }
                
                return result
            
            elif agent_name == "employee_agent":
                # employee_agent는 analyze_employee_performance 메서드 사용
                if hasattr(agent, 'analyze_employee_performance'):
                    result = agent.analyze_employee_performance(query)
                else:
                    result = agent.run(query)
                
                current_state["agent_type"] = agent_name
                return result
            
            elif agent_name == "client_agent":
                # client_agent는 async 함수
                logger.info(f"[EXECUTE_AGENT] Running client_agent with query: {query[:50]}...")
                result = asyncio.run(client_agent.run(query, session_id or "default"))
                
                current_state["agent_type"] = agent_name
                return result
            
            elif agent_name == "search_agent":
                # search_agent는 async 함수
                logger.info(f"[EXECUTE_AGENT] Running search_agent with query: {query[:50]}...")
                result = asyncio.run(search_agent_run(query, session_id or "default"))
                
                current_state["agent_type"] = agent_name
                return result
            
            else:
                # 다른 에이전트들
                return agent.run(query)
                
        except Exception as e:
            logger.error(f"{agent_name} execution error: {e}")
            return {"success": False, "error": str(e)}
    
    def _create_graph(self):
        """LangGraph 워크플로우 생성"""
        workflow = StateGraph(RouterState)
        
        # Tool Node 생성
        tool_node = ToolNode(self.tools)
        
        # 노드 추가
        workflow.add_node("check_session", self._check_session_node)
        workflow.add_node("route", self._route_node)
        workflow.add_node("continue", self._continue_conversation_node)
        workflow.add_node("tools", tool_node)
        workflow.add_node("final", self._final_node)
        
        # 시작점 설정
        workflow.set_entry_point("check_session")
        
        # 조건부 엣지
        workflow.add_conditional_edges(
            "check_session",
            self._session_router,
            {
                "has_session": "continue",
                "new_conversation": "route"
            }
        )
        
        workflow.add_conditional_edges(
            "route",
            self._route_decision,
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
    
    def _check_session_node(self, state: RouterState) -> RouterState:
        """세션 확인 노드"""
        session_id = state.get("session_id")
        
        if session_id and session_id in self.sessions:
            session = self.sessions[session_id]
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
    
    def _session_router(self, state: RouterState) -> str:
        """세션 라우팅 결정"""
        if state.get("is_continuation"):
            return "has_session"
        return "new_conversation"
    
    def _route_node(self, state: RouterState) -> RouterState:
        """LLM 라우팅 노드"""
        try:
            # 현재 상태 저장 (tool에서 접근용)
            self.current_state = state
            logger.info(f"[ROUTE_NODE] Setting current_state with session_id: {state.get('session_id')}")
            
            # 메시지 생성
            messages = state.get("messages", [])
            if not messages and state.get("user_input"):
                messages = [HumanMessage(content=state["user_input"])]
                state["messages"] = messages
            
            # LLM 호출
            response = self.llm.invoke(messages)
            
            # 응답 추가
            state["messages"].append(response)
            
            # Tool call이 없는 경우 처리
            if not response.tool_calls:
                state["error"] = "적절한 에이전트를 찾을 수 없습니다."
            
            return state
            
        except Exception as e:
            logger.error(f"Route node error: {e}")
            state["error"] = str(e)
            return state
    
    def _route_decision(self, state: RouterState) -> str:
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
    
    def _continue_conversation_node(self, state: RouterState) -> RouterState:
        """활성 세션의 대화 계속"""
        try:
            session_id = state["session_id"]
            session = self.sessions[session_id]
            agent_name = session["agent"]
            
            # 에이전트별 처리
            if agent_name == "docs_agent":
                agent = self.agents_config[agent_name]["instance"]
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
                agent = self.agents_config[agent_name]["instance"]
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
    
    def _final_node(self, state: RouterState) -> RouterState:
        """최종 처리 노드"""
        logger.info(f"[FINAL_NODE] Processing final node with requires_interrupt: {state.get('requires_interrupt')}")
        logger.info(f"[FINAL_NODE] Current state keys: {list(state.keys())}")
        
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
    
    def run(self, user_input: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Router 실행"""
        # 세션 ID 생성 또는 사용
        if not session_id:
            session_id = str(uuid.uuid4())
        
        initial_state = RouterState(
            messages=[],
            user_input=user_input,
            session_id=session_id,
            active_agent=None,
            is_continuation=False,
            context={},
            result=None,
            error=None,
            requires_interrupt=False,
            agent_type=None,
            thread_id=None,
            next_node=None,
            doc_type=None,
            state_info=None
        )
        
        try:
            # 그래프 실행
            final_state = self.graph.invoke(initial_state)
            
            # 에러 처리
            if final_state.get("error"):
                return {
                    "success": False,
                    "session_id": session_id,
                    "error": final_state["error"],
                    "requires_interrupt": False
                }
            
            # 인터럽트 처리
            if final_state.get("requires_interrupt"):
                result = final_state.get("result", {})
                logger.info(f"[RUN] Interrupt detected - final_state keys: {list(final_state.keys())}")
                logger.info(f"[RUN] final_state next_node: {final_state.get('next_node')}, doc_type: {final_state.get('doc_type')}")
                logger.info(f"[RUN] result next_node: {result.get('next_node') if result else 'None'}, doc_type: {result.get('doc_type') if result else 'None'}")
                
                return {
                    "success": False,
                    "interrupted": True,
                    "thread_id": final_state.get("thread_id"),
                    "session_id": session_id,
                    "agent_type": final_state.get("agent_type"),
                    "requires_interrupt": True,
                    "prompt": result.get("prompt") if result else None,
                    "next_node": final_state.get("next_node") or (result.get("next_node") if result else None),
                    "doc_type": final_state.get("doc_type") or (result.get("doc_type") if result else None),
                    "state_info": final_state.get("state_info") or (result.get("state_info") if result else {})
                }
            
            # 정상 결과
            result = final_state.get("result", {})
            return {
                "success": True,
                "session_id": session_id,
                "agent_type": final_state.get("agent_type"),
                "result": result,
                "requires_interrupt": False
            }
            
        except Exception as e:
            logger.error(f"Router execution error: {e}")
            return {
                "success": False,
                "session_id": session_id,
                "error": str(e),
                "requires_interrupt": False
            }
    
    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """세션 상태 조회"""
        if session_id in self.sessions:
            session_info = self.sessions[session_id]
            return {
                "exists": True,
                "session_id": session_id,
                "agent": session_info.get("agent"),
                "thread_id": session_info.get("thread_id"),
                "status": "active" if session_info.get("active") else "inactive"
            }
        else:
            return {
                "exists": False,
                "session_id": session_id,
                "message": "세션을 찾을 수 없습니다."
            }
    
    def resume(self, session_id: str, user_reply: str, reply_type: str = "user_reply") -> Dict[str, Any]:
        """인터럽트된 작업 재개"""
        session_info = self.sessions.get(session_id)
        if not session_info:
            return {
                "success": False,
                "error": "세션을 찾을 수 없습니다."
            }
        
        try:
            if session_info["agent"] == "docs_agent":
                thread_id = session_info["thread_id"]
                agent = self.agents_config["docs_agent"]["instance"]
                
                # API 모드 설정
                os.environ["NO_INPUT_MODE"] = "true"
                try:
                    result = agent.resume(thread_id, user_reply, reply_type)
                finally:
                    # 환경 변수 복원
                    os.environ.pop("NO_INPUT_MODE", None)
                
                # result가 None인 경우 처리
                if result is None:
                    return {
                        "success": False,
                        "error": "문서 생성이 중단되었습니다."
                    }
                
                # 완료 확인
                if result.get("success"):
                    session_info["active"] = False
                elif result.get("interrupted"):
                    # 계속 대화 필요
                    return {
                        "success": False,
                        "interrupted": True,
                        "thread_id": thread_id,
                        "session_id": session_id,
                        "prompt": result.get("prompt"),
                        "requires_interrupt": True,
                        "next_node": result.get("next_node"),
                        "doc_type": result.get("doc_type"),
                        "state_info": result.get("state_info", {})
                    }
                
                return result
            else:
                return {
                    "success": False,
                    "error": f"{session_info['agent']}는 인터럽트를 지원하지 않습니다."
                }
                
        except Exception as e:
            logger.error(f"Resume error: {e}")
            return {
                "success": False,
                "error": str(e)
            }