#!/usr/bin/env python3
"""
SkyBoot Mail 간단한 메일 발송 테스트
첨부파일 없이 기본 메일 발송 기능만 테스트
"""

import requests
import json
import sys

# 서버 설정
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"
LOGIN_URL = f"{BASE_URL}{API_PREFIX}/auth/login"
SEND_MAIL_URL = f"{BASE_URL}{API_PREFIX}/mail/send-json"

def test_simple_mail():
    """첨부파일 없는 간단한 메일 발송 테스트"""
    print("🧪 SkyBoot Mail 간단한 메일 발송 테스트 시작")
    print("=" * 50)
    
    # 1. 로그인 테스트
    print("\n🔐 로그인 테스트")
    print("-" * 30)
    
    login_data = {
        "user_id": "admin",
        "password": "admin123"
    }
    
    try:
        login_response = requests.post(LOGIN_URL, json=login_data)
        if login_response.status_code == 200:
            login_result = login_response.json()
            access_token = login_result.get("access_token")
            print(f"✅ 로그인 성공: {access_token[:20]}...")
        else:
            print(f"❌ 로그인 실패: {login_response.status_code}")
            print(f"   - 응답: {login_response.text}")
            return False
    except Exception as e:
        print(f"❌ 로그인 요청 실패: {str(e)}")
        return False
    
    # 2. 간단한 메일 발송 테스트
    print("\n📤 간단한 메일 발송 테스트")
    print("-" * 30)
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    mail_data = {
        "to": ["test@example.com"],
        "subject": "간단한 테스트 메일",
        "body_text": "이것은 첨부파일 없는 간단한 테스트 메일입니다.",
        "priority": "normal",
        "is_draft": False
    }
    
    print("📤 간단한 메일 발송 시작...")
    print(f"   - 수신자: {mail_data['to']}")
    print(f"   - 제목: {mail_data['subject']}")
    
    try:
        mail_response = requests.post(SEND_MAIL_URL, json=mail_data, headers=headers)
        print(f"📤 응답 상태 코드: {mail_response.status_code}")
        
        if mail_response.status_code == 200:
            mail_result = mail_response.json()
            print("✅ 메일 발송 성공!")
            print(f"   - 응답: {json.dumps(mail_result, indent=2, ensure_ascii=False)}")
            return True
        else:
            print(f"❌ 메일 발송 실패: {mail_response.status_code}")
            print(f"   - 응답: {mail_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 메일 발송 요청 실패: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_simple_mail()
    if success:
        print("\n🎉 모든 테스트가 성공적으로 완료되었습니다!")
        sys.exit(0)
    else:
        print("\n❌ 테스트가 실패했습니다.")
        sys.exit(1)