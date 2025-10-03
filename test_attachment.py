#!/usr/bin/env python3
"""
첨부파일 업로드 테스트 스크립트
"""

import requests
import json
import os
import tempfile

# 서버 설정
BASE_URL = "http://localhost:8000"
LOGIN_URL = f"{BASE_URL}/api/v1/auth/login"
SEND_MAIL_URL = f"{BASE_URL}/api/v1/mail/send"
SENT_MAIL_URL = f"{BASE_URL}/api/v1/mail/sent"

def create_test_file():
    """테스트용 첨부파일 생성"""
    content = "이것은 테스트 첨부파일입니다.\n첨부파일 업로드 기능을 테스트합니다."
    
    # 임시 파일 생성
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(content)
        return f.name

def login():
    """로그인하여 토큰 획득"""
    login_data = {
        "user_id": "testuser1",
        "password": "testpassword123"
    }
    
    try:
        print("🔐 로그인 중...")
        print(f"🔗 로그인 URL: {LOGIN_URL}")
        print(f"📝 로그인 데이터: {login_data}")
        response = requests.post(LOGIN_URL, json=login_data)
        print(f"📊 응답 상태 코드: {response.status_code}")
        print(f"📄 응답 내용: {response.text}")
        
        if response.status_code == 200:
             result = response.json()
             # 직접 access_token이 반환되는 경우
             if "access_token" in result:
                 token = result["access_token"]
                 print(f"✅ 로그인 성공: {token[:20]}...")
                 return token
             # success 필드가 있는 경우
             elif result.get("success"):
                 token = result["data"]["access_token"]
                 print(f"✅ 로그인 성공: {token[:20]}...")
                 return token
             else:
                 print(f"❌ 로그인 실패: {result.get('message', '알 수 없는 오류')}")
                 return None
        else:
            print(f"❌ 로그인 요청 실패: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ 로그인 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def send_mail_with_attachment(token, attachment_file):
    """첨부파일이 포함된 메일 발송"""
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # Form data 준비
    form_data = {
        "to_emails": "test@skyboot.com",
        "subject": "첨부파일 테스트 메일",
        "content": "이 메일에는 첨부파일이 포함되어 있습니다.",
        "priority": "normal"
    }
    
    # 첨부파일 준비
    files = []
    filename = os.path.basename(attachment_file)
    
    with open(attachment_file, 'rb') as f:
        files.append(('attachments', (filename, f, 'text/plain')))
        
        print("📤 첨부파일이 포함된 메일 발송 중...")
        print(f"   - 첨부파일: {filename}")
        
        response = requests.post(
            SEND_MAIL_URL,
            headers=headers,
            data=form_data,
            files=files
        )
    
    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            print("✅ 메일 발송 성공")
            print(f"   - 메일 ID: {result['data']['mail_uuid']}")
            return result['data']['mail_uuid']
        else:
            print(f"❌ 메일 발송 실패: {result.get('message', '알 수 없는 오류')}")
            return None
    else:
        print(f"❌ 메일 발송 요청 실패: {response.status_code}")
        print(f"응답: {response.text}")
        return None

def check_sent_mail(token):
    """보낸 메일함 확인"""
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    print("📋 보낸 메일함 확인 중...")
    response = requests.get(SENT_MAIL_URL, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            mails = result["data"]["mails"]
            print(f"✅ 보낸 메일함 조회 성공 - 총 {len(mails)}개 메일")
            
            if mails:
                latest_mail = mails[0]  # 가장 최근 메일
                print(f"   - 최근 메일 제목: {latest_mail['subject']}")
                print(f"   - 첨부파일 여부: {latest_mail['has_attachments']}")
                print(f"   - 첨부파일 개수: {latest_mail.get('attachment_count', 0)}")
                return latest_mail
            else:
                print("   - 보낸 메일이 없습니다.")
                return None
        else:
            print(f"❌ 보낸 메일함 조회 실패: {result.get('message', '알 수 없는 오류')}")
            return None
    else:
        print(f"❌ 보낸 메일함 조회 요청 실패: {response.status_code}")
        print(f"응답: {response.text}")
        return None

def main():
    """메인 테스트 함수"""
    print("🧪 첨부파일 업로드 테스트 시작")
    print("=" * 50)
    
    # 1. 테스트 파일 생성
    test_file = create_test_file()
    print(f"📄 테스트 파일 생성: {test_file}")
    
    try:
        # 2. 로그인
        token = login()
        if not token:
            return
        
        # 3. 첨부파일이 포함된 메일 발송
        mail_uuid = send_mail_with_attachment(token, test_file)
        if not mail_uuid:
            return
        
        # 4. 보낸 메일함 확인
        sent_mail = check_sent_mail(token)
        if sent_mail:
            if sent_mail['has_attachments']:
                print("🎉 첨부파일 업로드 테스트 성공!")
            else:
                print("⚠️ 메일은 발송되었지만 첨부파일이 없습니다.")
        
    finally:
        # 5. 테스트 파일 정리
        if os.path.exists(test_file):
            os.unlink(test_file)
            print(f"🗑️ 테스트 파일 삭제: {test_file}")
    
    print("=" * 50)
    print("🧪 첨부파일 업로드 테스트 완료")

if __name__ == "__main__":
    main()