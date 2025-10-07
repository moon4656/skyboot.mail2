#!/usr/bin/env python3
"""
MailUser 정보 확인 스크립트
"""

import requests
import json
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

def check_mail_user_data():
    """MailUser 테이블 데이터 확인"""
    print("🔍 MailUser 테이블 데이터 확인 중...")
    
    db = SessionLocal()
    try:
        # 모든 MailUser 조회
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
            ORDER BY created_at DESC
        """))
        
        mail_users = result.fetchall()
        
        if mail_users:
            print(f"📊 총 {len(mail_users)}개의 MailUser 발견:")
            for user in mail_users:
                print(f"  - user_id: {user.user_id}")
                print(f"    user_uuid: {user.user_uuid}")
                print(f"    org_id: {user.org_id}")
                print(f"    email: {user.email}")
                print(f"    display_name: {user.display_name}")
                print(f"    is_active: {user.is_active}")
                print(f"    created_at: {user.created_at}")
                print("    ---")
        else:
            print("❌ MailUser 테이블에 데이터가 없습니다!")
            
        # 일반 User 테이블도 확인
        print("\n🔍 User 테이블 데이터 확인 중...")
        result = db.execute(text("""
            SELECT 
                user_id,
                email,
                org_id,
                is_active,
                created_at
            FROM users 
            ORDER BY created_at DESC
            LIMIT 5
        """))
        
        users = result.fetchall()
        
        if users:
            print(f"📊 User 테이블에서 최근 {len(users)}개 사용자:")
            for user in users:
                print(f"  - user_id: {user.user_id}")
                print(f"    email: {user.email}")
                print(f"    org_id: {user.org_id}")
                print(f"    is_active: {user.is_active}")
                print(f"    created_at: {user.created_at}")
                print("    ---")
        else:
            print("❌ User 테이블에 데이터가 없습니다!")
            
    except Exception as e:
        print(f"❌ 데이터베이스 조회 오류: {str(e)}")
    finally:
        db.close()

def create_mail_user_for_existing_user():
    """기존 사용자를 위한 MailUser 생성"""
    print("\n🔧 기존 사용자를 위한 MailUser 생성 중...")
    
    db = SessionLocal()
    try:
        # 기존 사용자 중 MailUser가 없는 사용자 찾기
        result = db.execute(text("""
            SELECT u.user_id, u.email, u.org_id
            FROM users u
            LEFT JOIN mail_users mu ON u.user_id = mu.user_id
            WHERE mu.user_id IS NULL
            AND u.is_active = true
            LIMIT 5
        """))
        
        users_without_mail_user = result.fetchall()
        
        if users_without_mail_user:
            print(f"📊 MailUser가 없는 사용자 {len(users_without_mail_user)}명 발견:")
            
            for user in users_without_mail_user:
                print(f"  - {user.email} (user_id: {user.user_id}, org_id: {user.org_id})")
                
                # MailUser 생성
                import uuid
                user_uuid = str(uuid.uuid4())
                
                db.execute(text("""
                    INSERT INTO mail_users (
                        user_id, user_uuid, org_id, email, 
                        password_hash, display_name, is_active, 
                        created_at, updated_at
                    ) VALUES (
                        :user_id, :user_uuid, :org_id, :email,
                        'temp_hash', :display_name, true,
                        NOW(), NOW()
                    )
                """), {
                    'user_id': user.user_id,
                    'user_uuid': user_uuid,
                    'org_id': user.org_id,
                    'email': user.email,
                    'display_name': user.email.split('@')[0]
                })
                
                print(f"    ✅ MailUser 생성 완료 (UUID: {user_uuid})")
            
            db.commit()
            print(f"🎉 총 {len(users_without_mail_user)}명의 MailUser 생성 완료!")
        else:
            print("✅ 모든 사용자가 이미 MailUser를 가지고 있습니다.")
            
    except Exception as e:
        db.rollback()
        print(f"❌ MailUser 생성 오류: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    print("🔧 MailUser 정보 확인 및 생성 스크립트")
    print("=" * 50)
    
    # 1. 현재 MailUser 데이터 확인
    check_mail_user_data()
    
    # 2. 필요시 MailUser 생성
    create_mail_user_for_existing_user()
    
    # 3. 생성 후 다시 확인
    print("\n" + "=" * 50)
    print("🔍 생성 후 MailUser 데이터 재확인:")
    check_mail_user_data()
    
    print("\n✅ 스크립트 완료!")