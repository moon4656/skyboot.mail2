#!/usr/bin/env python3
"""
메일 발송 후 읽지 않은 메일 API 테스트
"""

import requests
import json
from datetime import datetime

# API 기본 설정
BASE_URL = "http://localhost:8001"
LOGIN_URL = f"{BASE_URL}/api/v1/auth/login"
UNREAD_MAIL_URL = f"{BASE_URL}/api/v1/mail/unread"
INBOX_URL = f"{BASE_URL}/api/v1/mail/inbox"

def login_user(email: str, password: str):
    """사용자 로그인"""
    print(f"🔐 사용자 로그인 중...")
    print("=" * 50)
    
    login_data = {
        "user_id": email,  # API가 user_id 필드를 요구함
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

def check_unread_mails(token: str):
    """읽지 않은 메일 확인"""
    print(f"\n📧 읽지 않은 메일 확인")
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
                    print(f"    {i}. ID: {mail_id}, 제목: {subject}")
                    print(f"       생성일: {created_at}, 폴더: {folder_name}")
            else:
                print(f"  📭 읽지 않은 메일이 없습니다.")
        else:
            print(f"  📊 응답 데이터: {data}")
        
        return data
    else:
        print(f"❌ 읽지 않은 메일 조회 실패: {response.text}")
        return None

def check_inbox(token: str):
    """받은편지함 확인"""
    print(f"\n📥 받은편지함 확인")
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
    print("🧪 메일 발송 후 읽지 않은 메일 API 테스트")
    print(f"시작 시간: {datetime.now()}")
    print("=" * 70)
    
    # admin01로 로그인 (기존에 성공했던 계정)
    token = login_user("admin01", "test")
    if not token:
        print("❌ 로그인 실패로 테스트 중단")
        return
    
    # 읽지 않은 메일 확인
    unread_result = check_unread_mails(token)
    
    # 받은편지함 확인
    inbox_result = check_inbox(token)
    
    print(f"\n🏁 테스트 완료")
    print("=" * 70)
    print(f"종료 시간: {datetime.now()}")

if __name__ == "__main__":
    main()