#!/usr/bin/env python3
"""
테스트 사용자 설정 스크립트
SkyBoot Mail SaaS 시스템 테스트를 위한 사용자 계정 생성

작성자: SkyBoot Mail 개발팀
작성일: 2024-12-29
"""

import requests
import json
from datetime import datetime

# 테스트 설정
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"

# 테스트 사용자 정보
TEST_USER = {
    "username": "testuser_advanced",
    "email": "testadvanced@skyboot.kr",
    "password": "testpassword123",
    "full_name": "고급 테스트 사용자"
}

def log_message(message: str, level: str = "INFO"):
    """로그 메시지 출력"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

def make_request(method: str, endpoint: str, data: dict = None) -> requests.Response:
    """API 요청 헬퍼 함수"""
    url = f"{BASE_URL}{API_PREFIX}{endpoint}"
    headers = {"Content-Type": "application/json"}
    
    if method.upper() == "POST":
        response = requests.post(url, headers=headers, json=data)
    elif method.upper() == "GET":
        response = requests.get(url, headers=headers)
    else:
        raise ValueError(f"지원하지 않는 HTTP 메서드: {method}")
    
    return response

def check_user_exists():
    """사용자 존재 여부 확인 (로그인 시도)"""
    log_message("🔍 기존 사용자 확인 중...")
    
    try:
        response = make_request("POST", "/auth/login", {
            "email": TEST_USER["email"],
            "password": TEST_USER["password"]
        })
        
        if response.status_code == 200:
            log_message("✅ 기존 사용자 로그인 성공")
            return True
        elif response.status_code == 401:
            log_message("❌ 사용자가 존재하지 않거나 비밀번호가 틀림")
            return False
        else:
            log_message(f"⚠️ 예상치 못한 응답: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        log_message(f"❌ 사용자 확인 중 오류: {str(e)}", "ERROR")
        return False

def register_user():
    """새 사용자 등록"""
    log_message("👤 새 사용자 등록 중...")
    
    try:
        response = make_request("POST", "/auth/register", TEST_USER)
        
        if response.status_code in [200, 201]:
            data = response.json()
            log_message(f"✅ 사용자 등록 성공: {data.get('email', TEST_USER['email'])}")
            return True
        elif response.status_code == 400:
            # 이미 존재하는 사용자일 수 있음
            error_data = response.json()
            if "already exists" in error_data.get("message", "").lower():
                log_message("⚠️ 사용자가 이미 존재함 - 로그인 시도")
                return check_login_with_existing_user()
            else:
                log_message(f"❌ 등록 실패: {error_data.get('message', response.text)}", "ERROR")
                return False
        else:
            log_message(f"❌ 등록 실패 - 상태코드: {response.status_code}, 응답: {response.text}", "ERROR")
            return False
            
    except Exception as e:
        log_message(f"❌ 사용자 등록 중 오류: {str(e)}", "ERROR")
        return False

def check_login_with_existing_user():
    """기존 사용자로 로그인 재시도"""
    log_message("🔐 기존 사용자로 로그인 재시도...")
    
    try:
        response = make_request("POST", "/auth/login", {
            "email": TEST_USER["email"],
            "password": TEST_USER["password"]
        })
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            log_message(f"✅ 로그인 성공 - 토큰: {token[:20]}...")
            return True
        else:
            log_message(f"❌ 로그인 실패 - {response.status_code}: {response.text}", "ERROR")
            return False
            
    except Exception as e:
        log_message(f"❌ 로그인 중 오류: {str(e)}", "ERROR")
        return False

def setup_mail_account():
    """메일 계정 초기화"""
    log_message("📧 메일 계정 초기화 중...")
    
    # 먼저 로그인하여 토큰 획득
    try:
        login_response = make_request("POST", "/auth/login", {
            "email": TEST_USER["email"],
            "password": TEST_USER["password"]
        })
        
        if login_response.status_code != 200:
            log_message("❌ 로그인 실패로 메일 계정 초기화 불가", "ERROR")
            return False
        
        token = login_response.json().get("access_token")
        
        # 메일 계정 초기화 API 호출
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        
        setup_response = requests.post(
            f"{BASE_URL}{API_PREFIX}/mail/setup-mail-account",
            headers=headers,
            json={}
        )
        
        if setup_response.status_code in [200, 201]:
            log_message("✅ 메일 계정 초기화 성공")
            return True
        else:
            log_message(f"⚠️ 메일 계정 초기화 응답: {setup_response.status_code} - {setup_response.text}")
            # 이미 초기화되어 있을 수 있으므로 경고로 처리
            return True
            
    except Exception as e:
        log_message(f"❌ 메일 계정 초기화 중 오류: {str(e)}", "ERROR")
        return False

def main():
    """메인 실행 함수"""
    print("🚀 테스트 사용자 설정 시작")
    print(f"대상 서버: {BASE_URL}")
    print(f"테스트 사용자: {TEST_USER['email']}")
    print("-" * 60)
    
    # 1. 기존 사용자 확인
    if check_user_exists():
        log_message("✅ 기존 사용자 사용 가능")
    else:
        # 2. 새 사용자 등록
        if not register_user():
            log_message("❌ 사용자 설정 실패", "ERROR")
            return False
    
    # 3. 메일 계정 초기화
    if not setup_mail_account():
        log_message("⚠️ 메일 계정 초기화 실패 (테스트는 계속 진행 가능)", "WARNING")
    
    print("\n" + "="*60)
    print("✅ 테스트 사용자 설정 완료!")
    print(f"이메일: {TEST_USER['email']}")
    print(f"비밀번호: {TEST_USER['password']}")
    print("이제 mail_advanced_router 테스트를 실행할 수 있습니다.")
    print("="*60)
    
    return True

if __name__ == "__main__":
    main()