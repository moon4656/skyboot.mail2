#!/usr/bin/env python3
"""
메일 발송 API 디버그 테스트
- 메일 발송 API의 상세 응답 확인
- 오류 메시지 및 상태 코드 분석
"""

import requests
import json
import time

# API 기본 설정
BASE_URL = "http://localhost:8001"
TEST_USER = {
    "user_id": "user01",
    "password": "test"
}

def login():
    """사용자 로그인"""
    print("🔐 로그인 시도...")
    
    login_data = {
        "user_id": TEST_USER["user_id"],
        "password": TEST_USER["password"]
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        headers=headers,
        json=login_data
    )
    
    print(f"로그인 응답 상태: {response.status_code}")
    print(f"로그인 응답 내용: {response.text}")
    
    if response.status_code == 200:
        result = response.json()
        token = result.get("access_token")
        print(f"✅ 로그인 성공! 토큰: {token[:50]}...")
        return token
    else:
        print(f"❌ 로그인 실패: {response.status_code} - {response.text}")
        return None

def send_mail_debug(token):
    """메일 발송 디버그 테스트"""
    print("\n📤 메일 발송 디버그 테스트...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    mail_data = {
        "to": ["testuser_folder@example.com"],
        "subject": f"디버그 테스트 메일 - {int(time.time())}",
        "body_text": "이것은 메일 발송 디버그 테스트입니다.",
        "priority": "normal",
        "is_draft": False
    }
    
    print(f"발송할 메일 데이터: {json.dumps(mail_data, indent=2, ensure_ascii=False)}")
    
    # JSON 방식으로 메일 발송
    response = requests.post(
        f"{BASE_URL}/api/v1/mail/send-json",
        headers=headers,
        json=mail_data
    )
    
    print(f"\n메일 발송 응답 상태: {response.status_code}")
    print(f"메일 발송 응답 헤더: {dict(response.headers)}")
    print(f"메일 발송 응답 내용: {response.text}")
    
    if response.status_code == 200:
        try:
            result = response.json()
            print(f"✅ 메일 발송 API 호출 성공!")
            print(f"응답 데이터: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            # mail_id 또는 mail_uuid 추출
            mail_id = None
            if 'result' in result:
                if isinstance(result['result'], dict):
                    mail_id = result['result'].get('mail_id') or result['result'].get('mail_uuid')
                elif isinstance(result['result'], str):
                    mail_id = result['result']
            elif 'data' in result:
                if isinstance(result['data'], dict):
                    mail_id = result['data'].get('mail_id') or result['data'].get('mail_uuid')
                elif isinstance(result['data'], str):
                    mail_id = result['data']
            elif 'mail_id' in result:
                mail_id = result['mail_id']
            elif 'mail_uuid' in result:
                mail_id = result['mail_uuid']
            
            print(f"추출된 메일 ID: {mail_id}")
            return mail_id
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON 파싱 오류: {e}")
            return None
    else:
        print(f"❌ 메일 발송 실패: {response.status_code}")
        try:
            error_detail = response.json()
            print(f"오류 상세: {json.dumps(error_detail, indent=2, ensure_ascii=False)}")
        except:
            print(f"오류 내용: {response.text}")
        return None

def check_sent_mails(token):
    """발송한 메일함 확인"""
    print("\n📬 발송한 메일함 확인...")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.get(
        f"{BASE_URL}/api/v1/mail/sent?page=1&limit=5",
        headers=headers
    )
    
    print(f"발송함 조회 응답 상태: {response.status_code}")
    print(f"발송함 조회 응답 내용: {response.text}")
    
    if response.status_code == 200:
        try:
            result = response.json()
            print(f"발송함 데이터: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            # 응답 구조 확인 - mails 필드와 pagination 정보가 함께 있음
            if 'mails' in result:
                mails = result['mails']
                pagination = result.get('pagination', {})
                total = pagination.get('total', len(mails))
                print(f"✅ 발송한 메일 수: {len(mails)}개 (전체: {total}개)")
                for i, mail in enumerate(mails[:3]):
                    print(f"  {i+1}. 메일 ID: {mail.get('mail_uuid', 'N/A')}")
                    print(f"     제목: {mail.get('subject', 'N/A')}")
                    print(f"     상태: {mail.get('status', 'N/A')}")
                    print(f"     발송시간: {mail.get('sent_at', 'N/A')}")
            elif isinstance(result, list):
                # result가 직접 메일 리스트인 경우
                mails = result
                print(f"✅ 발송한 메일 수: {len(mails)}개")
                for i, mail in enumerate(mails[:3]):
                    print(f"  {i+1}. 메일 ID: {mail.get('mail_uuid', 'N/A')}")
                    print(f"     제목: {mail.get('subject', 'N/A')}")
                    print(f"     상태: {mail.get('status', 'N/A')}")
                    print(f"     발송시간: {mail.get('sent_at', 'N/A')}")
            elif 'data' in result:
                data = result['data']
                if 'mails' in data:
                    mails = data['mails']
                    print(f"✅ 발송한 메일 수: {len(mails)}개")
                    for i, mail in enumerate(mails[:3]):
                        print(f"  {i+1}. 메일 ID: {mail.get('mail_uuid', 'N/A')}")
                        print(f"     제목: {mail.get('subject', 'N/A')}")
                        print(f"     상태: {mail.get('status', 'N/A')}")
                        print(f"     발송시간: {mail.get('sent_at', 'N/A')}")
                elif isinstance(data, list):
                    # data가 직접 메일 리스트인 경우
                    mails = data
                    print(f"✅ 발송한 메일 수: {len(mails)}개")
                    for i, mail in enumerate(mails[:3]):
                        print(f"  {i+1}. 메일 ID: {mail.get('mail_uuid', 'N/A')}")
                        print(f"     제목: {mail.get('subject', 'N/A')}")
                        print(f"     상태: {mail.get('status', 'N/A')}")
                        print(f"     발송시간: {mail.get('sent_at', 'N/A')}")
                else:
                    print("❌ 예상하지 못한 데이터 구조입니다.")
            else:
                print("❌ 메일 데이터를 찾을 수 없습니다.")
                
        except json.JSONDecodeError as e:
            print(f"❌ JSON 파싱 오류: {e}")
    else:
        print(f"❌ 발송함 조회 실패: {response.status_code}")

def main():
    """메인 함수"""
    print("=== 메일 발송 API 디버그 테스트 ===")
    
    # 1. 로그인
    token = login()
    if not token:
        return
    
    # 2. 메일 발송 디버그
    mail_id = send_mail_debug(token)
    
    # 3. 잠시 대기 (메일 처리 시간)
    print("\n⏳ 메일 처리 대기 중... (3초)")
    time.sleep(3)
    
    # 4. 발송한 메일함 확인
    check_sent_mails(token)
    
    print("\n=== 디버그 테스트 완료 ===")

if __name__ == "__main__":
    main()