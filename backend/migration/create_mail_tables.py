#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
메일 시스템 테이블 생성 스크립트

mail_models.py에 정의된 모든 테이블을 데이터베이스에 생성합니다.
"""

import sys
import os
from pathlib import Path

# backend 폴더를 sys.path에 추가
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import logging

# app.model에서 Base와 모든 모델 클래스 import
from app.database.base import Base
from app.model.mail_model import MailUser, Mail, MailRecipient, MailAttachment, MailFolder, MailInFolder, MailLog
from app.model.base_model import User, RefreshToken

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('create_tables.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# 데이터베이스 연결 설정
DATABASE_URL = os.getenv(
    "MAIL_DATABASE_URL",
    "postgresql://postgres:safe70!!@localhost:5432/skyboot.mail"
)

def check_database_connection(engine):
    """
    데이터베이스 연결을 확인합니다.
    
    Args:
        engine: SQLAlchemy 엔진 객체
        
    Returns:
        bool: 연결 성공 여부
    """
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            logger.info("✅ 데이터베이스 연결이 성공했습니다.")
            return True
    except Exception as e:
        logger.error(f"❌ 데이터베이스 연결 실패: {e}")
        return False

def get_existing_tables(engine):
    """
    기존 테이블 목록을 조회합니다.
    
    Args:
        engine: SQLAlchemy 엔진 객체
        
    Returns:
        list: 기존 테이블 이름 목록
    """
    try:
        with engine.connect() as connection:
            result = connection.execute(text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public'"
            ))
            tables = [row[0] for row in result.fetchall()]
            return tables
    except Exception as e:
        logger.error(f"❌ 기존 테이블 조회 실패: {e}")
        return []

def create_tables(engine):
    """
    모든 테이블을 생성합니다.
    
    Args:
        engine: SQLAlchemy 엔진 객체
        
    Returns:
        bool: 테이블 생성 성공 여부
    """
    try:
        logger.info("📋 테이블 생성을 시작합니다...")
        
        # 기존 테이블 확인
        existing_tables = get_existing_tables(engine)
        logger.info(f"기존 테이블: {existing_tables}")
        
        # 생성할 테이블 목록
        tables_to_create = [
            'mail_users', 'mails', 'mail_recipients', 'mail_attachments',
            'mail_folders', 'mail_in_folders', 'mail_logs', 'users', 'refresh_tokens'
        ]
        
        # 모든 테이블 생성
        Base.metadata.create_all(bind=engine)
        
        # 생성된 테이블 확인
        new_tables = get_existing_tables(engine)
        created_tables = [table for table in tables_to_create if table in new_tables]
        
        logger.info(f"✅ 테이블 생성 완료! 생성된 테이블: {created_tables}")
        
        # 각 테이블의 컬럼 정보 출력
        with engine.connect() as connection:
            for table in created_tables:
                logger.info(f"\n📋 {table} 테이블 구조:")
                result = connection.execute(text(f"""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_name = '{table}'
                    ORDER BY ordinal_position
                """))
                
                for row in result.fetchall():
                    column_name, data_type, is_nullable, column_default = row
                    nullable = "NULL" if is_nullable == "YES" else "NOT NULL"
                    default = f" DEFAULT {column_default}" if column_default else ""
                    logger.info(f"  - {column_name}: {data_type} {nullable}{default}")
        
        return True
        
    except SQLAlchemyError as e:
        logger.error(f"❌ 테이블 생성 중 SQLAlchemy 오류 발생: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ 테이블 생성 중 예상치 못한 오류 발생: {e}")
        return False

def create_default_folders(engine):
    """
    기본 메일 폴더를 생성합니다.
    
    Args:
        engine: SQLAlchemy 엔진 객체
    """
    try:
        from sqlalchemy.orm import sessionmaker
        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # 기본 폴더 데이터
        default_folders = [
            {"name": "받은편지함", "folder_type": "inbox", "is_system": True},
            {"name": "보낸편지함", "folder_type": "sent", "is_system": True},
            {"name": "임시보관함", "folder_type": "draft", "is_system": True},
            {"name": "휴지통", "folder_type": "trash", "is_system": True},
        ]
        
        # 시스템 사용자 생성 (폴더 생성용)
        system_user = db.query(MailUser).filter(MailUser.email == "system@skyboot.local").first()
        if not system_user:
            system_user = MailUser(
                email="system@skyboot.local",
                password_hash="system",
                display_name="시스템",
                is_active=True
            )
            db.add(system_user)
            db.commit()
            db.refresh(system_user)
            logger.info("✅ 시스템 사용자가 생성되었습니다.")
        
        # 기본 폴더 생성
        for folder_data in default_folders:
            existing_folder = db.query(MailFolder).filter(
                MailFolder.user_id == system_user.id,
                MailFolder.folder_type == folder_data["folder_type"]
            ).first()
            
            if not existing_folder:
                folder = MailFolder(
                    user_id=system_user.id,
                    name=folder_data["name"],
                    folder_type=folder_data["folder_type"],
                    is_system=folder_data["is_system"]
                )
                db.add(folder)
                logger.info(f"✅ '{folder_data['name']}' 폴더가 생성되었습니다.")
        
        db.commit()
        db.close()
        
        logger.info("✅ 기본 폴더 생성이 완료되었습니다.")
        
    except Exception as e:
        logger.error(f"❌ 기본 폴더 생성 실패: {e}")
        if 'db' in locals():
            db.rollback()
            db.close()

def main():
    """
    메인 실행 함수
    """
    logger.info("🚀 메일 시스템 테이블 생성을 시작합니다...")
    logger.info(f"데이터베이스 URL: {DATABASE_URL.replace(':safe70!!', ':****')}")
    
    try:
        # SQLAlchemy 엔진 생성
        engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            pool_recycle=300,
            echo=False  # SQL 쿼리 로깅 (필요시 True로 변경)
        )
        
        # 데이터베이스 연결 확인
        if not check_database_connection(engine):
            logger.error("❌ 데이터베이스 연결에 실패했습니다. 프로그램을 종료합니다.")
            return False
        
        # 테이블 생성
        if create_tables(engine):
            logger.info("✅ 모든 테이블이 성공적으로 생성되었습니다!")
            
            # 기본 폴더 생성
            create_default_folders(engine)
            
            logger.info("🎉 메일 시스템 초기화가 완료되었습니다!")
            return True
        else:
            logger.error("❌ 테이블 생성에 실패했습니다.")
            return False
            
    except Exception as e:
        logger.error(f"❌ 프로그램 실행 중 오류 발생: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ 메일 시스템 테이블 생성이 성공적으로 완료되었습니다!")
        print("📋 생성된 테이블:")
        print("  - mail_users (메일 사용자)")
        print("  - mails (메일)")
        print("  - mail_recipients (메일 수신자)")
        print("  - mail_attachments (메일 첨부파일)")
        print("  - mail_folders (메일 폴더)")
        print("  - mail_in_folders (메일-폴더 관계)")
        print("  - mail_logs (메일 로그)")
        print("\n🎯 다음 단계: 메일 API 서버를 시작하세요!")
    else:
        print("\n❌ 테이블 생성에 실패했습니다. 로그를 확인해주세요.")
        sys.exit(1)