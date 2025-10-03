#!/usr/bin/env python3
"""
메일 API UUID 생성 테스트 스크립트

실제 메일 발송 API에서 새로운 mail_uuid 형식이 올바르게 적용되는지 확인합니다.
"""

import requests
import json
import re
from datetime import datetime

# API 기본 설정
BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api/v1"

def get_auth_token():
    """테스트용 인증 토큰 획득"""
    print("🔐 인증 토큰 획득 중...")
    
    # 테스트 사용자로 로그인 (user_id 기반)
    login_data = {
        "user_id": "admin01",
        "password": "test"
    }
    
    try:
        response = requests.post(f"{API_URL}/auth/login", json=login_data)
        if response.status_code == 200:
            token = response.json().get("access_token")
            print("✅ 인증 토큰 획득 성공")
            return token
        else:
            print(f"❌ 로그인 실패: {response.status_code}")
            print(f"응답: {response.text}")
            return None
    except Exception as e:
        print(f"❌ 로그인 요청 중 오류: {e}")
        return None

def test_mail_send_api(token):
    """메일 발송 API 테스트"""
    print("\n📧 메일 발송 API 테스트 시작")
    print("=" * 50)
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # 테스트 메일 데이터 (Form 데이터 형식)
    mail_data = {
        "to_emails": "test@example.com",
        "subject": f"UUID 테스트 메일 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "content": "새로운 mail_uuid 형식 테스트를 위한 메일입니다.",
        "priority": "normal"
    }
    
    try:
        print("📤 메일 발송 요청 중...")
        response = requests.post(f"{API_URL}/mail/send", data=mail_data, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 메일 발송 성공")
            print(f"응답 데이터: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            # mail_uuid 확인
            if "mail_uuid" in result:
                mail_uuid = result["mail_uuid"]
                print(f"\n🔍 생성된 mail_uuid: {mail_uuid}")
                
                # 형식 검증: YYYYMMDD_HHMMSS_12자리UUID
                pattern = r'^\d{8}_\d{6}_[a-f0-9]{12}$'
                if re.match(pattern, mail_uuid):
                    print("✅ mail_uuid 형식 검증 통과")
                    
                    # 날짜/시간 부분 추출
                    date_part = mail_uuid[:8]
                    time_part = mail_uuid[9:15]
                    uuid_part = mail_uuid[16:]
                    
                    print(f"📅 날짜 부분: {date_part}")
                    print(f"🕐 시간 부분: {time_part}")
                    print(f"🔑 UUID 부분: {uuid_part} (길이: {len(uuid_part)})")
                    
                    # 현재 시간과 비교
                    current_time = datetime.now()
                    expected_date = current_time.strftime("%Y%m%d")
                    
                    if date_part == expected_date:
                        print("✅ 날짜 부분 정확함")
                    else:
                        print(f"⚠️ 날짜 부분 불일치 (예상: {expected_date}, 실제: {date_part})")
                    
                    return True
                else:
                    print("❌ mail_uuid 형식 검증 실패")
                    print(f"예상 형식: YYYYMMDD_HHMMSS_12자리UUID")
                    print(f"실제 형식: {mail_uuid}")
                    return False
            else:
                print("❌ 응답에 mail_uuid가 없습니다")
                return False
                
        else:
            print(f"❌ 메일 발송 실패: {response.status_code}")
            print(f"응답: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 메일 발송 요청 중 오류: {e}")
        return False

def test_mail_list_api(token):
    """메일 목록 API에서 mail_uuid 확인"""
    print("\n📋 메일 목록 API 테스트 시작")
    print("=" * 50)
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        print("📋 발송한 메일 목록 조회 중...")
        response = requests.get(f"{API_URL}/mail/sent", headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 메일 목록 조회 성공")
            
            if "mails" in result and len(result["mails"]) > 0:
                # 최근 메일 확인
                recent_mail = result["mails"][0]
                if "mail_uuid" in recent_mail:
                    mail_uuid = recent_mail["mail_uuid"]
                    print(f"🔍 최근 메일의 mail_uuid: {mail_uuid}")
                    
                    # 형식 검증
                    pattern = r'^\d{8}_\d{6}_[a-f0-9]{12}$'
                    if re.match(pattern, mail_uuid):
                        print("✅ 메일 목록에서도 새로운 형식 확인됨")
                        return True
                    else:
                        print("❌ 메일 목록의 mail_uuid 형식이 올바르지 않음")
                        return False
                else:
                    print("❌ 메일 데이터에 mail_uuid가 없습니다")
                    return False
            else:
                print("⚠️ 발송한 메일이 없습니다")
                return True
                
        else:
            print(f"❌ 메일 목록 조회 실패: {response.status_code}")
            print(f"응답: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 메일 목록 조회 중 오류: {e}")
        return False

def main():
    """메인 테스트 함수"""
    print("📧 SkyBoot Mail API UUID 테스트")
    print("새로운 형식: 년월일_시분초_uuid[12]")
    print()
    
    # 서버 연결 확인
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("❌ 서버가 실행되지 않았습니다. 먼저 서버를 시작해주세요.")
            return False
    except:
        print("❌ 서버에 연결할 수 없습니다. 먼저 서버를 시작해주세요.")
        return False
    
    print("✅ 서버 연결 확인됨")
    
    # 인증 토큰 획득
    token = get_auth_token()
    if not token:
        print("❌ 인증 토큰을 획득할 수 없습니다.")
        return False
    
    # 테스트 실행
    test1_result = test_mail_send_api(token)
    test2_result = test_mail_list_api(token)
    
    print("\n" + "=" * 50)
    print("📊 API 테스트 결과 요약")
    print(f"메일 발송 API 테스트: {'✅ 통과' if test1_result else '❌ 실패'}")
    print(f"메일 목록 API 테스트: {'✅ 통과' if test2_result else '❌ 실패'}")
    
    if test1_result and test2_result:
        print("\n🎉 모든 API 테스트 통과! 새로운 mail_uuid 형식이 API에서 올바르게 작동합니다.")
        return True
    else:
        print("\n❌ 일부 API 테스트 실패. 서버 로그를 확인해주세요.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)