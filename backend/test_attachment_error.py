#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
첨부파일 오류 재현 및 수정사항 테스트 스크립트
"""

import requests
import json

# API 기본 설정
BASE_URL = "http://localhost:8000"

def test_login():
    """테스트 사용자 로그인"""
    print("🔑 테스트 사용자 로그인...")
    
    login_data = {
        "user_id": "user01",
        "password": "test"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
        if response.status_code == 200:
            result = response.json()
            token = result.get("access_token")
            print("✅ 로그인 성공!")
            return token
        else:
            print(f"❌ 로그인 실패: {response.text}")
            return None
    except Exception as e:
        print(f"❌ 로그인 중 오류 발생: {e}")
        return None

def test_mail_with_string_attachment(token):
    """문자열 attachments로 오류 재현 테스트"""
    print("\n🧪 문자열 attachments로 오류 재현 테스트...")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # 잘못된 방법 - attachments에 문자열 전송
    form_data = {
        "to_emails": "test@example.com",
        "subject": "첨부파일 오류 테스트",
        "content": "이것은 첨부파일 오류를 재현하는 테스트입니다.",
        "priority": "normal",
        "attachments": "string"  # 이것이 오류 원인!
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/mail/send", data=form_data, headers=headers)
        print(f"응답 상태 코드: {response.status_code}")
        print(f"응답 내용: {response.text}")
        
        if response.status_code == 200:
            print("✅ 메일 발송 성공! (오류가 수정되었습니다)")
            return True
        else:
            print(f"❌ 메일 발송 실패: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 요청 중 오류 발생: {e}")
        return False

def test_mail_without_attachment(token):
    """첨부파일 없이 정상 메일 발송 테스트"""
    print("\n✅ 첨부파일 없이 정상 메일 발송 테스트...")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # 올바른 방법 - attachments 필드 제외
    form_data = {
        "to_emails": "test@example.com",
        "subject": "정상 메일 테스트",
        "content": "이것은 정상적인 메일 발송 테스트입니다.",
        "priority": "normal"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/mail/send", data=form_data, headers=headers)
        print(f"응답 상태 코드: {response.status_code}")
        print(f"응답 내용: {response.text}")
        
        if response.status_code == 200:
            print("✅ 메일 발송 성공!")
            return True
        else:
            print(f"❌ 메일 발송 실패: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 요청 중 오류 발생: {e}")
        return False

def main():
    """메인 테스트 함수"""
    print("🚀 첨부파일 오류 수정사항 테스트 시작")
    print("=" * 60)
    
    # 1. 로그인
    token = test_login()
    if not token:
        print("❌ 로그인 실패로 테스트 중단")
        return
    
    # 2. 문자열 attachments로 오류 재현 테스트
    test_mail_with_string_attachment(token)
    
    # 3. 정상 메일 발송 테스트
    test_mail_without_attachment(token)
    
    print("\n" + "=" * 60)
    print("🏁 첨부파일 오류 테스트 완료")

if __name__ == "__main__":
    main()