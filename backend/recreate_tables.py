#!/usr/bin/env python3
"""
데이터베이스 테이블 재생성 스크립트
기존 테이블을 삭제하고 새로운 스키마로 재생성합니다.
"""

import sys
import os
from pathlib import Path

# backend 폴더를 sys.path에 추가
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine, text
from app.model.base_model import Base, User, RefreshToken, LoginLog
from app.model.organization_model import Organization, OrganizationSettings, OrganizationUsage
from app.model.mail_model import MailUser, Mail, MailRecipient, MailAttachment, MailFolder, MailInFolder, MailLog
import logging
import uuid

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def recreate_tables():
    """기존 테이블을 삭제하고 새로운 스키마로 재생성합니다."""
    
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
        
        # 기존 테이블 삭제 (순서 중요 - 외래키 관계 고려)
        logger.info("🗑️ 기존 테이블 삭제 중...")
        
        with engine.connect() as connection:
            # 외래키 제약조건이 있는 테이블부터 삭제
            tables_to_drop = [
                'mail_in_folder',
                'mail_attachments', 
                'mail_recipients',
                'mail_logs',
                'mails',
                'mail_folders',
                'mail_users',
                'login_logs',
                'refresh_tokens',
                'users',
                'organization_usage',
                'organization_settings',
                'organizations'
            ]
            
            for table in tables_to_drop:
                try:
                    connection.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
                    logger.info(f"  ✅ {table} 테이블 삭제 완료")
                except Exception as e:
                    logger.warning(f"  ⚠️ {table} 테이블 삭제 실패 (무시): {e}")
            
            connection.commit()
        
        # 새로운 테이블 생성
        logger.info("🏗️ 새로운 테이블 생성 중...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ 모든 테이블 생성 완료!")
        
        # 기본 조직 생성
        logger.info("🏢 기본 조직 생성 중...")
        
        from sqlalchemy.orm import sessionmaker
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            # 기본 조직 생성
            default_org = Organization(
                org_id=str(uuid.uuid4()),
                org_code="default",
                name="기본 조직",
                domain="localhost",
                subdomain="default",
                admin_email="admin@localhost",
                status="active"
            )
            session.add(default_org)
            session.commit()
            
            logger.info(f"✅ 기본 조직 생성 완료: {default_org.org_id}")
            
            # 기본 조직 설정 생성 (키-값 쌍으로)
            settings_data = [
                ("max_users", "100", "number", "최대 사용자 수"),
                ("max_storage_gb", "10", "number", "최대 저장 용량(GB)"),
                ("features", '{"mail": true, "calendar": false, "contacts": true}', "json", "활성화된 기능"),
                ("theme", "default", "string", "기본 테마"),
                ("timezone", "Asia/Seoul", "string", "시간대")
            ]
            
            for key, value, type_, desc in settings_data:
                setting = OrganizationSettings(
                    org_id=default_org.org_id,
                    setting_key=key,
                    setting_value=value,
                    setting_type=type_,
                    description=desc
                )
                session.add(setting)
            
            # 기본 조직 사용량 생성
            from datetime import datetime
            org_usage = OrganizationUsage(
                org_id=default_org.org_id,
                usage_date=datetime.now(),
                current_users=0,
                current_storage_gb=0,
                emails_sent_today=0,
                emails_received_today=0
            )
            session.add(org_usage)
            
            session.commit()
            logger.info("✅ 기본 조직 설정 및 사용량 생성 완료!")
            
        except Exception as e:
            session.rollback()
            logger.error(f"❌ 기본 조직 생성 실패: {e}")
            raise
        finally:
            session.close()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 테이블 재생성 실패: {e}")
        return False

if __name__ == "__main__":
    success = recreate_tables()
    if success:
        print("\n🎉 테이블 재생성이 완료되었습니다!")
    else:
        print("\n💥 테이블 재생성에 실패했습니다.")
        sys.exit(1)