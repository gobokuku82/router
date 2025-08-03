# Employee Agent Module
"""
Employee Agent Module
직원 실적 분석 에이전트 모듈
"""
from typing import Dict, Any
from .employee_agent import run

# 하위 호환성을 위한 별칭
process_query = run

__all__ = ['run', 'process_query']