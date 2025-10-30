#!/usr/bin/env python3
"""
API를 통한 조직 삭제 테스트 스크립트
불필요한 UPDATE 쿼리가 발생하지 않는지 확인
"""

import requests
import json
import time

# API 기본 설정
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

def test_organization_deletion_via_api():
    """API를 통한 조직 삭제 테스트"""
    print("🔍 API를 통한 조직 삭제 테스트 시작")
    
    # 1. 조직 생성
    print("\n📝 1. 테스트 조직 생성")
    org_data = {
        "organization": {
            "name": "API 테스트 조직",
            "org_code": "apitest",
            "subdomain": "apitest",
            "description": "API 테스트용 조직",
            "domain": "apitest.com",
            "max_users": 100,
            "max_storage_gb": 50
        },
        "admin_email": "admin@apitest.com",
        "admin_password": "test123!@#",
        "admin_name": "API 테스트 관리자"
    }
    
    try:
        response = requests.post(f"{API_BASE}/organizations/", json=org_data)
        if response.status_code == 201:
            org_result = response.json()
            org_id = org_result["org_id"]
            print(f"✅ 조직 생성 성공: {org_result['name']}")
            print(f"   - 조직 ID: {org_id}")
        else:
            print(f"❌ 조직 생성 실패: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"❌ 조직 생성 중 오류: {e}")
        return
    
    # 2. 잠시 대기 (로그 확인을 위해)
    print("\n⏳ 2초 대기 중...")
    time.sleep(2)
    
    # 3. 조직 삭제 (force=true)
    print(f"\n🗑️ 2. 조직 삭제 테스트 (ID: {org_id})")
    try:
        response = requests.delete(f"{API_BASE}/organizations/{org_id}?force=true")
        if response.status_code == 200:
            print("✅ 조직 삭제 성공")
            print("   - 서버 로그를 확인하여 불필요한 UPDATE 쿼리가 없는지 확인하세요")
        else:
            print(f"❌ 조직 삭제 실패: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ 조직 삭제 중 오류: {e}")
    
    print("\n🔍 API 테스트 완료")
    print("📋 서버 터미널에서 다음을 확인하세요:")
    print("   - UPDATE mail_users SET org_id=... 쿼리가 없어야 함")
    print("   - DELETE FROM organizations WHERE org_id=... 쿼리만 있어야 함")

if __name__ == "__main__":
    test_organization_deletion_via_api()