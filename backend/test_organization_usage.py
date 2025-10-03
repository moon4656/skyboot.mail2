#!/usr/bin/env python3
"""
조직 사용량 업데이트 테스트 스크립트
"""

import requests
import json
import time

# 서버 설정
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"

def test_organization_usage_update():
    """조직 사용량 업데이트 테스트"""
    print("🧪 조직 사용량 업데이트 테스트 (수정된 코드)")
    print("=" * 60)

    # 1. 로그인
    print("🔐 관리자 로그인 중...")
    login_data = {
        "user_id": "user01",
        "password": "test"
    }

    login_response = requests.post(
        f"{BASE_URL}{API_PREFIX}/auth/login", 
        json=login_data,
        headers={"Content-Type": "application/json"}
    )
    print(f"로그인 상태: {login_response.status_code}")

    if login_response.status_code == 200:
        login_result = login_response.json()
        access_token = login_result["access_token"]
        print("✅ 로그인 성공")
        
        # 2. 메일 발송 (JSON API 사용)
        print("\n📤 메일 발송 중...")
        mail_data = {
            "to": ["moon4656@gmail.com"],
            "subject": "조직 사용량 업데이트 테스트 (수정된 코드)",
            "body_text": f"이것은 조직 사용량 업데이트 테스트 메일입니다.\n\n발송 시간: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n수정 사항:\n- send_email_smtp 메서드에 조직 사용량 업데이트 기능 추가\n- 메일 발송 성공 시 자동으로 organization_usage 테이블 업데이트",
            "priority": "normal"
        }
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "X-Organization-ID": "3856a8c1-84a4-4019-9133-655cacab4bc9",
            "Content-Type": "application/json"
        }
        
        mail_response = requests.post(
            f"{BASE_URL}{API_PREFIX}/mail/send-json",
            json=mail_data,
            headers=headers
        )
        
        print(f"메일 발송 상태: {mail_response.status_code}")
        if mail_response.status_code == 200:
            mail_result = mail_response.json()
            print("✅ 메일 발송 성공")
            print(f"메일 UUID: {mail_result.get('mail_uuid')}")
            print(f"발송 시간: {mail_result.get('sent_at')}")
        else:
            print(f"❌ 메일 발송 실패: {mail_response.text}")
            
    else:
        print(f"❌ 로그인 실패: {login_response.text}")

    print("\n🔍 테스트 완료 - 서버 로그를 확인하여 조직 사용량 업데이트 로그를 확인하세요.")

if __name__ == "__main__":
    test_organization_usage_update()