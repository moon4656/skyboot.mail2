#!/usr/bin/env python3
"""
테스트 사용자 생성 스크립트
"""

import requests
import json

def create_test_user():
    """테스트 사용자를 생성합니다."""
    print("Creating test user...")
    
    register_url = "http://localhost:8000/api/v1/auth/register"
    user_data = {
        "user_id": "testuser",
        "email": "testuser@example.com", 
        "username": "testuser",
        "password": "password123"
    }
    
    try:
        print(f"Attempting to register: {user_data['user_id']}")
        response = requests.post(register_url, json=user_data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200 or response.status_code == 201:
            print("✅ User created successfully!")
            return True
        else:
            print("❌ User creation failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_login_with_new_user():
    """새로 생성된 사용자로 로그인을 테스트합니다."""
    print("\nTesting login with new user...")
    
    login_url = "http://localhost:8000/api/v1/auth/login"
    login_data = {
        "user_id": "testuser",
        "password": "password123"
    }
    
    try:
        response = requests.post(login_url, json=login_data)
        print(f"Login Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Login successful!")
            print(f"Token: {result.get('access_token', '')[:20]}...")
            return result.get('access_token')
        else:
            print(f"❌ Login failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    # 사용자 생성 시도
    if create_test_user():
        # 로그인 테스트
        token = test_login_with_new_user()
        if token:
            print(f"\n🎉 Ready for mail testing with token: {token[:20]}...")
        else:
            print("\n❌ Login test failed")
    else:
        print("\n❌ User creation failed")