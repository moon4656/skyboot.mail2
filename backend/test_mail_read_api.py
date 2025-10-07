#!/usr/bin/env python3
"""
메일 읽음 처리 API 테스트 스크립트
특정 메일의 읽음 상태를 변경하고 데이터베이스 변화를 확인
"""

import requests
import json
import sys
import os
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.config import SaaSSettings

# 테스트 설정
BASE_URL = "http://localhost:8001"
API_BASE = f"{BASE_URL}/api/v1"

# 테스트 대상 메일
MAIL_UUID = '20251005_235140_009e55f6a7f6'

# 테스트 사용자 (메일 수신자)
TEST_USER = {
    "user_id": "user01",
    "password": "test"
}

def login_user(user_id, password):
    """사용자 로그인을 수행합니다."""
    try:
        print(f"🔐 로그인 시도: {user_id}")
        response = requests.post(
            f"{API_BASE}/auth/login",
            json={"user_id": user_id, "password": password},
            headers={"Content-Type": "application/json"}
        )
        
        print(f"📡 응답 상태 코드: {response.status_code}")
        print(f"📡 응답 내용: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            if token:
                print(f"✅ 로그인 성공: 토큰 획득")
                return token
            else:
                print(f"❌ 응답에 토큰이 없습니다: {data}")
                return None
        else:
            print(f"❌ {user_id} 로그인 실패: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ {user_id} 로그인 실패: {str(e)}")
        return None

def check_mail_read_status_db(mail_uuid):
    """데이터베이스에서 메일 읽음 상태 확인"""
    try:
        settings = SaaSSettings()
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()
        
        query = text("""
            SELECT 
                mif.user_uuid,
                mu.email as user_email,
                mif.is_read,
                mif.read_at,
                f.name as folder_name
            FROM mail_in_folders mif
            JOIN mail_users mu ON mif.user_uuid = mu.user_uuid
            JOIN mail_folders f ON mif.folder_uuid = f.folder_uuid
            WHERE mif.mail_uuid = :mail_uuid
            ORDER BY mu.email, f.name
        """)
        
        results = session.execute(query, {"mail_uuid": mail_uuid}).fetchall()
        session.close()
        
        return results
        
    except Exception as e:
        print(f"❌ 데이터베이스 조회 오류: {str(e)}")
        return []

def mark_mail_as_read(token, mail_uuid):
    """메일 읽음 처리 API 호출"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.post(f"{API_BASE}/mail/{mail_uuid}/read", headers=headers)
        
        print(f"📊 읽음 처리 API 응답:")
        print(f"   상태 코드: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   응답 내용: {json.dumps(result, indent=2, ensure_ascii=False)}")
            return result.get("success", False)
        else:
            print(f"   오류 응답: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ API 호출 오류: {str(e)}")
        return False

def mark_mail_as_unread(token, mail_uuid):
    """메일 읽지 않음 처리 API 호출"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.post(f"{API_BASE}/mail/{mail_uuid}/unread", headers=headers)
        
        print(f"📊 읽지 않음 처리 API 응답:")
        print(f"   상태 코드: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   응답 내용: {json.dumps(result, indent=2, ensure_ascii=False)}")
            return result.get("success", False)
        else:
            print(f"   오류 응답: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ API 호출 오류: {str(e)}")
        return False

def print_db_status(mail_uuid, title):
    """데이터베이스 상태 출력"""
    print(f"\n{title}")
    print("-" * 50)
    
    results = check_mail_read_status_db(mail_uuid)
    
    if results:
        for result in results:
            print(f"   사용자: {result.user_email}")
            print(f"   폴더: {result.folder_name}")
            print(f"   읽음 상태: {'읽음' if result.is_read else '읽지 않음'}")
            print(f"   읽은 시간: {result.read_at or '읽지 않음'}")
            print()
    else:
        print("   ❌ 데이터를 찾을 수 없습니다!")

def main():
    """메인 테스트 함수"""
    print("🔍 메일 읽음 처리 API 테스트 시작")
    print("=" * 60)
    print(f"시작 시간: {datetime.now()}")
    print(f"대상 메일: {MAIL_UUID}")
    print()
    
    # 1. 초기 상태 확인
    print_db_status(MAIL_UUID, "1️⃣ 초기 데이터베이스 상태")
    
    # 2. 사용자 로그인
    print("2️⃣ 사용자 로그인")
    print("-" * 50)
    token = login_user(TEST_USER["user_id"], TEST_USER["password"])
    
    if not token:
        print("❌ 로그인 실패로 테스트를 중단합니다.")
        return
    
    # 3. 메일 읽음 처리
    print("\n3️⃣ 메일 읽음 처리 API 호출")
    print("-" * 50)
    read_success = mark_mail_as_read(token, MAIL_UUID)
    
    # 4. 읽음 처리 후 상태 확인
    print_db_status(MAIL_UUID, "4️⃣ 읽음 처리 후 데이터베이스 상태")
    
    # 5. 메일 읽지 않음 처리
    print("5️⃣ 메일 읽지 않음 처리 API 호출")
    print("-" * 50)
    unread_success = mark_mail_as_unread(token, MAIL_UUID)
    
    # 6. 읽지 않음 처리 후 상태 확인
    print_db_status(MAIL_UUID, "6️⃣ 읽지 않음 처리 후 데이터베이스 상태")
    
    # 7. 결과 요약
    print("7️⃣ 테스트 결과 요약")
    print("-" * 50)
    print(f"   읽음 처리 API: {'성공' if read_success else '실패'}")
    print(f"   읽지 않음 처리 API: {'성공' if unread_success else '실패'}")
    
    print()
    print("🏁 테스트 완료")
    print("=" * 60)
    print(f"종료 시간: {datetime.now()}")

if __name__ == "__main__":
    main()