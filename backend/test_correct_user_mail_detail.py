#!/usr/bin/env python3
"""
올바른 사용자로 보낸 메일 상세 조회 테스트
"""

import requests
import json

def test_mail_detail_with_correct_user():
    """올바른 사용자로 메일 상세 조회 테스트"""
    
    base_url = "http://localhost:8000"
    
    # 1️⃣ testuser_folder 사용자로 로그인 (메일 발송자)
    print("1️⃣ testuser_folder 사용자 로그인...")
    
    # 먼저 testuser_folder의 user_id를 확인해야 합니다
    # 일반적으로 이메일에서 @ 앞부분을 사용하거나 별도 설정된 user_id를 사용
    
    # testuser_folder 사용자로 로그인
    login_data = {
        "user_id": "testuser_folder",
        "password": "test123"  # 재설정된 패스워드
    }
    
    token = None
    successful_user_id = "testuser_folder"
        
    try:
        response = requests.post(f"{base_url}/api/v1/auth/login", json=login_data)
        print(f"   로그인 상태: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if "access_token" in result:
                token = result["access_token"]
                print(f"   ✅ 로그인 성공! user_id: {successful_user_id}")
            else:
                print(f"   ❌ 로그인 실패: {result}")
        else:
            print(f"   ❌ 로그인 실패: {response.text}")
            
    except Exception as e:
        print(f"   ❌ 로그인 요청 오류: {str(e)}")
    
    if not token:
        print("❌ 모든 user_id로 로그인 실패. 사용자 생성이 필요할 수 있습니다.")
        return
    
    # 2️⃣ 보낸 메일함 조회
    print(f"\n2️⃣ {successful_user_id} 사용자의 보낸 메일함 조회...")
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{base_url}/api/v1/mail/sent", headers=headers)
        print(f"보낸 메일함 조회 상태: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            mails = result.get("data", {}).get("mails", [])
            print(f"✅ 보낸 메일 수: {len(mails)}")
            
            if mails:
                # 첫 번째 메일의 상세 정보 조회
                first_mail = mails[0]
                mail_uuid = first_mail["mail_uuid"]
                print(f"📧 첫 번째 메일 UUID: {mail_uuid}")
                
                # 3️⃣ 메일 상세 조회
                print(f"\n3️⃣ 메일 상세 조회 테스트...")
                detail_response = requests.get(
                    f"{base_url}/api/v1/mail/sent/{mail_uuid}", 
                    headers=headers
                )
                print(f"메일 상세 조회 상태: {detail_response.status_code}")
                
                if detail_response.status_code == 200:
                    detail_result = detail_response.json()
                    print("✅ 메일 상세 조회 성공!")
                    print(f"   제목: {detail_result['data']['subject']}")
                    print(f"   발송자: {detail_result['data']['sender_email']}")
                    print(f"   수신자: {detail_result['data']['to_emails']}")
                    print(f"   상태: {detail_result['data']['status']}")
                else:
                    print(f"❌ 메일 상세 조회 실패: {detail_response.text}")
            else:
                print("❌ 보낸 메일이 없습니다.")
        else:
            print(f"❌ 보낸 메일함 조회 실패: {response.text}")
            
    except Exception as e:
        print(f"❌ API 요청 오류: {str(e)}")

def main():
    """메인 함수"""
    print("🧪 올바른 사용자로 보낸 메일 상세 조회 테스트")
    print("=" * 60)
    
    test_mail_detail_with_correct_user()

if __name__ == "__main__":
    main()