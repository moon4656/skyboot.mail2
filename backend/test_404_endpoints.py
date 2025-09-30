#!/usr/bin/env python3
"""
404 Not Found 오류 테스트 스크립트 (인증 포함)
"""

import requests
import json
from datetime import datetime

# 기본 설정
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"

def get_auth_token():
    """테스트용 인증 토큰 획득"""
    try:
        # 로그인 시도
        login_data = {
            "email": "admin@skyboot.mail",
            "password": "admin123!@#"
        }
        
        response = requests.post(f"{BASE_URL}{API_PREFIX}/auth/login", json=login_data)
        if response.status_code == 200:
            token_data = response.json()
            return token_data.get("access_token")
        else:
            print(f"⚠️ 로그인 실패: {response.status_code}")
            return None
    except Exception as e:
        print(f"⚠️ 로그인 중 오류: {str(e)}")
        return None

def test_endpoints_with_auth():
    """인증 토큰을 사용한 엔드포인트 테스트"""
    print("🔍 404 Not Found 오류 테스트 시작 (인증 포함)")
    print("=" * 60)
    
    # 인증 토큰 획득
    print("🔑 인증 토큰 획득 중...")
    token = get_auth_token()
    
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
        print("✅ 인증 토큰 획득 성공")
    else:
        print("❌ 인증 토큰 획득 실패 - 인증 없이 테스트 진행")
    
    # 테스트할 엔드포인트 목록
    endpoints_to_test = [
        # mail_convenience_router 엔드포인트
        {
            "method": "GET",
            "url": f"{BASE_URL}{API_PREFIX}/mail/search/suggestions",
            "description": "검색 자동완성"
        },
        {
            "method": "POST", 
            "url": f"{BASE_URL}{API_PREFIX}/mail/search",
            "description": "메일 검색",
            "data": {"query": "test"}
        },
        {
            "method": "GET",
            "url": f"{BASE_URL}{API_PREFIX}/mail/stats",
            "description": "메일 통계"
        },
        {
            "method": "GET",
            "url": f"{BASE_URL}{API_PREFIX}/mail/unread",
            "description": "읽지 않은 메일"
        },
        {
            "method": "GET",
            "url": f"{BASE_URL}{API_PREFIX}/mail/starred",
            "description": "중요 표시된 메일"
        },
        
        # mail_advanced_router 엔드포인트
        {
            "method": "GET",
            "url": f"{BASE_URL}{API_PREFIX}/mail/folders",
            "description": "폴더 목록 조회"
        },
        {
            "method": "POST",
            "url": f"{BASE_URL}{API_PREFIX}/mail/folders",
            "description": "폴더 생성",
            "data": {"name": "test_folder"}
        },
        {
            "method": "GET",
            "url": f"{BASE_URL}{API_PREFIX}/mail/analytics",
            "description": "메일 분석"
        },
        {
            "method": "POST",
            "url": f"{BASE_URL}{API_PREFIX}/mail/backup",
            "description": "메일 백업"
        },
        
        # 존재하지 않는 엔드포인트 (404 확인용)
        {
            "method": "GET",
            "url": f"{BASE_URL}{API_PREFIX}/mail/nonexistent",
            "description": "존재하지 않는 엔드포인트 (404 확인용)"
        }
    ]
    
    results = []
    
    for endpoint in endpoints_to_test:
        try:
            print(f"\n📡 테스트: {endpoint['description']}")
            print(f"   URL: {endpoint['url']}")
            print(f"   Method: {endpoint['method']}")
            
            # 요청 실행
            if endpoint['method'] == 'GET':
                response = requests.get(endpoint['url'], headers=headers, timeout=10)
            elif endpoint['method'] == 'POST':
                data = endpoint.get('data', {})
                response = requests.post(endpoint['url'], json=data, headers=headers, timeout=10)
            else:
                print(f"   ❌ 지원하지 않는 메서드: {endpoint['method']}")
                continue
            
            # 결과 출력
            status_code = response.status_code
            if status_code == 404:
                print(f"   ❌ 404 Not Found - 엔드포인트가 등록되지 않음")
                status = "404_ERROR"
            elif status_code == 401:
                print(f"   🔒 401 Unauthorized - 인증 필요 (엔드포인트는 존재함)")
                status = "AUTH_REQUIRED"
            elif status_code == 403:
                print(f"   🚫 403 Forbidden - 권한 부족 (엔드포인트는 존재함)")
                status = "PERMISSION_DENIED"
            elif status_code == 422:
                print(f"   ⚠️ 422 Validation Error - 입력 데이터 오류 (엔드포인트는 존재함)")
                status = "VALIDATION_ERROR"
                # 상세 오류 정보 출력
                try:
                    error_detail = response.json()
                    print(f"      상세: {error_detail.get('message', 'N/A')}")
                except:
                    pass
            elif status_code == 500:
                print(f"   💥 500 Internal Server Error - 서버 오류")
                status = "SERVER_ERROR"
                # 상세 오류 정보 출력
                try:
                    error_detail = response.json()
                    print(f"      상세: {error_detail.get('message', 'N/A')}")
                except:
                    pass
            elif 200 <= status_code < 300:
                print(f"   ✅ {status_code} Success - 정상 작동")
                status = "SUCCESS"
            else:
                print(f"   ❓ {status_code} - 기타 응답")
                status = f"OTHER_{status_code}"
            
            results.append({
                "endpoint": endpoint['description'],
                "url": endpoint['url'],
                "method": endpoint['method'],
                "status_code": status_code,
                "status": status
            })
            
        except requests.exceptions.ConnectionError:
            print(f"   💔 연결 오류 - 서버가 실행되지 않음")
            results.append({
                "endpoint": endpoint['description'],
                "url": endpoint['url'],
                "method": endpoint['method'],
                "status_code": None,
                "status": "CONNECTION_ERROR"
            })
        except requests.exceptions.Timeout:
            print(f"   ⏰ 타임아웃 오류")
            results.append({
                "endpoint": endpoint['description'],
                "url": endpoint['url'],
                "method": endpoint['method'],
                "status_code": None,
                "status": "TIMEOUT"
            })
        except Exception as e:
            print(f"   💥 예상치 못한 오류: {str(e)}")
            results.append({
                "endpoint": endpoint['description'],
                "url": endpoint['url'],
                "method": endpoint['method'],
                "status_code": None,
                "status": f"ERROR: {str(e)}"
            })
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("📊 테스트 결과 요약")
    print("=" * 60)
    
    error_404_count = sum(1 for r in results if r['status'] == '404_ERROR')
    auth_required_count = sum(1 for r in results if r['status'] == 'AUTH_REQUIRED')
    permission_denied_count = sum(1 for r in results if r['status'] == 'PERMISSION_DENIED')
    validation_error_count = sum(1 for r in results if r['status'] == 'VALIDATION_ERROR')
    server_error_count = sum(1 for r in results if r['status'] == 'SERVER_ERROR')
    success_count = sum(1 for r in results if r['status'] == 'SUCCESS')
    total_count = len(results)
    
    print(f"📈 전체 테스트: {total_count}개")
    print(f"❌ 404 오류: {error_404_count}개")
    print(f"🔒 인증 필요: {auth_required_count}개")
    print(f"🚫 권한 부족: {permission_denied_count}개")
    print(f"⚠️ 검증 오류: {validation_error_count}개")
    print(f"💥 서버 오류: {server_error_count}개")
    print(f"✅ 정상 작동: {success_count}개")
    
    # 404 오류 상세 목록
    if error_404_count > 0:
        print(f"\n🚨 404 Not Found 오류 발생 엔드포인트:")
        for result in results:
            if result['status'] == '404_ERROR':
                print(f"   - {result['endpoint']}: {result['url']}")
    else:
        print(f"\n✅ 404 Not Found 오류가 발생한 엔드포인트가 없습니다.")
    
    # 서버 오류 상세 목록
    if server_error_count > 0:
        print(f"\n💥 서버 오류 발생 엔드포인트:")
        for result in results:
            if result['status'] == 'SERVER_ERROR':
                print(f"   - {result['endpoint']}: {result['url']}")
    
    # 결과를 JSON 파일로 저장
    with open('404_test_results_with_auth.json', 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "auth_token_used": token is not None,
            "summary": {
                "total": total_count,
                "404_errors": error_404_count,
                "auth_required": auth_required_count,
                "permission_denied": permission_denied_count,
                "validation_errors": validation_error_count,
                "server_errors": server_error_count,
                "success": success_count
            },
            "results": results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 상세 결과가 '404_test_results_with_auth.json' 파일에 저장되었습니다.")
    
    return results

if __name__ == "__main__":
    test_endpoints_with_auth()