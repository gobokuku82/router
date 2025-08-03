from passlib.context import CryptContext
from models.employees import Employee
from schemas.employee import EmployeeCreate
from sqlalchemy.orm import Session

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_employee_by_email(db: Session, email: str):
    return db.query(Employee).filter(
        Employee.email == email,
        Employee.is_deleted == False
    ).first()

def create_employee(db: Session, user: EmployeeCreate):
    hashed_password = pwd_context.hash(user.password)
    db_user = Employee(
        email=user.email,
        username=user.username,
        password=hashed_password,
        name=user.name,
        role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_all_employees(db: Session):
    return db.query(Employee).all() 