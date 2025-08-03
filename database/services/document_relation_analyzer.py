import logging
from typing import List, Dict, Any, Optional
import re
from sqlalchemy.orm import Session
from models.documents import Document
from models.document_relations import DocumentRelation
from models.document_interaction_map import DocumentInteractionMap
from models.document_sales_map import DocumentSalesMap
from models.customers import Customer
from models.products import Product
from models.employees import Employee
from services.openai_service import openai_service

logger = logging.getLogger(__name__)

class DocumentRelationAnalyzer:
    """문서 내용을 분석하여 관계를 자동으로 생성하는 서비스"""
    
    def __init__(self, db_session_factory=None):
        """
        문서 관계 분석기 초기화
        
        Args:
            db_session_factory: 데이터베이스 세션 팩토리
        """
        self.db_session_factory = db_session_factory
    
    def analyze_document_relations(self, doc_id: int, text: str, table_data: List[Dict] = None) -> Dict[str, Any]:
        """
        문서 내용을 분석하여 관계를 생성
        
        Args:
            doc_id: 문서 ID
            text: 문서 텍스트 내용
            table_data: 테이블 데이터 (선택사항)
            
        Returns:
            Dict: 분석 결과
        """
        try:
            relations_created = 0
            
            # 1. 고객명 추출 및 관계 생성
            customer_relations = self._extract_customer_relations(doc_id, text, table_data)
            relations_created += len(customer_relations)
            
            # 2. 제품명 추출 및 관계 생성
            product_relations = self._extract_product_relations(doc_id, text, table_data)
            relations_created += len(product_relations)
            
            # 3. 직원명 추출 및 관계 생성
            employee_relations = self._extract_employee_relations(doc_id, text, table_data)
            relations_created += len(employee_relations)
            
            # 4. 유사한 문서 찾기
            similar_docs = self._find_similar_documents(doc_id, text)
            relations_created += len(similar_docs)
            
            logger.info(f"문서 관계 분석 완료: {relations_created}개 관계 생성")
            
            return {
                'success': True,
                'message': f'문서 관계 분석 완료: {relations_created}개 관계 생성',
                'relations_created': relations_created,
                'customer_relations': customer_relations,
                'product_relations': product_relations,
                'employee_relations': employee_relations,
                'similar_docs': similar_docs
            }
            
        except Exception as e:
            logger.error(f"문서 관계 분석 중 오류: {e}")
            return {
                'success': False,
                'message': f'문서 관계 분석 중 오류 발생: {str(e)}',
                'relations_created': 0
            }
    
    def _extract_customer_relations(self, doc_id: int, text: str, table_data: List[Dict] = None) -> List[Dict]:
        """고객명 추출 및 관계 생성"""
        customer_names = []
        
        # 텍스트에서 고객명 추출
        customer_names.extend(self._extract_names_from_text(text, ['고객', '병원', '의원', '클리닉', '의료기관']))
        
        # 테이블 데이터에서 고객명 추출
        if table_data:
            for row in table_data:
                for key, value in row.items():
                    if any(keyword in key.lower() for keyword in ['고객', 'customer', '병원', 'hospital']):
                        if value and str(value).strip():
                            customer_names.append(str(value).strip())
        
        # 중복 제거
        customer_names = list(set(customer_names))
        
        # 데이터베이스에서 고객 찾기 및 관계 생성
        relations = []
        with self.db_session_factory() as session:
            for customer_name in customer_names:
                customer = session.query(Customer).filter(
                    Customer.customer_name.ilike(f"%{customer_name}%")
                ).first()
                
                if customer:
                    # 기존 관계 확인
                    existing_relation = session.query(DocumentRelation).filter(
                        DocumentRelation.doc_id == doc_id,
                        DocumentRelation.related_entity_type == 'customer',
                        DocumentRelation.related_entity_id == customer.customer_id
                    ).first()
                    
                    if not existing_relation:
                        # 새 관계 생성
                        relation = DocumentRelation(
                            doc_id=doc_id,
                            related_entity_type='customer',
                            related_entity_id=customer.customer_id,
                            confidence_score=80
                        )
                        session.add(relation)
                        session.commit()
                        relations.append({
                            'type': 'customer',
                            'entity_id': customer.customer_id,
                            'entity_name': customer.customer_name
                        })
                        logger.info(f"고객 관계 생성: {customer.customer_name}")
        
        return relations
    
    def _extract_product_relations(self, doc_id: int, text: str, table_data: List[Dict] = None) -> List[Dict]:
        """제품명 추출 및 관계 생성"""
        product_names = []
        
        # 텍스트에서 제품명 추출
        product_names.extend(self._extract_names_from_text(text, ['제품', '상품', '품목', '의료기기', '약품']))
        
        # 테이블 데이터에서 제품명 추출
        if table_data:
            for row in table_data:
                for key, value in row.items():
                    if any(keyword in key.lower() for keyword in ['제품', 'product', '상품', 'item']):
                        if value and str(value).strip():
                            product_names.append(str(value).strip())
        
        # 중복 제거
        product_names = list(set(product_names))
        
        # 데이터베이스에서 제품 찾기 및 관계 생성
        relations = []
        with self.db_session_factory() as session:
            for product_name in product_names:
                product = session.query(Product).filter(
                    Product.product_name.ilike(f"%{product_name}%")
                ).first()
                
                if product:
                    # 기존 관계 확인
                    existing_relation = session.query(DocumentRelation).filter(
                        DocumentRelation.doc_id == doc_id,
                        DocumentRelation.related_entity_type == 'product',
                        DocumentRelation.related_entity_id == product.product_id
                    ).first()
                    
                    if not existing_relation:
                        # 새 관계 생성
                        relation = DocumentRelation(
                            doc_id=doc_id,
                            related_entity_type='product',
                            related_entity_id=product.product_id,
                            confidence_score=80
                        )
                        session.add(relation)
                        session.commit()
                        relations.append({
                            'type': 'product',
                            'entity_id': product.product_id,
                            'entity_name': product.product_name
                        })
                        logger.info(f"제품 관계 생성: {product.product_name}")
        
        return relations
    
    def _extract_employee_relations(self, doc_id: int, text: str, table_data: List[Dict] = None) -> List[Dict]:
        """직원명 추출 및 관계 생성"""
        employee_names = []
        
        # 텍스트에서 직원명 추출
        employee_names.extend(self._extract_names_from_text(text, ['직원', '담당자', '사원', '매니저']))
        
        # 테이블 데이터에서 직원명 추출
        if table_data:
            for row in table_data:
                for key, value in row.items():
                    if any(keyword in key.lower() for keyword in ['직원', 'employee', '담당자', '담당']):
                        if value and str(value).strip():
                            employee_names.append(str(value).strip())
        
        # 중복 제거
        employee_names = list(set(employee_names))
        
        # 데이터베이스에서 직원 찾기 및 관계 생성
        relations = []
        with self.db_session_factory() as session:
            for employee_name in employee_names:
                employee = session.query(Employee).filter(
                    Employee.name.ilike(f"%{employee_name}%")
                ).first()
                
                if employee:
                    # 기존 관계 확인
                    existing_relation = session.query(DocumentRelation).filter(
                        DocumentRelation.doc_id == doc_id,
                        DocumentRelation.related_entity_type == 'employee',
                        DocumentRelation.related_entity_id == employee.employee_id
                    ).first()
                    
                    if not existing_relation:
                        # 새 관계 생성
                        relation = DocumentRelation(
                            doc_id=doc_id,
                            related_entity_type='employee',
                            related_entity_id=employee.employee_id,
                            confidence_score=80
                        )
                        session.add(relation)
                        session.commit()
                        relations.append({
                            'type': 'employee',
                            'entity_id': employee.employee_id,
                            'entity_name': employee.name
                        })
                        logger.info(f"직원 관계 생성: {employee.name}")
        
        return relations
    
    def _extract_names_from_text(self, text: str, keywords: List[str]) -> List[str]:
        """텍스트에서 키워드 기반으로 이름 추출"""
        names = []
        
        # 텍스트가 문자열인지 확인
        if not isinstance(text, str):
            logger.warning(f"텍스트가 문자열이 아닙니다: {type(text)}")
            return names
        
        # 간단한 패턴 매칭으로 이름 추출
        for keyword in keywords:
            # 키워드 주변의 텍스트에서 이름 패턴 찾기
            pattern = rf'{keyword}[^\n]*?([가-힣]{{2,4}})'
            matches = re.findall(pattern, text)
            names.extend(matches)
        
        return names
    
    def _find_similar_documents(self, doc_id: int, text: str) -> List[Dict]:
        """유사한 문서 찾기"""
        similar_docs = []
        
        try:
            # OpenAI를 사용하여 유사한 문서 찾기
            messages = [
                {"role": "system", "content": "다음 텍스트와 관련된 문서 유형을 분석해주세요."},
                {"role": "user", "content": f"텍스트: {text[:1000]}..."}
            ]
            
            response_text = openai_service.create_chat_completion(
                messages=messages,
                model="gpt-3.5-turbo",
                max_tokens=100,
                temperature=0.1
            )
            
            if not response_text:
                logger.warning("LLM 응답을 받지 못했습니다.")
                return similar_docs
            
            doc_type = response_text.strip()
            
            # 같은 유형의 문서 찾기
            with self.db_session_factory() as session:
                similar_documents = session.query(Document).filter(
                    Document.doc_id != doc_id,
                    Document.doc_type.ilike(f"%{doc_type}%")
                ).limit(5).all()
                
                for similar_doc in similar_documents:
                    # 기존 관계 확인
                    existing_relation = session.query(DocumentRelation).filter(
                        DocumentRelation.doc_id == doc_id,
                        DocumentRelation.related_entity_type == 'document',
                        DocumentRelation.related_entity_id == similar_doc.doc_id
                    ).first()
                    
                    if not existing_relation:
                        # 새 관계 생성
                        relation = DocumentRelation(
                            doc_id=doc_id,
                            related_entity_type='document',
                            related_entity_id=similar_doc.doc_id,
                            confidence_score=60
                        )
                        session.add(relation)
                        session.commit()
                        similar_docs.append({
                            'type': 'document',
                            'entity_id': similar_doc.doc_id,
                            'entity_name': similar_doc.doc_title
                        })
                        logger.info(f"유사 문서 관계 생성: {similar_doc.doc_title}")
        
        except Exception as e:
            logger.error(f"유사 문서 찾기 중 오류: {e}")
        
        return similar_docs
    
    def delete_document_relations(self, doc_id: int) -> Dict[str, Any]:
        """특정 문서의 모든 관계 삭제"""
        try:
            with self.db_session_factory() as session:
                # 해당 문서의 모든 관계 삭제
                deleted_count = session.query(DocumentRelation).filter(
                    DocumentRelation.doc_id == doc_id
                ).delete()
                
                session.commit()
                
                logger.info(f"문서 {doc_id}의 관계 {deleted_count}개 삭제 완료")
                
                return {
                    'success': True,
                    'message': f'문서 관계 {deleted_count}개 삭제 완료',
                    'deleted_count': deleted_count
                }
                
        except Exception as e:
            logger.error(f"문서 관계 삭제 중 오류: {e}")
            return {
                'success': False,
                'message': f'문서 관계 삭제 중 오류 발생: {str(e)}',
                'deleted_count': 0
            }

# 전역 인스턴스
from services.db import SessionLocal
document_relation_analyzer = DocumentRelationAnalyzer(db_session_factory=SessionLocal) 