#!/usr/bin/env python3
"""
user01 사용자의 실제 user_id 확인 스크립트

user01@example.com 사용자의 실제 user_id 값을 확인하고 올바른 로그인 정보로 테스트합니다.
"""
import sys
import os

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.config import settings
import requests

def get_db_session():
    """데이터베이스 세션 생성"""
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()

def check_user01_details():
    """user01 사용자의 상세 정보 확인"""
    print("🔍 user01 사용자 상세 정보 확인")
    print("=" * 60)
    
    try:
        db = get_db_session()
        
        # user01@example.com 사용자의 모든 정보 조회
        print("📋 user01@example.com 사용자 정보:")
        result = db.execute(text("""
            SELECT user_id, user_uuid, org_id, email, username, hashed_password, 
                   role, is_active, created_at
            FROM users
            WHERE email = 'user01@example.com';
        """))
        
        user = result.fetchone()
        if user:
            print(f"  user_id: {user[0]}")
            print(f"  user_uuid: {user[1]}")
            print(f"  org_id: {user[2]}")
            print(f"  email: {user[3]}")
            print(f"  username: {user[4]}")
            print(f"  hashed_password: {user[5][:50]}...")
            print(f"  role: {user[6]}")
            print(f"  is_active: {user[7]}")
            print(f"  created_at: {user[8]}")
            
            # 실제 user_id로 로그인 테스트
            actual_user_id = user[0]
            return actual_user_id
        else:
            print("  user01@example.com 사용자를 찾을 수 없습니다.")
            return None
        
        db.close()
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return None

def test_login_with_actual_user_id(user_id):
    """실제 user_id로 로그인 테스트"""
    if not user_id:
        print("\n❌ user_id가 없어 로그인 테스트를 건너뜁니다.")
        return None
    
    print(f"\n🔐 실제 user_id로 로그인 테스트")
    print("=" * 60)
    
    login_data = {
        "user_id": user_id,
        "password": "test"
    }
    
    try:
        response = requests.post("http://localhost:8001/api/v1/auth/login", json=login_data)
        print(f"로그인 응답 상태: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            access_token = result.get("access_token")
            print(f"✅ 로그인 성공! 토큰: {access_token[:50]}...")
            return access_token
        else:
            print(f"❌ 로그인 실패: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 로그인 요청 실패: {e}")
        return None

def test_login_with_email():
    """이메일로도 로그인 테스트 (혹시 email 필드로도 검색하는지 확인)"""
    print(f"\n🔐 이메일로 로그인 테스트")
    print("=" * 60)
    
    login_data = {
        "user_id": "user01@example.com",
        "password": "test"
    }
    
    try:
        response = requests.post("http://localhost:8001/api/v1/auth/login", json=login_data)
        print(f"로그인 응답 상태: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            access_token = result.get("access_token")
            print(f"✅ 이메일로 로그인 성공! 토큰: {access_token[:50]}...")
            return access_token
        else:
            print(f"❌ 이메일로 로그인 실패: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 이메일 로그인 요청 실패: {e}")
        return None

def test_mail_apis(token):
    """메일 API 테스트"""
    if not token:
        print("\n❌ 토큰이 없어 메일 API 테스트를 건너뜁니다.")
        return
    
    print(f"\n📧 메일 API 테스트")
    print("=" * 60)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 받은 메일함 테스트
    try:
        response = requests.get("http://localhost:8001/api/v1/mail/inbox", headers=headers)
        print(f"받은 메일함 응답 상태: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            mails = result.get("mails", [])
            pagination = result.get("pagination", {})
            total = pagination.get("total", 0)
            
            print(f"✅ 받은 메일함 조회 성공!")
            print(f"   총 메일 수: {total}")
            print(f"   현재 페이지 메일 수: {len(mails)}")
            
            if mails:
                first_mail = mails[0]
                print(f"   첫 번째 메일: {first_mail.get('subject', 'N/A')}")
        else:
            print(f"❌ 받은 메일함 조회 실패: {response.text}")
            
    except Exception as e:
        print(f"❌ 받은 메일함 요청 실패: {e}")
    
    # 보낸 메일함 테스트
    try:
        response = requests.get("http://localhost:8001/api/v1/mail/sent", headers=headers)
        print(f"\n보낸 메일함 응답 상태: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            mails = result.get("mails", [])
            pagination = result.get("pagination", {})
            total = pagination.get("total", 0)
            
            print(f"✅ 보낸 메일함 조회 성공!")
            print(f"   총 메일 수: {total}")
            print(f"   현재 페이지 메일 수: {len(mails)}")
            
            if mails:
                first_mail = mails[0]
                print(f"   첫 번째 메일: {first_mail.get('subject', 'N/A')}")
        else:
            print(f"❌ 보낸 메일함 조회 실패: {response.text}")
            
    except Exception as e:
        print(f"❌ 보낸 메일함 요청 실패: {e}")

def main():
    """메인 함수"""
    print("🔍 user01 사용자 상세 정보 확인 및 로그인 테스트")
    print("=" * 60)
    
    # 1. user01 사용자 상세 정보 확인
    actual_user_id = check_user01_details()
    
    # 2. 실제 user_id로 로그인 테스트
    token = test_login_with_actual_user_id(actual_user_id)
    
    # 3. 이메일로도 로그인 테스트
    if not token:
        token = test_login_with_email()
    
    # 4. 메일 API 테스트
    test_mail_apis(token)
    
    print("\n" + "=" * 60)
    print("🔍 user01 사용자 상세 정보 확인 및 로그인 테스트 완료")

if __name__ == "__main__":
    main()