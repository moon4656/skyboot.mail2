#!/usr/bin/env python3
"""
조직 관련 현재 엔드포인트 테스트 스크립트
"""

import requests
import json

# 테스트 설정
BASE_URL = "http://localhost:8000"
TEST_USER = {
    "user_id": "admin01",
    "email": "user02@example.com", 
    "password": "test"
}

def login():
    """로그인하여 토큰 획득"""
    login_url = f"{BASE_URL}/api/v1/auth/login"
    login_data = {
        "user_id": TEST_USER["user_id"],
        "password": TEST_USER["password"]
    }
    
    print(f"🔐 로그인 시도 - user_id: {TEST_USER['user_id']}, email: {TEST_USER['email']}")
    response = requests.post(login_url, json=login_data)
    
    if response.status_code == 200:
        token_data = response.json()
        print(f"✅ 로그인 성공: {token_data.get('access_token', 'No token')[:50]}...")
        return token_data["access_token"]
    else:
        print(f"❌ 로그인 실패: {response.status_code} - {response.text}")
        return None

def test_current_endpoints(token):
    """현재 조직 관련 엔드포인트 테스트"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. 현재 조직 정보 조회
    print("\n📋 1. 현재 조직 정보 조회 (/organizations/current)")
    response = requests.get(f"{BASE_URL}/api/v1/organizations/current", headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        org_data = response.json()
        print(f"✅ 조직 정보: {org_data.get('name', 'Unknown')} (org_id: {org_data.get('org_id', 'Unknown')})")
    else:
        print(f"❌ 실패: {response.text}")
        return
    
    # 2. 현재 조직 통계 조회
    print("\n📊 2. 현재 조직 통계 조회 (/organizations/current/stats)")
    response = requests.get(f"{BASE_URL}/api/v1/organizations/current/stats", headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        stats_data = response.json()
        print(f"✅ 통계 정보: {json.dumps(stats_data, indent=2, ensure_ascii=False)}")
    else:
        print(f"❌ 실패: {response.text}")
    
    # 3. 현재 조직 설정 조회
    print("\n⚙️ 3. 현재 조직 설정 조회 (/organizations/current/settings)")
    response = requests.get(f"{BASE_URL}/api/v1/organizations/current/settings", headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        settings_data = response.json()
        print(f"✅ 설정 정보: {json.dumps(settings_data, indent=2, ensure_ascii=False)}")
    else:
        print(f"❌ 실패: {response.text}")

def main():
    print("🚀 조직 관련 현재 엔드포인트 테스트 시작")
    print("=" * 50)
    
    # 로그인
    token = login()
    if not token:
        print("❌ 로그인 실패로 테스트 중단")
        return
    
    # 엔드포인트 테스트
    test_current_endpoints(token)
    
    print("\n" + "=" * 50)
    print("🏁 테스트 완료")

if __name__ == "__main__":
    main()