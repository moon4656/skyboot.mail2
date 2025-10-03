#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Terminal#1015-1020 오류 재현 및 수정사항 테스트 스크립트
attachments 필드 validation error 해결 확인
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
    """문자열 attachments로 오류 재현 테스트 (Terminal#1015-1020 오류)"""
    print("\n🧪 테스트 1: 문자열 attachments로 오류 재현...")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # 잘못된 방법 - attachments에 빈 문자열 전송 (오류 원인)
    form_data = {
        "to_emails": "test@example.com",
        "subject": "첨부파일 오류 테스트 - 문자열",
        "content": "이것은 첨부파일 오류를 재현하는 테스트입니다.",
        "priority": "normal",
        "attachments": ""  # 이것이 Terminal#1015-1020 오류 원인!
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/mail/send", data=form_data, headers=headers)
        print(f"응답 상태 코드: {response.status_code}")
        print(f"응답 내용: {response.text}")
        
        if response.status_code == 200:
            print("✅ 메일 발송 성공! (오류가 수정되었습니다)")
            return True
        elif response.status_code == 422:
            print("❌ Validation Error 여전히 발생 (수정 필요)")
            return False
        else:
            print(f"❌ 기타 오류: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 요청 중 오류 발생: {e}")
        return False

def test_mail_with_string_attachment_variant(token):
    """다른 형태의 문자열 attachments 테스트"""
    print("\n🧪 테스트 2: 다른 형태의 문자열 attachments...")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # 잘못된 방법 - attachments에 "string" 전송
    form_data = {
        "to_emails": "test@example.com",
        "subject": "첨부파일 오류 테스트 - string",
        "content": "이것은 첨부파일 오류를 재현하는 테스트입니다.",
        "priority": "normal",
        "attachments": "string"  # Terminal#1015-1020에서 언급된 오류!
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/mail/send", data=form_data, headers=headers)
        print(f"응답 상태 코드: {response.status_code}")
        print(f"응답 내용: {response.text}")
        
        if response.status_code == 200:
            print("✅ 메일 발송 성공! (오류가 수정되었습니다)")
            return True
        elif response.status_code == 422:
            print("❌ Validation Error 여전히 발생 (수정 필요)")
            return False
        else:
            print(f"❌ 기타 오류: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 요청 중 오류 발생: {e}")
        return False

def test_mail_without_attachment(token):
    """첨부파일 없이 정상 메일 발송 테스트"""
    print("\n✅ 테스트 3: 첨부파일 없이 정상 메일 발송...")
    
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

def test_mail_with_files_field(token):
    """files 필드를 사용한 첨부파일 테스트"""
    print("\n📎 테스트 4: files 필드를 사용한 첨부파일 테스트...")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # 올바른 방법 - 실제 파일 첨부
    form_data = {
        "to_emails": "test@example.com",
        "subject": "실제 첨부파일 테스트",
        "content": "이것은 실제 첨부파일이 있는 메일입니다.",
        "priority": "normal"
    }
    
    # 테스트용 파일 생성
    test_file_content = "이것은 테스트 첨부파일입니다."
    
    try:
        files = {
            'attachments': ('test.txt', test_file_content, 'text/plain')
        }
        
        response = requests.post(f"{BASE_URL}/api/v1/mail/send", data=form_data, files=files, headers=headers)
        print(f"응답 상태 코드: {response.status_code}")
        print(f"응답 내용: {response.text}")
        
        if response.status_code == 200:
            print("✅ 첨부파일 포함 메일 발송 성공!")
            return True
        else:
            print(f"❌ 첨부파일 포함 메일 발송 실패: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 요청 중 오류 발생: {e}")
        return False

def main():
    """메인 테스트 함수"""
    print("🚀 Terminal#1015-1020 오류 수정사항 테스트 시작")
    print("=" * 70)
    
    # 1. 로그인
    token = test_login()
    if not token:
        print("❌ 로그인 실패로 테스트 중단")
        return
    
    # 2. 문자열 attachments로 오류 재현 테스트
    result1 = test_mail_with_string_attachment(token)
    
    # 3. 다른 형태의 문자열 attachments 테스트
    result2 = test_mail_with_string_attachment_variant(token)
    
    # 4. 정상 메일 발송 테스트
    result3 = test_mail_without_attachment(token)
    
    # 5. 실제 첨부파일 테스트
    result4 = test_mail_with_files_field(token)
    
    print("\n" + "=" * 70)
    print("🏁 테스트 결과 요약")
    print(f"테스트 1 (빈 문자열 attachments): {'✅ 성공' if result1 else '❌ 실패'}")
    print(f"테스트 2 ('string' attachments): {'✅ 성공' if result2 else '❌ 실패'}")
    print(f"테스트 3 (attachments 없음): {'✅ 성공' if result3 else '❌ 실패'}")
    print(f"테스트 4 (실제 첨부파일): {'✅ 성공' if result4 else '❌ 실패'}")
    
    if result1 and result2:
        print("\n🎉 Terminal#1015-1020 오류가 성공적으로 수정되었습니다!")
    else:
        print("\n⚠️ 일부 테스트가 실패했습니다. 추가 수정이 필요합니다.")

if __name__ == "__main__":
    main()