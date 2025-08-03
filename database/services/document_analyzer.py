"""
문서 타입 자동 분석 서비스
문서의 확장자와 내용을 분석하여 자동으로 타입을 분류합니다.
"""

import re
import logging
from typing import Dict, Any, List, Tuple
from enum import Enum

logger = logging.getLogger(__name__)

class DocumentCategory(Enum):
    """문서 카테고리"""
    TABLE = "table"
    TEXT = "text"

class DocumentType(Enum):
    """문서 타입"""
    # 테이블 문서
    PERFORMANCE_DATA = "performance_data"    # 실적 자료
    CUSTOMER_INFO = "customer_info"          # 거래처 정보
    HR_DATA = "hr_data"                      # 인사 자료
    BRANCH_TARGET = "branch_target"          # 지점별 목표
    
    # 텍스트 문서
    REGULATION = "regulation"                # 내부 규정
    REPORT = "report"                        # 보고서

class DocumentAnalyzer:
    """문서 타입 자동 분석기"""
    
    def __init__(self):
        # 지원하는 파일 확장자
        self.supported_extensions = {
            "text": [".txt", ".docx", ".pdf"],
            "table": [".csv", ".xlsx", ".xls"]
        }
        
        # 테이블 문서 패턴
        self.table_patterns = {
            "performance_data": {
                "keywords": [
                    "담당자", "거래처명", "품목", "매출액", "합계", "년월"
                ],
                "column_patterns": [
                    r"담\s*당\s*자", r"ID", r"품\s*목", r"\d{6}", r"합\s*계"
                ]
            },
            "customer_info": {
                "keywords": [
                    "거래처ID", "월", "매출", "월방문횟수", "사용 예산", "총환자수"
                ],
                "column_patterns": [
                    r"거래처\s*ID", r"월", r"매\s*출", r"월\s*방문\s*횟수", r"사용\s*예산", r"총\s*환자\s*수"
                ]
            },
            "hr_data": {
                "keywords": [
                    "사번", "성명", "부서", "직급", "사업부", "지점", "연락처", 
                    "월평균사용예산", "최근 평가", "기본급", "성과급", "책임업무", "ID", "PW"
                ],
                "column_patterns": [
                    r"사\s*번", r"성\s*명", r"부\s*서", r"직\s*급", r"사업\s*부", r"지\s*점", r"연락\s*처",
                    r"월평균사용예산", r"최근\s*평가", r"기본급", r"성과급", r"책임\s*업무", r"ID", r"PW"
                ]
            },
            # "branch_target": {
            #     "keywords": [
            #         "지점", "지사", "영업소", "목표", "계획", "예산", "KPI",
            #         "매출목표", "판매목표", "실적목표", "달성목표", "분기목표",
            #         "branch", "office", "target", "goal", "plan", "budget"
            #     ],
            #     "column_patterns": [
            #         r"지\s*점", r"지\s*사", r"영업\s*소", r"목\s*표",
            #         r"계\s*획", r"예\s*산", r"KPI", r"매출\s*목표",
            #         r"판매\s*목표", r"실적\s*목표", r"달성\s*목표", r"분기\s*목표"
            #     ]
            # }
        }
        
        # 텍스트 문서 패턴
        self.text_patterns = {
            "regulation": {
                "keywords": [
                    "규정", "규칙", "지침", "정책", "가이드라인", "행동강령",
                    "제1장", "제2장", "제1조", "제2조", "목적", "정의", "준수",
                    "금지", "의무", "책임", "처벌", "위반", "조치",
                    "regulation", "policy", "guideline", "code", "rule"
                ],
                "structure_patterns": [
                    r"제\d+장\s*[^\n]+",  # 제1장 총칙
                    r"제\d+조\s*\[[^\]]+\]",  # 제1조[목적]
                    r"①\s*[^\n]+",  # ① 첫 번째 항목
                    r"②\s*[^\n]+",  # ② 두 번째 항목
                    r"본\s*규정", r"본\s*지침", r"본\s*정책"
                ]
            },
            "report": {
                "keywords": [
                    "보고서", "리포트", "분석", "현황", "결과", "통계",
                    "시장", "업계", "성과", "실적", "전망", "계획",
                    "report", "analysis", "status", "result", "statistics"
                ],
                "structure_patterns": [
                    r"\d+\.\s*[^\n]+",  # 1. 제목
                    r"[A-Z]\.\s*[^\n]+",  # A. 제목
                    r"[가-힣]\.\s*[^\n]+",  # 가. 제목
                    r"##\s*[^\n]+",  # ## 제목
                    r"#\s*[^\n]+",  # # 제목
                    r"[^\n]+\n[-=]{3,}",  # 제목\n--- 또는 ===
                    r"결\s*론", r"요\s*약", r"서\s*론", r"본\s*론"
                ]
            }
        }
    
    def analyze_document(self, text: str, filename: str) -> str:
        """
        문서를 분석하여 타입을 자동으로 분류합니다.
        
        Args:
            text: 문서 내용
            filename: 파일명
            
        Returns:
            문서 타입 문자열 (doc_type에 저장될 값)
        """
        try:
            logger.info(f"문서 분석 시작: {filename}")
            
            # 1. 파일 확장자 확인
            file_extension = self._get_file_extension(filename)
            
            if not file_extension:
                logger.warning(f"지원하지 않는 파일 형식: {filename}")
                return DocumentType.REPORT.value  # 기본값
            
            # 2. 확장자 기반 카테고리 분류
            if file_extension in self.supported_extensions["table"]:
                # 테이블 문서 분석
                return self._analyze_table_document(text)
            else:
                # 텍스트 문서 분석
                return self._analyze_text_document(text)
            
        except Exception as e:
            logger.error(f"문서 분석 중 오류 발생: {e}")
            return DocumentType.REPORT.value  # 기본값
    
    def _get_file_extension(self, filename: str) -> str:
        """파일 확장자를 추출합니다."""
        if not filename:
            return ""
        
        # 파일명에서 확장자 추출
        if '.' in filename:
            return '.' + filename.split('.')[-1].lower()
        return ""
    
    def _analyze_table_document(self, text: str) -> str:
        """테이블 문서 분석"""
        logger.info("테이블 문서 분석 시작")
        
        # 구체적인 타입 분류
        performance_data_score = self._calculate_table_score(text, "performance_data")
        customer_info_score = self._calculate_table_score(text, "customer_info")
        hr_data_score = self._calculate_table_score(text, "hr_data")
        # branch_target_score = self._calculate_table_score(text, "branch_target")
        
        # 각 분류별 점수 로깅
        logger.info(f"실적 자료 점수: {performance_data_score:.2f}")
        logger.info(f"거래처 정보 점수: {customer_info_score:.2f}")
        logger.info(f"인사 자료 점수: {hr_data_score:.2f}")
        # logger.info(f"지점별 목표 점수: {branch_target_score:.2f}")
        
        # 가장 높은 점수를 가진 타입 반환
        scores = {
            DocumentType.PERFORMANCE_DATA.value: performance_data_score,
            DocumentType.CUSTOMER_INFO.value: customer_info_score,
            DocumentType.HR_DATA.value: hr_data_score,
            # DocumentType.BRANCH_TARGET.value: branch_target_score
        }
        max_score_type = max(scores, key=scores.get)
        logger.info(f"최종 분류: {max_score_type} (점수: {scores[max_score_type]:.2f})")
        return max_score_type
    
    def _analyze_text_document(self, text: str) -> str:
        """텍스트 문서 분석"""
        logger.info("텍스트 문서 분석 시작")
        
        # 규정 문서 점수 계산
        regulation_score = self._calculate_text_score(text, "regulation")
        report_score = self._calculate_text_score(text, "report")
        
        if regulation_score > report_score:
            logger.info(f"내부 규정으로 분류 (점수: {regulation_score:.2f})")
            return DocumentType.REGULATION.value
        else:
            logger.info(f"보고서로 분류 (점수: {report_score:.2f})")
            return DocumentType.REPORT.value
    
    def _calculate_score(self, text: str, patterns: dict, weights: dict) -> float:
        """공통 점수 계산 메서드"""
        score = 0.0
        
        for pattern_type, weight in weights.items():
            if pattern_type in patterns:
                matches = 0
                for pattern in patterns[pattern_type]:
                    if isinstance(pattern, str):  # 키워드
                        if pattern.lower() in text.lower():
                            matches += 1
                    else:  # 정규식 패턴
                        if re.search(pattern, text, re.IGNORECASE):
                            matches += 1
                
                pattern_score = matches / len(patterns[pattern_type])
                score += pattern_score * weight
        
        return score
    
    def _calculate_table_score(self, text: str, table_type: str) -> float:
        """테이블 문서 타입별 점수 계산"""
        patterns = self.table_patterns[table_type]
        weights = {"keywords": 0.6, "column_patterns": 0.4}
        return self._calculate_score(text, patterns, weights)
    
    def _calculate_text_score(self, text: str, text_type: str) -> float:
        """텍스트 문서 타입별 점수 계산"""
        patterns = self.text_patterns[text_type]
        weights = {"keywords": 0.5, "structure_patterns": 0.5}
        return self._calculate_score(text, patterns, weights)
    
    def get_chunking_type(self, document_type: str) -> str:
        """
        문서 타입에 따른 청킹 타입을 반환합니다.
        
        Args:
            document_type: 문서 타입
            
        Returns:
            청킹 타입 ("regulation" 또는 "report")
        """
        if document_type in [DocumentType.REGULATION.value]:
            return "regulation"
        else:
            return "report"
    
    def is_supported_file(self, filename: str) -> bool:
        """
        파일이 지원되는 형식인지 확인합니다.
        
        Args:
            filename: 파일명
            
        Returns:
            지원 여부
        """
        extension = self._get_file_extension(filename)
        supported_extensions = (
            self.supported_extensions["text"] + 
            self.supported_extensions["table"]
        )
        return extension in supported_extensions

# 싱글턴 인스턴스
document_analyzer = DocumentAnalyzer() 