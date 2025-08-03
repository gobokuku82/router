from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base
from config import settings

# 중앙화된 설정에서 데이터베이스 URL 가져오기
SQLALCHEMY_DATABASE_URL = settings.get_database_url()

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 