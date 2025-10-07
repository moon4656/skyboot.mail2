from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import os
from typing import Generator
import logging

# 로깅 설정
logger = logging.getLogger(__name__)

# 데이터베이스 URL 설정
DATABASE_URL = os.getenv(
    "MAIL_DATABASE_URL",
    "postgresql://postgres:safe70!!@localhost:5432/skybootmail"
)

# SQLAlchemy 엔진 생성
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=False  # 개발 시에는 True로 설정하여 SQL 쿼리 로깅
)

# 세션 팩토리 생성
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base 클래스
Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """
    데이터베이스 세션을 생성하고 반환하는 의존성 함수
    
    Yields:
        Session: SQLAlchemy 데이터베이스 세션
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"데이터베이스 세션 오류: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def create_tables():
    """
    모든 테이블을 생성합니다.
    """
    try:
        # mail_models에서 모든 모델 임포트
        from ..model.mail_model import (
    MailUser, Mail, MailRecipient, MailAttachment, MailFolder, MailInFolder, MailLog
)
        
        # 테이블 생성
        Base.metadata.create_all(bind=engine)
        logger.info("✅ 메일 데이터베이스 테이블이 성공적으로 생성되었습니다.")
        
    except Exception as e:
        logger.error(f"❌ 테이블 생성 중 오류 발생: {e}")
        raise

def drop_tables():
    """
    모든 테이블을 삭제합니다. (주의: 개발 환경에서만 사용)
    """
    try:
        Base.metadata.drop_all(bind=engine)
        logger.warning("⚠️ 모든 메일 테이블이 삭제되었습니다.")
    except Exception as e:
        logger.error(f"❌ 테이블 삭제 중 오류 발생: {e}")
        raise

def init_default_folders(db, user_uuid: str, org_id: str):
    """
    사용자의 기본 폴더들을 생성합니다.
    
    Args:
        db: 데이터베이스 세션
        user_uuid: 사용자 UUID
        org_id: 조직 ID
    """
    from ..model.mail_model import MailFolder, FolderType
    import uuid
    
    default_folders = [
        {"name": "INBOX", "folder_type": FolderType.INBOX.value, "is_system": True},
        {"name": "SENT", "folder_type": FolderType.SENT.value, "is_system": True},
        {"name": "DRAFT", "folder_type": FolderType.DRAFT.value, "is_system": True},
        {"name": "TRASH", "folder_type": FolderType.TRASH.value, "is_system": True},
    ]
    
    try:
        for folder_data in default_folders:
            # 이미 존재하는지 확인
            existing_folder = db.query(MailFolder).filter(
                MailFolder.user_uuid == user_uuid,
                MailFolder.org_id == org_id,
                MailFolder.folder_type == folder_data["folder_type"]
            ).first()
            
            if not existing_folder:
                folder = MailFolder(
                    folder_uuid=str(uuid.uuid4()),
                    user_uuid=user_uuid,
                    org_id=org_id,
                    name=folder_data["name"],
                    folder_type=folder_data["folder_type"],
                    is_system=folder_data["is_system"]
                )
                db.add(folder)
        
        db.commit()
        logger.info(f"✅ 사용자 {user_uuid}의 기본 폴더가 생성되었습니다.")
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ 기본 폴더 생성 중 오류 발생: {e}")
        raise

def check_database_connection() -> bool:
    """
    데이터베이스 연결 상태를 확인합니다.
    
    Returns:
        bool: 연결 성공 여부
    """
    try:
        with engine.connect() as connection:
            connection.execute("SELECT 1")
        logger.info("✅ 데이터베이스 연결이 성공했습니다.")
        return True
    except Exception as e:
        logger.error(f"❌ 데이터베이스 연결 실패: {e}")
        return False

def get_database_info() -> dict:
    """
    데이터베이스 정보를 반환합니다.
    
    Returns:
        dict: 데이터베이스 정보
    """
    try:
        with engine.connect() as connection:
            # PostgreSQL 버전 확인
            result = connection.execute("SELECT version()")
            version = result.fetchone()[0]
            
            # 현재 데이터베이스명 확인
            result = connection.execute("SELECT current_database()")
            database_name = result.fetchone()[0]
            
            # 테이블 수 확인
            result = connection.execute(
                "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public'"
            )
            table_count = result.fetchone()[0]
            
        return {
            "database_url": DATABASE_URL.replace(":safe70!!", ":****"),  # 비밀번호 마스킹
            "database_name": database_name,
            "version": version,
            "table_count": table_count,
            "connection_status": "connected"
        }
    except Exception as e:
        logger.error(f"❌ 데이터베이스 정보 조회 실패: {e}")
        return {
            "database_url": DATABASE_URL.replace(":safe70!!", ":****"),
            "connection_status": "failed",
            "error": str(e)
        }

if __name__ == "__main__":
    # 직접 실행 시 테이블 생성
    print("메일 데이터베이스 초기화를 시작합니다...")
    
    # 연결 확인
    if check_database_connection():
        print("데이터베이스 연결 성공!")
        
        # 테이블 생성
        create_tables()
        print("테이블 생성 완료!")
        
        # 데이터베이스 정보 출력
        info = get_database_info()
        print(f"데이터베이스 정보: {info}")
    else:
        print("데이터베이스 연결 실패!")