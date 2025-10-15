#!/usr/bin/env python3
"""
메일 발송 API 테스트 스크립트
admin@skyboot.mail로 테스트 메일 발송
"""

import requests
import json

def test_mail_send():
    """메일 발송 API 테스트"""
    print("메일 발송 API 테스트 시작...")
    
    # 1. 먼저 로그인해서 토큰 획득
    login_url = "http://localhost:8000/api/v1/auth/login"
    login_data = {
        "user_id": "user01",
        "password": "test"
    }
    
    print(f"로그인 URL: {login_url}")
    print(f"로그인 데이터: {login_data}")
    
    try:
        login_response = requests.post(login_url, json=login_data)
        print(f"로그인 응답 상태 코드: {login_response.status_code}")
        
        if login_response.status_code == 200:
            login_result = login_response.json()
            access_token = login_result.get("access_token")
            print(f"로그인 성공! 토큰 획득: {access_token[:50]}...")
            
            # 2. 메일 발송 API 호출
            mail_url = "http://localhost:8000/api/v1/mail/send"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            # Form 데이터로 전송 (API가 Form을 기대함)
            mail_data = {
                "to_emails": "admin@skyboot.mail",
                "subject": "테스트 메일 발송",
                "content": "안녕하세요! 이것은 SkyBoot Mail 시스템에서 발송된 테스트 메일입니다.",
                "priority": "normal",
                "is_draft": "false"
            }
            
            print(f"\n메일 발송 URL: {mail_url}")
            print(f"메일 데이터: {mail_data}")
            print(f"헤더: {headers}")
            
            mail_response = requests.post(mail_url, headers=headers, data=mail_data)
            print(f"\n메일 발송 응답 상태 코드: {mail_response.status_code}")
            print(f"메일 발송 응답 헤더: {dict(mail_response.headers)}")
            
            if mail_response.status_code == 200:
                mail_result = mail_response.json()
                print(f"✅ 메일 발송 성공!")
                print(f"응답 데이터: {json.dumps(mail_result, indent=2, ensure_ascii=False)}")
            else:
                print(f"❌ 메일 발송 실패")
                print(f"응답 내용: {mail_response.text}")
                
        else:
            print(f"❌ 로그인 실패")
            print(f"응답 내용: {login_response.text}")
            
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")

if __name__ == "__main__":
    test_mail_send()