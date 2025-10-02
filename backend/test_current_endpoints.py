#!/usr/bin/env python3
"""
현재 조직 관련 엔드포인트 테스트 스크립트
"""

import requests
import json

# 서버 설정
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

# 테스트 사용자 정보 (admin 사용자)
TEST_USER = {
    "user_id": "admin01",  # admin 사용자 ID
    "email": "user02@example.com",
    "password": "test"
}

def login_user():
    """사용자 로그인"""
    print(f"🔐 사용자 로그인 중: {TEST_USER['user_id']} ({TEST_USER['email']})")
    
    response = requests.post(
        f"{API_BASE}/auth/login",
        json={
            "user_id": TEST_USER["user_id"],  # 실제 user_id 사용
            "password": TEST_USER["password"]
        },
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data["access_token"]
        print(f"✅ 로그인 성공: {access_token[:20]}...")
        return access_token
    else:
        print(f"❌ 로그인 실패: {response.status_code} - {response.text}")
        return None

def test_current_organization(token):
    """현재 조직 정보 조회 테스트"""
    print("\n1. /current 엔드포인트 테스트...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_BASE}/organizations/current", headers=headers)
    
    if response.status_code == 200:
        org_data = response.json()
        print(f"✅ 현재 조직 조회 성공: {org_data['name']}")
        print(f"   - org_id: {org_data['org_id']}")
        print(f"   - max_users: {org_data['max_users']}")
        print(f"   - settings: {org_data['settings']}")
        return org_data
    else:
        print(f"❌ 현재 조직 조회 실패: {response.status_code} - {response.text}")
        return None

def test_current_organization_stats(token):
    """현재 조직 통계 조회 테스트"""
    print("\n2. /current/stats 엔드포인트 테스트...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_BASE}/organizations/current/stats", headers=headers)
    
    if response.status_code == 200:
        stats_data = response.json()
        print(f"✅ 현재 조직 통계 조회 성공")
        print(f"📊 응답 데이터 구조:")
        print(json.dumps(stats_data, indent=2, ensure_ascii=False))
        return stats_data
    else:
        print(f"❌ 현재 조직 통계 조회 실패: {response.status_code} - {response.text}")
        return None

def test_current_organization_settings(token):
    """현재 조직 설정 조회 테스트"""
    print("\n3. /current/settings 엔드포인트 테스트...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_BASE}/organizations/current/settings", headers=headers)
    
    if response.status_code == 200:
        settings_data = response.json()
        print(f"✅ 현재 조직 설정 조회 성공")
        print(f"📊 응답 데이터 구조:")
        print(json.dumps(settings_data, indent=2, ensure_ascii=False))
        return settings_data
    else:
        print(f"❌ 현재 조직 설정 조회 실패: {response.status_code} - {response.text}")
        return None

def main():
    """메인 테스트 함수"""
    print("🔍 현재 조직 엔드포인트 테스트 시작")
    
    # 1. 로그인
    token = login_user()
    if not token:
        print("❌ 로그인 실패로 테스트 중단")
        return
    
    # 2. 현재 조직 정보 조회
    org_data = test_current_organization(token)
    
    # 3. 현재 조직 통계 조회
    stats_data = test_current_organization_stats(token)
    
    # 4. 현재 조직 설정 조회
    settings_data = test_current_organization_settings(token)
    
    print("\n🎉 모든 테스트 완료!")

if __name__ == "__main__":
    main()