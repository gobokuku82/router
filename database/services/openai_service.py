"""
OpenAI 공통 서비스
모든 서비스에서 공통으로 사용할 OpenAI 클라이언트를 제공합니다.
"""

import logging
import openai
from typing import Optional, List, Dict, Any
import json
from config import settings

logger = logging.getLogger(__name__)

class OpenAIService:
    """OpenAI 공통 서비스 클래스"""
    
    _instance = None
    _client = None
    
    def __new__(cls):
        """싱글턴 패턴으로 인스턴스 생성"""
        if cls._instance is None:
            cls._instance = super(OpenAIService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """초기화 (싱글턴이므로 한 번만 실행됨)"""
        if self._client is None:
            self._initialize_client()
    
    def _initialize_client(self):
        """OpenAI 클라이언트 초기화"""
        try:
            openai_config = settings.get_openai_config()
            api_key = openai_config.get("api_key")
            
            if not api_key:
                logger.warning("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
                self._client = None
                return
            
            self._client = openai.OpenAI(api_key=api_key)
            logger.info("OpenAI 클라이언트 초기화 성공")
            
        except Exception as e:
            logger.error(f"OpenAI 클라이언트 초기화 실패: {e}")
            self._client = None
    
    @property
    def client(self):
        """OpenAI 클라이언트 반환"""
        return self._client
    
    def is_available(self) -> bool:
        """OpenAI 클라이언트 사용 가능 여부"""
        return self._client is not None
    
    def create_embedding(self, text: str, model: str = "text-embedding-3-small") -> Optional[List[float]]:
        """
        텍스트 임베딩 생성
        
        Args:
            text: 임베딩할 텍스트
            model: 사용할 모델명
            
        Returns:
            Optional[List[float]]: 임베딩 벡터
        """
        if not self.is_available():
            logger.warning("OpenAI 클라이언트가 사용 불가능합니다.")
            return None
        
        try:
            response = self._client.embeddings.create(
                model=model,
                input=text
            )
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"임베딩 생성 실패: {e}")
            return None
    
    def create_chat_completion(self, messages: List[Dict[str, str]], 
                              model: str = "gpt-3.5-turbo", 
                              max_tokens: int = 1000, 
                              temperature: float = 0.1) -> Optional[str]:
        """
        채팅 완성 생성
        
        Args:
            messages: 메시지 리스트
            model: 사용할 모델명
            max_tokens: 최대 토큰 수
            temperature: 온도 설정
            
        Returns:
            Optional[str]: 응답 텍스트
        """
        if not self.is_available():
            logger.warning("OpenAI 클라이언트가 사용 불가능합니다.")
            return None
        
        try:
            response = self._client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"채팅 완성 생성 실패: {e}")
            return None
    
    def create_json_completion(self, messages: List[Dict[str, str]], 
                             model: str = "gpt-3.5-turbo", 
                             max_tokens: int = 1000, 
                             temperature: float = 0.1) -> Optional[Dict[str, Any]]:
        """
        JSON 응답 채팅 완성 생성
        
        Args:
            messages: 메시지 리스트
            model: 사용할 모델명
            max_tokens: 최대 토큰 수
            temperature: 온도 설정
            
        Returns:
            Optional[Dict[str, Any]]: 파싱된 JSON 응답
        """
        response_text = self.create_chat_completion(messages, model, max_tokens, temperature)
        
        if not response_text:
            return None
        
        try:
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error(f"JSON 파싱 실패: {e}")
            return None

# 전역 인스턴스
openai_service = OpenAIService() 