#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WSL 환경에서 외부 메일 전송 테스트 스크립트
moon4656@gmail.com으로 테스트 메일 발송
"""

import requests
import json
import time

# API 기본 설정
BASE_URL = "http://localhost:8000"
TEST_EMAIL = "moon4656@gmail.com"

def test_user_registration():
    """테스트 사용자 등록"""
    print("🔧 테스트 사용자 등록 시도...")
    
    user_data = {
        "user_id": "user01",
        "email": "user01@gmail.com", 
        "username": "user01",
        "password": "test",
        "org_code": "A001"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/auth/register", json=user_data)
        print(f"등록 상태 코드: {response.status_code}")
        print(f"등록 응답: {response.text}")
        
        if response.status_code == 201:
            print("✅ 사용자 등록 성공!")
            return True
        elif response.status_code == 400 and "already exists" in response.text:
            print("ℹ️ 사용자가 이미 존재합니다. 로그인을 시도합니다.")
            return True
        else:
            print(f"❌ 사용자 등록 실패: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 등록 중 오류 발생: {e}")
        return False

def test_user_login():
    """테스트 사용자 로그인"""
    print("\n🔑 테스트 사용자 로그인 시도...")
    
    login_data = {
        "user_id": "user01",
        "password": "test"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
        print(f"로그인 상태 코드: {response.status_code}")
        print(f"로그인 응답: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            token = result.get("access_token")
            print("✅ 로그인 성공!")
            print(f"토큰: {token[:50]}...")
            return token
        else:
            print(f"❌ 로그인 실패: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 로그인 중 오류 발생: {e}")
        return None

def send_test_mail(token):
    """외부 메일 주소로 테스트 메일 발송"""
    print(f"\n📧 {TEST_EMAIL}로 테스트 메일 발송 시도...")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    mail_content = f"""
안녕하세요!

이것은 WSL 환경에서 SkyBoot Mail 서버의 외부 메일 전송 테스트입니다.

테스트 정보:
- 발송 시간: {time.strftime('%Y-%m-%d %H:%M:%S')}
- 발송자: user01@example.com
- 수신자: {TEST_EMAIL}
- 메일 서버: Postfix + Dovecot
- 백엔드: FastAPI + PostgreSQL

메일이 정상적으로 수신되었다면 WSL 메일 서버가 올바르게 설정되었습니다.

감사합니다!
SkyBoot Mail Team
    """
    
    # Form 데이터로 전송
    form_data = {
        "to_emails": TEST_EMAIL,
        "subject": "WSL 메일 서버 테스트 - SkyBoot Mail",
        "content": mail_content,
        "priority": "normal"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/mail/send", data=form_data, headers=headers)
        print(f"메일 발송 상태 코드: {response.status_code}")
        print(f"메일 발송 응답: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 메일 발송 성공!")
            print(f"메일 ID: {result.get('mail_id', 'N/A')}")
            return True
        else:
            print(f"❌ 메일 발송 실패: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 메일 발송 중 오류 발생: {e}")
        return False

def check_mail_logs():
    """메일 발송 로그 확인"""
    print("\n📊 메일 발송 로그 확인...")
    
    try:
        # WSL에서 Postfix 로그 확인
        import subprocess
        result = subprocess.run(
            ["wsl", "tail", "-n", "20", "/var/log/mail.log"], 
            capture_output=True, 
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print("📋 최근 메일 로그:")
            print(result.stdout)
        else:
            print(f"❌ 로그 확인 실패: {result.stderr}")
            
    except Exception as e:
        print(f"❌ 로그 확인 중 오류 발생: {e}")

def main():
    """메인 테스트 함수"""
    print("🚀 WSL 메일 서버 외부 전송 테스트 시작")
    print(f"📧 대상 이메일: {TEST_EMAIL}")
    print("=" * 60)
    
    # 1. 사용자 등록
    # if not test_user_registration():
    #     print("❌ 사용자 등록 실패로 테스트 중단")
    #     return
    
    # 2. 사용자 로그인
    token = test_user_login()
    if not token:
        print("❌ 로그인 실패로 테스트 중단")
        return
    
    # 3. 메일 발송
    if send_test_mail(token):
        print(f"\n✅ {TEST_EMAIL}로 메일 발송 완료!")
        print("📱 Gmail에서 메일을 확인해주세요.")
        print("📁 스팸 폴더도 확인해보세요.")
    else:
        print("\n❌ 메일 발송 실패")
    
    # 4. 로그 확인
    check_mail_logs()
    
    print("\n" + "=" * 60)
    print("🏁 WSL 메일 서버 테스트 완료")

if __name__ == "__main__":
    main()