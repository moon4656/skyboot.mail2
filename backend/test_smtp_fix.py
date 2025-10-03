#!/usr/bin/env python3
"""
수정된 SMTP 설정으로 메일 발송 테스트
"""

import requests
import json
import sys
import os

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"

def login_user():
    """사용자 로그인"""
    login_url = f"{BASE_URL}{API_PREFIX}/auth/login"
    
    login_data = {
        "user_id": "admin01",
        "password": "test"
    }
    
    print("🔐 사용자 로그인 중...")
    response = requests.post(login_url, json=login_data)
    
    if response.status_code == 200:
        result = response.json()
        access_token = result.get("access_token")
        print(f"✅ 로그인 성공! 토큰: {access_token[:20]}...")
        return access_token
    else:
        print(f"❌ 로그인 실패: {response.status_code}")
        print(f"응답: {response.text}")
        return None

def send_test_mail(access_token):
    """테스트 메일 발송"""
    send_url = f"{BASE_URL}{API_PREFIX}/mail/send"
    
    # 실제 외부 이메일로 테스트
    mail_data = {
        "to_emails": "moon4656@gmail.com",
        "subject": "SMTP 수정 테스트 메일",
        "content": """안녕하세요!

이것은 SMTP 설정 수정 후 테스트 메일입니다.

수정 내용:
- send_email_smtp 메서드 추가
- SMTP 설정을 localhost:25로 변경
- WSL Postfix 서버 연동

발송 시간: 2025-10-03 12:12

메일이 정상적으로 도착했다면 수정이 성공한 것입니다!

감사합니다.
SkyBoot Mail 개발팀""",
        "priority": "high"
    }
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    print("\n📤 테스트 메일 발송 중...")
    print(f"URL: {send_url}")
    print(f"수신자: {mail_data['to_emails']}")
    print(f"제목: {mail_data['subject']}")
    
    try:
        # Form 데이터로 전송
        response = requests.post(
            send_url,
            data=mail_data,
            headers=headers
        )
        
        print(f"\n📊 응답 상태: {response.status_code}")
        print(f"📄 응답 내용: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ 메일 발송 성공!")
            print(f"   - 메일 UUID: {result.get('mail_uuid')}")
            print(f"   - 메시지: {result.get('message')}")
            print(f"   - 발송 시간: {result.get('sent_at')}")
            return True
        else:
            print(f"\n❌ 메일 발송 실패: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"   - 오류 상세: {error_detail}")
            except:
                print(f"   - 오류 내용: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 메일 발송 오류: {e}")
        return False

def main():
    print("🔧 SMTP 수정 후 메일 발송 테스트")
    print("=" * 50)
    
    # 1. 로그인
    access_token = login_user()
    if not access_token:
        print("❌ 로그인 실패로 테스트 중단")
        return False
    
    # 2. 메일 발송
    success = send_test_mail(access_token)
    
    print("\n" + "=" * 50)
    if success:
        print("✅ SMTP 수정 테스트 완료!")
        print("📬 moon4656@gmail.com 메일함을 확인해보세요.")
        print("📝 메일이 스팸함에 들어갈 수 있으니 스팸함도 확인해주세요.")
    else:
        print("❌ SMTP 수정 테스트 실패")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)