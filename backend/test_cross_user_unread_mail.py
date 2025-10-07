#!/usr/bin/env python3
"""
사용자 간 메일 송수신 및 읽지 않은 메일 테스트
- 발송자: user01 (기존 사용자)
- 수신자: recipient_1759679224 (새로 생성된 사용자)
"""

import requests
import json
import time

# API 기본 설정
BASE_URL = "http://localhost:8001"
HEADERS = {"Content-Type": "application/json"}

def login_user(user_id, password):
    """사용자 로그인"""
    login_data = {
        "user_id": user_id,
        "password": password
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        headers=HEADERS,
        json=login_data
    )
    
    if response.status_code == 200:
        result = response.json()
        token = result.get("access_token")
        print(f"✅ {user_id} 로그인 성공")
        return token
    else:
        print(f"❌ {user_id} 로그인 실패: {response.status_code} - {response.text}")
        return None

def send_mail(token, recipient_email, subject, content):
    """메일 발송"""
    mail_data = {
        "to": [recipient_email],  # 수신자 목록 (배열 형태)
        "subject": subject,
        "body_text": content  # content 대신 body_text 사용
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/mail/send-json",
        headers=headers,
        json=mail_data
    )
    
    if response.status_code == 200:
        result = response.json()
        mail_uuid = result.get("mail_uuid")
        print(f"✅ 메일 발송 성공: {mail_uuid}")
        return mail_uuid
    else:
        print(f"❌ 메일 발송 실패: {response.status_code} - {response.text}")
        return None

def get_unread_count(token):
    """읽지 않은 메일 수 조회 (stats API 사용)"""
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{BASE_URL}/api/v1/mail/stats",
        headers=headers
    )
    
    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            data = result.get("data", {})
            count = data.get("unread_count", 0)
            print(f"📧 읽지 않은 메일 수: {count}")
            return count
        else:
            print(f"❌ 읽지 않은 메일 수 조회 실패: {result.get('message', '알 수 없는 오류')}")
            return 0
    else:
        print(f"❌ 읽지 않은 메일 수 조회 실패: {response.status_code} - {response.text}")
        return 0

def get_inbox(token):
    """받은 메일함 조회"""
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{BASE_URL}/api/v1/mail/inbox",
        headers=headers
    )
    
    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            data = result.get("data", {})
            mails = data.get("mails", [])
            print(f"📧 받은 메일함: {len(mails)}개 메일")
            return mails
        else:
            print(f"❌ 받은 메일함 조회 실패: {result.get('message', '알 수 없는 오류')}")
            return []
    else:
        print(f"❌ 받은 메일함 조회 실패: {response.status_code} - {response.text}")
        return []

def mark_mail_as_read(token, mail_uuid):
    """메일 읽음 처리"""
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.post(
        f"{BASE_URL}/api/v1/mail/{mail_uuid}/read",
        headers=headers
    )
    
    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            print(f"✅ 메일 읽음 처리 성공: {mail_uuid}")
            return True
        else:
            print(f"❌ 메일 읽음 처리 실패: {result.get('message', '알 수 없는 오류')}")
            return False
    else:
        print(f"❌ 메일 읽음 처리 실패: {response.status_code} - {response.text}")
        return False

def main():
    """메인 테스트 함수"""
    print("=== 사용자 간 메일 송수신 및 읽지 않은 메일 테스트 ===")
    
    # 1. 발송자 로그인 (testuser_folder@example.com)
    print("\n1. 발송자 로그인")
    sender_token = login_user("testuser_folder", "test123")  # 비밀번호 확인됨
    if not sender_token:
        print("❌ 발송자 로그인 실패")
        return
    
    # 2. 수신자 로그인
    print("\n2. 수신자 로그인")
    recipient_token = login_user("recipient_1759679224", "recipient123")
    if not recipient_token:
        print("❌ 수신자 로그인 실패")
        return
    
    # 3. 수신자의 초기 읽지 않은 메일 수 확인
    print("\n3. 수신자 초기 읽지 않은 메일 수 확인")
    initial_unread_count = get_unread_count(recipient_token)
    
    # 4. 발송자가 수신자에게 메일 발송
    print("\n4. 메일 발송")
    mail_uuid = send_mail(sender_token, "recipient@test.example.com", "테스트 메일", "읽지 않은 메일 테스트입니다.")
    
    if not mail_uuid:
        print("❌ 메일 발송 실패")
        return
    
    # 5. 잠시 대기 (메일 처리 시간)
    print("\n5. 메일 처리 대기 (3초)")
    time.sleep(3)
    
    # 6. 수신자의 읽지 않은 메일 수 확인 (증가했는지)
    print("\n6. 수신자 읽지 않은 메일 수 확인")
    after_send_unread_count = get_unread_count(recipient_token)
    
    if after_send_unread_count > initial_unread_count:
        print(f"✅ 읽지 않은 메일 수 증가: {initial_unread_count} → {after_send_unread_count}")
    else:
        print(f"❌ 읽지 않은 메일 수 변화 없음: {initial_unread_count} → {after_send_unread_count}")
    
    # 7. 수신자의 받은 메일함 확인
    print("\n7. 수신자 받은 메일함 확인")
    inbox_mails = get_inbox(recipient_token)
    
    if inbox_mails:
        latest_mail = inbox_mails[0]
        mail_uuid = latest_mail.get("mail_uuid")
        subject = latest_mail.get("subject")
        is_read = latest_mail.get("is_read", False)
        
        print(f"📧 최신 메일: {subject}")
        print(f"📧 메일 UUID: {mail_uuid}")
        print(f"📧 읽음 상태: {is_read}")
        
        # 8. 메일을 읽음으로 표시
        if not is_read and mail_uuid:
            print("\n8. 메일 읽음 처리")
            if mark_mail_as_read(recipient_token, mail_uuid):
                # 9. 읽음 처리 후 읽지 않은 메일 수 확인
                print("\n9. 읽음 처리 후 읽지 않은 메일 수 확인")
                final_unread_count = get_unread_count(recipient_token)
                
                if final_unread_count < after_send_unread_count:
                    print(f"✅ 읽지 않은 메일 수 감소: {after_send_unread_count} → {final_unread_count}")
                    print("✅ 읽지 않은 메일 기능 정상 작동")
                else:
                    print(f"❌ 읽지 않은 메일 수 변화 없음: {after_send_unread_count} → {final_unread_count}")
        else:
            print("❌ 읽을 메일이 없거나 이미 읽음 상태")
    else:
        print("❌ 받은 메일함이 비어있음")
    
    print("\n=== 테스트 완료 ===")

if __name__ == "__main__":
    main()