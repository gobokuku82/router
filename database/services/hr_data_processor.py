"""
인사 자료 처리 서비스
XLSX/CSV 파일에서 추출한 인사 데이터를 PostgreSQL의 employees 테이블에 삽입합니다.
"""

import logging
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from models.employees import Employee
from services.db import get_db
import re
from passlib.context import CryptContext

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def is_email(val: str) -> bool:
    return bool(re.match(r"[^@]+@[^@]+\.[^@]+", val))

def process_hr_data(table_data: List[Dict[str, Any]]) -> int:
    """
    인사 자료를 처리하여 employees 테이블에 삽입합니다.
    Args:
        table_data: DataFrame에서 추출한 딕셔너리 리스트
    Returns:
        처리된 직원 수
    """
    try:
        logger.info(f"인사 자료 처리 시작: {len(table_data)}개 행")
        column_mapping = {
            "성명": "name", 
            "부서": "team",
            "직급": "position",
            "사업부": "business_unit",
            "지점": "branch",
            "연락처": "contact_number",
            "월평균사용예산": "avg_monthly_budget",
            "최근 평가": "latest_evaluation",
            "기본급(₩)": "base_salary",
            "성과급(₩)": "incentive_pay",
            "책임업무": "responsibilities",
            "ID": "email",  # 시스템 로그인 ID를 email로 사용
            "PW": "password"
        }
        processed_count = 0
        db = next(get_db())
        try:
            for row in table_data:
                employee_data = {}
                for korean_col, db_col in column_mapping.items():
                    if korean_col in row:
                        value = row[korean_col]
                        if db_col == "base_salary" or db_col == "incentive_pay" or db_col == "avg_monthly_budget":
                            if isinstance(value, str):
                                value = value.replace(",", "").replace("₩", "").strip()
                            try:
                                employee_data[db_col] = int(float(value)) if value else None
                            except (ValueError, TypeError):
                                employee_data[db_col] = None
                        elif db_col == "email":
                            if value and isinstance(value, str):
                                if is_email(value):
                                    employee_data[db_col] = value
                                else:
                                    employee_data[db_col] = f"{value}@jjs.co.kr"
                            else:
                                employee_data[db_col] = None
                        elif db_col == "password":
                            if value and isinstance(value, str):
                                employee_data[db_col] = pwd_context.hash(value)
                            else:
                                employee_data[db_col] = pwd_context.hash("default_password")
                        else:
                            employee_data[db_col] = str(value) if value else None
                if not employee_data.get("name"):
                    logger.warning(f"이름이 없는 행 건너뜀: {row}")
                    continue
                employee_data.setdefault("role", "user")
                employee_data.setdefault("is_active", True)
                if employee_data.get("email") and not employee_data.get("username"):
                    employee_data["username"] = employee_data["email"]
                existing_employee = db.query(Employee).filter(
                    Employee.name == employee_data["name"],
                    Employee.contact_number == employee_data.get("contact_number")
                ).first()
                if existing_employee:
                    logger.info(f"기존 직원 업데이트: {employee_data['name']}")
                    for key, value in employee_data.items():
                        if hasattr(existing_employee, key) and value is not None:
                            setattr(existing_employee, key, value)
                else:
                    logger.info(f"새 직원 추가: {employee_data['name']}")
                    new_employee = Employee(**employee_data)
                    db.add(new_employee)
                processed_count += 1
            db.commit()
            logger.info(f"인사 자료 처리 완료: {processed_count}명 처리됨")
        except Exception as e:
            db.rollback()
            logger.error(f"데이터베이스 처리 중 오류: {e}")
            raise
        finally:
            db.close()
        return processed_count
    except Exception as e:
        logger.error(f"인사 자료 처리 실패: {e}")
        raise 