#!/usr/bin/env python3
"""
Terminal#1014-1020 오류 수정 테스트 스크립트

이 스크립트는 다음 오류를 재현하고 수정사항을 검증합니다:
"Value error, Expected UploadFile, received: <class 'str'>"
"""

import requests
import json
import time

# 서버 설정
BASE_URL = "http://localhost:8000"
LOGIN_URL = f"{BASE_URL}/api/v1/auth/login"
MAIL_SEND_URL = f"{BASE_URL}/api/v1/mail/send"

def login_user():
    """테스트 사용자로 로그인하여 토큰을 얻습니다."""
    login_data = {
        "user_id": "admin01",
        "password": "test"
    }
    
    try:
        response = requests.post(LOGIN_URL, json=login_data)
        if response.status_code == 200:
            result = response.json()
            token = result.get("access_token")
            print(f"✅ 로그인 성공: {token[:20]}...")
            return token
        else:
            print(f"❌ 로그인 실패: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ 로그인 요청 오류: {str(e)}")
        return None

def test_attachments_string_error(token):
    """
    Terminal#1014-1020 오류 재현 테스트
    attachments 필드에 문자열을 보내서 validation 오류를 확인합니다.
    """
    print("\n🧪 테스트 1: attachments 필드에 문자열 전송 (오류 재현)")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # multipart/form-data로 전송 (attachments에 문자열 포함)
    data = {
        "to_emails": "moon4656@gmail.com",
        "subject": "테스트 메일 - 문자열 attachments",
        "content": "이 메일은 attachments 필드에 문자열을 보내는 테스트입니다.",
        "attachments": "string"  # 이것이 오류를 발생시킵니다
    }
    
    try:
        response = requests.post(MAIL_SEND_URL, headers=headers, data=data)
        print(f"📊 응답 상태: {response.status_code}")
        print(f"📋 응답 내용: {response.text[:500]}...")
        
        if response.status_code == 422:
            print("⚠️ 예상된 validation 오류 발생")
            return False
        elif response.status_code == 200:
            print("✅ 문자열 attachments가 안전하게 처리됨")
            return True
        else:
            print(f"❓ 예상하지 못한 응답: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 요청 오류: {str(e)}")
        return False

def test_attachments_list_with_string(token):
    """
    attachments 필드에 문자열이 포함된 리스트를 보내는 테스트
    """
    print("\n🧪 테스트 2: attachments 필드에 문자열 리스트 전송")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # multipart/form-data로 전송
    data = {
        "to_emails": "moon4656@gmail.com",
        "subject": "테스트 메일 - 문자열 리스트 attachments",
        "content": "이 메일은 attachments 필드에 문자열 리스트를 보내는 테스트입니다."
    }
    
    # attachments 필드에 여러 문자열 추가
    files = [
        ("attachments", ("", "string1", "text/plain")),
        ("attachments", ("", "string2", "text/plain"))
    ]
    
    try:
        response = requests.post(MAIL_SEND_URL, headers=headers, data=data, files=files)
        print(f"📊 응답 상태: {response.status_code}")
        print(f"📋 응답 내용: {response.text[:500]}...")
        
        if response.status_code == 422:
            print("⚠️ validation 오류 발생")
            return False
        elif response.status_code == 200:
            print("✅ 문자열 리스트가 안전하게 처리됨")
            return True
        else:
            print(f"❓ 예상하지 못한 응답: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 요청 오류: {str(e)}")
        return False

def test_normal_mail_without_attachments(token):
    """
    정상적인 메일 발송 테스트 (첨부파일 없음)
    """
    print("\n🧪 테스트 3: 정상적인 메일 발송 (첨부파일 없음)")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    data = {
        "to_emails": "moon4656@gmail.com",
        "subject": "테스트 메일 - 첨부파일 없음",
        "content": "이 메일은 첨부파일이 없는 정상적인 메일입니다."
    }
    
    try:
        response = requests.post(MAIL_SEND_URL, headers=headers, data=data)
        print(f"📊 응답 상태: {response.status_code}")
        print(f"📋 응답 내용: {response.text[:500]}...")
        
        if response.status_code == 200:
            print("✅ 정상적인 메일 발송 성공")
            return True
        else:
            print(f"❌ 메일 발송 실패: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 요청 오류: {str(e)}")
        return False

def main():
    """메인 테스트 실행 함수"""
    print("🚀 Terminal#1014-1020 오류 수정 테스트 시작")
    print("=" * 60)
    
    # 로그인
    token = login_user()
    if not token:
        print("❌ 로그인 실패로 테스트를 중단합니다.")
        return
    
    # 테스트 실행
    test_results = []
    
    # 테스트 1: 문자열 attachments
    result1 = test_attachments_string_error(token)
    test_results.append(("문자열 attachments 처리", result1))
    
    time.sleep(1)  # 서버 부하 방지
    
    # 테스트 2: 문자열 리스트 attachments
    result2 = test_attachments_list_with_string(token)
    test_results.append(("문자열 리스트 attachments 처리", result2))
    
    time.sleep(1)  # 서버 부하 방지
    
    # 테스트 3: 정상적인 메일 발송
    result3 = test_normal_mail_without_attachments(token)
    test_results.append(("정상적인 메일 발송", result3))
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("🏁 테스트 결과 요약")
    print("=" * 60)
    
    for test_name, result in test_results:
        status = "✅ 성공" if result else "❌ 실패"
        print(f"{test_name}: {status}")
    
    success_count = sum(1 for _, result in test_results if result)
    total_count = len(test_results)
    
    print(f"\n📊 전체 결과: {success_count}/{total_count} 테스트 성공")
    
    if success_count == total_count:
        print("🎉 모든 테스트가 성공했습니다! Terminal#1014-1020 오류가 해결되었습니다.")
    else:
        print("⚠️ 일부 테스트가 실패했습니다. 추가 수정이 필요합니다.")

if __name__ == "__main__":
    main()