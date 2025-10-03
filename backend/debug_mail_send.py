#!/usr/bin/env python3
"""
메일 발송 API 디버깅 스크립트
"""

import requests
import json
from datetime import datetime

def debug_mail_send():
    """메일 발송 API를 디버깅합니다."""
    print("Mail send API debugging started")
    print(f"Time: {datetime.now()}")
    print("=" * 60)
    
    # 로그인하여 토큰 획득
    login_url = "http://localhost:8000/api/v1/auth/login"
    login_data = {
        "user_id": "user01",
        "password": "test"
    }
    
    try:
        print("1. Login attempt...")
        login_response = requests.post(login_url, json=login_data)
        print(f"Login Status Code: {login_response.status_code}")
        
        if login_response.status_code == 200:
            login_result = login_response.json()
            access_token = login_result.get("access_token")
            print(f"Login successful, token obtained: {access_token[:20]}...")
            
            # 메일 발송 테스트
            mail_url = "http://localhost:8000/api/v1/mail/send"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            mail_data = {
                "to_emails": "moon4656@gmail.com",
                "subject": "Debug Test Mail",
                "content": "This is a debug test mail to check database storage.",
                "priority": "normal"
            }
            
            print("2. Mail send attempt...")
            print(f"URL: {mail_url}")
            print(f"Data: {mail_data}")
            
            mail_response = requests.post(mail_url, headers=headers, json=mail_data)
            print(f"Mail Status Code: {mail_response.status_code}")
            print(f"Mail Response: {mail_response.text}")
            
            if mail_response.status_code == 200:
                mail_result = mail_response.json()
                print("Mail send successful!")
                print(f"Mail UUID: {mail_result.get('mail_uuid')}")
                print(f"Sent at: {mail_result.get('sent_at')}")
            else:
                print("Mail send failed!")
                try:
                    error_detail = mail_response.json()
                    print(f"Error detail: {json.dumps(error_detail, indent=2)}")
                except:
                    print(f"Raw error response: {mail_response.text}")
        else:
            print("Login failed!")
            print(f"Response: {login_response.text}")
            
    except Exception as e:
        print(f"Error occurred: {e}")

if __name__ == "__main__":
    debug_mail_send()