#!/usr/bin/env python3
"""
실제 존재하는 사용자 정보 확인 스크립트
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 데이터베이스 연결 설정
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/skyboot_mail")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def check_users():
    """실제 사용자 정보 확인"""
    print("🔍 실제 사용자 정보 확인 중...")
    
    db = SessionLocal()
    try:
        # 모든 사용자 조회 (최근 10명)
        result = db.execute(text("""
            SELECT 
                user_id,
                email,
                org_id,
                is_active,
                created_at
            FROM users 
            WHERE is_active = true
            ORDER BY created_at DESC
            LIMIT 10
        """))
        
        users = result.fetchall()
        
        if users:
            print(f"📊 활성 사용자 {len(users)}명 발견:")
            for i, user in enumerate(users, 1):
                print(f"  {i}. user_id: {user.user_id}")
                print(f"     email: {user.email}")
                print(f"     org_id: {user.org_id}")
                print(f"     is_active: {user.is_active}")
                print(f"     created_at: {user.created_at}")
                print("     ---")
        else:
            print("❌ 활성 사용자가 없습니다!")
            
        # admin 사용자 찾기
        print("\n🔍 admin 사용자 찾기:")
        result = db.execute(text("""
            SELECT 
                user_id,
                email,
                org_id,
                is_active,
                created_at
            FROM users 
            WHERE user_id LIKE '%admin%' OR email LIKE '%admin%'
            ORDER BY created_at DESC
        """))
        
        admin_users = result.fetchall()
        
        if admin_users:
            print(f"📊 admin 사용자 {len(admin_users)}명 발견:")
            for i, user in enumerate(admin_users, 1):
                print(f"  {i}. user_id: {user.user_id}")
                print(f"     email: {user.email}")
                print(f"     org_id: {user.org_id}")
                print(f"     is_active: {user.is_active}")
                print(f"     created_at: {user.created_at}")
                print("     ---")
        else:
            print("❌ admin 사용자가 없습니다!")
            
    except Exception as e:
        print(f"❌ 사용자 확인 오류: {str(e)}")
    finally:
        db.close()

def check_mail_users():
    """MailUser 정보 확인"""
    print("\n🔍 MailUser 정보 확인 중...")
    
    db = SessionLocal()
    try:
        # 모든 MailUser 조회 (최근 10명)
        result = db.execute(text("""
            SELECT 
                user_id,
                user_uuid,
                org_id,
                email,
                display_name,
                is_active,
                created_at
            FROM mail_users 
            WHERE is_active = true
            ORDER BY created_at DESC
            LIMIT 10
        """))
        
        mail_users = result.fetchall()
        
        if mail_users:
            print(f"📊 활성 MailUser {len(mail_users)}명 발견:")
            for i, user in enumerate(mail_users, 1):
                print(f"  {i}. user_id: {user.user_id}")
                print(f"     user_uuid: {user.user_uuid}")
                print(f"     email: {user.email}")
                print(f"     org_id: {user.org_id}")
                print(f"     display_name: {user.display_name}")
                print(f"     is_active: {user.is_active}")
                print(f"     created_at: {user.created_at}")
                print("     ---")
        else:
            print("❌ 활성 MailUser가 없습니다!")
            
    except Exception as e:
        print(f"❌ MailUser 확인 오류: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    print("🔧 실제 사용자 정보 확인 스크립트")
    print("=" * 50)
    
    # 1. 일반 사용자 확인
    check_users()
    
    # 2. MailUser 확인
    check_mail_users()
    
    print("\n✅ 스크립트 완료!")