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

from ..employee_agent.employee_agent import EnhancedEmployeeAgent
from ..docs_agent import CreateDocumentAgent

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


class RouterAgent:
    """세션 기반 Router Agent"""
    
    def __init__(self):
        # 에이전트 설정 (메타데이터 포함)
        self.agents_config = {
            "docs_agent": {
                "instance": CreateDocumentAgent(),
                "metadata": {
                    "description": "문서 자동 생성 및 규정 검토를 담당합니다",
                    "capabilities": [
                        "영업방문 결과보고서 작성",
                        "제품설명회 시행 신청서 작성",
                        "제품설명회 시행 결과보고서 작성",
                        "템플릿 기반 문서 생성",
                        "컴플라이언스 검토"
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
                        "조직도 조회",
                        "성과 평가 및 목표 달성률 분석",
                        "실적 트렌드 분석"
                    ],
                    "examples": [
                        "김철수 실적 분석해줘",
                        "영업팀 성과 보여줘",
                        "이번달 실적 조회"
                    ]
                }
            },
            "client_agent": {
                "instance": None,  # 아직 미구현
                "metadata": {
                    "description": "고객 및 거래처에 대한 정보를 제공합니다",
                    "capabilities": [
                        "병원, 약국 등 고객 정보 조회",
                        "매출 추이 분석",
                        "거래 이력 조회",
                        "고객 등급 분류",
                        "잠재 고객 분석"
                    ],
                    "examples": [
                        "삼성병원 거래 이력 조회",
                        "A등급 고객 리스트",
                        "이번달 신규 거래처"
                    ]
                }
            },
            "search_agent": {
                "instance": None,  # 아직 미구현
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
            session_id = current_state.get("session_id")
            context = current_state.get("context", {})
            
            # 에이전트별 실행
            if agent_name == "docs_agent":
                # thread_id 확인 (세션에 있을 수 있음)
                thread_id = None
                if session_id and session_id in self.sessions:
                    thread_id = self.sessions[session_id].get("thread_id")
                
                result = agent.run(user_input=query, thread_id=thread_id)
                
                # 인터럽트 처리
                if isinstance(result, dict) and result.get("interrupted"):
                    current_state["requires_interrupt"] = True
                    current_state["agent_type"] = agent_name
                    
                    # 세션 생성/업데이트
                    if session_id:
                        self.sessions[session_id] = {
                            "agent": agent_name,
                            "thread_id": result.get("thread_id"),
                            "active": True,
                            "context": context
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
                result = agent.run(
                    user_input=state["user_input"],
                    thread_id=session.get("thread_id")
                )
                
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
                        state["result"] = json.loads(msg.content)
                    else:
                        state["result"] = msg.content
                    
                    # Tool name에서 agent_type 추출
                    if msg.name and msg.name.startswith('call_'):
                        state["agent_type"] = msg.name.replace('call_', '')
                    
                    break  # 첫 번째 ToolMessage를 찾으면 중단
                    
                except json.JSONDecodeError:
                    state["result"] = {"content": msg.content}
                except Exception as e:
                    logger.error(f"Tool message processing error: {e}")
        
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
            thread_id=None
        )
        
        try:
            # 그래프 실행
            final_state = self.graph.invoke(initial_state)
            
            # 에러 처리
            if final_state.get("error"):
                return {
                    "success": False,
                    "error": final_state["error"],
                    "requires_interrupt": False
                }
            
            # 인터럽트 처리
            if final_state.get("requires_interrupt"):
                return {
                    "success": False,
                    "interrupted": True,
                    "thread_id": final_state.get("thread_id"),
                    "session_id": session_id,
                    "agent_type": final_state.get("agent_type"),
                    "requires_interrupt": True,
                    "prompt": final_state.get("result", {}).get("prompt")
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
                "error": str(e),
                "requires_interrupt": False
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
                result = agent.resume(thread_id, user_reply, reply_type)
                
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
                        "requires_interrupt": True
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