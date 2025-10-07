#!/usr/bin/env python3
"""
완전한 읽지 않은 메일 API 테스트
admin01이 다른 사용자에게 메일을 보내고, 수신자로 로그인하여 읽지 않은 메일 확인
"""

import requests
import json
from datetime import datetime

# API 기본 설정
BASE_URL = "http://localhost:8001"
LOGIN_URL = f"{BASE_URL}/api/v1/auth/login"
SEND_MAIL_URL = f"{BASE_URL}/api/v1/mail/send"
UNREAD_MAIL_URL = f"{BASE_URL}/api/v1/mail/unread"
INBOX_URL = f"{BASE_URL}/api/v1/mail/inbox"

def login_user(user_id: str, password: str):
    """사용자 로그인"""
    print(f"🔐 사용자 로그인 중: {user_id}")
    print("=" * 50)
    
    login_data = {
        "user_id": user_id,
        "password": password
    }
    
    headers = {"Content-Type": "application/json"}
    response = requests.post(LOGIN_URL, json=login_data, headers=headers)
    print(f"로그인 응답 상태: {response.status_code}")
    
    if response.status_code == 200:
        response_data = response.json()
        
        # 다양한 응답 구조 처리
        if isinstance(response_data, dict):
            if "access_token" in response_data:
                token = response_data["access_token"]
            elif "token" in response_data:
                token = response_data["token"]
            elif "data" in response_data and isinstance(response_data["data"], dict):
                if "access_token" in response_data["data"]:
                    token = response_data["data"]["access_token"]
                elif "token" in response_data["data"]:
                    token = response_data["data"]["token"]
                else:
                    token = str(response_data["data"])
            else:
                # 응답 전체를 문자열로 변환하여 토큰 추출 시도
                response_str = str(response_data)
                if "access_token" in response_str:
                    import re
                    match = re.search(r"'access_token':\s*'([^']+)'", response_str)
                    if match:
                        token = match.group(1)
                    else:
                        token = response_str
                else:
                    token = response_str
        else:
            token = str(response_data)
        
        print(f"✅ 로그인 성공! 토큰: {token[:20]}...")
        return token
    else:
        print(f"❌ 로그인 실패: {response.text}")
        return None

def send_test_mail(token: str, recipient: str):
    """테스트 메일 발송"""
    print(f"\n📧 테스트 메일 발송: {recipient}")
    print("=" * 50)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Form 데이터로 메일 발송
    mail_data = {
        "to_emails": recipient,
        "subject": "읽지 않은 메일 API 테스트",
        "content": "이 메일은 읽지 않은 메일 API 테스트를 위한 메일입니다."
    }
    
    response = requests.post(SEND_MAIL_URL, data=mail_data, headers=headers)
    print(f"메일 발송 응답 상태: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 메일 발송 성공!")
        print(f"응답 데이터: {json.dumps(data, indent=2, ensure_ascii=False)}")
        return data.get("mail_uuid")
    else:
        print(f"❌ 메일 발송 실패: {response.text}")
        return None

def check_unread_mails(token: str, user_name: str):
    """읽지 않은 메일 확인"""
    print(f"\n📧 {user_name}의 읽지 않은 메일 확인")
    print("=" * 50)
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(UNREAD_MAIL_URL, headers=headers)
    
    print(f"읽지 않은 메일 응답 상태: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 읽지 않은 메일 조회 성공!")
        print(f"📊 읽지 않은 메일 결과:")
        
        if isinstance(data, dict):
            total_count = data.get('total_count', 0)
            current_count = len(data.get('mails', []))
            print(f"  - 총 읽지 않은 메일 수: {total_count}")
            print(f"  - 현재 페이지 메일 수: {current_count}")
            
            if current_count > 0:
                print(f"  📬 읽지 않은 메일 목록:")
                for i, mail in enumerate(data.get('mails', []), 1):
                    mail_id = str(mail.get('mail_uuid', 'N/A'))
                    subject = str(mail.get('subject', 'N/A'))
                    created_at = str(mail.get('created_at', 'N/A'))
                    folder_name = str(mail.get('folder_name', 'N/A'))
                    is_read = mail.get('is_read', 'N/A')
                    print(f"    {i}. ID: {mail_id}, 제목: {subject}")
                    print(f"       생성일: {created_at}, 폴더: {folder_name}, 읽음: {is_read}")
            else:
                print(f"  📭 읽지 않은 메일이 없습니다.")
        else:
            print(f"  📊 응답 데이터: {data}")
        
        return data
    else:
        print(f"❌ 읽지 않은 메일 조회 실패: {response.text}")
        return None

def check_inbox(token: str, user_name: str):
    """받은편지함 확인"""
    print(f"\n📥 {user_name}의 받은편지함 확인")
    print("=" * 50)
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(INBOX_URL, headers=headers)
    
    print(f"받은편지함 응답 상태: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 받은편지함 조회 성공!")
        print(f"📊 받은편지함 결과:")
        
        if isinstance(data, dict):
            total_count = data.get('total_count', 0)
            current_count = len(data.get('mails', []))
            print(f"  - 총 메일 수: {total_count}")
            print(f"  - 현재 페이지 메일 수: {current_count}")
            
            if current_count > 0:
                print(f"  📬 받은편지함 메일 목록:")
                for i, mail in enumerate(data.get('mails', []), 1):
                    mail_id = str(mail.get('mail_uuid', 'N/A'))
                    subject = str(mail.get('subject', 'N/A'))
                    created_at = str(mail.get('created_at', 'N/A'))
                    is_read = mail.get('is_read', False)
                    print(f"    {i}. ID: {mail_id}, 제목: {subject}")
                    print(f"       생성일: {created_at}, 읽음: {is_read}")
            else:
                print(f"  📭 받은편지함이 비어있습니다.")
        else:
            print(f"  📊 응답 데이터: {data}")
        
        return data
    else:
        print(f"❌ 받은편지함 조회 실패: {response.text}")
        return None

def main():
    print("🧪 완전한 읽지 않은 메일 API 테스트")
    print(f"시작 시간: {datetime.now()}")
    print("=" * 70)
    
    # 1단계: admin01로 로그인하여 메일 발송
    print("1️⃣ 1단계: admin01로 로그인하여 메일 발송")
    admin_token = login_user("admin01", "test")
    if not admin_token:
        print("❌ admin01 로그인 실패로 테스트 중단")
        return
    
    # admin01이 user01에게 메일 발송
    mail_uuid = send_test_mail(admin_token, "user01@example.com")
    if not mail_uuid:
        print("❌ 메일 발송 실패로 테스트 중단")
        return
    
    # 2단계: user01로 로그인하여 읽지 않은 메일 확인
    print("\n2️⃣ 2단계: user01로 로그인하여 읽지 않은 메일 확인")
    user01_token = login_user("user01", "test")
    if not user01_token:
        print("❌ user01 로그인 실패로 테스트 중단")
        return
    
    # user01의 읽지 않은 메일 확인
    unread_result = check_unread_mails(user01_token, "user01")
    
    # user01의 받은편지함 확인
    inbox_result = check_inbox(user01_token, "user01")
    
    # 3단계: 결과 분석
    print("\n3️⃣ 3단계: 결과 분석")
    print("=" * 50)
    
    if unread_result and inbox_result:
        unread_count = unread_result.get('total_count', 0) if isinstance(unread_result, dict) else 0
        inbox_count = inbox_result.get('total_count', 0) if isinstance(inbox_result, dict) else 0
        
        print(f"📊 분석 결과:")
        print(f"  - 받은편지함 총 메일 수: {inbox_count}")
        print(f"  - 읽지 않은 메일 수: {unread_count}")
        
        if unread_count > 0:
            print(f"✅ 읽지 않은 메일 API가 정상적으로 작동합니다!")
            print(f"   📧 발송한 메일이 읽지 않은 상태로 수신되었습니다.")
        else:
            print(f"⚠️ 읽지 않은 메일이 0개입니다.")
            if inbox_count > 0:
                print(f"   📧 받은편지함에는 메일이 있지만 읽지 않은 메일로 분류되지 않았습니다.")
                print(f"   🔍 is_read 필드 설정이나 필터링 로직을 확인해야 합니다.")
            else:
                print(f"   📭 받은편지함도 비어있습니다. 메일 수신 로직을 확인해야 합니다.")
    
    print(f"\n🏁 테스트 완료")
    print("=" * 70)
    print(f"종료 시간: {datetime.now()}")

if __name__ == "__main__":
    main()