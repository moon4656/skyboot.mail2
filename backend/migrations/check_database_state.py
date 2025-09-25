#!/usr/bin/env python3
"""
데이터베이스 상태 확인 스크립트

마이그레이션 전후 데이터베이스 상태를 확인합니다.
"""

import sys
import os

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.config import settings

def check_database_state():
    """
    현재 데이터베이스 상태를 확인합니다.
    """
    print("🔍 데이터베이스 상태 확인")
    print("=" * 50)
    
    # 데이터베이스 연결
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    try:
        # 1. 테이블별 레코드 수 확인
        print("📊 테이블별 레코드 수:")
        
        mail_users = session.execute(text("SELECT COUNT(*) as count FROM mail_users")).fetchone()
        print(f"   - MailUser: {mail_users.count}개")
        
        mail_folders = session.execute(text("SELECT COUNT(*) as count FROM mail_folders")).fetchone()
        print(f"   - MailFolder: {mail_folders.count}개")
        
        mail_recipients = session.execute(text("SELECT COUNT(*) as count FROM mail_recipients")).fetchone()
        print(f"   - MailRecipient: {mail_recipients.count}개")
        
        mails = session.execute(text("SELECT COUNT(*) as count FROM mails")).fetchone()
        print(f"   - Mail: {mails.count}개")
        
        # 2. MailUser 샘플 데이터 확인
        print("\n👤 MailUser 샘플 데이터:")
        sample_users = session.execute(text("""
            SELECT id, email, user_id 
            FROM mail_users 
            LIMIT 5
        """)).fetchall()
        
        for user in sample_users:
            print(f"   - ID: {user.id}, Email: {user.email}, UserID: {user.user_id}")
        
        # 3. MailFolder의 user_id 참조 상태 확인
        print("\n📁 MailFolder user_id 참조 상태:")
        folder_refs = session.execute(text("""
            SELECT 
                COUNT(*) as total_folders,
                COUNT(CASE WHEN mu.user_id IS NOT NULL THEN 1 END) as valid_user_id_refs,
                COUNT(CASE WHEN mu.id IS NOT NULL THEN 1 END) as valid_id_refs
            FROM mail_folders mf
            LEFT JOIN mail_users mu ON mf.user_id = mu.user_id
            LEFT JOIN mail_users mu2 ON mf.user_id = mu2.id::text
        """)).fetchone()
        
        print(f"   - 총 폴더 수: {folder_refs.total_folders}")
        print(f"   - user_id로 매칭되는 폴더: {folder_refs.valid_user_id_refs}")
        print(f"   - id로 매칭되는 폴더: {folder_refs.valid_id_refs}")
        
        # 4. MailRecipient의 recipient_id 참조 상태 확인
        print("\n📧 MailRecipient recipient_id 참조 상태:")
        recipient_refs = session.execute(text("""
            SELECT 
                COUNT(*) as total_recipients,
                COUNT(CASE WHEN mu.user_id IS NOT NULL THEN 1 END) as valid_user_id_refs,
                COUNT(CASE WHEN mu.id IS NOT NULL THEN 1 END) as valid_id_refs
            FROM mail_recipients mr
            LEFT JOIN mail_users mu ON mr.recipient_id = mu.user_id
            LEFT JOIN mail_users mu2 ON mr.recipient_id = mu2.id::text
        """)).fetchone()
        
        print(f"   - 총 수신자 수: {recipient_refs.total_recipients}")
        print(f"   - user_id로 매칭되는 수신자: {recipient_refs.valid_user_id_refs}")
        print(f"   - id로 매칭되는 수신자: {recipient_refs.valid_id_refs}")
        
        # 5. Mail의 sender_uuid 참조 상태 확인
        print("\n✉️ Mail sender_uuid 참조 상태:")
        mail_refs = session.execute(text("""
            SELECT 
                COUNT(*) as total_mails,
                COUNT(CASE WHEN mu.user_id IS NOT NULL THEN 1 END) as valid_user_id_refs,
                COUNT(CASE WHEN mu.id IS NOT NULL THEN 1 END) as valid_id_refs
            FROM mails m
            LEFT JOIN mail_users mu ON m.sender_uuid = mu.user_id
            LEFT JOIN mail_users mu2 ON m.sender_uuid = mu2.id::text
        """)).fetchone()
        
        print(f"   - 총 메일 수: {mail_refs.total_mails}")
        print(f"   - user_id로 매칭되는 메일: {mail_refs.valid_user_id_refs}")
        print(f"   - id로 매칭되는 메일: {mail_refs.valid_id_refs}")
        
        # 6. 마이그레이션 필요성 판단
        print("\n🔍 마이그레이션 필요성 분석:")
        
        needs_folder_migration = folder_refs.valid_id_refs > folder_refs.valid_user_id_refs
        needs_recipient_migration = recipient_refs.valid_id_refs > recipient_refs.valid_user_id_refs
        needs_mail_migration = mail_refs.valid_id_refs > mail_refs.valid_user_id_refs
        
        if needs_folder_migration:
            print("   ⚠️ MailFolder 테이블에 마이그레이션이 필요합니다.")
        else:
            print("   ✅ MailFolder 테이블은 이미 올바른 상태입니다.")
            
        if needs_recipient_migration:
            print("   ⚠️ MailRecipient 테이블에 마이그레이션이 필요합니다.")
        else:
            print("   ✅ MailRecipient 테이블은 이미 올바른 상태입니다.")
            
        if needs_mail_migration:
            print("   ⚠️ Mail 테이블에 마이그레이션이 필요합니다.")
        else:
            print("   ✅ Mail 테이블은 이미 올바른 상태입니다.")
        
        if needs_folder_migration or needs_recipient_migration or needs_mail_migration:
            print("\n🚀 마이그레이션 실행을 권장합니다.")
        else:
            print("\n✅ 모든 테이블이 올바른 상태입니다. 마이그레이션이 필요하지 않습니다.")
        
    except Exception as e:
        print(f"❌ 데이터베이스 상태 확인 중 오류 발생: {e}")
        
    finally:
        session.close()

if __name__ == "__main__":
    check_database_state()
