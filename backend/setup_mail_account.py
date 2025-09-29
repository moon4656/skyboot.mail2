#!/usr/bin/env python3
"""
메일 계정 초기화 스크립트

사용자의 메일 계정을 초기화하여 메일 사용자를 생성합니다.
"""

import requests
import json
import sys

# API 기본 설정
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

def login_user(email: str, password: str) -> str:
    """
    사용자 로그인하여 액세스 토큰을 반환합니다.
    
    Args:
        email: 사용자 이메일
        password: 비밀번호
    
    Returns:
        액세스 토큰 또는 None
    """
    print(f"🔐 로그인 시도 - {email}")
    
    login_data = {
        "email": email,
        "password": password
    }
    
    try:
        response = requests.post(f"{API_BASE}/auth/login", json=login_data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            access_token = result.get('access_token')
            print(f"✅ 로그인 성공")
            return access_token
        else:
            print(f"❌ 로그인 실패: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 로그인 요청 오류: {str(e)}")
        return None

def setup_mail_account(access_token: str) -> bool:
    """
    메일 계정을 초기화합니다.
    
    Args:
        access_token: 액세스 토큰
    
    Returns:
        초기화 성공 여부
    """
    print(f"\n📧 메일 계정 초기화 시도")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(f"{API_BASE}/mail/setup-mail-account", headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 메일 계정 초기화 성공")
            print(f"Message: {result.get('message', 'N/A')}")
            
            data = result.get('data', {})
            if data:
                print(f"Mail User ID: {data.get('mail_user_id', 'N/A')}")
                print(f"Email: {data.get('email', 'N/A')}")
            
            return True
        else:
            print(f"❌ 메일 계정 초기화 실패: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 메일 계정 초기화 요청 오류: {str(e)}")
        return False

def test_inbox_after_setup(access_token: str) -> bool:
    """
    메일 계정 초기화 후 받은 메일함을 테스트합니다.
    
    Args:
        access_token: 액세스 토큰
    
    Returns:
        테스트 성공 여부
    """
    print(f"\n📥 받은 메일함 테스트")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(f"{API_BASE}/mail/inbox", headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 받은 메일함 조회 성공")
            
            data = result.get('data', {})
            mails = data.get('mails', [])
            total = data.get('total', 0)
            
            print(f"총 메일 수: {total}")
            print(f"현재 페이지 메일 수: {len(mails)}")
            
            return True
        else:
            print(f"❌ 받은 메일함 조회 실패: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 받은 메일함 조회 요청 오류: {str(e)}")
        return False

def main():
    """메인 함수"""
    print("🧪 메일 계정 초기화 및 테스트")
    print("=" * 50)
    
    # 테스트 사용자 정보
    email = "admin@skyboot.kr"
    password = "admin123"
    
    # 1. 로그인
    access_token = login_user(email, password)
    if not access_token:
        print("❌ 로그인 실패로 테스트 중단")
        sys.exit(1)
    
    # 2. 메일 계정 초기화
    if not setup_mail_account(access_token):
        print("❌ 메일 계정 초기화 실패로 테스트 중단")
        sys.exit(1)
    
    # 3. 받은 메일함 테스트
    if test_inbox_after_setup(access_token):
        print("\n🎉 모든 테스트 성공!")
        sys.exit(0)
    else:
        print("\n⚠️ 받은 메일함 테스트 실패")
        sys.exit(1)

if __name__ == "__main__":
    main()