#!/usr/bin/env python3
"""
누락된 데이터베이스 테이블 생성 스크립트
"""

import sys
import os
from pathlib import Path

# backend 폴더를 sys.path에 추가
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import logging

# app.model에서 Base와 모든 모델 클래스 import
from app.database.base import Base

# 모든 모델 import
from app.model.base_model import User, RefreshToken
from app.model.organization_model import Organization, OrganizationSettings, OrganizationUsage
from app.model.mail_model import MailUser, Mail, MailRecipient, MailAttachment, MailFolder, MailInFolder, MailLog

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_missing_tables():
    """누락된 테이블들을 생성합니다."""
    
    # 환경변수에서 DATABASE_URL 읽기
    database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:safe70%21%21@localhost:5432/skybootmail')
    
    try:
        # 데이터베이스 엔진 생성
        engine = create_engine(database_url, echo=True)
        
        logger.info("🚀 데이터베이스 연결 시도...")
        
        # 연결 테스트
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            logger.info("✅ 데이터베이스 연결 성공!")
        
        # 기존 테이블 확인
        with engine.connect() as connection:
            result = connection.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name
            """))
            existing_tables = [row[0] for row in result.fetchall()]
            logger.info(f"📋 기존 테이블: {existing_tables}")
        
        # 모든 테이블 생성 (이미 존재하는 테이블은 건너뜀)
        logger.info("📊 테이블 생성 시작...")
        Base.metadata.create_all(bind=engine)
        
        # 생성 후 테이블 확인
        with engine.connect() as connection:
            result = connection.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name
            """))
            new_tables = [row[0] for row in result.fetchall()]
            logger.info(f"📋 생성 후 테이블: {new_tables}")
        
        # 새로 생성된 테이블 확인
        created_tables = [table for table in new_tables if table not in existing_tables]
        if created_tables:
            logger.info(f"✅ 새로 생성된 테이블: {created_tables}")
        else:
            logger.info("ℹ️ 새로 생성된 테이블이 없습니다. (모든 테이블이 이미 존재)")
        
        # 기본 조직 생성
        create_default_organization(engine)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 테이블 생성 실패: {e}")
        return False

def create_default_organization(engine):
    """기본 조직을 생성합니다."""
    try:
        from sqlalchemy.orm import sessionmaker
        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # 기본 조직이 이미 존재하는지 확인
        existing_org = db.query(Organization).filter(Organization.org_code == "default").first()
        
        if not existing_org:
            # 기본 조직 생성
            default_org = Organization(
                org_code="default",
                name="기본 조직",
                display_name="기본 조직",
                description="시스템 기본 조직",
                subdomain="default",
                admin_email="admin@skyboot.local",
                admin_name="시스템 관리자",
                status="active",
                is_active=True
            )
            
            db.add(default_org)
            db.commit()
            db.refresh(default_org)
            
            logger.info(f"✅ 기본 조직이 생성되었습니다: {default_org.org_id}")
        else:
            logger.info(f"ℹ️ 기본 조직이 이미 존재합니다: {existing_org.org_id}")
        
        db.close()
        
    except Exception as e:
        logger.error(f"❌ 기본 조직 생성 실패: {e}")

if __name__ == "__main__":
    success = create_missing_tables()
    if success:
        print("\n🎉 테이블 생성이 완료되었습니다!")
    else:
        print("\n💥 테이블 생성에 실패했습니다.")
        sys.exit(1)