#!/usr/bin/env python3
"""
사용자 API 테스트 스크립트

수정된 스키마로 사용자 등록 및 로그인을 테스트합니다.
"""
import requests
import json
import sys
import time

# API 기본 URL
BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_server_status():
    """서버 상태 확인"""
    try:
        # health 엔드포인트는 /health에 있음 (API 버전 없음)
        response = requests.get("http://127.0.0.1:8000/health")
        print(f"✅ 서버 상태: {response.status_code}")
        if response.status_code == 200:
            print(f"   응답: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ 서버 연결 실패: {e}")
        return False

def test_user_registration():
    """사용자 등록 테스트"""
    print("\n📝 사용자 등록 테스트")
    
    # 테스트 사용자 데이터 (타임스탬프로 고유한 이메일 생성)
    timestamp = int(time.time())
    user_data = {
        "email": f"admin{timestamp}@skyboot.com",
        "username": f"admin{timestamp}",
        "password": "admin123"
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-Tenant-ID": "skyboot"  # 기본 조직
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/register",
            json=user_data,
            headers=headers
        )
        
        print(f"   상태 코드: {response.status_code}")
        print(f"   응답 헤더: {dict(response.headers)}")
        
        if response.status_code == 201:
            user_info = response.json()
            print(f"✅ 사용자 등록 성공!")
            print(f"   사용자 ID: {user_info.get('user_id')}")
            print(f"   이메일: {user_info.get('email')}")
            print(f"   사용자명: {user_info.get('username')}")
            return user_data  # 등록된 사용자 데이터 반환
        else:
            print(f"❌ 사용자 등록 실패")
            print(f"   응답: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 등록 요청 오류: {e}")
        return None

def test_user_login(user_data):
    """사용자 로그인 테스트"""
    print("\n🔐 사용자 로그인 테스트")
    
    # 로그인 데이터 (등록된 사용자 정보 사용)
    login_data = {
        "email": user_data["email"],
        "password": user_data["password"]
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-Tenant-ID": "skyboot"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json=login_data,
            headers=headers
        )
        
        print(f"   상태 코드: {response.status_code}")
        
        if response.status_code == 200:
            login_info = response.json()
            print(f"✅ 로그인 성공!")
            print(f"   액세스 토큰: {login_info.get('access_token')[:50]}...")
            print(f"   토큰 타입: {login_info.get('token_type')}")
            return login_info.get('access_token')
        else:
            print(f"❌ 로그인 실패")
            print(f"   응답: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 로그인 요청 오류: {e}")
        return None

def test_protected_endpoint(access_token):
    """보호된 엔드포인트 테스트"""
    print("\n🔒 보호된 엔드포인트 테스트")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-Tenant-ID": "skyboot"
    }
    
    try:
        response = requests.get(
            f"{BASE_URL}/auth/me",
            headers=headers
        )
        
        print(f"   상태 코드: {response.status_code}")
        
        if response.status_code == 200:
            user_info = response.json()
            print(f"✅ 사용자 정보 조회 성공!")
            print(f"   사용자 ID: {user_info.get('id')}")
            print(f"   이메일: {user_info.get('email')}")
            return True
        else:
            print(f"❌ 사용자 정보 조회 실패")
            print(f"   응답: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 요청 오류: {e}")
        return False

def main():
    """메인 테스트 함수"""
    print("🚀 사용자 API 테스트 시작")
    print("=" * 50)
    
    # 1. 서버 상태 확인
    if not test_server_status():
        print("❌ 서버가 실행되지 않았습니다. 테스트를 중단합니다.")
        sys.exit(1)
    
    # 2. 사용자 등록 테스트
    user_data = test_user_registration()
    if not user_data:
        print("❌ 사용자 등록 실패. 테스트를 중단합니다.")
        sys.exit(1)
    
    # 3. 사용자 로그인 테스트
    access_token = test_user_login(user_data)
    if not access_token:
        print("❌ 로그인 실패. 테스트를 중단합니다.")
        sys.exit(1)
    
    # 4. 보호된 엔드포인트 테스트
    if not test_protected_endpoint(access_token):
        print("❌ 보호된 엔드포인트 테스트 실패.")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("🎉 모든 테스트가 성공적으로 완료되었습니다!")

if __name__ == "__main__":
    main()