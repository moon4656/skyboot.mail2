#!/usr/bin/env python3
"""
API 엔드포인트 확인 및 테스트 스크립트

현재 실행 중인 FastAPI 서버의 엔드포인트를 확인하고 테스트합니다.
"""
import requests
import json

def check_server_status():
    """서버 상태 확인"""
    print("🔍 서버 상태 확인")
    print("=" * 60)
    
    try:
        response = requests.get("http://localhost:8001/")
        print(f"✅ 서버 응답 상태: {response.status_code}")
        if response.status_code == 200:
            print(f"   응답 내용: {response.text[:100]}...")
    except Exception as e:
        print(f"❌ 서버 연결 실패: {e}")

def check_openapi_spec():
    """OpenAPI 스펙 확인"""
    print("\n🔍 OpenAPI 스펙 확인")
    print("=" * 60)
    
    try:
        response = requests.get("http://localhost:8001/openapi.json")
        if response.status_code == 200:
            spec = response.json()
            print(f"✅ OpenAPI 스펙 조회 성공")
            print(f"   제목: {spec.get('info', {}).get('title', 'N/A')}")
            print(f"   버전: {spec.get('info', {}).get('version', 'N/A')}")
            
            # 엔드포인트 목록 출력
            paths = spec.get('paths', {})
            print(f"\n📋 사용 가능한 엔드포인트 ({len(paths)}개):")
            
            auth_endpoints = []
            mail_endpoints = []
            other_endpoints = []
            
            for path, methods in paths.items():
                for method, details in methods.items():
                    endpoint_info = f"{method.upper()} {path}"
                    summary = details.get('summary', 'N/A')
                    
                    if '/auth' in path:
                        auth_endpoints.append(f"    - {endpoint_info} ({summary})")
                    elif '/mail' in path:
                        mail_endpoints.append(f"    - {endpoint_info} ({summary})")
                    else:
                        other_endpoints.append(f"    - {endpoint_info} ({summary})")
            
            if auth_endpoints:
                print(f"\n  🔐 인증 관련 엔드포인트:")
                for endpoint in auth_endpoints[:10]:  # 최대 10개만 표시
                    print(endpoint)
            
            if mail_endpoints:
                print(f"\n  📧 메일 관련 엔드포인트:")
                for endpoint in mail_endpoints[:10]:  # 최대 10개만 표시
                    print(endpoint)
            
            if other_endpoints:
                print(f"\n  🔧 기타 엔드포인트:")
                for endpoint in other_endpoints[:5]:  # 최대 5개만 표시
                    print(endpoint)
            
            return spec
        else:
            print(f"❌ OpenAPI 스펙 조회 실패: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ OpenAPI 스펙 조회 중 오류: {e}")
        return None

def test_auth_endpoints():
    """인증 엔드포인트 테스트"""
    print("\n🔐 인증 엔드포인트 테스트")
    print("=" * 60)
    
    # 가능한 로그인 엔드포인트들 (OpenAPI 스펙에서 확인된 실제 엔드포인트)
    login_endpoints = [
        "/api/v1/auth/login",
        "/auth/login",
        "/api/auth/login", 
        "/login",
        "/api/login"
    ]
    
    login_data = {
        "user_id": "user01@example.com",
        "password": "test"
    }
    
    for endpoint in login_endpoints:
        try:
            url = f"http://localhost:8001{endpoint}"
            print(f"\n🧪 테스트: POST {endpoint}")
            
            response = requests.post(url, json=login_data)
            print(f"   응답 상태: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                if "access_token" in result:
                    print(f"   ✅ 로그인 성공! 토큰: {result['access_token'][:50]}...")
                    return result["access_token"], endpoint
                else:
                    print(f"   ⚠️ 응답에 토큰이 없음: {result}")
            elif response.status_code == 404:
                print(f"   ❌ 엔드포인트 없음")
            else:
                print(f"   ❌ 로그인 실패: {response.text}")
                
        except Exception as e:
            print(f"   ❌ 요청 실패: {e}")
    
    return None, None

def test_mail_endpoints(token, auth_endpoint):
    """메일 엔드포인트 테스트"""
    if not token:
        print("\n❌ 토큰이 없어 메일 엔드포인트 테스트를 건너뜁니다.")
        return
    
    print(f"\n📧 메일 엔드포인트 테스트 (토큰 사용)")
    print("=" * 60)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 가능한 메일 엔드포인트들 (OpenAPI 스펙에서 확인된 실제 엔드포인트)
    mail_endpoints = [
        ("/api/v1/mail/inbox", "받은 메일함 조회"),
        ("/api/v1/mail/sent", "보낸 메일함 조회"),
        ("/mail/unread", "읽지 않은 메일 조회"),
        ("/mail/inbox", "받은 메일함 조회"),
        ("/api/mail/unread", "읽지 않은 메일 조회 (api prefix)"),
        ("/api/mail/inbox", "받은 메일함 조회 (api prefix)")
    ]
    
    for endpoint, description in mail_endpoints:
        try:
            url = f"http://localhost:8001{endpoint}"
            print(f"\n🧪 테스트: GET {endpoint} ({description})")
            
            response = requests.get(url, headers=headers)
            print(f"   응답 상태: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                total = result.get('total', 0)
                mails_count = len(result.get('mails', []))
                print(f"   ✅ 성공! 총 개수: {total}, 메일 수: {mails_count}")
                
                if mails_count > 0:
                    first_mail = result['mails'][0]
                    subject = first_mail.get('subject', 'N/A')
                    print(f"   첫 번째 메일: {subject}")
                
            elif response.status_code == 404:
                print(f"   ❌ 엔드포인트 없음")
            else:
                print(f"   ❌ 요청 실패: {response.text}")
                
        except Exception as e:
            print(f"   ❌ 요청 실패: {e}")

def main():
    """메인 함수"""
    print("🔍 API 엔드포인트 확인 및 테스트")
    print("=" * 60)
    
    # 1. 서버 상태 확인
    check_server_status()
    
    # 2. OpenAPI 스펙 확인
    spec = check_openapi_spec()
    
    # 3. 인증 엔드포인트 테스트
    token, auth_endpoint = test_auth_endpoints()
    
    # 4. 메일 엔드포인트 테스트
    test_mail_endpoints(token, auth_endpoint)
    
    print("\n" + "=" * 60)
    print("🔍 API 엔드포인트 확인 및 테스트 완료")
    
    if token:
        print(f"✅ 성공적으로 로그인했습니다. 인증 엔드포인트: {auth_endpoint}")
    else:
        print("❌ 로그인에 실패했습니다. 엔드포인트나 인증 정보를 확인해주세요.")

if __name__ == "__main__":
    main()