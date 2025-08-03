"""
통합 State 정의 모듈
모든 에이전트가 사용하는 State 타입들을 정의합니다.
"""
from typing import TypedDict, List, Optional, Dict, Any
from langchain_core.messages import HumanMessage


class BaseState(TypedDict):
    """
    모든 에이전트가 공유하는 기본 상태
    """
    messages: List[HumanMessage]
    session_id: str
    agent_type: Optional[str]
    error: Optional[str]


class InterruptableState(BaseState):
    """
    Human-in-the-loop를 지원하는 에이전트용 상태
    인터럽트와 사용자 입력을 처리할 수 있습니다.
    """
    user_reply: Optional[str]  # 사용자 응답
    interrupt_type: Optional[str]  # 인터럽트 타입 (verification, manual_selection, user_input 등)


class DocsState(InterruptableState):
    """
    문서 작성 에이전트(docs_agent)용 상태
    기존 docs_agent의 State를 그대로 유지합니다.
    """
    doc_type: Optional[str]
    template_content: Optional[str]
    filled_data: Optional[dict]
    violation: Optional[str]
    final_doc: Optional[str]
    retry_count: int
    restart_classification: Optional[bool]
    classification_retry_count: Optional[int]
    classification_failed: Optional[bool]
    skip_verification: Optional[bool]
    end_process: Optional[bool]
    parse_retry_count: Optional[int]
    parse_failed: Optional[bool]
    verification_reply: Optional[str]  # 분류 검증용 사용자 입력
    verification_result: Optional[str]  # 긍정/부정 분류 결과
    user_content: Optional[str]  # 문서 내용 (separate_document_type_and_content에서 추출)
    skip_ask_fields: Optional[bool]  # ask_required_fields 스킵 플래그


class EmployeeState(BaseState):
    """
    직원 실적 분석 에이전트(employee_agent)용 상태
    단방향 플로우를 가진 분석형 에이전트입니다.
    """
    query: str
    query_analysis: Optional[Dict[str, Any]]
    employee_name: Optional[str]
    start_period: Optional[str]
    end_period: Optional[str]
    analysis_type: Optional[str]
    performance_data: Optional[Dict[str, Any]]
    target_data: Optional[Dict[str, Any]]
    analysis_results: Optional[Dict[str, Any]]
    report: Optional[str]


class RouterState(BaseState):
    """
    라우터 에이전트(router_agent)용 상태
    질문을 분류하고 적절한 에이전트로 라우팅합니다.
    """
    target_agent: Optional[str]  # 분류된 대상 에이전트 (docs_agent, employee_agent 등)
    sub_agent_state: Optional[Dict[str, Any]]  # 하위 에이전트로 전달할 상태
    sub_agent_result: Optional[Dict[str, Any]]  # 하위 에이전트의 실행 결과
    requires_interrupt: Optional[bool]  # 인터럽트가 필요한지 여부
    classification_confidence: Optional[float]  # 분류 신뢰도


class SessionInfo(TypedDict):
    """
    세션 관리를 위한 정보
    """
    session_id: str
    thread_id: str
    agent_type: str
    created_at: str
    last_updated: str
    status: str  # active, interrupted, completed, error
    interrupt_info: Optional[Dict[str, Any]]  # 인터럽트 상태 정보