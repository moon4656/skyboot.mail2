#!/usr/bin/env python3
"""
test@skyboot.kr 사용자의 메일 계정 초기화 스크립트
"""

import requests
import json
import sys

# API 기본 설정
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"
TEST_EMAIL = "test@skyboot.kr"
TEST_PASSWORD = "test123"

def login():
    """로그인하여 토큰 획득"""
    print("🔐 로그인 중...")
    
    login_data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    }
    
    try:
        response = requests.post(f"{BASE_URL}{API_PREFIX}/auth/login", json=login_data)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 로그인 성공!")
            return result.get('access_token')
        else:
            print(f"❌ 로그인 실패: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 로그인 오류: {e}")
        return None

def setup_mail_account(token):
    """메일 계정 초기화"""
    print("\n📧 메일 계정 초기화 중...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(f"{BASE_URL}{API_PREFIX}/mail/setup-mail-account", headers=headers)
        print(f"메일 계정 초기화 응답 상태: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 메일 계정 초기화 성공!")
            print(f"메일 사용자 UUID: {result.get('data', {}).get('user_uuid')}")
            print(f"이메일: {result.get('data', {}).get('email')}")
            print(f"표시명: {result.get('data', {}).get('display_name')}")
            return True
        else:
            print(f"❌ 메일 계정 초기화 실패: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 메일 계정 초기화 오류: {e}")
        return False

def test_inbox_after_setup(token):
    """메일 계정 설정 후 inbox 테스트"""
    print("\n📬 Inbox 테스트...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(f"{BASE_URL}{API_PREFIX}/mail/inbox", headers=headers)
        print(f"Inbox API 응답 상태: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Inbox API 성공!")
            print(f"총 메일 수: {result.get('total_count', 0)}")
            return True
        else:
            print(f"❌ Inbox API 실패: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Inbox API 오류: {e}")
        return False

def main():
    """메인 함수"""
    print("=" * 60)
    print("📧 test@skyboot.kr 메일 계정 초기화 및 테스트")
    print("=" * 60)
    
    # 1. 로그인
    token = login()
    if not token:
        print("❌ 로그인 실패로 중단")
        sys.exit(1)
    
    # 2. 메일 계정 초기화
    setup_success = setup_mail_account(token)
    if not setup_success:
        print("❌ 메일 계정 초기화 실패")
        sys.exit(1)
    
    # 3. Inbox 테스트
    inbox_success = test_inbox_after_setup(token)
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("📋 결과 요약")
    print("=" * 60)
    print(f"로그인: ✅ 성공")
    print(f"메일 계정 초기화: {'✅ 성공' if setup_success else '❌ 실패'}")
    print(f"Inbox API: {'✅ 성공' if inbox_success else '❌ 실패'}")
    
    if setup_success and inbox_success:
        print("\n🎉 모든 작업 완료! MailFolder.user_uuid -> user_id 수정이 성공적으로 적용되었습니다.")
        return True
    else:
        print("\n⚠️ 일부 작업 실패")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)