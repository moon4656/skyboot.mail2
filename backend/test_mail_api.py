#!/usr/bin/env python3
"""
메일 API 테스트 스크립트

받은 메일함, 보낸 메일함, 휴지통 API를 테스트합니다.
"""

import requests
import json
import sys
from typing import Dict, Any

# API 기본 설정
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

def test_login(email: str, password: str) -> Dict[str, Any]:
    """
    로그인 테스트
    
    Args:
        email: 사용자 이메일
        password: 비밀번호
    
    Returns:
        로그인 결과 (토큰 포함)
    """
    print(f"\n🔐 로그인 테스트 - {email}")
    
    login_data = {
        "email": email,
        "password": password
    }
    
    try:
        response = requests.post(f"{API_BASE}/auth/login", json=login_data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 로그인 성공")
            print(f"Access Token: {result.get('access_token', 'N/A')[:50]}...")
            return result
        else:
            print(f"❌ 로그인 실패: {response.text}")
            return {}
            
    except Exception as e:
        print(f"❌ 로그인 요청 오류: {str(e)}")
        return {}

def test_inbox_api(access_token: str) -> bool:
    """
    받은 메일함 API 테스트
    
    Args:
        access_token: 인증 토큰
    
    Returns:
        테스트 성공 여부
    """
    print(f"\n📥 받은 메일함 API 테스트")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    try:
        # 받은 메일함 조회
        response = requests.get(f"{API_BASE}/mail/inbox", headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 받은 메일함 조회 성공")
            print(f"메일 수: {len(result.get('mails', []))}")
            print(f"총 개수: {result.get('total', 0)}")
            return True
        else:
            print(f"❌ 받은 메일함 조회 실패: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 받은 메일함 API 요청 오류: {str(e)}")
        return False

def test_sent_api(access_token: str) -> bool:
    """
    보낸 메일함 API 테스트
    
    Args:
        access_token: 인증 토큰
    
    Returns:
        테스트 성공 여부
    """
    print(f"\n📤 보낸 메일함 API 테스트")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    try:
        # 보낸 메일함 조회
        response = requests.get(f"{API_BASE}/mail/sent", headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 보낸 메일함 조회 성공")
            print(f"메일 수: {len(result.get('mails', []))}")
            print(f"총 개수: {result.get('total', 0)}")
            return True
        else:
            print(f"❌ 보낸 메일함 조회 실패: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 보낸 메일함 API 요청 오류: {str(e)}")
        return False

def test_trash_api(access_token: str) -> bool:
    """
    휴지통 API 테스트
    
    Args:
        access_token: 인증 토큰
    
    Returns:
        테스트 성공 여부
    """
    print(f"\n🗑️ 휴지통 API 테스트")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    try:
        # 휴지통 조회
        response = requests.get(f"{API_BASE}/mail/trash", headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 휴지통 조회 성공")
            print(f"메일 수: {len(result.get('mails', []))}")
            print(f"총 개수: {result.get('total', 0)}")
            return True
        else:
            print(f"❌ 휴지통 조회 실패: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 휴지통 API 요청 오류: {str(e)}")
        return False

def main():
    """메인 테스트 함수"""
    print("🧪 메일 API 테스트 시작")
    print("=" * 50)
    
    # 테스트할 계정들
    test_accounts = [
        {"email": "user@skyboot.com", "password": "password123"},
    ]
    
    success_count = 0
    total_tests = 0
    
    for account in test_accounts:
        email = account["email"]
        password = account["password"]
        
        print(f"\n{'='*50}")
        print(f"🧪 테스트 계정: {email}")
        print(f"{'='*50}")
        
        # 로그인 테스트
        login_result = test_login(email, password)
        
        if login_result and "access_token" in login_result:
            access_token = login_result["access_token"]
            
            # 각 API 테스트
            tests = [
                ("받은 메일함", test_inbox_api),
                ("보낸 메일함", test_sent_api),
                ("휴지통", test_trash_api),
            ]
            
            for test_name, test_func in tests:
                total_tests += 1
                if test_func(access_token):
                    success_count += 1
                    print(f"✅ {test_name} 테스트 성공")
                else:
                    print(f"❌ {test_name} 테스트 실패")
        else:
            print(f"❌ {email} 로그인 실패로 API 테스트 건너뜀")
            total_tests += 3  # 3개 API 테스트를 건너뜀
    
    # 결과 요약
    print(f"\n{'='*50}")
    print(f"🏁 테스트 결과 요약")
    print(f"{'='*50}")
    print(f"총 테스트: {total_tests}")
    print(f"성공: {success_count}")
    print(f"실패: {total_tests - success_count}")
    print(f"성공률: {(success_count/total_tests*100):.1f}%" if total_tests > 0 else "0%")
    
    if success_count == total_tests:
        print(f"🎉 모든 테스트 성공!")
        sys.exit(0)
    else:
        print(f"⚠️ 일부 테스트 실패")
        sys.exit(1)

if __name__ == "__main__":
    main()