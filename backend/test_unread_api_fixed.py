#!/usr/bin/env python3
"""
수정된 상태에서 읽지 않은 메일 조회 API 테스트

MailFolder 테이블 수정 후 API가 정상 작동하는지 확인합니다.
"""
import requests
import json

def test_login():
    """로그인 테스트"""
    print("🔐 로그인 테스트")
    
    login_data = {
        "email": "user01@example.com",
        "password": "test"
    }
    
    response = requests.post("http://localhost:8001/auth/login", json=login_data)
    print(f"로그인 응답 상태: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        access_token = result.get("access_token")
        print(f"✅ 로그인 성공! 토큰: {access_token[:50]}...")
        return access_token
    else:
        print(f"❌ 로그인 실패: {response.text}")
        return None

def test_unread_mails(token):
    """읽지 않은 메일 조회 테스트"""
    print("\n📧 읽지 않은 메일 조회 테스트")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get("http://localhost:8001/mail/unread", headers=headers)
    print(f"읽지 않은 메일 조회 응답 상태: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 읽지 않은 메일 조회 성공!")
        print(f"   총 개수: {result.get('total', 0)}")
        print(f"   메일 수: {len(result.get('mails', []))}")
        
        # 첫 번째 메일 정보 출력
        mails = result.get('mails', [])
        if mails:
            first_mail = mails[0]
            print(f"   첫 번째 메일: {first_mail.get('subject', 'N/A')}")
            print(f"   발송자: {first_mail.get('sender_email', 'N/A')}")
            print(f"   읽음 상태: {first_mail.get('is_read', 'N/A')}")
        
        return result
    else:
        print(f"❌ 읽지 않은 메일 조회 실패: {response.text}")
        return None

def test_inbox_mails(token):
    """받은 메일함 조회 테스트"""
    print("\n📥 받은 메일함 조회 테스트")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get("http://localhost:8001/mail/inbox", headers=headers)
    print(f"받은 메일함 조회 응답 상태: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 받은 메일함 조회 성공!")
        print(f"   총 개수: {result.get('total', 0)}")
        print(f"   메일 수: {len(result.get('mails', []))}")
        
        # 첫 번째 메일 정보 출력
        mails = result.get('mails', [])
        if mails:
            first_mail = mails[0]
            print(f"   첫 번째 메일: {first_mail.get('subject', 'N/A')}")
            print(f"   발송자: {first_mail.get('sender_email', 'N/A')}")
        
        return result
    else:
        print(f"❌ 받은 메일함 조회 실패: {response.text}")
        return None

def move_mails_to_inbox():
    """sent 폴더의 메일들을 inbox로 이동 (테스트용)"""
    print("\n🔄 테스트용: sent 폴더 메일을 inbox로 이동")
    
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    from app.config import settings
    
    try:
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # user01의 inbox 폴더 UUID 조회
        result = db.execute(text("""
            SELECT mf.folder_uuid
            FROM mail_folders mf
            LEFT JOIN mail_users mu ON mf.user_uuid = mu.user_uuid
            WHERE mu.email = 'user01@example.com' AND mf.folder_type = 'INBOX'
        """))
        
        inbox_folder = result.fetchone()
        if not inbox_folder:
            print("❌ user01의 inbox 폴더를 찾을 수 없습니다.")
            return False
        
        inbox_uuid = inbox_folder[0]
        print(f"📥 inbox 폴더 UUID: {inbox_uuid}")
        
        # sent 폴더의 메일 몇 개를 inbox로 이동
        result = db.execute(text("""
            UPDATE mail_in_folders 
            SET folder_uuid = :inbox_uuid
            WHERE user_uuid = (
                SELECT user_uuid FROM mail_users WHERE email = 'user01@example.com'
            )
            AND folder_uuid != :inbox_uuid
            AND mail_uuid IN (
                SELECT mail_uuid FROM mail_in_folders 
                WHERE user_uuid = (
                    SELECT user_uuid FROM mail_users WHERE email = 'user01@example.com'
                )
                LIMIT 5
            )
        """), {"inbox_uuid": inbox_uuid})
        
        moved_count = result.rowcount
        db.commit()
        db.close()
        
        print(f"✅ {moved_count}개의 메일을 inbox로 이동했습니다.")
        return True
        
    except Exception as e:
        print(f"❌ 메일 이동 중 오류: {e}")
        return False

def main():
    """메인 함수"""
    print("🧪 수정된 상태에서 읽지 않은 메일 조회 API 테스트")
    print("=" * 60)
    
    # 1. 로그인
    token = test_login()
    if not token:
        return
    
    # 2. 현재 상태에서 테스트
    print("\n📊 현재 상태에서 API 테스트:")
    unread_result = test_unread_mails(token)
    inbox_result = test_inbox_mails(token)
    
    # 3. 메일을 inbox로 이동 후 재테스트
    if move_mails_to_inbox():
        print("\n📊 메일 이동 후 API 재테스트:")
        unread_result_after = test_unread_mails(token)
        inbox_result_after = test_inbox_mails(token)
        
        # 결과 비교
        print("\n📈 결과 비교:")
        print(f"읽지 않은 메일 - 이동 전: {unread_result.get('total', 0) if unread_result else 0}, 이동 후: {unread_result_after.get('total', 0) if unread_result_after else 0}")
        print(f"받은 메일함 - 이동 전: {inbox_result.get('total', 0) if inbox_result else 0}, 이동 후: {inbox_result_after.get('total', 0) if inbox_result_after else 0}")
    
    print("\n" + "=" * 60)
    print("🧪 API 테스트 완료")

if __name__ == "__main__":
    main()