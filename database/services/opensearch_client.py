# OpenSearchClient: 실전 서비스용 OpenSearch 연동 클래스
from opensearchpy import OpenSearch, exceptions, helpers, ConnectionTimeout
from sentence_transformers import SentenceTransformer
from FlagEmbedding import FlagReranker
import logging
import re
import json
import time
from typing import List, Dict, Any, Optional, Union
from config import settings

# 로거 설정
logger = logging.getLogger(__name__)

class OpenSearchClient:
    def __init__(self, max_retries: int = 3, timeout: int = 10):
        """OpenSearch 클라이언트 초기화"""
        self.client = None
        self._model = None
        self._reranker = None
        self._embedding_dim = None
        self._default_embedding_dim = 1024
        
        # 클라이언트 생성
        self.client = self._create_client_with_retry(max_retries, timeout)
        
        # 모델 미리 로드 (백그라운드에서)
        if self.client:
            self._preload_models()

    def _preload_models(self):
        """모델들을 미리 로드합니다 (백그라운드에서)"""
        try:
            logger.info("🚀 모델 사전 로딩 시작...")
            
            # 임베딩 모델 미리 로드
            if not self._model:
                logger.info("🤖 임베딩 모델 사전 로딩 중...")
                self._model = self._embeddings_model()
                if self._model:
                    self._embedding_dim = len(self._model.encode("dummy_text"))
                    logger.info(f"✅ 임베딩 모델 사전 로딩 완료 (차원: {self._embedding_dim})")
                else:
                    logger.error("❌ 임베딩 모델 사전 로딩 실패")
            
            # 재순위 모델 미리 로드
            if not self._reranker:
                logger.info("🔄 재순위 모델 사전 로딩 중...")
                self._reranker = self._rerank_model()
                if self._reranker:
                    logger.info("✅ 재순위 모델 사전 로딩 완료")
                else:
                    logger.error("❌ 재순위 모델 사전 로딩 실패")
                    
            logger.info("🎉 모든 모델 사전 로딩 완료")
            
        except Exception as e:
            logger.error(f"❌ 모델 사전 로딩 중 오류: {e}")

    def _create_client_with_retry(self, max_retries: int, timeout: int):
        """
        재시도 로직을 포함한 OpenSearch 클라이언트 생성
        
        Args:
            max_retries: 최대 재시도 횟수
            timeout: 연결 타임아웃 (초)
            
        Returns:
            OpenSearch 클라이언트 또는 None
        """
        try:
            # 중앙화된 설정에서 OpenSearch 설정 가져오기
            opensearch_config = settings.get_opensearch_config()
            host = opensearch_config["host"]
            port = opensearch_config["port"]
            username = opensearch_config.get("username", "admin")
            password = opensearch_config["password"]
            
            logger.info(f"🔗 OpenSearch 연결 시도: {host}:{port}, 사용자: {username}")
            
            for attempt in range(max_retries):
                try:
                    logger.info(f"📡 연결 시도 {attempt + 1}/{max_retries} (타임아웃: {timeout}초)")
                    
                    # OpenSearch 클라이언트 초기화
                    client = OpenSearch(
                        hosts=[{"host": host, "port": port}],
                        timeout=timeout,
                        verify_certs=False,  # 개발 환경에서는 SSL 검증 비활성화
                        ssl_show_warn=False
                    )
                    
                    # ping 테스트로 연결 확인
                    if client.ping():
                        logger.info(f"✅ OpenSearch 연결 성공 (시도 {attempt + 1}/{max_retries})")
                        return client
                    else:
                        logger.warning(f"⚠️ OpenSearch ping 실패 (시도 {attempt + 1}/{max_retries})")
                        
                except ConnectionTimeout as e:
                    logger.warning(f"⏰ 연결 타임아웃 (시도 {attempt + 1}/{max_retries}): {e}")
                except Exception as e:
                    logger.warning(f"❌ OpenSearch 연결 실패 (시도 {attempt + 1}/{max_retries}): {e}")
                    logger.warning(f"오류 타입: {type(e).__name__}")
                
                # 마지막 시도가 아니면 잠시 대기 후 재시도
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2  # 2초, 4초, 6초...
                    logger.info(f"⏳ {wait_time}초 후 재시도...")
                    time.sleep(wait_time)
            
            logger.error(f"❌ OpenSearch 연결 최종 실패 ({max_retries}회 시도)")
            return None
            
        except Exception as e:
            logger.error(f"❌ OpenSearch 설정 로드 실패: {e}")
            return None

    @property
    def model(self):
        """임베딩 모델 지연 로딩"""
        if self._model is None:
            logger.info("🤖 임베딩 모델 로딩 시작...")
            self._model = self._embeddings_model()
            if self._model:
                self._embedding_dim = len(self._model.encode("dummy_text"))
                logger.info(f"✅ 임베딩 모델 로딩 완료 (차원: {self._embedding_dim})")
            else:
                logger.error("❌ 임베딩 모델 로딩 실패")
        return self._model

    @property
    def reranker(self):
        """재순위 모델 지연 로딩"""
        if self._reranker is None:
            logger.info("🔄 재순위 모델 로딩 시작...")
            self._reranker = self._rerank_model()
            if self._reranker:
                logger.info("✅ 재순위 모델 로딩 완료")
            else:
                logger.error("❌ 재순위 모델 로딩 실패")
        return self._reranker

    @property
    def embedding_dim(self):
        """임베딩 차원 반환"""
        if self._embedding_dim is None:
            # KURE-v1 모델은 1024차원 벡터를 생성
            return 1024
        return self._embedding_dim

    def _check_client(self) -> bool:
        """클라이언트 초기화 상태를 확인합니다."""
        if not self.client:
            logger.error("OpenSearch 클라이언트가 초기화되지 않았습니다.")
            return False
        return True

    def _format_search_results(self, hits: List[Dict], source_type: str) -> List[Dict[str, Any]]:
        """
        검색 결과를 표준 형식으로 포맷팅합니다.
        
        Args:
            hits: OpenSearch 검색 결과 hits
            source_type: 검색 소스 타입 (예: "opensearch_vector_search")
            
        Returns:
            포맷팅된 검색 결과 리스트
        """
        results = []
        for hit in hits:
            source = hit["_source"]
            results.append({
                "content": source.get("content", ""),
                "metadata": {
                    "document_id": source.get("document_id"),
                    "chunk_index": source.get("chunk_index"),
                    "file_name": source.get("file_name"),
                    "title": source.get("title")
                },
                "score": hit["_score"],
                "rank": len(results) + 1,
                "source": source_type
            })
        return results

    def chunk_text_to_sentences(self, text: str, document_type: str = "report") -> List[Dict[str, Any]]:
        """
        문서 종류에 따라 텍스트를 지능적으로 분할합니다.
        
        Args:
            text: 분할할 텍스트
            document_type: 문서 종류 ("regulation" 또는 "report")
            
        Returns:
            청킹된 문서 리스트 (각 청크는 metadata 포함)
        """
        if document_type == "regulation":
            return self._chunk_regulation_document(text)
        else:
            return self._chunk_report_document(text)

    def _chunk_regulation_document(self, text: str) -> List[Dict[str, Any]]:
        """
        내부 규정 문서를 장/조 기준으로 분할합니다.
        
        Args:
            text: 내부 규정 문서 텍스트
            
        Returns:
            청킹된 규정 문서 리스트
        """
        chunks = []
        
        # 장(Chapter) 패턴 매칭
        chapter_pattern = r'제(\d+)장\s*([^\n]+)'
        article_pattern = r'제(\d+)조\s*\[([^\]]+)\]\s*([^\n]+)'
        
        lines = text.split('\n')
        current_chapter = None
        current_article = None
        current_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 장(Chapter) 매칭
            chapter_match = re.match(chapter_pattern, line)
            if chapter_match:
                # 이전 청크 저장
                if current_content and current_chapter:
                    chunks.append({
                        "content": '\n'.join(current_content),
                        "chapter": current_chapter,
                        "article": current_article,
                        "metadata": {
                            "type": "regulation",
                            "chapter_num": current_chapter.get("number"),
                            "chapter_title": current_chapter.get("title"),
                            "article_num": current_article.get("number") if current_article else None,
                            "article_title": current_article.get("title") if current_article else None
                        }
                    })
                
                # 새 장 시작
                current_chapter = {
                    "number": chapter_match.group(1),
                    "title": chapter_match.group(2).strip()
                }
                current_article = None
                current_content = [line]
                continue
            
            # 조(Article) 매칭
            article_match = re.match(article_pattern, line)
            if article_match:
                # 이전 청크 저장
                if current_content and current_chapter:
                    chunks.append({
                        "content": '\n'.join(current_content),
                        "chapter": current_chapter,
                        "article": current_article,
                        "metadata": {
                            "type": "regulation",
                            "chapter_num": current_chapter.get("number"),
                            "chapter_title": current_chapter.get("title"),
                            "article_num": current_article.get("number") if current_article else None,
                            "article_title": current_article.get("title") if current_article else None
                        }
                    })
                
                # 새 조 시작
                current_article = {
                    "number": article_match.group(1),
                    "title": article_match.group(2).strip()
                }
                current_content = [line]
                continue
            
            # 일반 내용 추가
            current_content.append(line)
        
        # 마지막 청크 저장
        if current_content and current_chapter:
            chunks.append({
                "content": '\n'.join(current_content),
                "chapter": current_chapter,
                "article": current_article,
                "metadata": {
                    "type": "regulation",
                    "chapter_num": current_chapter.get("number"),
                    "chapter_title": current_chapter.get("title"),
                    "article_num": current_article.get("number") if current_article else None,
                    "article_title": current_article.get("title") if current_article else None
                }
            })
        
        # 빈 청크 제거 및 최소 길이 필터링
        filtered_chunks = []
        for chunk in chunks:
            content = chunk["content"].strip()
            if len(content) > 10:  # 최소 10자 이상
                filtered_chunks.append(chunk)
        
        logger.info(f"내부 규정 문서 청킹 완료: {len(filtered_chunks)}개 청크 생성")
        return filtered_chunks

    def _chunk_report_document(self, text: str) -> List[Dict[str, Any]]:
        """
        보고서 문서를 소제목 기준으로 분할합니다.
        
        Args:
            text: 보고서 문서 텍스트
            
        Returns:
            청킹된 보고서 문서 리스트
        """
        chunks = []
        
        # 소제목 패턴들 (다양한 형식 지원)
        subtitle_patterns = [
            r'^(\d+\.\s*[^\n]+)',  # 1. 제목
            r'^([A-Z]\.\s*[^\n]+)',  # A. 제목
            r'^([가-힣]+\.\s*[^\n]+)',  # 가. 제목
            r'^([^\n]+)\n[-=]{3,}',  # 제목\n--- 또는 ===
            r'^##\s*([^\n]+)',  # ## 제목
            r'^#\s*([^\n]+)',  # # 제목
        ]
        
        lines = text.split('\n')
        current_subtitle = None
        current_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 소제목 매칭 확인
            subtitle_found = False
            for pattern in subtitle_patterns:
                match = re.match(pattern, line)
                if match:
                    # 이전 청크 저장
                    if current_content and current_subtitle:
                        chunks.append({
                            "content": '\n'.join(current_content),
                            "subtitle": current_subtitle,
                            "metadata": {
                                "type": "report",
                                "subtitle": current_subtitle,
                                "subtitle_level": self._get_subtitle_level(current_subtitle)
                            }
                        })
                    
                    # 새 소제목 시작
                    current_subtitle = match.group(1) if len(match.groups()) > 0 else line
                    current_content = [line]
                    subtitle_found = True
                    break
            
            if not subtitle_found:
                # 일반 내용 추가
                current_content.append(line)
        
        # 마지막 청크 저장
        if current_content and current_subtitle:
            chunks.append({
                "content": '\n'.join(current_content),
                "subtitle": current_subtitle,
                "metadata": {
                    "type": "report",
                    "subtitle": current_subtitle,
                    "subtitle_level": self._get_subtitle_level(current_subtitle)
                }
            })
        
        # 소제목이 없는 경우 문장 단위로 분할
        if not chunks:
            sentences = re.split(r'[.!?]+', text)
            for i, sentence in enumerate(sentences):
                sentence = sentence.strip()
                if len(sentence) > 20:  # 최소 20자 이상
                    chunks.append({
                        "content": sentence,
                        "subtitle": f"문장 {i+1}",
                        "metadata": {
                            "type": "report",
                            "subtitle": f"문장 {i+1}",
                            "subtitle_level": 0
                        }
                    })
        
        # 빈 청크 제거 및 최소 길이 필터링
        filtered_chunks = []
        for chunk in chunks:
            content = chunk["content"].strip()
            if len(content) > 20:  # 최소 20자 이상
                filtered_chunks.append(chunk)
        
        logger.info(f"보고서 문서 청킹 완료: {len(filtered_chunks)}개 청크 생성")
        return filtered_chunks

    def _get_subtitle_level(self, subtitle: str) -> int:
        """
        소제목의 레벨을 판단합니다.
        
        Args:
            subtitle: 소제목 텍스트
            
        Returns:
            소제목 레벨 (1, 2, 3, ...)
        """
        if re.match(r'^\d+\.', subtitle):
            return 1
        elif re.match(r'^[A-Z]\.', subtitle):
            return 2
        elif re.match(r'^[가-힣]\.', subtitle):
            return 3
        elif subtitle.startswith('##'):
            return 2
        elif subtitle.startswith('#'):
            return 1
        else:
            return 1

    def _rerank_model(self):
        """재순위 모델 로드 (private 메서드)"""
        try:
            logger.info("🔄 BGE Reranker 모델 로드 중...")
            reranker = FlagReranker('dragonkue/bge-reranker-v2-m3-ko', use_fp16=True, use_auth_token=None)
            logger.info("✅ BGE Reranker 모델 로드 완료")
            return reranker
        except Exception as e:
            logger.error(f"❌ Reranker 모델 로드 실패: {e}")
            return None

    def _embeddings_model(self):
        """임베딩 모델 로드 (private 메서드)"""
        try:
            logger.info("🤖 임베딩 모델 로드 중...")
            model = SentenceTransformer("dragonkue/snowflake-arctic-embed-l-v2.0-ko")
            logger.info("✅ 임베딩 모델 로드 완료")
            return model
        except Exception as e:
            logger.error(f"❌ 임베딩 모델 로드 실패: {e}")
            return None

    @property
    def DOCUMENT_INDEX_MAPPING(self) -> Dict[str, Any]:
        return {
            "settings": {
                "index": {
                    "knn": True
                }
            },
            "mappings": {
                "properties": {
                    "document_id": {"type": "keyword"},
                    "chunk_index": {"type": "integer"},
                    "content": {"type": "text"},
                    "embedding": {
                        "type": "knn_vector",
                        "dimension": self.embedding_dim,
                        "method": {
                            "name": "hnsw",
                            "space_type": "cosinesimil",
                            "engine": "lucene"
                        }
                    },
                    "file_name": {"type": "keyword"},
                    "title": {"type": "text"},
                    "document_type": {"type": "keyword"},
                    # 내부 규정 관련 필드
                    "chapter_num": {"type": "keyword"},
                    "chapter_title": {"type": "text"},
                    "article_num": {"type": "keyword"},
                    "article_title": {"type": "text"},
                    # 보고서 관련 필드
                    "subtitle": {"type": "text"},
                    "subtitle_level": {"type": "integer"}
                }
            }
        }

    def create_index(self, index_name: str, mapping: Optional[Dict[str, Any]] = None) -> bool:
        """
        인덱스를 생성합니다.
        
        Args:
            index_name: 생성할 인덱스 이름
            mapping: 인덱스 매핑 (None이면 기본 매핑 사용)
            
        Returns:
            인덱스 생성 성공 여부
        """
        if not self._check_client():
            return False
        
        try:
            if not self.client.indices.exists(index=index_name):
                mapping_to_use = mapping or self.DOCUMENT_INDEX_MAPPING
                self.client.indices.create(index=index_name, body=mapping_to_use)
                logger.info(f"'{index_name}' 인덱스를 매핑과 함께 생성했습니다.")
                return True
            logger.info(f"'{index_name}' 인덱스가 이미 존재합니다.")
            return True
        except exceptions.OpenSearchException as e:
            logger.error(f"인덱스 생성 중 오류 발생: {e}")
            return False

    def create_index_with_mapping(self, index_name: str, mapping: Dict[str, Any]) -> bool:
        """사용자 정의 매핑으로 인덱스를 생성합니다."""
        return self.create_index(index_name, mapping)

    def create_index_if_not_exists(self, index_name: str) -> bool:
        """기본 매핑으로 인덱스를 생성합니다."""
        return self.create_index(index_name)

    def index_document(self, index_name: str, document: Dict[str, Any], refresh: bool = False) -> Optional[Dict[str, Any]]:
        if not self._check_client():
            return None
        try:
            params = {"refresh": "true" if refresh else "false"}
            response = self.client.index(index=index_name, body=document, params=params)
            logger.info(f"'{index_name}' 인덱스에 문서 ID '{response['_id']}'로 색인되었습니다.")
            return response
        except exceptions.RequestError as e:
            logger.error(f"문서 색인 중 오류 발생 (잘못된 요청): {e}")
        except exceptions.OpenSearchException as e:
            logger.error(f"문서 색인 중 예외적 오류 발생: {e}")
        return None

    def bulk_index_documents(self, index_name: str, documents: List[Dict[str, Any]], refresh: bool = False) -> bool:
        if not self._check_client():
            return False
        actions = [
            {"_index": index_name, "_source": doc}
            for doc in documents
        ]
        try:
            success, failed = helpers.bulk(self.client, actions, refresh=refresh)
            logger.info(f"Bulk 작업 완료: 성공 {success}건, 실패 {len(failed)}건")
            return not failed
        except exceptions.OpenSearchException as e:
            logger.error(f"Bulk 색인 중 예외적 오류 발생: {e}")
            return False

    def search_document(self, index_name: str, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        if not self._check_client():
            return []
        try:
            response = self.client.search(index=index_name, body=query)
            hits = response["hits"]["hits"]
            logger.info(f"'{index_name}' 인덱스에서 {len(hits)}개의 문서를 찾았습니다.")
            return [{"score": hit["_score"], "source": hit["_source"]} for hit in hits]
        except exceptions.NotFoundError:
            logger.warning(f"검색 실패: '{index_name}' 인덱스가 존재하지 않습니다.")
        except exceptions.RequestError as e:
            logger.error(f"문서 검색 중 오류 발생 (잘못된 쿼리): {e}")
        except exceptions.OpenSearchException as e:
            logger.error(f"문서 검색 중 예외적 오류 발생: {e}")
        return []

    def index_document_chunks(self, index_name: str, doc_id: int, doc_title: str, file_name: str, text: str, document_type: str = "report") -> bool:
        """
        문서를 청킹하여 OpenSearch에 인덱싱합니다.
        
        Args:
            index_name: 인덱스 이름
            doc_id: 문서 ID
            doc_title: 문서 제목
            file_name: 파일명
            text: 원본 텍스트
            document_type: 문서 종류 ("regulation" 또는 "report")
            
        Returns:
            인덱싱 성공 여부
        """
        if not self._check_client():
            return False
        
        try:
            # 인덱스가 없으면 생성
            self.create_index_if_not_exists(index_name)
            
            # 문서 청킹 수행
            chunks = self.chunk_text_to_sentences(text, document_type)
            
            if not chunks:
                logger.warning(f"문서 {doc_id}에서 청킹할 내용을 찾을 수 없습니다.")
                return False
            
            # 청킹된 문서를 벡터로 변환하여 인덱싱
            documents = []
            for i, chunk in enumerate(chunks):
                content = chunk["content"]
                if content.strip():  # 빈 내용 제외
                    # 내용을 벡터로 변환
                    embedding = self.model.encode(content)
                    
                    # 문서 정보 구성
                    document = {
                        "document_id": doc_id,
                        "chunk_index": i,
                        "content": content,
                        "embedding": embedding.tolist(),
                        "file_name": file_name,
                        "title": doc_title,
                        "document_type": document_type
                    }
                    
                    # 문서 종류별 메타데이터 추가
                    if document_type == "regulation":
                        metadata = chunk.get("metadata", {})
                        document.update({
                            "chapter_num": metadata.get("chapter_num"),
                            "chapter_title": metadata.get("chapter_title"),
                            "article_num": metadata.get("article_num"),
                            "article_title": metadata.get("article_title")
                        })
                    else:  # report
                        metadata = chunk.get("metadata", {})
                        document.update({
                            "subtitle": metadata.get("subtitle"),
                            "subtitle_level": metadata.get("subtitle_level", 1)
                        })
                    
                    documents.append(document)
            
            # Bulk 인덱싱 수행
            success = self.bulk_index_documents(index_name, documents, refresh=True)
            
            if success:
                logger.info(f"문서 {doc_id}의 {len(documents)}개 청킹을 OpenSearch에 저장했습니다. (문서 타입: {document_type})")
            else:
                logger.error(f"문서 {doc_id}의 청킹 인덱싱에 실패했습니다.")
            
            return success
            
        except Exception as e:
            logger.error(f"문서 청킹 인덱싱 실패: {e}")
            return False

    def delete_document_chunks(self, index_name: str, document_id: int) -> bool:
        """
        특정 문서의 모든 청킹을 삭제합니다.
        
        Args:
            index_name: 인덱스 이름
            document_id: 삭제할 문서 ID
            
        Returns:
            삭제 성공 여부
        """
        if not self._check_client():
            return False
        
        try:
            # 문서 ID로 모든 청킹 삭제
            query = {
                "query": {
                    "term": {
                        "document_id": document_id
                    }
                }
            }
            
            response = self.client.delete_by_query(index=index_name, body=query)
            deleted_count = response.get("deleted", 0)
            
            logger.info(f"문서 {document_id}의 {deleted_count}개 청킹을 OpenSearch에서 삭제했습니다.")
            return True
            
        except exceptions.OpenSearchException as e:
            logger.error(f"문서 청킹 삭제 실패: {e}")
            return False

    def create_search_pipeline(self, pipeline_id: str = "hybrid-minmax-pipeline") -> bool:
        """
        OpenSearch 3.0+ 호환 하이브리드 검색용 search pipeline 생성
        
        Args:
            pipeline_id: 생성할 파이프라인 ID
            
        Returns:
            파이프라인 생성 성공 여부
        """
        if not self._check_client():
            return False
            
        pipeline_body = {
            "description": "하이브리드 점수 정규화 및 결합 파이프라인",
            "phase_results_processors": [
                {
                    "normalization-processor": {
                        "normalization": { 
                            "technique": "min_max" 
                        },
                        "combination": {
                            "technique": "arithmetic_mean",
                            "parameters": {
                                "weights": [0.3, 0.7]  # BM25: 0.3, 벡터: 0.7
                            }
                        }
                    }
                }
            ]
        }

        try:
            # 파이프라인 생성 또는 업데이트
            response = self.client.transport.perform_request(
                method="PUT",
                url=f"/_search/pipeline/{pipeline_id}",
                body=pipeline_body
            )
            logger.info(f"✅ Search pipeline '{pipeline_id}' 생성/업데이트 완료")
            logger.debug(f"응답: {response}")
            return True
        except Exception as e:
            logger.error(f"❌ Search pipeline 생성 실패: {e}")
            return False

    def get_search_pipeline(self, pipeline_id: str = "hybrid-minmax-pipeline") -> Optional[Dict[str, Any]]:
        """
        생성된 search pipeline 정보 조회
        
        Args:
            pipeline_id: 조회할 파이프라인 ID
            
        Returns:
            파이프라인 정보 또는 None
        """
        if not self._check_client():
            return None
            
        try:
            response = self.client.transport.perform_request(
                method="GET",
                url=f"/_search/pipeline/{pipeline_id}"
            )
            logger.info(f"📋 Search pipeline '{pipeline_id}' 정보 조회 완료")
            return response
        except Exception as e:
            logger.error(f"❌ Search pipeline 조회 실패: {e}")
            return None

    def delete_search_pipeline(self, pipeline_id: str = "hybrid-minmax-pipeline") -> bool:
        """
        search pipeline 삭제
        
        Args:
            pipeline_id: 삭제할 파이프라인 ID
            
        Returns:
            삭제 성공 여부
        """
        if not self._check_client():
            return False
            
        try:
            response = self.client.transport.perform_request(
                method="DELETE",
                url=f"/_search/pipeline/{pipeline_id}"
            )
            logger.info(f"🗑️ Search pipeline '{pipeline_id}' 삭제 완료")
            return True
        except Exception as e:
            logger.error(f"❌ Search pipeline 삭제 실패: {e}")
            return False

    def search_with_pipeline(self, 
                           query_text: str,
                           keywords: Union[str, List[str]] = None, 
                           pipeline_id: str = "hybrid-minmax-pipeline", 
                           index_name: str = "documents", 
                           top_k: int = 10,
                           use_rerank: bool = True,
                           rerank_top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Search pipeline을 사용한 하이브리드 검색
        
        Args:
            query_text: 검색 쿼리 텍스트
            keywords: 키워드 또는 키워드 리스트 (None이면 query_text 사용)
            pipeline_id: 사용할 search pipeline ID
            index_name: 검색 대상 인덱스
            top_k: 반환할 결과 수
            use_rerank: 리랭커 사용 여부
            rerank_top_k: 리랭크 후 반환할 결과 수
            
        Returns:
            검색 결과 리스트 (리랭크 적용 시 리랭크된 결과)
        """
        if not self._check_client():
            return []
            
        logger.info(f"\n=== Search Pipeline 기반 하이브리드 검색 시작 ===")
        logger.info(f"Pipeline ID: {pipeline_id}")
        logger.info(f"Query: {query_text}")
        logger.info(f"Keywords: {keywords}")
        
        try:
            # 키워드 처리
            if keywords is None:
                keyword_text = query_text
            elif isinstance(keywords, list):
                keyword_text = " ".join(keywords)
            else:
                keyword_text = keywords
            
            # 벡터 임베딩 생성
            query_vector = self.model.encode(query_text).tolist()
            logger.info(f"생성된 벡터 차원: {len(query_vector)}")
            
            # 하이브리드 쿼리 구성
            query_body = {
                "size": top_k,
                "query": {
                    "hybrid": {
                        "queries": [
                            {
                                "multi_match": {
                                    "query": keyword_text,
                                    "fields": ["content^2", "title^1.5", "file_name^1.0"],
                                    "type": "best_fields",
                                    "fuzziness": "AUTO"
                                }
                            },
                            {
                                "knn": {
                                    "embedding": {
                                        "vector": query_vector,
                                        "k": top_k
                                    }
                                }
                            }
                        ]
                    }
                },
                "_source": {
                    "excludes": ["embedding"]  # 벡터 필드 제외
                }
            }

            # Search pipeline 파라미터 설정
            params = {"search_pipeline": pipeline_id}
            
            logger.debug(f"실행 중인 쿼리: {json.dumps(query_body, indent=2, ensure_ascii=False)}")

            # 검색 실행
            response = self.client.search(index=index_name, body=query_body, params=params)
            
            # 결과 처리
            hits = response.get("hits", {}).get("hits", [])
            results = []
            
            logger.info(f"✅ Search pipeline 검색 완료: {len(hits)}개 결과")
            
            for i, hit in enumerate(hits):
                result = {
                    "score": hit["_score"],
                    "source": hit["_source"]
                }
                results.append(result)
                
                # 결과 로깅
                source = hit["_source"]
                logger.info(f"\n{i+1}. Pipeline 점수: {hit['_score']:.6f}")
                logger.info(f"   문서명: {source.get('title', 'N/A')}")
                logger.info(f"   파일명: {source.get('file_name', 'N/A')}")
                logger.info(f"   내용: {source.get('content', 'N/A')[:100]}...")
            
            # 리랭크 적용 (무조건 적용)
            if results:
                if self.reranker:
                    logger.info(f"\n🔄 BGE Reranker로 상위 {rerank_top_k}개 선별 중...")
                    reranked_results = self._rerank_documents_with_pipeline(query_text, results, rerank_top_k)
                    
                    logger.info(f"\n=== BGE Reranker 최종 결과 (상위 {len(reranked_results)}개) ===")
                    for i, doc in enumerate(reranked_results):
                        source = doc['source']
                        logger.info(f"\n{i+1}. 리랭크 점수: {doc['rerank_score']:.6f}")
                        logger.info(f"   Pipeline 점수: {doc['score']:.6f}")
                        logger.info(f"   문서명: {source.get('title', 'N/A')}")
                        logger.info(f"   파일명: {source.get('file_name', 'N/A')}")
                        logger.info(f"   내용: {source.get('content', 'N/A')[:100]}...")
                    
                    return reranked_results
                else:
                    logger.warning("⚠️ 재순위 모델이 로드되지 않아 기본 검색 결과를 반환합니다.")
                    return results
            else:
                logger.warning("⚠️ 검색 결과가 없어 재순위를 적용할 수 없습니다.")
                return results
            
        except Exception as e:
            logger.error(f"❌ Search pipeline 검색 오류: {e}")
            return []

    def _rerank_documents_with_pipeline(self, query_text: str, documents: List[Dict[str, Any]], top_k: int = 3) -> List[Dict[str, Any]]:
        """
        BGE Reranker를 사용하여 문서를 리랭크 (Search Pipeline용)
        
        Args:
            query_text: 쿼리 텍스트
            documents: 리랭크할 문서 리스트
            top_k: 반환할 상위 문서 수
            
        Returns:
            리랭크된 문서 리스트
        """
        if not documents or not self.reranker:
            return documents[:top_k]
        
        logger.info(f"BGE Reranker 리랭크 시작 - 대상 문서: {len(documents)}개")
        
        try:
            # Reranker를 위한 쿼리-문서 쌍 생성
            query_doc_pairs = []
            for doc in documents:
                source = doc['source']
                doc_text = f"{source.get('title', '')} {source.get('content', '')}"
                query_doc_pairs.append([query_text, doc_text])
            
            # Reranker 점수 계산
            rerank_scores = self.reranker.compute_score(query_doc_pairs)
            
            if rerank_scores is None:
                logger.warning("리랭크 점수 계산에 실패했습니다.")
                return documents[:top_k]
            
            # numpy 배열을 리스트로 변환
            if hasattr(rerank_scores, 'tolist'):
                rerank_scores = rerank_scores.tolist()
            else:
                rerank_scores = list(rerank_scores)
            
            logger.info(f"리랭크 점수 범위: {min(rerank_scores):.6f} ~ {max(rerank_scores):.6f}")
            
            # 점수를 문서에 추가
            for i, doc in enumerate(documents):
                doc['rerank_score'] = rerank_scores[i]
            
            # 리랭크 점수로 정렬하여 상위 top_k개 반환
            reranked_results = sorted(documents, key=lambda x: x['rerank_score'], reverse=True)[:top_k]
            
            return reranked_results
            
        except Exception as e:
            logger.error(f"Reranker 적용 중 오류 발생: {e}")
            return documents[:top_k]

# 전역 OpenSearch 클라이언트 인스턴스 생성 (10초 타임아웃 + 3회 재시도)
opensearch_client = OpenSearchClient(max_retries=3, timeout=10) 