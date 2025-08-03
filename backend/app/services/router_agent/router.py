"""
라우터 에이전트 메인 모듈
사용자 질문을 분류하고 적절한 에이전트로 라우팅합니다.
"""
from typing import Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage
import uuid
import json
from pathlib import Path
import sys

# 상위 경로 추가
sys.path.append(str(Path(__file__).parent.parent))

from ..common.state import RouterState, BaseState
from .classifier import AgentClassifier

# 각 에이전트 임포트
from ..docs_agent.create_document_agent import CreateDocumentAgent
from ..employee_agent.employee_agent import EnhancedEmployeeAgent


class RouterAgent:
    """
    메인 라우터 에이전트
    질문을 분류하고 적절한 하위 에이전트로 라우팅합니다.
    """
    
    def __init__(self):
        """라우터 에이전트 초기화"""
        self.classifier = AgentClassifier()
        
        # 하위 에이전트 인스턴스
        self.docs_agent = CreateDocumentAgent()
        self.employee_agent = EnhancedEmployeeAgent()
        
        # 세션 저장소
        self.sessions: Dict[str, Dict[str, Any]] = {}
        
        # 그래프 구성
        self.graph = self._build_graph()
        
    def _build_graph(self):
        """
        LangGraph 워크플로우 구성
        
        Returns:
            CompiledGraph: 컴파일된 그래프
        """
        workflow = StateGraph(RouterState)
        
        # 노드 추가
        workflow.add_node("classify_query", self._classify_query_node)
        workflow.add_node("route_to_agent", self._route_to_agent_node)
        workflow.add_node("aggregate_result", self._aggregate_result_node)
        
        # 엣지 연결
        workflow.set_entry_point("classify_query")
        workflow.add_edge("classify_query", "route_to_agent")
        workflow.add_edge("route_to_agent", "aggregate_result")
        workflow.add_edge("aggregate_result", END)
        
        # 메모리 체크포인터 추가
        memory = MemorySaver()
        return workflow.compile(checkpointer=memory)
    
    def _classify_query_node(self, state: RouterState) -> RouterState:
        """
        사용자 질문을 분류하는 노드
        
        Args:
            state: 현재 상태
            
        Returns:
            RouterState: 업데이트된 상태
        """
        try:
            # 최신 사용자 메시지 추출
            if not state.get("messages"):
                state["error"] = "메시지가 없습니다."
                return state
            
            user_query = state["messages"][-1].content
            print(f"[CLASSIFY] 질문 분류 중: {user_query}")
            
            # 질문 분류
            agent_name, confidence, analysis = self.classifier.classify(user_query)
            
            print(f"[CLASSIFY] 결과: {agent_name} (신뢰도: {confidence:.2f})")
            
            # 상태 업데이트
            state["target_agent"] = agent_name
            state["classification_confidence"] = confidence
            
            # 분석 정보를 sub_agent_state에 저장
            state["sub_agent_state"] = {
                "classification_analysis": analysis,
                "original_query": user_query
            }
            
            # 낮은 신뢰도 경고
            if confidence < 0.5:
                print(f"[WARNING] 낮은 분류 신뢰도: {confidence:.2f}")
                if analysis.get("fallback"):
                    print("[INFO] 기본값(docs_agent)으로 진행합니다.")
            
        except Exception as e:
            print(f"[ERROR] 질문 분류 오류: {e}")
            state["error"] = f"질문 분류 오류: {str(e)}"
            state["target_agent"] = "docs_agent"  # 오류 시 기본값
            state["classification_confidence"] = 0.1
        
        return state
    
    def _route_to_agent_node(self, state: RouterState) -> RouterState:
        """
        분류된 에이전트로 라우팅하는 노드
        
        Args:
            state: 현재 상태
            
        Returns:
            RouterState: 업데이트된 상태
        """
        target_agent = state.get("target_agent")
        user_query = state["messages"][-1].content
        
        print(f"[ROUTE] {target_agent}로 라우팅 중...")
        
        try:
            if target_agent == "docs_agent":
                result = self._handle_docs_agent(user_query, state)
            elif target_agent == "employee_agent":
                result = self._handle_employee_agent(user_query, state)
            else:
                raise ValueError(f"알 수 없는 에이전트: {target_agent}")
            
            state["sub_agent_result"] = result
            
        except Exception as e:
            print(f"[ERROR] 에이전트 실행 오류: {e}")
            state["error"] = f"에이전트 실행 오류: {str(e)}"
            state["sub_agent_result"] = {
                "success": False,
                "error": str(e)
            }
        
        return state
    
    def _handle_docs_agent(self, user_query: str, state: RouterState) -> Dict[str, Any]:
        """
        문서 작성 에이전트 처리
        
        Args:
            user_query: 사용자 질문
            state: 현재 상태
            
        Returns:
            Dict: 실행 결과
        """
        try:
            # docs_agent 실행
            result = self.docs_agent.run(user_input=user_query)
            
            # 인터럽트 발생 확인
            if result.get("thread_id") and not result.get("success"):
                # 세션 정보 저장
                session_id = state["session_id"]
                self.sessions[session_id] = {
                    "agent": "docs_agent",
                    "thread_id": result["thread_id"],
                    "status": "interrupted",
                    "state": state
                }
                
                state["requires_interrupt"] = True
                
                return {
                    "success": False,
                    "interrupted": True,
                    "thread_id": result["thread_id"],
                    "message": "사용자 입력이 필요합니다.",
                    "agent": "docs_agent"
                }
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "agent": "docs_agent"
            }
    
    def _handle_employee_agent(self, user_query: str, state: RouterState) -> Dict[str, Any]:
        """
        직원 실적 분석 에이전트 처리
        
        Args:
            user_query: 사용자 질문
            state: 현재 상태
            
        Returns:
            Dict: 실행 결과
        """
        try:
            # employee_agent는 인터럽트가 없으므로 직접 실행
            result = self.employee_agent.analyze_employee_performance(user_query)
            
            # 표준 형식으로 변환
            return {
                "success": result.get("success", False),
                "agent": "employee_agent",
                "response": result.get("report", ""),
                "data": {
                    "employee_name": result.get("employee_name"),
                    "period": result.get("period"),
                    "total_performance": result.get("total_performance"),
                    "achievement_rate": result.get("achievement_rate"),
                    "evaluation": result.get("evaluation"),
                    "analysis_details": result.get("analysis_details", {})
                },
                "error": result.get("error")
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "agent": "employee_agent"
            }
    
    def _aggregate_result_node(self, state: RouterState) -> RouterState:
        """
        결과를 집계하고 최종 응답을 준비하는 노드
        
        Args:
            state: 현재 상태
            
        Returns:
            RouterState: 최종 상태
        """
        sub_result = state.get("sub_agent_result", {})
        
        if sub_result.get("success"):
            print(f"[SUCCESS] {sub_result.get('agent')} 실행 완료")
        elif sub_result.get("interrupted"):
            print(f"[INTERRUPT] {sub_result.get('agent')} 인터럽트 발생")
        else:
            print(f"[ERROR] {sub_result.get('agent')} 실행 실패: {sub_result.get('error')}")
        
        return state
    
    def run(self, user_query: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        라우터 에이전트 실행
        
        Args:
            user_query: 사용자 질문
            session_id: 세션 ID (선택사항)
            
        Returns:
            Dict: 실행 결과
        """
        # 세션 ID 생성 또는 사용
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # 초기 상태 생성
        initial_state = {
            "messages": [HumanMessage(content=user_query)],
            "session_id": session_id,
            "agent_type": "router",
            "error": None,
            "target_agent": None,
            "sub_agent_state": None,
            "sub_agent_result": None,
            "requires_interrupt": None,
            "classification_confidence": None
        }
        
        # 설정
        config = {"configurable": {"thread_id": session_id}}
        
        try:
            # 그래프 실행
            result = self.graph.invoke(initial_state, config)
            
            # 결과 처리
            sub_result = result.get("sub_agent_result", {})
            
            return {
                "success": not bool(result.get("error")),
                "session_id": session_id,
                "target_agent": result.get("target_agent"),
                "classification_confidence": result.get("classification_confidence"),
                "requires_interrupt": result.get("requires_interrupt", False),
                "result": sub_result,
                "error": result.get("error")
            }
            
        except Exception as e:
            print(f"[ERROR] 라우터 실행 오류: {e}")
            return {
                "success": False,
                "session_id": session_id,
                "error": str(e)
            }
    
    def resume_session(self, session_id: str, user_reply: str, reply_type: str = "user_reply") -> Dict[str, Any]:
        """
        인터럽트된 세션 재개
        
        Args:
            session_id: 세션 ID
            user_reply: 사용자 응답
            reply_type: 응답 타입
            
        Returns:
            Dict: 재개 결과
        """
        # 세션 정보 확인
        session_info = self.sessions.get(session_id)
        if not session_info:
            return {
                "success": False,
                "error": "세션을 찾을 수 없습니다."
            }
        
        try:
            if session_info["agent"] == "docs_agent":
                # docs_agent의 resume 메서드 호출
                thread_id = session_info["thread_id"]
                result = self.docs_agent.resume(thread_id, user_reply, reply_type)
                
                # 완료 확인
                if result.get("success"):
                    self.sessions[session_id]["status"] = "completed"
                elif result.get("interrupted"):
                    # 여전히 인터럽트 상태
                    return {
                        "success": False,
                        "interrupted": True,
                        "thread_id": thread_id,
                        "next_node": result.get("next_node"),
                        "message": "추가 입력이 필요합니다."
                    }
                
                return result
            else:
                return {
                    "success": False,
                    "error": f"{session_info['agent']}는 인터럽트를 지원하지 않습니다."
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"세션 재개 오류: {str(e)}"
            }
    
    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """
        세션 상태 조회
        
        Args:
            session_id: 세션 ID
            
        Returns:
            Dict: 세션 상태 정보
        """
        session_info = self.sessions.get(session_id)
        
        if not session_info:
            return {
                "exists": False,
                "message": "세션을 찾을 수 없습니다."
            }
        
        return {
            "exists": True,
            "session_id": session_id,
            "agent": session_info.get("agent"),
            "status": session_info.get("status"),
            "thread_id": session_info.get("thread_id")
        }