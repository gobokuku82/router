from services.opensearch_client import opensearch_client
import re
import logging
from typing import List, Dict, Any, Optional

DOCUMENT_INDEX_NAME = "document_chunks"
SEARCH_PIPELINE_ID = "hybrid-minmax-pipeline"

# 로깅 설정
logger = logging.getLogger(__name__)

# 고급 키워드 추출 서비스 import
from services.keyword_extractor import keyword_extractor

# Search Pipeline 초기화 함수
def initialize_search_pipeline():
    """Search Pipeline을 초기화합니다."""
    try:
        # Search Pipeline 생성
        pipeline_created = opensearch_client.create_search_pipeline(SEARCH_PIPELINE_ID)
        if pipeline_created:
            logger.info(f"✅ Search Pipeline '{SEARCH_PIPELINE_ID}' 초기화 완료")
        else:
            logger.warning(f"⚠️ Search Pipeline '{SEARCH_PIPELINE_ID}' 초기화 실패")
        return pipeline_created
    except Exception as e:
        logger.error(f"❌ Search Pipeline 초기화 중 오류: {e}")
        return False

# 자연어 질문에서 키워드 추출 함수 (OpenAI 기반)
def extract_keywords_from_question(question: str, top_k: int = 10) -> List[str]:
    """
    자연어 질문에서 검색 키워드를 추출합니다.
    
    Args:
        question: 질문 텍스트
        top_k: 추출할 키워드 수
    
    Returns:
        키워드 리스트
    """
    try:
        # OpenAI를 사용한 키워드 추출
        keywords = keyword_extractor.extract_keywords(question, top_k)
        
        # 키워드만 추출 (점수 제외)
        return [kw for kw, score in keywords]
        
    except Exception as e:
        logger.error(f"키워드 추출 실패: {e}")
        # 실패 시 기본 방법 사용
        return extract_keywords_fallback(question, top_k)

def extract_keywords_fallback(question: str, top_k: int = 10) -> List[str]:
    """기본 키워드 추출 방법 (fallback)"""
    # 한국어 조사, 어미, 불용어 제거
    stop_words = {
        '이', '가', '을', '를', '의', '에', '에서', '로', '으로', '와', '과', '도', '는', '은', '이', '가',
        '어떻게', '무엇', '언제', '어디', '왜', '어떤', '몇', '얼마', '어떠한', '무슨', '어느', '어떤',
        '있나요', '있습니까', '입니까', '인가요', '인지', '인지요', '인가', '인지', '인지요',
        '알려주세요', '알려주시기', '알려주시면', '알려주시겠습니까', '알려주시겠어요',
        '해주세요', '해주시기', '해주시면', '해주시겠습니까', '해주시겠어요',
        '좋겠습니까', '좋겠어요', '좋을까요', '좋을지', '좋을지요',
        '있을까요', '있을지', '있을지요', '될까요', '될지', '될지요'
    }
    
    # 특수문자 제거 및 소문자 변환
    cleaned_question = re.sub(r'[^\w\s가-힣]', ' ', question.lower())
    
    # 단어 분리
    words = cleaned_question.split()
    
    # 불용어 제거 및 2글자 이상 단어만 유지
    keywords = [word for word in words if word not in stop_words and len(word) >= 2]
    
    # 중복 제거
    keywords = list(set(keywords))
    
    # 최대 top_k개 키워드로 제한
    return keywords[:top_k]

# 문서 내용 요약 함수
def summarize_documents(documents: List[Dict[str, Any]], question: str) -> str:
    """검색된 문서들을 요약하여 답변을 생성합니다."""
    if not documents:
        return "죄송합니다. 질문과 관련된 문서를 찾을 수 없습니다."
    
    # 문서 내용들을 결합
    combined_content = ""
    for i, doc in enumerate(documents[:3], 1):  # 상위 3개 문서만 사용
        # 수정: source 안의 content에 접근
        source = doc.get("source", {})
        content = source.get("content", "")
        if content:
            combined_content += f"문서 {i}: {content}\n\n"
    
    if not combined_content.strip():
        return "죄송합니다. 문서 내용을 추출할 수 없습니다."
    
    # 간단한 요약 로직 (실제로는 더 정교한 요약 모델 사용 권장)
    sentences = re.split(r'[.!?]', combined_content)
    relevant_sentences = []
    
    # 질문 키워드가 포함된 문장들을 우선 선택
    question_keywords = extract_keywords_from_question(question)
    
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) > 10:  # 너무 짧은 문장 제외
            # 키워드가 포함된 문장 우선 선택
            if any(keyword in sentence for keyword in question_keywords):
                relevant_sentences.append(sentence)
    
    # 키워드가 포함된 문장이 부족하면 전체에서 선택
    if len(relevant_sentences) < 2:
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20 and sentence not in relevant_sentences:
                relevant_sentences.append(sentence)
                if len(relevant_sentences) >= 5:  # 최대 5개 문장
                    break
    
    # 요약 생성
    if relevant_sentences:
        summary = " ".join(relevant_sentences[:3])  # 상위 3개 문장만 사용
        if len(summary) > 500:  # 너무 길면 자르기
            summary = summary[:500] + "..."
        return summary
    else:
        return "관련 문서를 찾았지만, 질문에 대한 구체적인 답변을 추출하기 어렵습니다."

# 신뢰도 점수 계산 함수
def calculate_confidence_score(search_results: List[Dict[str, Any]]) -> float:
    """검색 결과의 신뢰도 점수를 계산합니다."""
    if not search_results:
        return 0.0
    
    # 검색 점수의 평균을 신뢰도로 사용
    scores = [result.get("score", 0.0) for result in search_results]
    avg_score = sum(scores) / len(scores)
    
    # 점수를 0-1 범위로 정규화 (일반적으로 검색 점수는 0-10 범위)
    normalized_score = min(avg_score / 10.0, 1.0)
    
    return round(normalized_score, 2)

# 자연어 질문-답변 함수
def question_answering(question: str, top_k: int = 5, include_sources: bool = True) -> Dict[str, Any]:
    """
    질문에 대한 답변을 생성합니다.
    
    Args:
        question: 사용자 질문
        top_k: 검색할 문서 수
        include_sources: 소스 정보 포함 여부
        
    Returns:
        답변 결과 딕셔너리
    """
    try:
        # 1. 키워드 추출
        keywords = extract_keywords_from_question(question, top_k=5)
        logger.info(f"추출된 키워드: {keywords}")
        
        # 2. Search Pipeline 기반 하이브리드 검색 수행
        search_results = []
        try:
            # Search Pipeline 기반 하이브리드 검색 수행 (재순위 무조건 적용)
            search_results = opensearch_client.search_with_pipeline(
                query_text=question,
                keywords=keywords,
                pipeline_id=SEARCH_PIPELINE_ID,
                index_name=DOCUMENT_INDEX_NAME,
                top_k=top_k,
                use_rerank=True,  # 무조건 재순위 적용
                rerank_top_k=3
            )
            
            if not search_results:
                logger.warning("OpenSearch 검색 결과가 없습니다.")
                # 폴백 검색 결과
                search_results = [{
                    "content": f"'{question}'와 관련된 기본 문서입니다.",
                    "metadata": {"type": "fallback", "query": question},
                    "score": 0.5,
                    "rank": 1,
                    "source": "fallback_search"
                }]
                
        except Exception as e:
            logger.warning(f"OpenSearch 검색 실패: {e}")
            # 폴백 검색 결과
            search_results = [{
                "content": f"'{question}'와 관련된 기본 문서입니다.",
                "metadata": {"type": "fallback", "query": question},
                "score": 0.5,
                "rank": 1,
                "source": "fallback_search"
            }]
        
        if not search_results:
            return {
                "success": True,
                "question": question,
                "answer": "죄송합니다. 질문과 관련된 문서를 찾을 수 없습니다.",
                "summary": None,
                "sources": [],
                "search_results": [],
                "total_sources": 0,
                "confidence_score": 0.0
            }
        
        # 3. 문서 요약 생성
        answer = summarize_documents(search_results, question)
        
        # 4. 원본 문서 정보 추출
        sources = []
        if include_sources:
            for i, result in enumerate(search_results, 1):
                source = result.get("source", {})
                source_info = {
                    "rank": i,
                    "document_name": source.get("title", "N/A"),
                    "chapter": source.get("chapter_title", "N/A"),
                    "section": source.get("article_title", "N/A"),
                    "file_name": source.get("file_name", "N/A"),
                    "score": result.get("score", 0.0),
                    "content_preview": source.get("content", "")[:200] + "..." if len(source.get("content", "")) > 200 else source.get("content", "")
                }
                sources.append(source_info)
        
        # 5. 신뢰도 점수 계산
        confidence_score = calculate_confidence_score(search_results)
        
        # 6. 요약 생성 (선택적)
        summary = None
        if len(search_results) > 1:
            summary = f"총 {len(search_results)}개의 관련 문서를 찾았습니다. 주요 내용은 다음과 같습니다: {answer[:300]}..."
        
        logger.info(f"QA 처리 완료: {len(search_results)}개 문서에서 정보를 찾았습니다.")
        
        return {
            "success": True,
            "question": question,
            "answer": answer,
            "summary": summary,
            "sources": sources,
            "search_results": search_results,
            "total_sources": len(search_results),
            "confidence_score": confidence_score
        }
        
    except Exception as e:
        logger.error(f"QA 처리 오류: {e}")
        return {
            "success": False,
            "question": question,
            "answer": f"질문 처리 중 오류가 발생했습니다: {str(e)}",
            "summary": None,
            "sources": [],
            "search_results": [],
            "total_sources": 0,
            "confidence_score": 0.0
        }

# 필요한 경우, 아래와 같이 헬퍼 함수로 래핑해서 사용 가능

def create_index_with_mapping(index_name, mapping):
    return opensearch_client.create_index_with_mapping(index_name, mapping)

def index_document(index_name, document, refresh=False):
    return opensearch_client.index_document(index_name, document, refresh)

def bulk_index_documents(index_name, documents, refresh=False):
    return opensearch_client.bulk_index_documents(index_name, documents, refresh)

def search_document(index_name, query):
    return opensearch_client.search_document(index_name, query)

def get_embedding_model():
    return opensearch_client.model

def create_index_if_not_exists(index_name):
    return opensearch_client.create_index_if_not_exists(index_name)

def index_document_chunks(doc_id, doc_title, file_name, text, document_type="report"):
    """문서 청킹을 OpenSearch에 인덱싱합니다."""
    try:
        # OpenSearch에 문서 청킹 저장
        success = opensearch_client.index_document_chunks(
            index_name=DOCUMENT_INDEX_NAME,
            doc_id=doc_id,
            doc_title=doc_title,
            file_name=file_name,
            text=text,
            document_type=document_type
        )
        
        if success:
            logger.info(f"문서 {doc_id}의 청킹을 OpenSearch에 저장했습니다. (문서 타입: {document_type})")
        else:
            logger.error(f"문서 {doc_id}의 청킹 인덱싱에 실패했습니다.")
        
        return success
        
    except Exception as e:
        logger.error(f"문서 청킹 인덱싱 실패: {e}")
        return False

def delete_document_chunks_from_opensearch(index_name, document_id):
    """OpenSearch에서 특정 문서의 청킹을 삭제합니다."""
    try:
        # OpenSearch에서 문서 청킹 삭제
        success = opensearch_client.delete_document_chunks(
            index_name=index_name,
            document_id=document_id
        )
        
        if success:
            logger.info(f"문서 {document_id}의 청킹을 OpenSearch에서 삭제했습니다.")
        else:
            logger.error(f"문서 {document_id}의 청킹 삭제에 실패했습니다.")
        
        return success
        
    except Exception as e:
        logger.error(f"문서 청킹 삭제 실패: {e}")
        return False 