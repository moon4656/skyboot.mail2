#!/usr/bin/env python3
"""
조직 설정 업데이트 기능 테스트 스크립트
"""

import requests
import json
import sys

# 테스트 설정
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"

# 테스트 사용자 정보
TEST_USER_ID = "admin01"
TEST_PASSWORD = "test"

def get_auth_token():
    """인증 토큰 획득"""
    login_url = f"{BASE_URL}{API_PREFIX}/auth/login"
    login_data = {
        "user_id": TEST_USER_ID,
        "password": TEST_PASSWORD
    }
    
    try:
        response = requests.post(login_url, json=login_data)
        if response.status_code == 200:
            token_data = response.json()
            print(f"✅ 로그인 성공: {TEST_USER_ID}")
            return token_data.get("access_token")
        else:
            print(f"❌ 로그인 실패: {response.status_code}")
            print(f"응답: {response.text}")
            return None
    except Exception as e:
        print(f"❌ 로그인 오류: {str(e)}")
        return None

def test_organization_settings_update(token):
    """조직 설정 업데이트 테스트"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. 현재 조직 설정 조회
    print("\n🔍 1. 현재 조직 설정 조회")
    settings_url = f"{BASE_URL}{API_PREFIX}/organizations/current/settings"
    
    try:
        response = requests.get(settings_url, headers=headers)
        if response.status_code == 200:
            current_settings = response.json()
            print(f"✅ 현재 설정 조회 성공")
            print(f"조직 ID: {current_settings.get('organization', {}).get('org_id')}")
            print(f"현재 설정: {json.dumps(current_settings.get('settings', {}), indent=2, ensure_ascii=False)}")
            
            org_id = current_settings.get('organization', {}).get('org_id')
            if not org_id:
                print("❌ 조직 ID를 찾을 수 없습니다.")
                return False
        else:
            print(f"❌ 현재 설정 조회 실패: {response.status_code}")
            print(f"응답: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 현재 설정 조회 오류: {str(e)}")
        return False
    
    # 2. 조직 설정 업데이트 테스트
    print(f"\n🔧 2. 조직 설정 업데이트 테스트 (조직 ID: {org_id})")
    update_url = f"{BASE_URL}{API_PREFIX}/organizations/{org_id}/settings"
    
    # 테스트할 설정 데이터
    update_data = {
        "mail_retention_days": 180,
        "max_attachment_size_mb": 50,
        "enable_spam_filter": True,
        "enable_virus_scan": False,
        "enable_encryption": True,
        "backup_enabled": True,
        "backup_retention_days": 60,
        "notification_settings": {
            "email_notifications": True,
            "system_alerts": False,
            "security_alerts": True,
            "maintenance_notifications": False
        },
        "security_settings": {
            "password_policy": {
                "min_length": 10,
                "require_uppercase": True,
                "require_lowercase": True,
                "require_numbers": True,
                "require_special_chars": False
            },
            "session_timeout_minutes": 240,
            "max_login_attempts": 3,
            "lockout_duration_minutes": 15,
            "require_2fa": True
        },
        "feature_flags": {
            "advanced_search": True,
            "mail_templates": False,
            "auto_reply": True,
            "mail_forwarding": False,
            "calendar_integration": True,
            "mobile_app": True,
            "api_access": False
        }
    }
    
    print(f"업데이트할 설정: {json.dumps(update_data, indent=2, ensure_ascii=False)}")
    
    try:
        response = requests.put(update_url, json=update_data, headers=headers)
        if response.status_code == 200:
            updated_settings = response.json()
            print(f"✅ 설정 업데이트 성공")
            print(f"업데이트된 설정: {json.dumps(updated_settings.get('settings', {}), indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ 설정 업데이트 실패: {response.status_code}")
            print(f"응답: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 설정 업데이트 오류: {str(e)}")
        return False
    
    # 3. 업데이트된 설정 재조회 및 검증
    print(f"\n🔍 3. 업데이트된 설정 재조회 및 검증")
    
    try:
        response = requests.get(settings_url, headers=headers)
        if response.status_code == 200:
            final_settings = response.json()
            print(f"✅ 최종 설정 조회 성공")
            
            settings_data = final_settings.get('settings', {})
            
            # 주요 설정 값 검증
            print(f"\n📊 설정 값 검증:")
            print(f"- 메일 보관 기간: {settings_data.get('mail_retention_days')} (예상: 180)")
            print(f"- 최대 첨부파일 크기: {settings_data.get('max_attachment_size_mb')} (예상: 50)")
            print(f"- 스팸 필터: {settings_data.get('enable_spam_filter')} (예상: True)")
            print(f"- 암호화: {settings_data.get('enable_encryption')} (예상: True)")
            
            # security_settings와 feature_flags는 JSON 문자열로 저장될 수 있음
            try:
                security_settings = settings_data.get('security_settings', '{}')
                if isinstance(security_settings, str):
                    security_settings = json.loads(security_settings)
                require_2fa = security_settings.get('require_2fa')
                print(f"- 2FA 필수: {require_2fa} (예상: True)")
            except (json.JSONDecodeError, AttributeError) as e:
                print(f"- 2FA 필수: 파싱 오류 ({e})")
                
            try:
                feature_flags = settings_data.get('feature_flags', '{}')
                if isinstance(feature_flags, str):
                    feature_flags = json.loads(feature_flags)
                advanced_search = feature_flags.get('advanced_search')
                print(f"- 고급 검색: {advanced_search} (예상: True)")
            except (json.JSONDecodeError, AttributeError) as e:
                print(f"- 고급 검색: 파싱 오류 ({e})")
            
            # 검증 (문자열과 불린 값 모두 고려)
            success = True
            
            # 숫자 값 검증
            mail_retention = settings_data.get('mail_retention_days')
            if str(mail_retention) != "180":
                print(f"❌ 메일 보관 기간 불일치: {mail_retention}")
                success = False
                
            max_attachment = settings_data.get('max_attachment_size_mb')
            if str(max_attachment) != "50":
                print(f"❌ 최대 첨부파일 크기 불일치: {max_attachment}")
                success = False
            
            # 불린 값 검증 (문자열 "true"/"false"와 불린 True/False 모두 고려)
            spam_filter = settings_data.get('enable_spam_filter')
            if not (spam_filter == True or spam_filter == "true"):
                print(f"❌ 스팸 필터 설정 불일치: {spam_filter}")
                success = False
                
            encryption = settings_data.get('enable_encryption')
            if not (encryption == True or encryption == "true"):
                print(f"❌ 암호화 설정 불일치: {encryption}")
                success = False
            
            if success:
                print(f"✅ 모든 설정 값이 올바르게 업데이트되었습니다!")
            else:
                print(f"❌ 일부 설정 값이 올바르게 업데이트되지 않았습니다.")
                
            return success
        else:
            print(f"❌ 최종 설정 조회 실패: {response.status_code}")
            print(f"응답: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 최종 설정 조회 오류: {str(e)}")
        return False

def main():
    """메인 함수"""
    print("🧪 조직 설정 업데이트 기능 테스트 시작")
    print("=" * 60)
    
    # 1. 인증 토큰 획득
    token = get_auth_token()
    if not token:
        print("❌ 인증 실패로 테스트를 중단합니다.")
        sys.exit(1)
    
    # 2. 조직 설정 업데이트 테스트
    success = test_organization_settings_update(token)
    
    print("\n" + "=" * 60)
    if success:
        print("✅ 조직 설정 업데이트 기능 테스트 완료 - 모든 테스트 통과!")
    else:
        print("❌ 조직 설정 업데이트 기능 테스트 실패")
        sys.exit(1)

if __name__ == "__main__":
    main()