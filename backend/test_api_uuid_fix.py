#!/usr/bin/env python3
"""
UUID 수정 후 API 엔드포인트 테스트 스크립트
"""

import requests
import json
import uuid
import time

BASE_URL = "http://localhost:8000"

def test_user_registration():
    """사용자 등록 테스트 (UUID 생성 포함)"""
    print("🧪 사용자 등록 테스트 시작...")
    
    try:
        # 고유한 사용자 정보 생성
        unique_id = str(uuid.uuid4())[:8]
        user_data = {
            "email": f"test_{unique_id}@skyboot.com",
            "username": f"testuser_{unique_id}",
            "password": "testpassword123",
            "org_id": "test_org_001"
        }
        
        print(f"   등록할 사용자: {user_data['email']}")
        
        response = requests.post(f"{BASE_URL}/api/v1/auth/register", json=user_data)
        
        if response.status_code == 201:
            result = response.json()
            print(f"   ✅ 사용자 등록 성공")
            print(f"   전체 응답: {result}")
            print(f"   사용자 UUID: {result.get('user_uuid', 'N/A')}")
            return True, result
        else:
            print(f"   ❌ 사용자 등록 실패: {response.status_code}")
            print(f"   응답: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"   ❌ 사용자 등록 중 오류: {str(e)}")
        return False, None

def test_mail_folder_creation(access_token):
    """메일 폴더 생성 테스트 (UUID 생성 포함)"""
    print("\n🧪 메일 폴더 생성 테스트 시작...")
    
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        folder_data = {
            "name": f"테스트폴더_{str(uuid.uuid4())[:8]}",
            "folder_type": "custom"
        }
        
        print(f"   생성할 폴더: {folder_data['name']}")
        
        response = requests.post(f"{BASE_URL}/api/v1/mail/folders", json=folder_data, headers=headers)
        
        if response.status_code in [200, 201]:
            result = response.json()
            print(f"   ✅ 폴더 생성 성공")
            print(f"   폴더 UUID: {result.get('folder_uuid', 'N/A')}")
            return True, result
        else:
            print(f"   ❌ 폴더 생성 실패: {response.status_code}")
            print(f"   응답: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"   ❌ 폴더 생성 중 오류: {str(e)}")
        return False, None

def test_mail_sending(access_token):
    """메일 발송 테스트 (UUID 생성 포함)"""
    print("\n🧪 메일 발송 테스트 시작...")
    
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        mail_data = {
            "to_emails": ["test@example.com"],
            "subject": f"테스트 메일 {str(uuid.uuid4())[:8]}",
            "content": "UUID 수정 테스트용 메일입니다.",
            "priority": "normal"
        }
        
        print(f"   발송할 메일: {mail_data['subject']}")
        
        response = requests.post(f"{BASE_URL}/api/v1/mail/send", json=mail_data, headers=headers)
        
        if response.status_code in [200, 201]:
            result = response.json()
            print(f"   ✅ 메일 발송 성공")
            print(f"   메일 UUID: {result.get('mail_uuid', 'N/A')}")
            return True, result
        else:
            print(f"   ❌ 메일 발송 실패: {response.status_code}")
            print(f"   응답: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"   ❌ 메일 발송 중 오류: {str(e)}")
        return False, None

def test_login(email, password):
    """로그인 테스트"""
    print(f"\n🧪 로그인 테스트 시작... ({email})")
    
    try:
        login_data = {
            "email": email,
            "password": password,
            "org_id": "test_org_001"
        }
        
        response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
        
        if response.status_code == 200:
            result = response.json()
            access_token = result.get("access_token")
            print(f"   ✅ 로그인 성공")
            print(f"   액세스 토큰: {access_token[:20] if access_token else 'None'}...")
            return True, access_token
        else:
            print(f"   ❌ 로그인 실패: {response.status_code}")
            print(f"   응답: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"   ❌ 로그인 중 오류: {str(e)}")
        return False, None

def check_server_status():
    """서버 상태 확인"""
    print("🔍 서버 상태 확인...")
    
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code == 200:
            print("   ✅ 서버가 정상적으로 실행 중입니다.")
            return True
        else:
            print(f"   ❌ 서버 응답 오류: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("   ❌ 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.")
        return False
    except Exception as e:
        print(f"   ❌ 서버 상태 확인 중 오류: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("UUID 수정 후 API 엔드포인트 테스트")
    print("=" * 60)
    
    # 서버 상태 확인
    if not check_server_status():
        print("\n💥 서버가 실행되지 않아 테스트를 중단합니다.")
        exit(1)
    
    # 테스트 결과 저장
    test_results = {
        "user_registration": False,
        "login": False,
        "folder_creation": False,
        "mail_sending": False
    }
    
    # 1. 사용자 등록 테스트
    reg_success, reg_result = test_user_registration()
    test_results["user_registration"] = reg_success
    
    if reg_success:
        user_email = reg_result.get("email")
        
        # 2. 로그인 테스트
        login_success, access_token = test_login(user_email, "testpassword123")
        test_results["login"] = login_success
        
        if login_success:
            # 3. 폴더 생성 테스트
            folder_success, folder_result = test_mail_folder_creation(access_token)
            test_results["folder_creation"] = folder_success
            
            # 4. 메일 발송 테스트
            mail_success, mail_result = test_mail_sending(access_token)
            test_results["mail_sending"] = mail_success
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("테스트 결과 요약:")
    print("=" * 60)
    
    for test_name, result in test_results.items():
        status = "✅ 통과" if result else "❌ 실패"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    # 전체 결과
    all_passed = all(test_results.values())
    if all_passed:
        print("\n🎉 모든 API 테스트 통과! UUID 수정이 성공적으로 적용되었습니다.")
    else:
        print("\n💥 일부 API 테스트 실패! 추가 확인이 필요합니다.")
        failed_tests = [name for name, result in test_results.items() if not result]
        print(f"실패한 테스트: {', '.join(failed_tests)}")