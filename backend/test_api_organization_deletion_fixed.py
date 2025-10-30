#!/usr/bin/env python3
"""
수정된 서버에서 API를 통한 조직 삭제 테스트
"""

import requests
import json
import time

def test_api_organization_deletion():
    """API를 통한 조직 삭제 테스트 - UPDATE 쿼리가 실행되지 않는지 확인"""
    
    base_url = "http://localhost:8000/api/v1"
    
    try:
        print("🏢 조직 생성 중...")
        
        # 조직 생성 (고유한 이름 사용)
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        
        create_data = {
            "organization": {
                "name": f"API 테스트 조직 {unique_id}",
                "org_code": f"APITEST{unique_id[:4].upper()}",
                "subdomain": f"apitest{unique_id[:4]}",
                "domain": f"apitest{unique_id[:4]}.example.com",
                "description": "API 테스트용 조직",
                "max_storage_gb": 10
            },
            "admin_email": f"admin@apitest{unique_id[:4]}.example.com",
            "admin_password": "TestPassword123!",
            "admin_name": "API 테스트 관리자"
        }
        
        create_response = requests.post(
            f"{base_url}/organizations/",
            json=create_data,
            headers={"Content-Type": "application/json"}
        )
        
        if create_response.status_code != 201:
            print(f"❌ 조직 생성 실패: {create_response.status_code}")
            print(f"응답: {create_response.text}")
            return
        
        org_data = create_response.json()
        org_id = org_data["org_id"]
        org_name = org_data["name"]
        
        print(f"✅ 조직 생성 완료: {org_name} (ID: {org_id})")
        
        # 2초 대기
        print("⏳ 2초 대기 중...")
        time.sleep(2)
        
        # 관리자 로그인하여 토큰 획득
        print("🔐 관리자 로그인 중...")
        login_data = {
            "user_id": "admin",  # 시스템 관리자
            "password": "admin123"
        }
        
        login_response = requests.post(
            f"{base_url}/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        if login_response.status_code != 200:
            print(f"❌ 로그인 실패: {login_response.status_code}")
            print(f"응답: {login_response.text}")
            return
        
        token_data = login_response.json()
        access_token = token_data["access_token"]
        
        print("✅ 로그인 성공")
        
        # 조직 강제 삭제 (하드 삭제)
        print(f"🗑️ 조직 강제 삭제 중: {org_id}")
        
        delete_response = requests.delete(
            f"{base_url}/organizations/{org_id}?force=true",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
        )
        
        if delete_response.status_code == 204:
            print("✅ 조직 삭제 완료!")
            print("📋 서버 로그를 확인하여 다음을 검증하세요:")
            print("   ❌ UPDATE mail_users SET org_id=... 쿼리가 실행되지 않았는지")
            print("   ✅ DELETE FROM organizations WHERE org_id=... 쿼리만 실행되었는지")
        else:
            print(f"❌ 조직 삭제 실패: {delete_response.status_code}")
            print(f"응답: {delete_response.text}")
            
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_api_organization_deletion()