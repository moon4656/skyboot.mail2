#!/usr/bin/env python3
"""
moonsoo 사용자로 외부 이메일 주소에 테스트 메일 발송

PostgreSQL을 사용하여 실제 메일 발송 기능을 테스트합니다.
"""
import requests
import json
import sys
from datetime import datetime

# FastAPI 서버 URL
BASE_URL = "http://localhost:8000"

def send_test_email():
    """moonsoo 사용자로 외부 이메일에 테스트 메일 발송"""
    
    try:
        # 1. moonsoo 사용자 로그인
        print("1. moonsoo 사용자 로그인 중...")
        login_response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={
                "email": "moonsoo@skyboot.com",
                "password": "test"
            }
        )
        
        if login_response.status_code != 200:
            print(f"❌ moonsoo 로그인 실패: {login_response.status_code}")
            print(f"응답: {login_response.text}")
            return False
        
        login_data = login_response.json()
        access_token = login_data["access_token"]
        print(f"✅ moonsoo 로그인 성공")
        
        # 2. 헤더 설정
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # 3. 테스트 메일 데이터 준비
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        mail_data = {
            "to": ["moon4656@gmail.com"],
            "subject": f"SkyBoot Mail 테스트 - {current_time}",
            "body_text": f"""
안녕하세요!

이것은 SkyBoot Mail SaaS 시스템에서 발송하는 테스트 메일입니다.

📧 발송자: moonsoo@skyboot.com
🕐 발송 시간: {current_time}
🏢 조직: SkyBoot
🔧 시스템: PostgreSQL 기반 다중 조직 메일 서버

메일 발송 기능이 정상적으로 작동하고 있습니다.

감사합니다.
SkyBoot Mail 개발팀
            """.strip(),
            "priority": "normal",
            "is_draft": False
        }
        
        # 4. 메일 발송 API 호출
        print("2. 외부 이메일 주소로 테스트 메일 발송 중...")
        print(f"   - 수신자: {mail_data['to'][0]}")
        print(f"   - 제목: {mail_data['subject']}")
        
        send_response = requests.post(
            f"{BASE_URL}/api/v1/mail/send-json",
            json=mail_data,
            headers=headers
        )
        
        if send_response.status_code == 200:
            send_result = send_response.json()
            print(f"✅ 메일 발송 성공!")
            print(f"   - 메일 ID: {send_result.get('mail_id')}")
            print(f"   - 상태: {send_result.get('status')}")
            print(f"   - 메시지: {send_result.get('message')}")
            
            # 5. 발송된 메일 상태 확인
            mail_id = send_result.get('mail_id')
            if mail_id:
                print("3. 발송된 메일 상태 확인 중...")
                status_response = requests.get(
                    f"{BASE_URL}/api/v1/mail/{mail_id}/status",
                    headers=headers
                )
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    print(f"✅ 메일 상태 조회 성공!")
                    print(f"   - 현재 상태: {status_data.get('status')}")
                    print(f"   - 발송 시간: {status_data.get('sent_at')}")
                    print(f"   - 수신자: {status_data.get('recipient')}")
                else:
                    print(f"⚠️ 메일 상태 조회 실패: {status_response.status_code}")
                    print(f"응답: {status_response.text}")
            
            # 6. 발송함 확인
            print("4. 발송함 확인 중...")
            sent_response = requests.get(
                f"{BASE_URL}/api/v1/mail/sent",
                headers=headers,
                params={"limit": 5}
            )
            
            if sent_response.status_code == 200:
                sent_data = sent_response.json()
                print(f"✅ 발송함 조회 성공!")
                print(f"   - 총 발송 메일 수: {sent_data.get('total', 0)}")
                
                mails = sent_data.get('mails', [])
                if mails:
                    latest_mail = mails[0]
                    print(f"   - 최근 발송 메일:")
                    print(f"     * 제목: {latest_mail.get('subject')}")
                    print(f"     * 수신자: {latest_mail.get('recipient')}")
                    print(f"     * 상태: {latest_mail.get('status')}")
            else:
                print(f"⚠️ 발송함 조회 실패: {sent_response.status_code}")
                print(f"응답: {sent_response.text}")
            
            return True
            
        else:
            print(f"❌ 메일 발송 실패: {send_response.status_code}")
            print(f"응답: {send_response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ FastAPI 서버에 연결할 수 없습니다.")
        print("서버가 실행 중인지 확인해주세요: uvicorn main:app --host 0.0.0.0 --port 8000 --reload")
        return False
    except Exception as e:
        print(f"❌ 예상치 못한 오류 발생: {str(e)}")
        return False

if __name__ == "__main__":
    print("📧 SkyBoot Mail 외부 이메일 발송 테스트 시작")
    print("=" * 60)
    
    success = send_test_email()
    
    print("=" * 60)
    if success:
        print("✅ 외부 이메일 발송 테스트 완료!")
        print("\n📬 moon4656@gmail.com 메일함을 확인해보세요.")
        print("📝 메일이 스팸함에 들어갈 수 있으니 스팸함도 확인해주세요.")
    else:
        print("❌ 외부 이메일 발송 테스트 실패")
        sys.exit(1)