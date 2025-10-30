#!/usr/bin/env python3
"""
API를 통한 메일 발송 테스트 스크립트 (서버 재시작 후)
"""

import requests
import json

def login_and_get_token():
    """로그인하여 JWT 토큰을 얻습니다"""
    
    print("🔐 로그인 중...")
    
    login_url = "http://localhost:8000/api/v1/auth/login"
    login_data = {
        "user_id": "user01",
        "password": "test"
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-Organization-ID": "3856a8c1-84a4-4019-9133-655cacab4bc9"
    }
    
    try:
        response = requests.post(login_url, json=login_data, headers=headers, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            token = result.get("access_token")
            print(f"✅ 로그인 성공! 토큰 획득")
            return token
        else:
            print(f"❌ 로그인 실패: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 로그인 오류: {e}")
        return None

def test_api_mail_send():
    """API를 통한 메일 발송 테스트"""
    
    print("🧪 API 메일 발송 테스트 시작")
    
    # 먼저 로그인하여 토큰 획득
    token = login_and_get_token()
    if not token:
        print("❌ 토큰을 얻을 수 없어 테스트를 중단합니다.")
        return False
    
    # API 엔드포인트
    url = "http://localhost:8000/api/v1/mail/send-json"
    
    # 테스트 데이터
    payload = {
        "to": ["moon4656@hibiznet.com"],
        "subject": "🧪 API 메일 발송 테스트 (서버 재시작 후)",
        "body_text": "이 메일은 서버 재시작 후 SMTP 설정이 올바르게 적용되었는지 확인하는 테스트입니다.\n\n발신자 주소가 Gmail SMTP 설정에 맞게 자동으로 변경되어야 합니다."
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": "3856a8c1-84a4-4019-9133-655cacab4bc9",  # 테스트 조직 ID
        "X-User-ID": "user01"  # 테스트 사용자 ID
    }
    
    try:
        print(f"📤 API 요청 전송 중...")
        print(f"   URL: {url}")
        print(f"   수신자: {payload['to']}")
        print(f"   제목: {payload['subject']}")
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        print(f"\n📊 응답 결과:")
        print(f"   상태 코드: {response.status_code}")
        print(f"   응답 헤더: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   응답 내용: {json.dumps(result, indent=2, ensure_ascii=False)}")
            print(f"\n✅ API 메일 발송 테스트 성공!")
            return True
        else:
            print(f"   오류 응답: {response.text}")
            print(f"\n❌ API 메일 발송 테스트 실패!")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 요청 오류: {e}")
        return False
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        return False

if __name__ == "__main__":
    success = test_api_mail_send()
    if success:
        print("\n🎉 테스트 완료: SMTP 설정이 올바르게 적용되었습니다!")
    else:
        print("\n⚠️ 테스트 실패: SMTP 설정을 다시 확인해주세요.")