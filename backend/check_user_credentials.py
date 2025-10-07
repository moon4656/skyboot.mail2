#!/usr/bin/env python3
"""
사용자 인증 정보 확인 스크립트

데이터베이스에서 실제 사용자 정보와 비밀번호를 확인합니다.
"""
import sys
import os

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.config import settings
import bcrypt

def get_db_session():
    """데이터베이스 세션 생성"""
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()

def check_users():
    """사용자 정보 확인"""
    print("🔍 사용자 정보 확인")
    print("=" * 60)
    
    try:
        db = get_db_session()
        
        # 1. 모든 사용자 조회
        print("📋 전체 사용자 목록:")
        result = db.execute(text("""
            SELECT email, hashed_password, is_active, created_at
            FROM users
            ORDER BY created_at DESC
            LIMIT 10;
        """))
        
        users = result.fetchall()
        for i, user in enumerate(users):
            print(f"  {i+1}. 이메일: {user[0]}")
            print(f"     비밀번호 해시: {user[1][:50]}...")
            print(f"     활성화: {user[2]}")
            print(f"     생성일: {user[3]}")
            print()
        
        # 2. user01 사용자 상세 정보
        print("📋 user01 사용자 상세 정보:")
        result = db.execute(text("""
            SELECT email, hashed_password, is_active, user_uuid, created_at
            FROM users
            WHERE email LIKE '%user01%'
            ORDER BY created_at DESC;
        """))
        
        user01_users = result.fetchall()
        if user01_users:
            for user in user01_users:
                print(f"  이메일: {user[0]}")
                print(f"  비밀번호 해시: {user[1]}")
                print(f"  활성화: {user[2]}")
                print(f"  UUID: {user[3]}")
                print(f"  생성일: {user[4]}")
                print()
        else:
            print("  user01 사용자를 찾을 수 없습니다.")
        
        # 3. 비밀번호 검증 테스트
        if user01_users:
            user = user01_users[0]
            email = user[0]
            stored_hash = user[1]
            
            print("🔐 비밀번호 검증 테스트:")
            test_passwords = ["test", "test123", "password", "user01"]
            
            for test_password in test_passwords:
                try:
                    # bcrypt 해시 검증
                    is_valid = bcrypt.checkpw(test_password.encode('utf-8'), stored_hash.encode('utf-8'))
                    print(f"  비밀번호 '{test_password}': {'✅ 일치' if is_valid else '❌ 불일치'}")
                    
                    if is_valid:
                        print(f"  🎉 올바른 비밀번호를 찾았습니다: '{test_password}'")
                        return email, test_password
                except Exception as e:
                    print(f"  비밀번호 '{test_password}' 검증 중 오류: {e}")
        
        db.close()
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
    
    return None, None

def test_login_with_credentials(email, password):
    """올바른 인증 정보로 로그인 테스트"""
    if not email or not password:
        print("\n❌ 올바른 인증 정보를 찾을 수 없어 로그인 테스트를 건너뜁니다.")
        return None
    
    print(f"\n🔐 올바른 인증 정보로 로그인 테스트")
    print("=" * 60)
    
    import requests
    
    login_data = {
        "user_id": email,
        "password": password
    }
    
    try:
        response = requests.post("http://localhost:8001/api/v1/auth/login", json=login_data)
        print(f"로그인 응답 상태: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            access_token = result.get("data", {}).get("access_token") or result.get("access_token")
            print(f"✅ 로그인 성공! 토큰: {access_token[:50]}...")
            return access_token
        else:
            print(f"❌ 로그인 실패: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 로그인 요청 실패: {e}")
        return None

def test_mail_apis(token):
    """메일 API 테스트"""
    if not token:
        print("\n❌ 토큰이 없어 메일 API 테스트를 건너뜁니다.")
        return
    
    print(f"\n📧 메일 API 테스트")
    print("=" * 60)
    
    import requests
    
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
    print("🔍 사용자 인증 정보 확인 및 API 테스트")
    print("=" * 60)
    
    # 1. 사용자 정보 확인
    email, password = check_users()
    
    # 2. 올바른 인증 정보로 로그인 테스트
    token = test_login_with_credentials(email, password)
    
    # 3. 메일 API 테스트
    test_mail_apis(token)
    
    print("\n" + "=" * 60)
    print("🔍 사용자 인증 정보 확인 및 API 테스트 완료")

if __name__ == "__main__":
    main()