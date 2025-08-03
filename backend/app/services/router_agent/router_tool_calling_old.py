"""
Router Agent - LangGraph + Tool Calling 기반 라우팅 시스템
"""
from typing import Dict, Any, List, TypedDict, Optional, Annotated
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import BaseMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
import logging
from datetime import datetime
import uuid

from ..employee_agent.employee_agent import EmployeeAgent
from ..docs_agent.create_document_agent import CreateDocumentAgent

logger = logging.getLogger(__name__)


class RouterState(TypedDict):
    """Router Agent State"""
    messages: List[BaseMessage]
    user_input: str
    thread_id: Optional[str]
    session_id: Optional[str]
    result: Optional[Dict[str, Any]]
    error: Optional[str]
    requires_interrupt: bool
    agent_type: Optional[str]


class RouterAgent:
    """LangGraph + Tool Calling 기반 Router Agent"""
    
    def __init__(self):
        # 에이전트 초기화
        self.docs_agent = CreateDocumentAgent()
        self.employee_agent = EmployeeAgent()
        
        # Tool 정의
        self.tools = [
            self._create_docs_agent_tool(),
            self._create_employee_agent_tool(),
            self._create_client_agent_tool(),
            self._create_search_agent_tool()
        ]
        
        # LLM with tools
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0
        ).bind_tools(self.tools)
        
        # Graph 생성
        self.graph = self._create_graph()
        
        # 세션 저장소
        self.sessions: Dict[str, Dict[str, Any]] = {}
    
    def _create_docs_agent_tool(self):
        """문서 작성 에이전트 도구 생성"""
        @tool
        def call_docs_agent(query: Annotated[str, "문서 작성 요청"]) -> Dict[str, Any]:
            """
            문서 자동 생성 및 규정 검토를 담당합니다.
            - 영업방문 결과보고서 작성
            - 제품설명회 시행 신청서 작성
            - 제품설명회 시행 결과보고서 작성
            - 기타 업무 문서 및 템플릿 기반 문서 생성
            - 컴플라이언스 검토
            """
            try:
                thread_id = self.current_thread_id
                result = self.docs_agent.run(user_input=query, thread_id=thread_id)
                
                # 인터럽트 처리
                if isinstance(result, dict) and result.get("interrupted"):
                    self.current_state["requires_interrupt"] = True
                    self.current_state["agent_type"] = "docs_agent"
                    
                    # 세션 저장
                    session_id = self.current_state.get("session_id")
                    if session_id:
                        self.sessions[session_id] = {
                            "agent": "docs_agent",
                            "thread_id": thread_id,
                            "status": "interrupted"
                        }
                
                return result
            except Exception as e:
                logger.error(f"Docs agent error: {e}")
                return {"success": False, "error": str(e)}
        
        return call_docs_agent
    
    def _create_employee_agent_tool(self):
        """직원 정보 에이전트 도구 생성"""
        @tool
        def call_employee_agent(query: Annotated[str, "직원 정보 조회 요청"]) -> Dict[str, Any]:
            """
            사내 직원에 대한 정보 제공을 담당합니다.
            - 개인 실적 조회 및 분석
            - 인사 이력, 직책, 소속 부서 확인
            - 조직도 조회
            - 성과 평가 및 목표 달성률 분석
            - 실적 트렌드 분석
            """
            try:
                if hasattr(self.employee_agent, 'analyze_employee_performance'):
                    result = self.employee_agent.analyze_employee_performance(query)
                else:
                    result = self.employee_agent.run(query)
                
                self.current_state["agent_type"] = "employee_agent"
                return result
            except Exception as e:
                logger.error(f"Employee agent error: {e}")
                return {"success": False, "error": str(e)}
        
        return call_employee_agent
    
    def _create_client_agent_tool(self):
        """고객 정보 에이전트 도구 생성"""
        @tool
        def call_client_agent(query: Annotated[str, "고객/거래처 정보 조회"]) -> Dict[str, Any]:
            """
            고객 및 거래처에 대한 정보를 제공합니다.
            병원, 제약영업과 관련된 질문에만 답변합니다.
            - 특정 고객의 매출 추이
            - 거래 이력 조회
            - 고객 등급 분류
            - 잠재 고객 분석
            - 영업 성과 분석
            """
            # 아직 구현되지 않음
            logger.warning("Client agent not implemented yet")
            return {
                "success": False,
                "error": "Client agent는 아직 구현되지 않았습니다.",
                "message": "담당자에게 문의해주세요."
            }
        
        return call_client_agent
    
    def _create_search_agent_tool(self):
        """검색 에이전트 도구 생성"""
        @tool
        def call_search_agent(query: Annotated[str, "내부 정보 검색 요청"]) -> Dict[str, Any]:
            """
            내부 데이터베이스에서 정보 검색을 수행합니다.
            - 문서 검색
            - 사내 규정 및 정책 조회
            - 업무 매뉴얼 검색
            - 제품 정보 조회
            - 교육 자료 검색
            - 정제된 DB 또는 벡터DB 기반 검색
            """
            # 아직 구현되지 않음
            logger.warning("Search agent not implemented yet")
            return {
                "success": False,
                "error": "Search agent는 아직 구현되지 않았습니다.",
                "message": "담당자에게 문의해주세요."
            }
        
        return call_search_agent
    
    def _create_graph(self):
        """LangGraph 워크플로우 생성"""
        workflow = StateGraph(RouterState)
        
        # Tool Node 생성
        tool_node = ToolNode(self.tools)
        
        # 노드 추가
        workflow.add_node("agent", self._agent_node)
        workflow.add_node("tools", tool_node)
        workflow.add_node("final", self._final_node)
        
        # 시작점 설정
        workflow.set_entry_point("agent")
        
        # 조건부 엣지
        workflow.add_conditional_edges(
            "agent",
            self._should_continue,
            {
                "tools": "tools",
                "final": "final",
                "error": "final"
            }
        )
        
        workflow.add_edge("tools", "final")
        workflow.add_edge("final", END)
        
        return workflow.compile()
    
    def _agent_node(self, state: RouterState) -> RouterState:
        """LLM 에이전트 노드"""
        try:
            # 현재 상태 저장 (tool에서 접근용)
            self.current_state = state
            self.current_thread_id = state.get("thread_id")
            
            # 메시지 생성
            messages = state.get("messages", [])
            if not messages and state.get("user_input"):
                from langchain_core.messages import HumanMessage
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
            logger.error(f"Agent node error: {e}")
            state["error"] = str(e)
            return state
    
    def _should_continue(self, state: RouterState) -> str:
        """다음 노드 결정"""
        messages = state.get("messages", [])
        if not messages:
            return "error"
        
        last_message = messages[-1]
        
        # 에러가 있으면 종료
        if state.get("error"):
            return "error"
        
        # Tool call이 있으면 tools로
        if isinstance(last_message, AIMessage) and last_message.tool_calls:
            return "tools"
        
        # 그 외는 final로
        return "final"
    
    def _final_node(self, state: RouterState) -> RouterState:
        """최종 처리 노드"""
        # Tool 실행 결과 추출
        messages = state.get("messages", [])
        
        if len(messages) >= 2:
            # 마지막 메시지가 tool 결과인 경우
            last_message = messages[-1]
            if hasattr(last_message, 'content'):
                try:
                    import json
                    # Tool 반환값이 문자열로 올 수 있음
                    if isinstance(last_message.content, str):
                        state["result"] = json.loads(last_message.content)
                    else:
                        state["result"] = last_message.content
                except:
                    state["result"] = {"content": last_message.content}
        
        return state
    
    def run(self, user_input: str, thread_id: Optional[str] = None) -> Dict[str, Any]:
        """Router 실행"""
        session_id = str(uuid.uuid4())
        
        initial_state = RouterState(
            messages=[],
            user_input=user_input,
            thread_id=thread_id,
            session_id=session_id,
            result=None,
            error=None,
            requires_interrupt=False,
            agent_type=None
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
                    "thread_id": thread_id,
                    "session_id": session_id,
                    "agent_type": final_state.get("agent_type"),
                    "requires_interrupt": True
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
                result = self.docs_agent.resume(thread_id, user_reply, reply_type)
                
                # 완료 확인
                if result.get("success"):
                    session_info["status"] = "completed"
                
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