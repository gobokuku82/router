from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from schemas.employee import EmployeeCreate, EmployeeInfo
from services.user_service import get_employee_by_email, create_employee
from services.db import get_db
from models.employees import Employee
from sqlalchemy.exc import IntegrityError
from routers.user_router import get_current_admin_user
from services.opensearch_service import delete_document_chunks_from_opensearch, DOCUMENT_INDEX_NAME
import subprocess
import os
from config import settings


router = APIRouter()

@router.post("/register-employee", response_model=EmployeeInfo)
def register_employee(user: EmployeeCreate, db: Session = Depends(get_db), admin: EmployeeInfo = Depends(get_current_admin_user)):
    db_user = get_employee_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    new_user = create_employee(db, user)
    return EmployeeInfo.from_orm(new_user)

@router.post("/init-admin", response_model=EmployeeInfo)
def init_admin(user: EmployeeCreate, db: Session = Depends(get_db)):
    """
    최초 1회만 사용 가능한 관리자 계정 생성 API (인증 불필요)
    이미 관리자가 존재하면 400 에러 반환
    """
    # 1. 기존 관리자 확인 (soft delete 고려)
    existing_admin = db.query(Employee).filter(
        Employee.role == "admin",
        Employee.is_deleted == False
    ).first()
    if existing_admin:
        raise HTTPException(status_code=400, detail="관리자 계정이 이미 존재합니다.")
    
    # 2. 역할 검증
    if user.role != "admin":
        raise HTTPException(status_code=400, detail="role은 반드시 'admin'이어야 합니다.")
    
    # 3. 이메일 중복 체크
    existing_user = get_employee_by_email(db, email=user.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="이메일이 이미 존재합니다.")
    
    # 4. 사용자명 중복 체크
    existing_username = db.query(Employee).filter(
        Employee.username == user.username,
        Employee.is_deleted == False
    ).first()
    if existing_username:
        raise HTTPException(status_code=400, detail="사용자명이 이미 존재합니다.")
    
    try:
        # 5. 관리자 계정 생성
        new_user = create_employee(db, user)
        return EmployeeInfo.from_orm(new_user)
    except IntegrityError as e:
        db.rollback()
        # 더 구체적인 오류 메시지 제공
        if "email" in str(e).lower():
            raise HTTPException(status_code=400, detail="이메일이 이미 존재합니다.")
        elif "username" in str(e).lower():
            raise HTTPException(status_code=400, detail="사용자명이 이미 존재합니다.")
        else:
            raise HTTPException(status_code=400, detail="데이터베이스 제약 조건 위반: " + str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"관리자 계정 생성 중 오류 발생: {str(e)}")

@router.post("/migrate")
def run_alembic_migration():
    """
    Alembic migration을 실행하는 관리자용 API입니다.
    기존 테이블을 모두 삭제하고 새로 생성합니다.
    운영 환경에서는 반드시 인증/권한 체크를 추가하세요!
    """
    try:
        env = os.environ.copy()
        # 현재 파일의 위치를 기준으로 프로젝트 루트 디렉터리 계산
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, ".."))
        env["PYTHONPATH"] = project_root
        # alembic 명령어 실행 디렉터리 (프로젝트 루트)
        alembic_dir = project_root
        
        # 1. 기존 마이그레이션을 모두 되돌리기 (테이블 삭제)
        # IF EXISTS 옵션으로 안전하게 처리
        downgrade_result = subprocess.run(
            ["alembic", "downgrade", "base"],
            cwd=alembic_dir,
            capture_output=True,
            text=True,
            check=False,  # downgrade 실패해도 계속 진행
            env=env
        )
        
        # 2. 최신 마이그레이션으로 업그레이드 (테이블 재생성)
        upgrade_result = subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd=alembic_dir,
            capture_output=True,
            text=True,
            check=True,
            env=env
        )
        
        return {
            "success": True, 
            "message": "테이블 삭제 후 재생성 완료",
            "downgrade_stdout": downgrade_result.stdout,
            "downgrade_stderr": downgrade_result.stderr,
            "upgrade_stdout": upgrade_result.stdout
        }
    except subprocess.CalledProcessError as e:
        return {"success": False, "stderr": e.stderr}

@router.delete("/cleanup-corrupted-documents")
def cleanup_corrupted_documents(admin: EmployeeInfo = Depends(get_current_admin_user)):
    """
    깨진 문서 데이터를 정리하는 관리자용 API입니다.
    OpenSearch에서 깨진 텍스트가 포함된 문서 청크들을 삭제합니다.
    """
    try:
        from services.opensearch_client import opensearch_client
        
        if not opensearch_client or not opensearch_client.client:
            raise HTTPException(status_code=500, detail="OpenSearch 클라이언트가 초기화되지 않았습니다.")
        
        # 깨진 텍스트 패턴을 찾아서 삭제
        corrupted_patterns = [
            "ߩ+)]N",  # 실제 결과에서 발견된 패턴
            "\\u6M~g~l",
            "zi'$&3",
            "xml]O0"
        ]
        
        deleted_count = 0
        
        for pattern in corrupted_patterns:
            try:
                # 깨진 패턴이 포함된 문서 검색
                query = {
                    "query": {
                        "wildcard": {
                            "content": f"*{pattern}*"
                        }
                    }
                }
                
                response = opensearch_client.client.search(
                    index=DOCUMENT_INDEX_NAME,
                    body=query,
                    size=100
                )
                
                # 검색된 문서들 삭제
                for hit in response["hits"]["hits"]:
                    doc_id = hit["_id"]
                    opensearch_client.client.delete(
                        index=DOCUMENT_INDEX_NAME,
                        id=doc_id
                    )
                    deleted_count += 1
                    
            except Exception as e:
                print(f"패턴 '{pattern}' 삭제 중 오류: {e}")
                continue
        
        return {
            "success": True,
            "message": f"깨진 문서 데이터 정리 완료: {deleted_count}개 청크 삭제됨",
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"깨진 문서 정리 중 오류 발생: {str(e)}") 