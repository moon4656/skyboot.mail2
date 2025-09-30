#!/usr/bin/env python3
"""
경성 조직과 moonsoo 사용자 생성 및 외부 메일 발송 스크립트

이 스크립트는 다음 작업을 수행합니다:
1. 경성대학교 조직 생성
2. moonsoo@kyungsung.ac.kr 사용자 생성
3. 메일 계정 및 폴더 설정
4. moon4656@gmail.com으로 테스트 메일 발송
"""

import asyncio
import sys
import os
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import requests
import json

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
import bcrypt

# 데이터베이스 설정
DATABASE_URL = "postgresql://skyboot_user:skyboot_password@localhost:5432/skyboot_mail"
API_BASE_URL = "http://localhost:8000"

def get_db_session():
    """데이터베이스 세션을 생성합니다."""
    engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()

def create_kyungsung_organization() -> Optional[int]:
    """
    경성대학교 조직을 생성합니다.
    
    Returns:
        생성된 조직의 ID, 이미 존재하면 기존 조직 ID
    """
    print("📋 경성대학교 조직 생성 중...")
    
    db = get_db_session()
    try:
        # 기존 조직 확인
        result = db.execute(text("""
            SELECT id FROM organizations 
            WHERE name = '경성대학교' OR org_code = 'KYUNGSUNG' OR domain = 'kyungsung.ac.kr'
        """))
        existing_org = result.fetchone()
        
        if existing_org:
            org_id = existing_org[0]
            print(f"✅ 경성대학교 조직이 이미 존재합니다. (ID: {org_id})")
            return org_id
        
        # 새 조직 생성
        org_uuid = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc)
        
        db.execute(text("""
            INSERT INTO organizations (
                org_uuid, name, org_code, subdomain, domain, description,
                max_users, max_storage_gb, is_active, created_at, updated_at
            ) VALUES (
                :org_uuid, :name, :org_code, :subdomain, :domain, :description,
                :max_users, :max_storage_gb, :is_active, :created_at, :updated_at
            )
        """), {
            "org_uuid": org_uuid,
            "name": "경성대학교",
            "org_code": "KYUNGSUNG",
            "subdomain": "kyungsung",
            "domain": "kyungsung.ac.kr",
            "description": "경성대학교 메일 시스템",
            "max_users": 1000,
            "max_storage_gb": 100,
            "is_active": True,
            "created_at": created_at,
            "updated_at": created_at
        })
        
        # 생성된 조직 ID 조회
        result = db.execute(text("SELECT id FROM organizations WHERE org_uuid = :org_uuid"), 
                          {"org_uuid": org_uuid})
        org_id = result.fetchone()[0]
        
        db.commit()
        print(f"✅ 경성대학교 조직이 성공적으로 생성되었습니다. (ID: {org_id})")
        return org_id
        
    except Exception as e:
        db.rollback()
        print(f"❌ 조직 생성 중 오류 발생: {e}")
        return None
    finally:
        db.close()

def create_moonsoo_user(organization_id: int) -> Optional[int]:
    """
    moonsoo 사용자를 생성합니다.
    
    Args:
        organization_id: 조직 ID
        
    Returns:
        생성된 사용자의 ID, 이미 존재하면 기존 사용자 ID
    """
    print("👤 moonsoo 사용자 생성 중...")
    
    db = get_db_session()
    try:
        # 기존 사용자 확인
        result = db.execute(text("""
            SELECT id FROM users 
            WHERE email = 'moonsoo@kyungsung.ac.kr' OR username = 'moonsoo'
        """))
        existing_user = result.fetchone()
        
        if existing_user:
            user_id = existing_user[0]
            print(f"✅ moonsoo 사용자가 이미 존재합니다. (ID: {user_id})")
            
            # 비밀번호 업데이트
            password_hash = bcrypt.hashpw("test123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            db.execute(text("""
                UPDATE users SET password_hash = :password_hash, updated_at = :updated_at
                WHERE id = :user_id
            """), {
                "password_hash": password_hash,
                "updated_at": datetime.now(timezone.utc),
                "user_id": user_id
            })
            db.commit()
            print("✅ 사용자 비밀번호가 업데이트되었습니다.")
            return user_id
        
        # 새 사용자 생성
        user_uuid = str(uuid.uuid4())
        password_hash = bcrypt.hashpw("test123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        created_at = datetime.now(timezone.utc)
        
        db.execute(text("""
            INSERT INTO users (
                user_uuid, username, email, password_hash, full_name,
                organization_id, role, is_active, is_verified,
                created_at, updated_at
            ) VALUES (
                :user_uuid, :username, :email, :password_hash, :full_name,
                :organization_id, :role, :is_active, :is_verified,
                :created_at, :updated_at
            )
        """), {
            "user_uuid": user_uuid,
            "username": "moonsoo",
            "email": "moonsoo@kyungsung.ac.kr",
            "password_hash": password_hash,
            "full_name": "문수",
            "organization_id": organization_id,
            "role": "user",
            "is_active": True,
            "is_verified": True,
            "created_at": created_at,
            "updated_at": created_at
        })
        
        # 생성된 사용자 ID 조회
        result = db.execute(text("SELECT id FROM users WHERE user_uuid = :user_uuid"), 
                          {"user_uuid": user_uuid})
        user_id = result.fetchone()[0]
        
        db.commit()
        print(f"✅ moonsoo 사용자가 성공적으로 생성되었습니다. (ID: {user_id})")
        return user_id
        
    except Exception as e:
        db.rollback()
        print(f"❌ 사용자 생성 중 오류 발생: {e}")
        return None
    finally:
        db.close()

def create_mail_user_and_folders(user_id: int, organization_id: int) -> bool:
    """
    메일 사용자와 기본 폴더를 생성합니다.
    
    Args:
        user_id: 사용자 ID
        organization_id: 조직 ID
        
    Returns:
        성공 여부
    """
    print("📧 메일 계정 및 폴더 설정 중...")
    
    db = get_db_session()
    try:
        # 메일 사용자 생성
        result = db.execute(text("""
            SELECT id FROM mail_users WHERE user_id = :user_id
        """), {"user_id": user_id})
        existing_mail_user = result.fetchone()
        
        if not existing_mail_user:
            mail_user_uuid = str(uuid.uuid4())
            created_at = datetime.now(timezone.utc)
            
            db.execute(text("""
                INSERT INTO mail_users (
                    mail_user_uuid, user_id, organization_id, email,
                    quota_mb, used_storage_mb, is_active, created_at, updated_at
                ) VALUES (
                    :mail_user_uuid, :user_id, :organization_id, :email,
                    :quota_mb, :used_storage_mb, :is_active, :created_at, :updated_at
                )
            """), {
                "mail_user_uuid": mail_user_uuid,
                "user_id": user_id,
                "organization_id": organization_id,
                "email": "moonsoo@kyungsung.ac.kr",
                "quota_mb": 1024,
                "used_storage_mb": 0,
                "is_active": True,
                "created_at": created_at,
                "updated_at": created_at
            })
            
            # 메일 사용자 ID 조회
            result = db.execute(text("SELECT id FROM mail_users WHERE mail_user_uuid = :mail_user_uuid"), 
                              {"mail_user_uuid": mail_user_uuid})
            mail_user_id = result.fetchone()[0]
            print(f"✅ 메일 사용자가 생성되었습니다. (ID: {mail_user_id})")
        else:
            mail_user_id = existing_mail_user[0]
            print(f"✅ 메일 사용자가 이미 존재합니다. (ID: {mail_user_id})")
        
        # 기본 폴더 생성
        default_folders = [
            ("Inbox", "받은편지함", "inbox"),
            ("Sent", "보낸편지함", "sent"),
            ("Draft", "임시보관함", "draft"),
            ("Trash", "휴지통", "trash")
        ]
        
        for folder_name, folder_name_kr, folder_type in default_folders:
            result = db.execute(text("""
                SELECT id FROM mail_folders 
                WHERE mail_user_id = :mail_user_id AND folder_type = :folder_type
            """), {"mail_user_id": mail_user_id, "folder_type": folder_type})
            
            if not result.fetchone():
                folder_uuid = str(uuid.uuid4())
                db.execute(text("""
                    INSERT INTO mail_folders (
                        folder_uuid, mail_user_id, organization_id, folder_name,
                        folder_name_kr, folder_type, is_system, is_active,
                        created_at, updated_at
                    ) VALUES (
                        :folder_uuid, :mail_user_id, :organization_id, :folder_name,
                        :folder_name_kr, :folder_type, :is_system, :is_active,
                        :created_at, :updated_at
                    )
                """), {
                    "folder_uuid": folder_uuid,
                    "mail_user_id": mail_user_id,
                    "organization_id": organization_id,
                    "folder_name": folder_name,
                    "folder_name_kr": folder_name_kr,
                    "folder_type": folder_type,
                    "is_system": True,
                    "is_active": True,
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc)
                })
                print(f"✅ {folder_name_kr} 폴더가 생성되었습니다.")
        
        db.commit()
        print("✅ 메일 계정 설정이 완료되었습니다.")
        return True
        
    except Exception as e:
        db.rollback()
        print(f"❌ 메일 계정 설정 중 오류 발생: {e}")
        return False
    finally:
        db.close()

def login_and_get_token() -> Optional[str]:
    """
    moonsoo 사용자로 로그인하여 액세스 토큰을 획득합니다.
    
    Returns:
        액세스 토큰 또는 None
    """
    print("🔐 moonsoo 사용자 로그인 중...")
    
    try:
        login_data = {
            "username": "moonsoo@kyungsung.ac.kr",
            "password": "test123"
        }
        
        response = requests.post(
            f"{API_BASE_URL}/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get("access_token")
            print("✅ 로그인 성공!")
            return access_token
        else:
            print(f"❌ 로그인 실패: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 로그인 중 오류 발생: {e}")
        return None

def send_test_email(access_token: str) -> bool:
    """
    moon4656@gmail.com으로 테스트 메일을 발송합니다.
    
    Args:
        access_token: 인증 토큰
        
    Returns:
        발송 성공 여부
    """
    print("📤 테스트 메일 발송 중...")
    
    try:
        mail_data = {
            "recipients": ["moon4656@gmail.com"],
            "subject": "경성대학교 메일 시스템 테스트",
            "content": """안녕하세요!

이것은 경성대학교 SkyBoot Mail 시스템에서 발송하는 테스트 메일입니다.

발송자: moonsoo@kyungsung.ac.kr
시스템: SkyBoot Mail SaaS
조직: 경성대학교

메일 시스템이 정상적으로 작동하고 있습니다.

감사합니다.
""",
            "content_type": "text",
            "priority": "normal"
        }
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            f"{API_BASE_URL}/mail/send",
            json=mail_data,
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 테스트 메일이 성공적으로 발송되었습니다!")
            print(f"📧 메일 ID: {result.get('mail_id', 'N/A')}")
            return True
        else:
            print(f"❌ 메일 발송 실패: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 메일 발송 중 오류 발생: {e}")
        return False

def main():
    """메인 실행 함수"""
    print("🚀 경성대학교 조직 및 moonsoo 사용자 설정 시작")
    print("=" * 60)
    
    # 1. 경성대학교 조직 생성
    org_id = create_kyungsung_organization()
    if not org_id:
        print("❌ 조직 생성에 실패했습니다. 프로그램을 종료합니다.")
        return
    
    # 2. moonsoo 사용자 생성
    user_id = create_moonsoo_user(org_id)
    if not user_id:
        print("❌ 사용자 생성에 실패했습니다. 프로그램을 종료합니다.")
        return
    
    # 3. 메일 계정 및 폴더 설정
    if not create_mail_user_and_folders(user_id, org_id):
        print("❌ 메일 계정 설정에 실패했습니다. 프로그램을 종료합니다.")
        return
    
    # 4. 로그인 및 토큰 획득
    access_token = login_and_get_token()
    if not access_token:
        print("❌ 로그인에 실패했습니다. 프로그램을 종료합니다.")
        return
    
    # 5. 테스트 메일 발송
    if send_test_email(access_token):
        print("\n🎉 모든 작업이 성공적으로 완료되었습니다!")
        print("📧 moon4656@gmail.com으로 테스트 메일이 발송되었습니다.")
    else:
        print("\n⚠️ 메일 발송에 실패했습니다.")
    
    print("=" * 60)
    print("✅ 프로그램 실행 완료")

if __name__ == "__main__":
    main()