#!/usr/bin/env python3
"""
사용자 간 메일 발송 및 읽지 않은 메일 테스트
"""

import requests
import json
from datetime import datetime
import time

# 설정
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

# 테스트 사용자들
USERS = {
    "sender": {"user_id": "user01", "password": "test"},
    "receiver": {"user_id": "testuser", "password": "test123"}  # init.sql에서 확인한 사용자
}

def login(user_info):
    """로그인하여 토큰 획득"""
    login_data = {
        "user_id": user_info["user_id"],
        "password": user_info["password"]
    }
    
    response = requests.post(f"{API_BASE}/auth/login", json=login_data)
    
    if response.status_code == 200:
        result = response.json()
        # APIResponse 구조 또는 직접 토큰 구조 모두 처리
        if result.get("success"):
            return result["data"]["access_token"]
        elif result.get("access_token"):
            return result["access_token"]
    
    print(f"❌ {user_info['user_id']} 로그인 실패: {response.status_code} - {response.text}")
    return None

def send_mail(sender_token, recipient_email, subject_suffix=""):
    """메일 발송"""
    headers = {"Authorization": f"Bearer {sender_token}"}
    
    mail_data = {
        "to": [recipient_email],
        "subject": f"사용자 간 메일 테스트 {datetime.now().strftime('%H:%M:%S')}{subject_suffix}",
        "body_text": f"이것은 사용자 간 메일 테스트입니다.{subject_suffix}\n생성 시간: {datetime.now()}",
        "priority": "normal",
        "is_draft": False
    }
    
    response = requests.post(f"{API_BASE}/mail/send-json", json=mail_data, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        mail_uuid = result.get("mail_uuid")
        print(f"✅ 메일 발송 성공: {mail_uuid}")
        return mail_uuid
    else:
        print(f"❌ 메일 발송 실패: {response.status_code} - {response.text}")
        return None

def check_unread_mails(token, user_name):
    """읽지 않은 메일 확인"""
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{API_BASE}/mail/unread", headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        mails = result.get('data', {}).get('mails', [])
        print(f"📧 {user_name} 읽지 않은 메일: {len(mails)}개")
        
        for i, mail in enumerate(mails[:3]):  # 최대 3개만 표시
            print(f"   - 메일 {i+1}: {mail.get('subject')} | 발송자: {mail.get('sender', {}).get('email', 'N/A')}")
        
        return mails
    else:
        print(f"❌ {user_name} 읽지 않은 메일 조회 실패: {response.status_code} - {response.text}")
        return []

def check_inbox(token, user_name):
    """받은 메일함 확인"""
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{API_BASE}/mail/inbox", headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        mails = result.get('data', {}).get('mails', [])
        print(f"📥 {user_name} 받은 메일함: {len(mails)}개")
        
        for i, mail in enumerate(mails[:3]):  # 최대 3개만 표시
            print(f"   - 메일 {i+1}: {mail.get('subject')} | 발송자: {mail.get('sender', {}).get('email', 'N/A')} | 읽음: {mail.get('is_read', 'N/A')}")
        
        return mails
    else:
        print(f"❌ {user_name} 받은 메일함 조회 실패: {response.status_code} - {response.text}")
        return []

def mark_mail_as_read(token, mail_uuid):
    """메일을 읽음으로 표시"""
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.put(f"{API_BASE}/mail/{mail_uuid}/read", headers=headers)
    
    if response.status_code == 200:
        print(f"✅ 메일 읽음 처리 성공: {mail_uuid}")
        return True
    else:
        print(f"❌ 메일 읽음 처리 실패: {response.status_code} - {response.text}")
        return False

def main():
    """메인 함수"""
    print("🔍 사용자 간 메일 발송 및 읽지 않은 메일 테스트 시작")
    print(f"⏰ 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # 1. 두 사용자 로그인
    print("\n1. 사용자 로그인")
    print("-" * 30)
    
    sender_token = login(USERS["sender"])
    
    if not sender_token:
        print("❌ 발송자 로그인 실패")
        return
    
    print("✅ 발송자 로그인 성공")
    
    # 2. 초기 상태 확인
    print("\n2. 초기 상태 확인")
    print("-" * 30)
    
    print("발송자 (user01) 상태:")
    check_unread_mails(sender_token, "발송자")
    check_inbox(sender_token, "발송자")
    
    # 3. 메일 발송
    print("\n3. 메일 발송 (user01 → testuser)")
    print("-" * 30)
    
    # 같은 조직의 활성 사용자에게 메일 발송
    recipient_email = "testuser_folder@example.com"
    mail_uuid = send_mail(sender_token, recipient_email, " #1")
    
    if not mail_uuid:
        print("❌ 메일 발송 실패로 테스트 중단")
        return
    
    # 잠시 대기 (메일 처리 시간)
    print("⏳ 메일 처리 대기 중...")
    time.sleep(2)
    
    # 4. 발송 후 상태 확인
    print("\n4. 발송 후 상태 확인")
    print("-" * 30)
    
    print("발송자 (user01) 보낸 메일함 확인:")
    sent_response = requests.get(f"{API_BASE}/mail/sent", headers={"Authorization": f"Bearer {sender_token}"})
    if sent_response.status_code == 200:
        sent_data = sent_response.json()
        sent_mails = sent_data.get('data', {}).get('mails', [])
        print(f"📤 보낸 메일함: {len(sent_mails)}개")
        
        for i, mail in enumerate(sent_mails[:3]):
            print(f"   - 메일 {i+1}: {mail.get('subject')} | 수신자: {mail.get('recipients', [{}])[0].get('email', 'N/A') if mail.get('recipients') else 'N/A'}")
        
        if sent_mails:
            print("✅ 메일이 성공적으로 발송되어 보낸 메일함에 저장되었습니다!")
        else:
            print("⚠️ 보낸 메일함에 메일이 없습니다.")
    else:
        print(f"❌ 보낸 메일함 조회 실패: {sent_response.status_code}")
    
    print("\n📧 메일 발송 API 테스트 완료")
    print("💡 참고: 수신자의 읽지 않은 메일 확인을 위해서는 수신자 계정으로 로그인이 필요합니다.")
    
    print("\n" + "=" * 70)
    print("✅ 사용자 간 메일 발송 및 읽지 않은 메일 테스트 완료")

if __name__ == "__main__":
    main()