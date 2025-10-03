"""
메일 발송 테스트 스크립트
"""
import requests
import json
import sys
import os

# API 기본 설정
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"

def login_user01():
    """user01으로 로그인하여 토큰을 얻습니다."""
    
    login_url = f"{BASE_URL}{API_PREFIX}/auth/login"
    login_data = {
        "user_id": "user01",
        "password": "test"
    }
    
    print("🔐 user01 로그인 시도...")
    print(f"URL: {login_url}")
    print(f"Data: {login_data}")
    
    try:
        response = requests.post(
            login_url,
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get("access_token")
            print(f"✅ 로그인 성공! 토큰: {access_token[:50]}...")
            return access_token
        else:
            print(f"❌ 로그인 실패: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 로그인 오류: {e}")
        return None

def send_test_mail(access_token):
    """테스트 메일을 발송합니다."""
    
    send_url = f"{BASE_URL}{API_PREFIX}/mail/send"
    
    # 메일 데이터 (form-data 형식)
    mail_data = {
        "to_emails": "test@example.com",
        "subject": "테스트 메일",
        "content": "안녕하세요! 이것은 테스트 메일입니다.",
        "priority": "normal"
    }
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    print("\n📤 메일 발송 시도...")
    print(f"URL: {send_url}")
    print(f"Data: {mail_data}")
    
    try:
        response = requests.post(
            send_url,
            data=mail_data,  # form-data로 전송
            headers=headers
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 메일 발송 성공!")
            print(f"   - mail_uuid: {result.get('mail_uuid')}")
            print(f"   - message: {result.get('message')}")
            print(f"   - sent_at: {result.get('sent_at')}")
            return True
        else:
            print(f"❌ 메일 발송 실패: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"   - 오류 상세: {error_detail}")
            except:
                print(f"   - 오류 내용: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 메일 발송 오류: {e}")
        return False

def send_real_mail_test(access_token):
    """실제 이메일 주소로 메일을 발송합니다."""
    
    send_url = f"{BASE_URL}{API_PREFIX}/mail/send"
    
    # 실제 메일 데이터 (WSL Postfix 테스트용)
    mail_data = {
        "to_emails": "moon4656@gmail.com",  # 실제 도메인으로 테스트
        "subject": "Postfix WSL 테스트 메일",
        "content": """안녕하세요!

이것은 WSL에 설치된 Postfix를 통한 메일 발송 테스트입니다.

테스트 내용:
- 발신자: user01
- 수신자: moon4656@gmail.com
- 메일 서버: WSL Postfix
- 시간: 2025-10-03

메일이 정상적으로 발송되었다면 Postfix 설정이 올바르게 되어 있는 것입니다.

감사합니다!""",
        "priority": "high"
    }
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    print("\n📤 실제 메일 발송 시도 (Postfix WSL)...")
    print(f"URL: {send_url}")
    print(f"Data: {mail_data}")
    
    try:
        response = requests.post(
            send_url,
            data=mail_data,
            headers=headers
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 실제 메일 발송 성공!")
            print(f"   - mail_uuid: {result.get('mail_uuid')}")
            print(f"   - message: {result.get('message')}")
            print(f"   - sent_at: {result.get('sent_at')}")
            print(f"   - failed_recipients: {result.get('failed_recipients', [])}")
            print("\n💡 WSL에서 메일 로그 확인:")
            print("   sudo tail -f /var/log/mail.log")
            return True
        else:
            print(f"❌ 실제 메일 발송 실패: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"   - 오류 상세: {error_detail}")
            except:
                print(f"   - 오류 내용: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 실제 메일 발송 오류: {e}")
        return False

def main():
    """메인 테스트 함수"""
    
    print("🚀 메일 발송 테스트 시작")
    print("=" * 60)
    
    # 1. 로그인
    access_token = login_user01()
    if not access_token:
        print("\n❌ 로그인 실패로 테스트를 중단합니다.")
        print("💡 먼저 조직을 활성화해주세요: python activate_user01_org.py")
        return
    
    # 2. 기본 메일 발송 테스트
    print("\n" + "="*60)
    print("📋 테스트 1: 기본 메일 발송")
    send_test_mail(access_token)
    
    # 3. 실제 메일 발송 테스트 (Postfix)
    print("\n" + "="*60)
    print("📋 테스트 2: 실제 메일 발송 (Postfix WSL)")
    send_real_mail_test(access_token)
    
    print("\n🎉 메일 발송 테스트 완료!")
    print("\n💡 추가 확인사항:")
    print("   1. WSL에서 메일 로그 확인: sudo tail -f /var/log/mail.log")
    print("   2. Postfix 상태 확인: sudo systemctl status postfix")
    print("   3. 메일 큐 확인: sudo postqueue -p")

if __name__ == "__main__":
    main()