#!/usr/bin/env python3
"""
FastAPI 서버를 통해 moonsoo 테스트 사용자 생성

PostgreSQL 직접 연결 대신 API를 통해 사용자를 생성합니다.
"""
import requests
import json
import sys

# FastAPI 서버 URL
BASE_URL = "http://localhost:8000"

def create_moonsoo_user():
    """API를 통해 moonsoo 사용자 생성"""
    
    try:
        # 1. 관리자 로그인하여 토큰 획득
        print("1. 관리자 로그인 중...")
        login_response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={
                "email": "admin@skyboot.com",
                "password": "Admin123!@#"
            }
        )
        
        if login_response.status_code != 200:
            print(f"❌ 관리자 로그인 실패: {login_response.status_code}")
            print(f"응답: {login_response.text}")
            return False
        
        login_data = login_response.json()
        access_token = login_data["access_token"]
        print(f"✅ 관리자 로그인 성공")
        
        # 2. 헤더 설정
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # 3. moonsoo 사용자 생성
        print("2. moonsoo 사용자 생성 중...")
        user_data = {
            "email": "moonsoo@skyboot.com",
            "username": "moonsoo",
            "password": "test",
            "full_name": "문수 테스트"
        }
        
        register_response = requests.post(
            f"{BASE_URL}/api/v1/auth/register",
            json=user_data,
            headers=headers
        )
        
        if register_response.status_code == 201:
            user_info = register_response.json()
            print(f"✅ moonsoo 사용자 생성 성공!")
            print(f"   - 사용자 ID: {user_info.get('user_id')}")
            print(f"   - 이메일: {user_info.get('email')}")
            print(f"   - 조직 ID: {user_info.get('org_id')}")
            
        elif register_response.status_code == 400:
            # 이미 존재하는 사용자일 수 있음
            error_data = register_response.json()
            if "이미 존재" in str(error_data):
                print("⚠️ moonsoo 사용자가 이미 존재합니다.")
            else:
                print(f"❌ 사용자 생성 실패: {error_data}")
                return False
        else:
            print(f"❌ 사용자 생성 실패: {register_response.status_code}")
            print(f"응답: {register_response.text}")
            return False
        
        # 4. moonsoo 사용자 로그인 테스트
        print("3. moonsoo 사용자 로그인 테스트 중...")
        moonsoo_login_response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={
                "email": "moonsoo@skyboot.com",
                "password": "test"
            }
        )
        
        if moonsoo_login_response.status_code == 200:
            moonsoo_data = moonsoo_login_response.json()
            print(f"✅ moonsoo 사용자 로그인 성공!")
            print(f"   - 토큰 타입: {moonsoo_data.get('token_type')}")
            print(f"   - 만료 시간: {moonsoo_data.get('expires_in')}초")
            
            # 5. moonsoo 사용자 정보 조회
            print("4. moonsoo 사용자 정보 조회 중...")
            moonsoo_headers = {
                "Authorization": f"Bearer {moonsoo_data['access_token']}"
            }
            
            me_response = requests.get(
                f"{BASE_URL}/api/v1/auth/me",
                headers=moonsoo_headers
            )
            
            if me_response.status_code == 200:
                me_data = me_response.json()
                print(f"✅ moonsoo 사용자 정보 조회 성공!")
                print(f"   - 사용자명: {me_data.get('username')}")
                print(f"   - 이메일: {me_data.get('email')}")
                print(f"   - 역할: {me_data.get('role')}")
                print(f"   - 활성 상태: {me_data.get('is_active')}")
                
                return True
            else:
                print(f"❌ 사용자 정보 조회 실패: {me_response.status_code}")
                print(f"응답: {me_response.text}")
                return False
        else:
            print(f"❌ moonsoo 사용자 로그인 실패: {moonsoo_login_response.status_code}")
            print(f"응답: {moonsoo_login_response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ FastAPI 서버에 연결할 수 없습니다.")
        print("서버가 실행 중인지 확인해주세요: uvicorn main:app --host 0.0.0.0 --port 8000 --reload")
        return False
    except Exception as e:
        print(f"❌ 예상치 못한 오류 발생: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 FastAPI를 통한 moonsoo 사용자 생성 시작")
    print("=" * 50)
    
    success = create_moonsoo_user()
    
    print("=" * 50)
    if success:
        print("✅ moonsoo 사용자 생성 및 테스트 완료!")
        print("\n📧 이제 다음 단계로 메일 발송 테스트를 진행할 수 있습니다:")
        print("   - 이메일: moonsoo@skyboot.com")
        print("   - 비밀번호: test")
    else:
        print("❌ moonsoo 사용자 생성 실패")
        sys.exit(1)