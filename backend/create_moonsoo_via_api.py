#!/usr/bin/env python3
"""
FastAPI를 통해 moonsoo 테스트 사용자 생성 스크립트
외부 메일 발송 테스트를 위한 사용자 계정 생성
"""

import requests
import json
import sys

# API 서버 설정
API_BASE_URL = "http://localhost:8000"

def create_moonsoo_user_via_api():
    """FastAPI를 통해 moonsoo 테스트 사용자 생성"""
    try:
        print("🔧 FastAPI를 통해 moonsoo 테스트 사용자 생성 중...")
        
        # 1. 먼저 admin 계정으로 로그인하여 토큰 획득
        print("🔑 관리자 계정으로 로그인 중...")
        login_data = {
            "username": "admin@skyboot.com",
            "password": "admin123"
        }
        
        login_response = requests.post(
            f"{API_BASE_URL}/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if login_response.status_code != 200:
            print(f"❌ 관리자 로그인 실패: {login_response.status_code}")
            print(f"응답: {login_response.text}")
            return False
        
        login_result = login_response.json()
        access_token = login_result.get("access_token")
        
        if not access_token:
            print("❌ 액세스 토큰을 받지 못했습니다.")
            return False
        
        print("✅ 관리자 로그인 성공")
        
        # 2. 조직 정보 확인
        print("🏢 조직 정보 확인 중...")
        headers = {"Authorization": f"Bearer {access_token}"}
        
        org_response = requests.get(
            f"{API_BASE_URL}/organizations/",
            headers=headers
        )
        
        if org_response.status_code == 200:
            organizations = org_response.json()
            print(f"✅ 조직 목록 확인: {len(organizations)}개 조직")
            
            # SkyBoot 조직 찾기
            skyboot_org = None
            for org in organizations:
                if org.get("org_code") == "SKYBOOT":
                    skyboot_org = org
                    break
            
            if not skyboot_org:
                print("❌ SkyBoot 조직을 찾을 수 없습니다.")
                return False
            
            print(f"✅ SkyBoot 조직 확인: {skyboot_org['name']}")
        else:
            print(f"⚠️ 조직 정보 확인 실패: {org_response.status_code}")
            print("기본 조직으로 진행합니다.")
        
        # 3. moonsoo 사용자 생성
        print("👤 moonsoo 사용자 생성 중...")
        user_data = {
            "username": "moonsoo",
            "email": "moonsoo@skyboot.com",
            "password": "test",
            "role": "user",
            "is_active": True,
            "is_email_verified": True
        }
        
        user_response = requests.post(
            f"{API_BASE_URL}/users/",
            json=user_data,
            headers=headers
        )
        
        if user_response.status_code == 201:
            user_result = user_response.json()
            print("✅ moonsoo 테스트 사용자 생성 완료")
            print(f"   - 이메일: {user_result.get('email')}")
            print(f"   - 사용자명: {user_result.get('username')}")
            print(f"   - 비밀번호: test")
            print(f"   - 역할: {user_result.get('role')}")
            return True
        elif user_response.status_code == 400:
            error_detail = user_response.json()
            if "already exists" in str(error_detail).lower():
                print("⚠️ moonsoo 사용자가 이미 존재합니다.")
                print("✅ 기존 사용자를 사용합니다.")
                return True
            else:
                print(f"❌ 사용자 생성 실패: {error_detail}")
                return False
        else:
            print(f"❌ 사용자 생성 실패: {user_response.status_code}")
            print(f"응답: {user_response.text}")
            return False
        
    except requests.exceptions.ConnectionError:
        print("❌ FastAPI 서버에 연결할 수 없습니다.")
        print("서버가 실행 중인지 확인해주세요: http://localhost:8000")
        return False
    except Exception as e:
        print(f"❌ 사용자 생성 실패: {e}")
        return False

def test_moonsoo_login():
    """moonsoo 사용자 로그인 테스트"""
    try:
        print("\n🔐 moonsoo 사용자 로그인 테스트 중...")
        
        login_data = {
            "username": "moonsoo@skyboot.com",
            "password": "test"
        }
        
        login_response = requests.post(
            f"{API_BASE_URL}/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if login_response.status_code == 200:
            login_result = login_response.json()
            print("✅ moonsoo 사용자 로그인 성공")
            print(f"   - 토큰 타입: {login_result.get('token_type')}")
            print(f"   - 액세스 토큰: {login_result.get('access_token')[:20]}...")
            return True
        else:
            print(f"❌ moonsoo 사용자 로그인 실패: {login_response.status_code}")
            print(f"응답: {login_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 로그인 테스트 실패: {e}")
        return False

if __name__ == "__main__":
    print("🚀 FastAPI를 통한 moonsoo 테스트 사용자 생성 시작")
    
    # 사용자 생성
    user_created = create_moonsoo_user_via_api()
    
    if user_created:
        # 로그인 테스트
        login_success = test_moonsoo_login()
        
        if login_success:
            print("\n✅ 모든 작업이 완료되었습니다!")
            print("📧 이제 moonsoo@skyboot.com 계정으로 메일 발송 테스트를 진행할 수 있습니다.")
        else:
            print("\n⚠️ 사용자는 생성되었지만 로그인 테스트에 실패했습니다.")
    else:
        print("\n❌ 사용자 생성에 실패했습니다.")
        sys.exit(1)