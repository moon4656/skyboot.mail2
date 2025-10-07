#!/usr/bin/env python3
"""
수신자 사용자 로그인 테스트
- testuser_folder@example.com 사용자의 로그인 정보 확인
- 다양한 패스워드 조합 시도
"""

import requests
import json

# API 기본 설정
BASE_URL = "http://localhost:8001"

def try_login(user_id, password):
    """로그인 시도"""
    print(f"🔐 로그인 시도: {user_id} / {password}")
    
    login_data = {
        "user_id":  "user01",
        "password": "test"
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        headers=headers,
        json=login_data
    )
    
    print(f"응답 상태: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        token = result.get("access_token")
        print(f"✅ 로그인 성공! 토큰: {token[:50]}...")
        return token
    else:
        print(f"❌ 로그인 실패: {response.text}")
        return None

def main():
    """메인 함수"""
    print("=== 수신자 사용자 로그인 테스트 ===")
    
    # 다양한 패스워드 조합 시도
    test_combinations = [
        ("testuser_folder", "password"),
        ("testuser_folder", "test"),
        ("testuser_folder", "123456"),
        ("testuser_folder", "testuser_folder"),
        ("testuser_folder@example.com", "password"),
        ("testuser_folder@example.com", "test"),
        ("testuser_folder@example.com", "123456"),
        ("testuser_folder@example.com", "testuser_folder"),
    ]
    
    for user_id, password in test_combinations:
        token = try_login(user_id, password)
        if token:
            print(f"🎉 성공한 조합: {user_id} / {password}")
            break
        print()
    else:
        print("❌ 모든 로그인 시도 실패")
    
    print("\n=== 테스트 완료 ===")

if __name__ == "__main__":
    main()