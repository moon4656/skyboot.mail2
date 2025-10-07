#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API를 통해 테스트용 읽지 않은 메일 생성

메일 발송 API를 사용하여 user01에게 메일을 보내고 읽지 않은 상태로 만듭니다.
"""

import requests
import json
from datetime import datetime

# 테스트 설정
BASE_URL = "http://localhost:8001"
API_BASE = f"{BASE_URL}/api/v1"

# 테스트 사용자 정보
TEST_USER = {
    "user_id": "user01",
    "password": "test"
}

def login_user():
    """사용자 로그인"""
    print(f"🔐 사용자 로그인 중...")
    print("=" * 50)
    
    try:
        response = requests.post(f"{API_BASE}/auth/login", json=TEST_USER)
        print(f"로그인 응답 상태: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            # 다양한 응답 구조 처리
            token = None
            if isinstance(result, dict):
                if "access_token" in result:
                    token = result["access_token"]
                elif "data" in result and isinstance(result["data"], dict):
                    token = result["data"].get("access_token")
                elif "token" in result:
                    token = result["token"]
            
            if token:
                print(f"✅ 로그인 성공! 토큰: {token[:20]}...")
                return token
            else:
                print(f"❌ 로그인 응답에서 토큰을 찾을 수 없습니다.")
                return None
        else:
            print(f"❌ 로그인 실패: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 로그인 요청 실패: {e}")
        return None

def send_test_mail(token):
    """테스트 메일 발송"""
    if not token:
        print(f"\n❌ 토큰이 없어 메일 발송을 건너뜁니다.")
        return False
    
    print(f"\n📧 테스트 메일 발송")
    print("=" * 50)
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # 메일 발송 데이터 (Form 데이터 형식)
    mail_data = {
        "to_emails": "user01@skyboot.mail",  # 쉼표로 구분된 문자열
        "subject": f"읽지 않은 메일 테스트 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "content": "이것은 읽지 않은 메일 API 테스트를 위한 메일입니다.",
        "priority": "normal",
        "is_draft": "false"
    }
    
    try:
        response = requests.post(f"{API_BASE}/mail/send", headers=headers, data=mail_data)
        print(f"메일 발송 응답 상태: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 메일 발송 성공!")
            print(f"응답 데이터: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            if result.get("success"):
                data = result.get("data", {})
                mail_uuid = data.get("mail_uuid")
                print(f"📧 발송된 메일 UUID: {mail_uuid}")
                return mail_uuid
            else:
                print(f"❌ 메일 발송 실패: {result.get('message')}")
                return None
        else:
            print(f"❌ 메일 발송 실패: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 메일 발송 요청 실패: {e}")
        return None

def check_inbox_api(token):
    """받은편지함 API 확인"""
    if not token:
        print(f"\n❌ 토큰이 없어 받은편지함 확인을 건너뜁니다.")
        return
    
    print(f"\n📥 받은편지함 확인")
    print("=" * 50)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{API_BASE}/mail/inbox", headers=headers)
        print(f"받은편지함 응답 상태: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 받은편지함 조회 성공!")
            
            if result.get("success"):
                data = result.get("data", {})
                mails = data.get("mails", [])
                total = data.get("total", 0)
                
                print(f"📊 받은편지함 결과:")
                print(f"  - 총 메일 수: {total}")
                print(f"  - 현재 페이지 메일 수: {len(mails)}")
                
                if mails:
                    print(f"\n📧 최근 메일 목록:")
                    for i, mail in enumerate(mails[:3], 1):  # 최근 3개만 표시
                        subject = mail.get('subject', 'No Subject')
                        sender = mail.get('sender_email', 'Unknown')
                        is_read = mail.get('is_read', 'Unknown')
                        
                        print(f"  {i}. {subject}")
                        print(f"     발송자: {sender}")
                        print(f"     읽음상태: {is_read}")
                        print()
            else:
                print(f"❌ 받은편지함 조회 실패: {result.get('message')}")
        else:
            print(f"❌ 받은편지함 조회 실패: {response.text}")
            
    except Exception as e:
        print(f"❌ 받은편지함 요청 실패: {e}")

def check_unread_api(token):
    """읽지 않은 메일 API 확인"""
    if not token:
        print(f"\n❌ 토큰이 없어 읽지 않은 메일 확인을 건너뜁니다.")
        return
    
    print(f"\n📧 읽지 않은 메일 확인")
    print("=" * 50)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{API_BASE}/mail/unread", headers=headers)
        print(f"읽지 않은 메일 응답 상태: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 읽지 않은 메일 조회 성공!")
            
            if result.get("success"):
                data = result.get("data", {})
                mails = data.get("mails", [])
                total = data.get("total", 0)
                
                print(f"📊 읽지 않은 메일 결과:")
                print(f"  - 총 읽지 않은 메일 수: {total}")
                print(f"  - 현재 페이지 메일 수: {len(mails)}")
                
                if mails:
                    print(f"\n📧 읽지 않은 메일 목록:")
                    for i, mail in enumerate(mails, 1):
                        subject = mail.get('subject', 'No Subject')
                        sender = mail.get('sender_email', 'Unknown')
                        is_read = mail.get('is_read', 'Unknown')
                        
                        print(f"  {i}. {subject}")
                        print(f"     발송자: {sender}")
                        print(f"     읽음상태: {is_read}")
                        print()
                    
                    return total
                else:
                    print(f"  📭 읽지 않은 메일이 없습니다.")
                    return 0
            else:
                print(f"❌ 읽지 않은 메일 조회 실패: {result.get('message')}")
                return 0
        else:
            print(f"❌ 읽지 않은 메일 조회 실패: {response.text}")
            return 0
            
    except Exception as e:
        print(f"❌ 읽지 않은 메일 요청 실패: {e}")
        return 0

def main():
    """메인 함수"""
    print(f"🧪 API를 통한 읽지 않은 메일 테스트")
    print(f"시작 시간: {datetime.now()}")
    print("=" * 70)
    
    # 1. 사용자 로그인
    token = login_user()
    
    if not token:
        print(f"❌ 로그인 실패로 테스트를 중단합니다.")
        return
    
    # 2. 현재 읽지 않은 메일 확인
    print(f"\n🔍 현재 상태 확인")
    initial_unread = check_unread_api(token)
    
    # 3. 테스트 메일 발송
    mail_uuid = send_test_mail(token)
    
    if mail_uuid:
        print(f"\n⏳ 메일 처리 대기 중... (3초)")
        import time
        time.sleep(3)
        
        # 4. 발송 후 상태 확인
        print(f"\n🔍 발송 후 상태 확인")
        check_inbox_api(token)
        final_unread = check_unread_api(token)
        
        # 5. 결과 비교
        print(f"\n📊 결과 비교")
        print("=" * 50)
        print(f"발송 전 읽지 않은 메일: {initial_unread}개")
        print(f"발송 후 읽지 않은 메일: {final_unread}개")
        
        if final_unread > initial_unread:
            print(f"✅ 성공! 읽지 않은 메일이 증가했습니다. (+{final_unread - initial_unread}개)")
        elif final_unread == initial_unread:
            print(f"⚠️ 읽지 않은 메일 수가 변하지 않았습니다. 메일이 받은편지함에 도착하지 않았을 수 있습니다.")
        else:
            print(f"❓ 예상치 못한 결과입니다.")
    
    print(f"\n🏁 테스트 완료")
    print("=" * 70)
    print(f"종료 시간: {datetime.now()}")

if __name__ == "__main__":
    main()