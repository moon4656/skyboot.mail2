#!/usr/bin/env python3
"""
조직 관련 모든 엔드포인트 종합 테스트 스크립트
"""

import requests
import json
import sys
from datetime import datetime

# 설정
BASE_URL = "http://localhost:8000"
TEST_USER_ID = "admin01"
TEST_PASSWORD = "test"

def get_auth_token():
    """인증 토큰 획득"""
    print("🔐 인증 토큰 획득 중...")
    
    response = requests.post(f"{BASE_URL}/api/v1/auth/login", json={"user_id": TEST_USER_ID, "password": TEST_PASSWORD})
    
    if response.status_code == 200:
        token_data = response.json()
        print(f"✅ 로그인 성공: {TEST_USER_ID}")
        return token_data["access_token"]
    else:
        print(f"❌ 로그인 실패: {response.status_code}")
        print(f"   응답: {response.text}")
        return None

def test_endpoint(method, endpoint, headers, data=None, expected_status=200):
    """엔드포인트 테스트 헬퍼 함수"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, json=data)
        elif method.upper() == "PUT":
            response = requests.put(url, headers=headers, json=data)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            print(f"❌ 지원하지 않는 HTTP 메서드: {method}")
            return False
        
        if response.status_code == expected_status:
            print(f"✅ {method} {endpoint} - 성공 ({response.status_code})")
            return True
        else:
            print(f"❌ {method} {endpoint} - 실패 ({response.status_code})")
            print(f"   응답: {response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"❌ {method} {endpoint} - 예외 발생: {str(e)}")
        return False

def test_organization_endpoints(token):
    """조직 관련 엔드포인트 테스트"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n📋 조직 관련 엔드포인트 테스트 시작")
    print("=" * 60)
    
    # 테스트할 엔드포인트 목록
    endpoints = [
        # 현재 조직 관련 엔드포인트 (우선순위 높음)
        ("GET", "/api/v1/organizations/current", 200),
        ("GET", "/api/v1/organizations/current/stats", 200),
        ("GET", "/api/v1/organizations/current/settings", 200),
        
        # 조직 목록 및 관리 엔드포인트
        ("GET", "/api/v1/organizations/list", 200),
        
        # 특정 조직 ID를 사용한 엔드포인트 (현재 조직 ID 사용)
        # 이 부분은 실제 조직 ID를 얻은 후 테스트
    ]
    
    success_count = 0
    total_count = len(endpoints)
    
    # 기본 엔드포인트 테스트
    for method, endpoint, expected_status in endpoints:
        if test_endpoint(method, endpoint, headers, expected_status=expected_status):
            success_count += 1
    
    # 현재 조직 정보를 얻어서 특정 조직 ID 엔드포인트 테스트
    print("\n🔍 현재 조직 정보 획득 중...")
    response = requests.get(f"{BASE_URL}/api/v1/organizations/current", headers=headers)
    
    if response.status_code == 200:
        org_data = response.json()
        org_id = org_data.get("org_id")
        
        if org_id:
            print(f"📌 현재 조직 ID: {org_id}")
            
            # 특정 조직 ID를 사용한 엔드포인트 테스트
            specific_endpoints = [
                ("GET", f"/api/v1/organizations/{org_id}", 200),
                ("GET", f"/api/v1/organizations/{org_id}/stats", 200),
                ("GET", f"/api/v1/organizations/{org_id}/settings", 200),
            ]
            
            print("\n📋 특정 조직 ID 엔드포인트 테스트")
            print("-" * 40)
            
            for method, endpoint, expected_status in specific_endpoints:
                if test_endpoint(method, endpoint, headers, expected_status=expected_status):
                    success_count += 1
                total_count += 1
        else:
            print("❌ 조직 ID를 찾을 수 없습니다.")
    else:
        print("❌ 현재 조직 정보를 가져올 수 없습니다.")
    
    # 결과 출력
    print("\n" + "=" * 60)
    print(f"📊 테스트 결과: {success_count}/{total_count} 성공")
    
    if success_count == total_count:
        print("🎉 모든 조직 관련 엔드포인트가 정상 작동합니다!")
        return True
    else:
        print(f"⚠️ {total_count - success_count}개의 엔드포인트에서 문제가 발견되었습니다.")
        return False

def test_router_priority():
    """라우터 우선순위 테스트"""
    print("\n🔀 라우터 우선순위 테스트")
    print("=" * 60)
    
    token = get_auth_token()
    if not token:
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # /current/* 경로가 /{org_id}/* 경로보다 우선 처리되는지 확인
    test_cases = [
        ("/api/v1/organizations/current", "현재 조직 정보"),
        ("/api/v1/organizations/current/stats", "현재 조직 통계"),
        ("/api/v1/organizations/current/settings", "현재 조직 설정"),
    ]
    
    all_passed = True
    
    for endpoint, description in test_cases:
        print(f"🧪 {description} 테스트: {endpoint}")
        
        response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
        
        if response.status_code == 200:
            print(f"✅ {description} - 정상 작동")
        else:
            print(f"❌ {description} - 실패 ({response.status_code})")
            print(f"   응답: {response.text[:100]}...")
            all_passed = False
    
    return all_passed

def main():
    """메인 함수"""
    print("🚀 SkyBoot Mail 조직 엔드포인트 종합 테스트")
    print(f"⏰ 테스트 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # 1. 인증 토큰 획득
    token = get_auth_token()
    if not token:
        print("❌ 인증 실패로 테스트를 중단합니다.")
        sys.exit(1)
    
    # 2. 라우터 우선순위 테스트
    router_test_passed = test_router_priority()
    
    # 3. 모든 조직 엔드포인트 테스트
    endpoint_test_passed = test_organization_endpoints(token)
    
    # 4. 최종 결과
    print("\n" + "=" * 80)
    print("🏁 최종 테스트 결과")
    print("=" * 80)
    
    if router_test_passed and endpoint_test_passed:
        print("🎉 모든 테스트가 성공적으로 완료되었습니다!")
        print("✅ 라우터 순서 수정이 정상적으로 적용되었습니다.")
        print("✅ 모든 조직 관련 엔드포인트가 정상 작동합니다.")
        sys.exit(0)
    else:
        print("❌ 일부 테스트에서 문제가 발견되었습니다.")
        if not router_test_passed:
            print("   - 라우터 우선순위 테스트 실패")
        if not endpoint_test_passed:
            print("   - 엔드포인트 테스트 실패")
        sys.exit(1)

if __name__ == "__main__":
    main()