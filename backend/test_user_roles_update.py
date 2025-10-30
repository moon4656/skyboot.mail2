#!/usr/bin/env python3
"""
사용자 정보 수정에서 roles 필드 업데이트 테스트 스크립트
"""

import requests
import json
import sys

# API 기본 설정
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

def login_admin():
    """관리자 로그인"""
    login_data = {
        "user_id": "admin",
        "password": "test"
    }
    
    response = requests.post(f"{API_BASE}/auth/login", json=login_data)
    if response.status_code == 200:
        token_data = response.json()
        return token_data["access_token"]
    else:
        print(f"❌ 관리자 로그인 실패: {response.status_code}")
        print(f"응답: {response.text}")
        return None

def get_user_info(access_token, user_id):
    """사용자 정보 조회"""
    headers = {"Authorization": f"Bearer {access_token}"}
    
    response = requests.get(f"{API_BASE}/users/{user_id}", headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ 사용자 정보 조회 실패: {response.status_code}")
        print(f"응답: {response.text}")
        return None

def update_user_roles(access_token, user_id, update_data):
    """사용자 정보 수정 (roles 포함)"""
    headers = {"Authorization": f"Bearer {access_token}"}
    
    response = requests.put(f"{API_BASE}/users/{user_id}", headers=headers, json=update_data)
    print(f"📤 사용자 정보 수정 요청:")
    print(f"   URL: {API_BASE}/users/{user_id}")
    print(f"   데이터: {json.dumps(update_data, ensure_ascii=False, indent=2)}")
    print(f"   응답 상태: {response.status_code}")
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ 사용자 정보 수정 실패: {response.status_code}")
        print(f"응답: {response.text}")
        return None

def main():
    print("🧪 사용자 roles 필드 업데이트 테스트 시작")
    print("=" * 50)
    
    # 1. 관리자 로그인
    print("\n1️⃣ 관리자 로그인")
    access_token = login_admin()
    if not access_token:
        sys.exit(1)
    print("✅ 관리자 로그인 성공")
    
    # 2. 테스트할 사용자 ID (기존 사용자 사용)
    test_user_id = "admin"  # admin 사용자 자신을 테스트
    
    # 3. 수정 전 사용자 정보 조회
    print(f"\n2️⃣ 수정 전 사용자 정보 조회 (user_id: {test_user_id})")
    user_before = get_user_info(access_token, test_user_id)
    if not user_before:
        sys.exit(1)
    
    print(f"수정 전 사용자 정보:")
    print(f"  - username: {user_before.get('username')}")
    print(f"  - full_name: {user_before.get('full_name')}")
    print(f"  - role: {user_before.get('role')}")
    print(f"  - is_active: {user_before.get('is_active')}")
    
    # 4. 사용자 정보 수정 (roles 필드 포함)
    print(f"\n3️⃣ 사용자 정보 수정 (roles 필드 포함)")
    import time
    unique_suffix = int(time.time())
    update_data = {
        "is_active": True,
        "roles": ["admin"],
        "username": f"admin_updated_{unique_suffix}"
    }
    
    updated_user = update_user_roles(access_token, test_user_id, update_data)
    if not updated_user:
        sys.exit(1)
    
    print("✅ 사용자 정보 수정 성공")
    print(f"수정 후 응답:")
    print(json.dumps(updated_user, ensure_ascii=False, indent=2))
    
    # 5. 수정 후 사용자 정보 재조회
    print(f"\n4️⃣ 수정 후 사용자 정보 재조회")
    user_after = get_user_info(access_token, test_user_id)
    if not user_after:
        sys.exit(1)
    
    print(f"수정 후 사용자 정보:")
    print(f"  - username: {user_after.get('username')}")
    print(f"  - full_name: {user_after.get('full_name')}")
    print(f"  - role: {user_after.get('role')}")
    print(f"  - is_active: {user_after.get('is_active')}")
    
    # 6. 결과 검증
    print(f"\n5️⃣ 결과 검증")
    
    # role 필드가 변경되었는지 확인
    expected_role = update_data["roles"][0]  # "admin"
    actual_role = user_after.get("role")
    
    if actual_role == expected_role:
        print(f"✅ roles 필드 업데이트 성공: {expected_role}")
    else:
        print(f"❌ roles 필드 업데이트 실패:")
        print(f"   기대값: {expected_role}")
        print(f"   실제값: {actual_role}")
    
    # 다른 필드들도 확인
    if user_after.get("username") == update_data["username"]:
        print(f"✅ username 필드 업데이트 성공: {update_data['username']}")
    else:
        print(f"❌ username 필드 업데이트 실패")
    
    if user_after.get("is_active") == update_data["is_active"]:
        print(f"✅ is_active 필드 업데이트 성공: {update_data['is_active']}")
    else:
        print(f"❌ is_active 필드 업데이트 실패")
    
    print("\n🎉 테스트 완료!")

if __name__ == "__main__":
    main()