#!/usr/bin/env python3
"""
생성된 메일 데이터 확인 스크립트
"""

import requests
import json
from datetime import datetime

# 설정
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

# 테스트 사용자 정보
TEST_USER = {
    "user_id": "user01",
    "password": "test"
}

def login():
    """로그인하여 토큰 획득"""
    login_data = {
        "user_id": TEST_USER["user_id"],
        "password": TEST_USER["password"]
    }
    
    response = requests.post(f"{API_BASE}/auth/login", json=login_data)
    
    if response.status_code == 200:
        result = response.json()
        # APIResponse 구조 또는 직접 토큰 구조 모두 처리
        if result.get("success"):
            return result["data"]["access_token"]
        elif result.get("access_token"):
            return result["access_token"]
    
    print(f"❌ 로그인 실패: {response.status_code} - {response.text}")
    return None

def check_mail_data(token):
    """메일 데이터 확인"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("📧 메일 데이터 확인")
    print("=" * 60)
    
    # 1. 받은 메일함 확인
    print("\n1. 받은 메일함 (inbox) 확인:")
    inbox_response = requests.get(f"{API_BASE}/mail/inbox", headers=headers)
    if inbox_response.status_code == 200:
        inbox_data = inbox_response.json()
        print(f"   - 상태: {inbox_response.status_code}")
        print(f"   - 메일 수: {len(inbox_data.get('data', {}).get('mails', []))}")
        
        mails = inbox_data.get('data', {}).get('mails', [])
        for i, mail in enumerate(mails[:3]):  # 최대 3개만 표시
            print(f"   - 메일 {i+1}: {mail.get('mail_uuid')} | {mail.get('subject')} | 읽음: {mail.get('is_read', 'N/A')}")
    else:
        print(f"   - 실패: {inbox_response.status_code} - {inbox_response.text}")
    
    # 2. 보낸 메일함 확인
    print("\n2. 보낸 메일함 (sent) 확인:")
    sent_response = requests.get(f"{API_BASE}/mail/sent", headers=headers)
    if sent_response.status_code == 200:
        sent_data = sent_response.json()
        print(f"   - 상태: {sent_response.status_code}")
        print(f"   - 메일 수: {len(sent_data.get('data', {}).get('mails', []))}")
        
        mails = sent_data.get('data', {}).get('mails', [])
        for i, mail in enumerate(mails[:3]):  # 최대 3개만 표시
            print(f"   - 메일 {i+1}: {mail.get('mail_uuid')} | {mail.get('subject')} | 상태: {mail.get('status', 'N/A')}")
    else:
        print(f"   - 실패: {sent_response.status_code} - {sent_response.text}")
    
    # 3. 읽지 않은 메일 확인
    print("\n3. 읽지 않은 메일 확인:")
    unread_response = requests.get(f"{API_BASE}/mail/unread", headers=headers)
    if unread_response.status_code == 200:
        unread_data = unread_response.json()
        print(f"   - 상태: {unread_response.status_code}")
        print(f"   - 메일 수: {len(unread_data.get('data', {}).get('mails', []))}")
        
        mails = unread_data.get('data', {}).get('mails', [])
        for i, mail in enumerate(mails[:3]):  # 최대 3개만 표시
            print(f"   - 메일 {i+1}: {mail.get('mail_uuid')} | {mail.get('subject')} | 읽음: {mail.get('is_read', 'N/A')}")
    else:
        print(f"   - 실패: {unread_response.status_code} - {unread_response.text}")
    
    # 4. 메일 통계 확인
    print("\n4. 메일 통계 확인:")
    stats_response = requests.get(f"{API_BASE}/mail/stats", headers=headers)
    if stats_response.status_code == 200:
        stats_data = stats_response.json()
        print(f"   - 상태: {stats_response.status_code}")
        stats = stats_data.get('data', {})
        print(f"   - 총 메일: {stats.get('total_mails', 'N/A')}")
        print(f"   - 읽지 않은 메일: {stats.get('unread_count', 'N/A')}")
        print(f"   - 받은 메일: {stats.get('inbox_count', 'N/A')}")
        print(f"   - 보낸 메일: {stats.get('sent_count', 'N/A')}")
    else:
        print(f"   - 실패: {stats_response.status_code} - {stats_response.text}")

def main():
    """메인 함수"""
    print("🔍 메일 데이터 확인 시작")
    print(f"⏰ 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 로그인
    token = login()
    if not token:
        print("❌ 로그인 실패로 테스트 중단")
        return
    
    print("✅ 로그인 성공")
    
    # 메일 데이터 확인
    check_mail_data(token)
    
    print("\n✅ 메일 데이터 확인 완료")

if __name__ == "__main__":
    main()