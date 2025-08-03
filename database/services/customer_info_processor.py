import logging
import re
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from models.customers import Customer
from services.db import get_db
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

def extract_name_and_address(raw_name: str):
    # 예: '미라클신경과의원(강서구 화곡동)' -> ('미라클신경과의원', '강서구 화곡동')
    match = re.match(r"(.+?)\((.+)\)", raw_name)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return raw_name.strip(), None

def process_customer_info(table_data: List[Dict[str, Any]], engine=None) -> int:
    """
    거래처 정보 문서 데이터를 customers 테이블에만 저장
    Args:
        table_data: DataFrame에서 추출한 딕셔너리 리스트
        engine: sqlalchemy engine (필요시)
    Returns:
        처리된 행 수
    """
    processed_count = 0
    skipped_count = 0
    db = next(get_db())
    
    # 중복 처리를 위한 고객명 추적
    processed_customers = set()
    
    try:
        for row in table_data:
            # 1. 고객명/주소 추출
            raw_name = row.get("거래처ID")
            if not raw_name:
                logger.warning(f"거래처ID 없는 행 건너뜀: {row}")
                continue
            customer_name, address = extract_name_and_address(raw_name)
            
            # 2. 이미 처리된 고객인지 확인 (중복 방지)
            if customer_name in processed_customers:
                logger.info(f"이미 처리된 거래처 건너뜀: {customer_name}")
                skipped_count += 1
                continue
            
            # 3. 총환자수
            total_patients = row.get("총환자수")
            try:
                total_patients = int(str(total_patients).replace(",", "").strip()) if total_patients else None
            except Exception:
                total_patients = None
            
            # 4. customers 테이블에서 기존 고객 확인 (고객명 + 주소 조합으로 체크)
            existing_customer = db.query(Customer).filter(
                Customer.customer_name == customer_name,
                Customer.address == address
            ).first()
            
            if existing_customer:
                # 기존 고객 정보 업데이트
                if address and existing_customer.address != address:
                    existing_customer.address = address
                if total_patients is not None:
                    existing_customer.total_patients = total_patients
                db.add(existing_customer)
                logger.info(f"거래처 정보 업데이트: {customer_name} (기존 ID: {existing_customer.customer_id})")
            else:
                # 새 고객 등록
                new_customer = Customer(
                    customer_name=customer_name,
                    address=address,
                    total_patients=total_patients
                )
                db.add(new_customer)
                logger.info(f"새 거래처 등록: {customer_name}")
            
            # 처리된 고객명을 추적에 추가
            processed_customers.add(customer_name)
            processed_count += 1
        
        db.commit()
        logger.info(f"거래처 정보 처리 완료: {processed_count}명 처리됨, {skipped_count}명 중복 건너뜀")
        
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"DB 처리 중 오류: {e}")
        raise
    finally:
        db.close()
    return processed_count 