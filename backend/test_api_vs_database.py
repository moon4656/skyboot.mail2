#!/usr/bin/env python3
"""
API vs 데이터베이스 비교 테스트

데이터베이스에는 3개의 읽지 않은 메일이 있는데 
API가 0개를 반환하는 이유를 파악합니다.
"""
import sys
import os
import requests
import json

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.config import settings

# API 설정
API_BASE_URL = "http://localhost:8001"

def get_db_session():
    """데이터베이스 세션 생성"""
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()

def login_user():
    """사용자 로그인"""
    print("🔐 사용자 로그인 중...")
    
    login_data = {
        "user_id": "user01",
        "password": "test"
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            token = result.get("access_token")
            print(f"✅ 로그인 성공! 토큰: {token[:20]}...")
            return token
        else:
            print(f"❌ 로그인 실패: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 로그인 오류: {e}")
        return None

def test_unread_api(token):
    """읽지 않은 메일 API 테스트"""
    print(f"\n📧 읽지 않은 메일 API 테스트")
    print("=" * 50)
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/v1/mail/unread",
            headers=headers
        )
        
        print(f"📊 API 응답:")
        print(f"   상태 코드: {response.status_code}")
        print(f"   응답 헤더: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   응답 데이터: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            # 읽지 않은 메일 수 확인
            if isinstance(result, list):
                unread_count = len(result)
            elif isinstance(result, dict) and 'data' in result:
                unread_count = len(result['data']) if isinstance(result['data'], list) else 0
            elif isinstance(result, dict) and 'unread_mails' in result:
                unread_count = len(result['unread_mails']) if isinstance(result['unread_mails'], list) else 0
            else:
                unread_count = 0
            
            print(f"   📧 API에서 반환된 읽지 않은 메일 수: {unread_count}개")
            return unread_count
        else:
            print(f"   ❌ API 오류: {response.text}")
            return 0
            
    except Exception as e:
        print(f"❌ API 테스트 오류: {e}")
        return 0

def check_database_unread():
    """데이터베이스에서 직접 읽지 않은 메일 확인"""
    print(f"\n🗄️ 데이터베이스 직접 확인")
    print("=" * 50)
    
    user_uuid = '3b959219-da10-42bb-9693-0aa3ed502cd3'  # user01의 UUID
    
    try:
        db = get_db_session()
        
        # 읽지 않은 메일 쿼리 (API와 동일한 로직)
        result = db.execute(text("""
            SELECT 
                m.mail_uuid,
                m.subject,
                m.created_at,
                mif.is_read,
                mf.name as folder_name,
                mf.folder_type,
                mif.user_uuid,
                mf.user_uuid as folder_user_uuid
            FROM mails m
            JOIN mail_in_folders mif ON m.mail_uuid = mif.mail_uuid
            JOIN mail_folders mf ON mif.folder_uuid = mf.folder_uuid
            WHERE mf.user_uuid = :user_uuid 
            AND mf.folder_type = 'inbox'
            AND mif.is_read = false
            ORDER BY m.created_at DESC;
        """), {"user_uuid": user_uuid})
        
        unread_mails = result.fetchall()
        print(f"📧 데이터베이스 읽지 않은 메일: {len(unread_mails)}개")
        
        for i, mail in enumerate(unread_mails, 1):
            mail_uuid = mail[0][:8]
            subject = mail[1]
            created_at = mail[2]
            is_read = mail[3]
            folder_name = mail[4]
            folder_type = mail[5]
            mif_user_uuid = mail[6][:8] if mail[6] else 'None'
            folder_user_uuid = mail[7][:8] if mail[7] else 'None'
            
            print(f"  {i}. {mail_uuid}... | {subject}")
            print(f"     폴더: {folder_name} ({folder_type})")
            print(f"     읽음상태: {is_read}, 생성시간: {created_at}")
            print(f"     MIF 사용자: {mif_user_uuid}..., 폴더 사용자: {folder_user_uuid}...")
            print()
        
        db.close()
        return len(unread_mails)
        
    except Exception as e:
        print(f"❌ 데이터베이스 확인 오류: {e}")
        return 0

def check_user_authentication():
    """사용자 인증 정보 확인"""
    print(f"\n👤 사용자 인증 정보 확인")
    print("=" * 50)
    
    try:
        db = get_db_session()
        
        # user01 정보 확인
        result = db.execute(text("""
            SELECT user_id, email, user_uuid, is_active
            FROM users
            WHERE user_id = 'user01';
        """))
        
        user_info = result.fetchone()
        if user_info:
            user_id = user_info[0]
            email = user_info[1]
            user_uuid = user_info[2]
            is_active = user_info[3]
            
            print(f"📋 사용자 정보:")
            print(f"   ID: {user_id}")
            print(f"   이메일: {email}")
            print(f"   UUID: {user_uuid}")
            print(f"   활성화: {is_active}")
            
            return user_uuid
        else:
            print(f"❌ user01을 찾을 수 없습니다")
            return None
        
        db.close()
        
    except Exception as e:
        print(f"❌ 사용자 정보 확인 오류: {e}")
        return None

def test_other_mail_apis(token):
    """다른 메일 API들도 테스트"""
    print(f"\n📬 다른 메일 API 테스트")
    print("=" * 50)
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    apis_to_test = [
        ("/api/v1/mail/inbox", "받은 메일함"),
        ("/api/v1/mail/sent", "보낸 메일함"),
    ]
    
    for endpoint, name in apis_to_test:
        try:
            response = requests.get(f"{API_BASE_URL}{endpoint}", headers=headers)
            print(f"📧 {name} ({endpoint}):")
            print(f"   상태: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list):
                    count = len(result)
                elif isinstance(result, dict) and 'data' in result:
                    count = len(result['data']) if isinstance(result['data'], list) else 0
                else:
                    count = 0
                print(f"   메일 수: {count}개")
            else:
                print(f"   오류: {response.text}")
            print()
            
        except Exception as e:
            print(f"   ❌ {name} API 오류: {e}")

def main():
    """메인 함수"""
    print("🔍 API vs 데이터베이스 비교 테스트")
    print("=" * 60)
    
    # 1. 사용자 인증 정보 확인
    user_uuid = check_user_authentication()
    if not user_uuid:
        print("❌ 사용자 정보를 확인할 수 없습니다.")
        return
    
    # 2. 데이터베이스에서 직접 읽지 않은 메일 확인
    db_unread_count = check_database_unread()
    
    # 3. 사용자 로그인
    token = login_user()
    if not token:
        print("❌ 로그인에 실패했습니다.")
        return
    
    # 4. 읽지 않은 메일 API 테스트
    api_unread_count = test_unread_api(token)
    
    # 5. 다른 메일 API들도 테스트
    test_other_mail_apis(token)
    
    # 6. 결과 비교
    print(f"\n🎯 결과 비교")
    print("=" * 60)
    print(f"📊 데이터베이스 읽지 않은 메일: {db_unread_count}개")
    print(f"📊 API 응답 읽지 않은 메일: {api_unread_count}개")
    
    if db_unread_count != api_unread_count:
        print(f"⚠️ 불일치 발견! 데이터베이스와 API 응답이 다릅니다.")
        print(f"   차이: {db_unread_count - api_unread_count}개")
    else:
        print(f"✅ 일치! 데이터베이스와 API 응답이 동일합니다.")
    
    print("\n" + "=" * 60)
    print("🔍 API vs 데이터베이스 비교 테스트 완료")

if __name__ == "__main__":
    main()