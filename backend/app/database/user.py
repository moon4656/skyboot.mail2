from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import os
from ..config import settings

# 데이터베이스 URL 설정
DATABASE_URL = getattr(settings, 'DATABASE_URL', 
    "postgresql://postgres:password@localhost:5432/skyboot_mail")

# SQLAlchemy 엔진 생성 (성능 최적화)
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # 연결 상태 확인 활성화
    pool_recycle=3600,   # 1시간마다 연결 재생성
    pool_size=10,        # 연결 풀 크기
    max_overflow=20,     # 최대 추가 연결 수
    echo=False,          # 개발 시에는 True로 설정하여 SQL 쿼리 로그 확인 가능
    connect_args={
        "connect_timeout": 5,        # 연결 타임아웃 단축
        "client_encoding": "utf8",   # UTF-8 인코딩 명시적 설정
        "options": "-c client_encoding=utf8 -c timezone=Asia/Seoul"  # 추가 인코딩 및 시간대 설정
    },
    # PostgreSQL 드라이버에 UTF-8 처리 강제 설정
    execution_options={"autocommit": False},
    # 한글 처리를 위한 추가 설정
    pool_reset_on_return='commit'
)

# 세션 로컬 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base 클래스 생성
Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """
    데이터베이스 세션을 생성하고 반환합니다.
    
    Yields:
        Session: SQLAlchemy 데이터베이스 세션
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """
    모든 테이블을 생성합니다.
    """
    Base.metadata.create_all(bind=engine)

def drop_tables():
    """
    모든 테이블을 삭제합니다. (주의: 개발 환경에서만 사용)
    """
    Base.metadata.drop_all(bind=engine)