"""
세션 및 메모리 관리 모듈
에이전트 간 세션 상태를 관리하고 저장합니다.
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import os
from pathlib import Path
import pickle
import uuid
from .state import SessionInfo


class SessionManager:
    """
    세션 관리자
    에이전트 실행 상태와 히스토리를 관리합니다.
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        세션 관리자 초기화
        
        Args:
            storage_path: 세션 저장 경로 (None이면 메모리만 사용)
        """
        self.sessions: Dict[str, SessionInfo] = {}
        self.storage_path = storage_path
        
        if storage_path:
            self.storage_dir = Path(storage_path)
            self.storage_dir.mkdir(parents=True, exist_ok=True)
            self._load_sessions()
    
    def create_session(
        self, 
        agent_type: str, 
        session_id: Optional[str] = None,
        thread_id: Optional[str] = None
    ) -> str:
        """
        새 세션 생성
        
        Args:
            agent_type: 에이전트 타입
            session_id: 세션 ID (None이면 자동 생성)
            thread_id: 스레드 ID (None이면 자동 생성)
            
        Returns:
            str: 생성된 세션 ID
        """
        if not session_id:
            session_id = str(uuid.uuid4())
        
        if not thread_id:
            thread_id = str(uuid.uuid4())
        
        session_info: SessionInfo = {
            "session_id": session_id,
            "thread_id": thread_id,
            "agent_type": agent_type,
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "status": "active",
            "interrupt_info": None
        }
        
        self.sessions[session_id] = session_info
        self._save_session(session_id)
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[SessionInfo]:
        """
        세션 정보 조회
        
        Args:
            session_id: 세션 ID
            
        Returns:
            Optional[SessionInfo]: 세션 정보 (없으면 None)
        """
        return self.sessions.get(session_id)
    
    def update_session(
        self, 
        session_id: str, 
        status: Optional[str] = None,
        interrupt_info: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> bool:
        """
        세션 정보 업데이트
        
        Args:
            session_id: 세션 ID
            status: 새 상태
            interrupt_info: 인터럽트 정보
            **kwargs: 추가 필드
            
        Returns:
            bool: 성공 여부
        """
        session = self.sessions.get(session_id)
        if not session:
            return False
        
        if status:
            session["status"] = status
        
        if interrupt_info is not None:
            session["interrupt_info"] = interrupt_info
        
        session["last_updated"] = datetime.now().isoformat()
        
        # 추가 필드 업데이트
        for key, value in kwargs.items():
            if key in session:
                session[key] = value
        
        self._save_session(session_id)
        return True
    
    def delete_session(self, session_id: str) -> bool:
        """
        세션 삭제
        
        Args:
            session_id: 세션 ID
            
        Returns:
            bool: 성공 여부
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            self._delete_session_file(session_id)
            return True
        return False
    
    def list_sessions(
        self, 
        agent_type: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[SessionInfo]:
        """
        세션 목록 조회
        
        Args:
            agent_type: 필터할 에이전트 타입
            status: 필터할 상태
            
        Returns:
            List[SessionInfo]: 세션 목록
        """
        sessions = list(self.sessions.values())
        
        if agent_type:
            sessions = [s for s in sessions if s["agent_type"] == agent_type]
        
        if status:
            sessions = [s for s in sessions if s["status"] == status]
        
        # 최신순 정렬
        sessions.sort(key=lambda x: x["last_updated"], reverse=True)
        
        return sessions
    
    def cleanup_old_sessions(self, days: int = 7) -> int:
        """
        오래된 세션 정리
        
        Args:
            days: 보관 기간 (일)
            
        Returns:
            int: 삭제된 세션 수
        """
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days)
        deleted_count = 0
        
        for session_id, session in list(self.sessions.items()):
            try:
                last_updated = datetime.fromisoformat(session["last_updated"])
                if last_updated < cutoff_date:
                    self.delete_session(session_id)
                    deleted_count += 1
            except:
                pass
        
        return deleted_count
    
    def _save_session(self, session_id: str):
        """세션을 파일로 저장"""
        if not self.storage_path:
            return
        
        session = self.sessions.get(session_id)
        if not session:
            return
        
        file_path = self.storage_dir / f"{session_id}.json"
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(session, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[WARNING] 세션 저장 실패: {e}")
    
    def _delete_session_file(self, session_id: str):
        """세션 파일 삭제"""
        if not self.storage_path:
            return
        
        file_path = self.storage_dir / f"{session_id}.json"
        if file_path.exists():
            try:
                file_path.unlink()
            except Exception as e:
                print(f"[WARNING] 세션 파일 삭제 실패: {e}")
    
    def _load_sessions(self):
        """저장된 세션들을 로드"""
        if not self.storage_path:
            return
        
        for file_path in self.storage_dir.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    session = json.load(f)
                    self.sessions[session["session_id"]] = session
            except Exception as e:
                print(f"[WARNING] 세션 로드 실패 {file_path}: {e}")


class ConversationMemory:
    """
    대화 메모리 관리
    에이전트 대화 히스토리를 관리합니다.
    """
    
    def __init__(self, max_history: int = 100):
        """
        대화 메모리 초기화
        
        Args:
            max_history: 최대 히스토리 길이
        """
        self.conversations: Dict[str, List[Dict[str, Any]]] = {}
        self.max_history = max_history
    
    def add_message(
        self, 
        session_id: str, 
        role: str, 
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        메시지 추가
        
        Args:
            session_id: 세션 ID
            role: 역할 (user, assistant, system)
            content: 메시지 내용
            metadata: 추가 메타데이터
        """
        if session_id not in self.conversations:
            self.conversations[session_id] = []
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        self.conversations[session_id].append(message)
        
        # 최대 길이 제한
        if len(self.conversations[session_id]) > self.max_history:
            self.conversations[session_id] = self.conversations[session_id][-self.max_history:]
    
    def get_conversation(
        self, 
        session_id: str, 
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        대화 히스토리 조회
        
        Args:
            session_id: 세션 ID
            limit: 조회할 메시지 수 제한
            
        Returns:
            List[Dict]: 대화 히스토리
        """
        messages = self.conversations.get(session_id, [])
        
        if limit:
            return messages[-limit:]
        
        return messages
    
    def clear_conversation(self, session_id: str):
        """
        대화 히스토리 삭제
        
        Args:
            session_id: 세션 ID
        """
        if session_id in self.conversations:
            del self.conversations[session_id]
    
    def get_summary(self, session_id: str) -> Dict[str, Any]:
        """
        대화 요약 정보 반환
        
        Args:
            session_id: 세션 ID
            
        Returns:
            Dict: 요약 정보
        """
        messages = self.conversations.get(session_id, [])
        
        if not messages:
            return {
                "message_count": 0,
                "first_message": None,
                "last_message": None
            }
        
        return {
            "message_count": len(messages),
            "first_message": messages[0]["timestamp"],
            "last_message": messages[-1]["timestamp"],
            "user_messages": len([m for m in messages if m["role"] == "user"]),
            "assistant_messages": len([m for m in messages if m["role"] == "assistant"])
        }


# 전역 인스턴스 (선택적 사용)
default_session_manager = SessionManager()
default_conversation_memory = ConversationMemory()