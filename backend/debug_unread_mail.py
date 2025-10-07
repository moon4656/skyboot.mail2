#!/usr/bin/env python3
"""
읽지 않은 메일 조회 기능 디버깅 스크립트

user01/test 계정으로 읽지 않은 메일 조회 기능을 테스트하고 문제점을 파악합니다.
"""
import requests
import json
import time
from datetime import datetime
import sys
import os

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.config import settings

# 설정
BASE_URL = "http://localhost:8001/api/v1"
TEST_USER = {
    "user_id": "user01",
    "password": "test"
}

def get_db_session():
    """데이터베이스 세션 생성"""
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()

def login_user():
    """사용자 로그인"""
    print("=== 1. 사용자 로그인 ===")
    login_data = {
        "user_id": TEST_USER["user_id"],
        "password": TEST_USER["password"]
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    print(f"로그인 상태: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"로그인 응답: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        # 직접 access_token이 반환되는 구조
        if "access_token" in result:
            access_token = result["access_token"]
            print(f"✅ 로그인 성공")
            return access_token
        else:
            print(f"❌ 로그인 실패: access_token이 응답에 없습니다.")
            return None
    else:
        print(f"❌ 로그인 실패: {response.text}")
        return None

def get_user_info(headers):
    """사용자 정보 조회"""
    print("\n=== 2. 사용자 정보 조회 ===")
    response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    print(f"사용자 정보 조회 상태: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"사용자 정보: {result}")
        return result
    else:
        print(f"❌ 사용자 정보 조회 실패: {response.text}")
        return None

def check_database_structure():
    """데이터베이스 구조 확인"""
    print("\n=== 3. 데이터베이스 구조 확인 ===")
    
    try:
        db = get_db_session()
        
        # 1. MailInFolder 테이블의 전체 구조 확인
        print("📋 MailInFolder 테이블 전체 구조 확인:")
        result = db.execute(text("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'mail_in_folders' 
            ORDER BY ordinal_position;
        """))
        
        columns = result.fetchall()
        for col in columns:
            print(f"  - {col[0]}: {col[1]} (nullable: {col[2]})")
        
        # 2. Mail 테이블의 read_at 필드 확인
        print("\n📋 Mail 테이블 구조 확인:")
        result = db.execute(text("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'mails' 
            AND column_name = 'read_at'
            ORDER BY column_name;
        """))
        
        columns = result.fetchall()
        for col in columns:
            print(f"  - {col[0]}: {col[1]} (nullable: {col[2]})")
        
        # 3. 전체 메일 데이터 확인 (모든 사용자)
        print("\n📋 전체 메일 데이터 확인:")
        result = db.execute(text("""
            SELECT 
                m.mail_uuid,
                m.subject,
                m.status,
                mif.is_read as folder_is_read,
                mif.read_at as folder_read_at,
                mu.email as user_email,
                mu.user_id
            FROM mails m
            LEFT JOIN mail_in_folders mif ON m.mail_uuid = mif.mail_uuid
            LEFT JOIN mail_users mu ON mif.user_uuid = mu.user_uuid
            ORDER BY m.created_at DESC
            LIMIT 20;
        """))
        
        mails = result.fetchall()
        print(f"  총 {len(mails)}개의 메일 발견:")
        for mail in mails:
            print(f"    - {mail[1]} | 상태: {mail[2]} | Folder.is_read: {mail[3]} | Folder.read_at: {mail[4]} | 사용자: {mail[5]} ({mail[6]})")
        
        # 4. user01 관련 데이터 확인 (컬럼명 수정)
        print("\n📋 user01 관련 데이터 확인:")
        result = db.execute(text("""
            SELECT user_uuid, email, user_id, is_active
            FROM mail_users 
            WHERE email LIKE '%user01%' OR user_id LIKE '%user01%'
            ORDER BY created_at DESC;
        """))
        
        users = result.fetchall()
        print(f"  user01 관련 사용자 {len(users)}명 발견:")
        for user in users:
            print(f"    - UUID: {user[0]} | 이메일: {user[1]} | ID: {user[2]} | 활성: {user[3]}")
            
        # 5. 특정 사용자의 메일함 확인 (실제 컬럼명 사용)
        if users:
            user_uuid = users[0][0]
            print(f"\n📋 {users[0][1]} 사용자의 메일함 확인:")
            result = db.execute(text("""
                SELECT 
                    mif.mail_uuid,
                    mif.is_read,
                    mif.read_at,
                    m.subject,
                    m.status
                FROM mail_in_folders mif
                LEFT JOIN mails m ON mif.mail_uuid = m.mail_uuid
                WHERE mif.user_uuid = :user_uuid
                ORDER BY mif.created_at DESC
                LIMIT 10;
            """), {"user_uuid": user_uuid})
            
            folders = result.fetchall()
            print(f"    메일함에 {len(folders)}개의 메일:")
            for folder in folders:
                print(f"      - {folder[3]} | 읽음: {folder[1]} | 읽은시간: {folder[2]} | 상태: {folder[4]}")
                
            # 6. 읽지 않은 메일 개수 확인
            print(f"\n📋 읽지 않은 메일 개수:")
            result = db.execute(text("""
                SELECT COUNT(*) as total_count, 
                       SUM(CASE WHEN is_read = false THEN 1 ELSE 0 END) as unread_count
                FROM mail_in_folders 
                WHERE user_uuid = :user_uuid;
            """), {"user_uuid": user_uuid})
            
            stats = result.fetchone()
            if stats:
                print(f"      - 총 메일: {stats[0]}개, 읽지않음: {stats[1]}개")
        
        db.close()
        
    except Exception as e:
        print(f"❌ 데이터베이스 확인 중 오류: {e}")

def test_unread_mail_api(headers):
    """읽지 않은 메일 API 테스트"""
    print("\n=== 4. 읽지 않은 메일 API 테스트 ===")
    
    response = requests.get(f"{BASE_URL}/mail/unread", headers=headers)
    print(f"읽지 않은 메일 조회 상태: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"API 응답: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        if result.get("success"):
            data = result.get("data", {})
            mails = data.get("mails", [])
            total = data.get("total", 0)
            
            print(f"\n📊 읽지 않은 메일 결과:")
            print(f"  - 총 개수: {total}")
            print(f"  - 조회된 개수: {len(mails)}")
            
            if mails:
                print(f"  📧 메일 목록:")
                for i, mail in enumerate(mails, 1):
                    print(f"    {i}. {mail.get('subject', 'No Subject')}")
                    print(f"       발송자: {mail.get('sender_email', 'Unknown')}")
                    print(f"       읽음상태: {mail.get('is_read', 'Unknown')}")
                    print(f"       생성일: {mail.get('created_at', 'Unknown')}")
            else:
                print("  📭 읽지 않은 메일이 없습니다.")
        else:
            print(f"❌ API 실패: {result.get('message')}")
    else:
        print(f"❌ API 호출 실패: {response.text}")

def test_inbox_api(headers):
    """받은 메일함 API 테스트 (비교용)"""
    print("\n=== 5. 받은 메일함 API 테스트 (비교용) ===")
    
    response = requests.get(f"{BASE_URL}/mail/inbox", headers=headers)
    print(f"받은 메일함 조회 상태: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        mails = result.get("mails", [])
        pagination = result.get("pagination", {})
        
        print(f"📊 받은 메일함 결과:")
        print(f"  - 총 개수: {pagination.get('total', 0)}")
        print(f"  - 조회된 개수: {len(mails)}")
        
        if mails:
            print(f"  📧 메일 목록:")
            for i, mail in enumerate(mails, 1):
                print(f"    {i}. {mail.get('subject', 'No Subject')}")
                sender = mail.get('sender', {})
                print(f"       발송자: {sender.get('email', 'Unknown') if sender else 'Unknown'}")
                print(f"       읽음상태: {mail.get('is_read', 'Unknown')}")
                print(f"       생성일: {mail.get('created_at', 'Unknown')}")
        else:
            print("  📭 받은 메일이 없습니다.")
    else:
        print(f"❌ 받은 메일함 조회 실패: {response.text}")

def main():
    """메인 함수"""
    print("🔍 읽지 않은 메일 조회 기능 디버깅 시작")
    print("=" * 60)
    
    # 1. 로그인
    access_token = login_user()
    if not access_token:
        print("❌ 로그인 실패로 테스트를 중단합니다.")
        return
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # 2. 사용자 정보 조회
    user_info = get_user_info(headers)
    
    # 3. 데이터베이스 구조 확인
    check_database_structure()
    
    # 4. 읽지 않은 메일 API 테스트
    test_unread_mail_api(headers)
    
    # 5. 받은 메일함 API 테스트 (비교용)
    test_inbox_api(headers)
    
    print("\n" + "=" * 60)
    print("🔍 읽지 않은 메일 조회 기능 디버깅 완료")

if __name__ == "__main__":
    main()