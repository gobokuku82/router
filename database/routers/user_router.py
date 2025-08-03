from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from datetime import datetime, timedelta
from schemas.employee import EmployeeCreate, EmployeeLogin, EmployeeInfo
from services.user_service import get_employee_by_email, create_employee, verify_password, get_all_employees
from services.db import get_db
from pydantic import BaseModel
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Optional, List
from sqlalchemy.exc import IntegrityError
from models.employees import Employee
from config import settings

# 중앙화된 설정에서 JWT 설정 가져오기
jwt_config = settings.get_jwt_config()
SECRET_KEY = jwt_config["secret_key"]
ALGORITHM = jwt_config["algorithm"]
ACCESS_TOKEN_EXPIRE_MINUTES = jwt_config["access_token_expire_minutes"]

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/user/login")

router = APIRouter()

# JWT 관련 함수
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_employee_by_email(db, email=email)
    if user is None:
        raise credentials_exception
    return user

def get_current_admin_user(current_user: EmployeeInfo = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return current_user

class Token(BaseModel):
    access_token: str
    token_type: str

@router.post("/login", response_model=Token)
def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = get_employee_by_email(db, email=form_data.username)
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    access_token = create_access_token(data={"sub": user.email, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=EmployeeInfo)
def get_me(current_user: EmployeeInfo = Depends(get_current_user)):
    return EmployeeInfo.from_orm(current_user)

@router.get("/employees", response_model=List[EmployeeInfo])
def list_employees(db: Session = Depends(get_db), current_user: EmployeeInfo = Depends(get_current_admin_user)):
    employees = get_all_employees(db)
    return [EmployeeInfo.from_orm(emp) for emp in employees]

@router.get("/employees/all", response_model=List[EmployeeInfo])
def list_employees_for_user(db: Session = Depends(get_db), current_user: EmployeeInfo = Depends(get_current_user)):
    employees = get_all_employees(db)
    return [EmployeeInfo.from_orm(emp) for emp in employees] 