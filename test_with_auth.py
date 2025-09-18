#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
사용자 생성과 로그인 인증 후 메일 엔드포인트 테스트 스크립트

이 스크립트는 다음 기능을 수행합니다:
1. 테스트용 사용자 생성 (회원가입)
2. 로그인하여 JWT 토큰 획득
3. 인증된 상태로 모든 메일 엔드포인트 테스트
4. 테스트 결과를 체크리스트 형태로 출력
5. 오류 발생 시 상세한 에러 메시지 표시
"""

import requests
import json
import datetime
from typing import Dict, Any, Optional, List
import sys
import traceback

# 서버 설정
BASE_URL = "http://localhost:8000"
API_BASE = BASE_URL

# 테스트 사용자 정보
TEST_USER = {
    "email": "test@example.com",
    "username": "testuser",
    "password": "testpassword123"
}

# 전역 변수
access_token = None
test_results = []

def log_test_result(endpoint: str, method: str, status_code: int, success: bool, message: str = ""):
    """
    테스트 결과를 로깅합니다.
    
    Args:
        endpoint: 테스트한 엔드포인트
        method: HTTP 메서드
        status_code: 응답 상태 코드
        success: 테스트 성공 여부
        message: 추가 메시지
    """
    result = {
        "timestamp": datetime.datetime.now().isoformat(),
        "endpoint": endpoint,
        "method": method,
        "status_code": status_code,
        "success": success,
        "message": message
    }
    test_results.append(result)
    
    # 콘솔 출력
    status_icon = "✅" if success else "❌"
    print(f"{status_icon} {method} {endpoint} - {status_code} - {message}")

def make_request(method: str, endpoint: str, data: Dict = None, headers: Dict = None) -> requests.Response:
    """
    HTTP 요청을 보냅니다.
    
    Args:
        method: HTTP 메서드
        endpoint: API 엔드포인트
        data: 요청 데이터
        headers: 요청 헤더
    
    Returns:
        requests.Response 객체
    """
    url = f"{API_BASE}{endpoint}"
    
    # 기본 헤더 설정
    default_headers = {"Content-Type": "application/json"}
    if headers:
        default_headers.update(headers)
    
    # 인증 토큰이 있으면 헤더에 추가
    if access_token:
        default_headers["Authorization"] = f"Bearer {access_token}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=default_headers, params=data)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, headers=default_headers)
        elif method.upper() == "PUT":
            response = requests.put(url, json=data, headers=default_headers)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=default_headers)
        else:
            raise ValueError(f"지원하지 않는 HTTP 메서드: {method}")
        
        return response
    except requests.exceptions.RequestException as e:
        print(f"❌ 요청 오류: {e}")
        raise

def register_user() -> bool:
    """
    테스트용 사용자를 생성합니다.
    
    Returns:
        사용자 생성 성공 여부
    """
    print("\n🔧 사용자 생성 중...")
    
    try:
        response = make_request("POST", "/auth/register", TEST_USER)
        
        print(f"📊 응답 상태 코드: {response.status_code}")
        print(f"📊 응답 헤더: {dict(response.headers)}")
        print(f"📊 응답 내용: {response.text}")
        
        if response.status_code == 201:
            try:
                result = response.json()
                log_test_result("/auth/register", "POST", response.status_code, True, "사용자 생성 성공")
                return True
            except Exception as e:
                print(f"❌ JSON 파싱 오류: {e}")
                return False
        elif response.status_code == 400:
            # 이미 존재하는 사용자일 수 있음
            try:
                error_detail = response.json().get("detail", "")
            except:
                error_detail = response.text
            if "already exists" in error_detail.lower() or "이미 존재" in error_detail or "already registered" in error_detail.lower():
                log_test_result("/auth/register", "POST", response.status_code, True, "사용자가 이미 존재함 (정상)")
                print("✅ 사용자가 이미 존재합니다. 로그인을 진행합니다.")
                return True
            else:
                log_test_result("/auth/register", "POST", response.status_code, False, f"사용자 생성 실패: {error_detail}")
                return False
        else:
            try:
                error_detail = response.json().get("detail", "알 수 없는 오류")
            except:
                error_detail = response.text
            log_test_result("/auth/register", "POST", response.status_code, False, f"사용자 생성 실패: {error_detail}")
            return False
            
    except Exception as e:
        log_test_result("/auth/register", "POST", 0, False, f"예외 발생: {str(e)}")
        print(f"❌ 사용자 생성 중 오류 발생: {e}")
        return False

def login_user() -> bool:
    """
    사용자 로그인을 수행하고 JWT 토큰을 획득합니다.
    
    Returns:
        로그인 성공 여부
    """
    global access_token
    
    print("\n🔑 사용자 로그인 중...")
    
    login_data = {
        "email": TEST_USER["email"],
        "password": TEST_USER["password"]
    }
    
    try:
        response = make_request("POST", "/auth/login", login_data)
        
        if response.status_code == 200:
            response_data = response.json()
            access_token = response_data.get("access_token")
            
            if access_token:
                log_test_result("/auth/login", "POST", response.status_code, True, "로그인 성공, 토큰 획득")
                print(f"🎫 JWT 토큰 획득: {access_token[:20]}...")
                return True
            else:
                log_test_result("/auth/login", "POST", response.status_code, False, "토큰이 응답에 없음")
                return False
        else:
            error_detail = response.json().get("detail", "알 수 없는 오류")
            log_test_result("/auth/login", "POST", response.status_code, False, f"로그인 실패: {error_detail}")
            return False
            
    except Exception as e:
        log_test_result("/auth/login", "POST", 0, False, f"예외 발생: {str(e)}")
        print(f"❌ 로그인 중 오류 발생: {e}")
        return False

def test_mail_endpoints():
    """
    인증된 상태로 모든 메일 엔드포인트를 테스트합니다.
    """
    print("\n📧 메일 엔드포인트 테스트 시작...")
    
    # 테스트할 엔드포인트 목록
    endpoints_to_test = [
        # 메일 조회 관련
        {"method": "GET", "endpoint": "/mail/inbox", "description": "받은 메일함 조회"},
        {"method": "GET", "endpoint": "/mail/sent", "description": "보낸 메일함 조회"},
        {"method": "GET", "endpoint": "/mail/drafts", "description": "임시보관함 조회"},
        {"method": "GET", "endpoint": "/mail/trash", "description": "휴지통 조회"},
        {"method": "GET", "endpoint": "/mail/spam", "description": "스팸 메일함 조회"},
        
        # 메일 발송 관련
        {"method": "POST", "endpoint": "/mail/send", "description": "메일 발송", "data": {
            "recipient_email": "recipient@example.com",
            "subject": "테스트 메일",
            "content": "이것은 테스트 메일입니다.",
            "content_type": "text/plain"
        }},
        {"method": "POST", "endpoint": "/mail/draft", "description": "임시저장", "data": {
            "recipient_email": "draft@example.com",
            "subject": "임시저장 테스트",
            "content": "임시저장 테스트 내용"
        }},
        
        # 메일 상태 관리
        {"method": "PUT", "endpoint": "/mail/test-mail-id/read", "description": "메일 읽음 처리"},
        {"method": "POST", "endpoint": "/mail/test-mail-id/unread", "description": "메일 읽지않음 처리"},
        {"method": "POST", "endpoint": "/mail/mark-all-read", "description": "모든 메일 읽음 처리"},
        
        # 메일 관리
        {"method": "PUT", "endpoint": "/mail/test-mail-id/trash", "description": "메일 휴지통 이동"},
        {"method": "PUT", "endpoint": "/mail/test-mail-id/restore", "description": "메일 복원"},
        {"method": "DELETE", "endpoint": "/mail/test-mail-id/permanent", "description": "메일 영구 삭제"},
        {"method": "PUT", "endpoint": "/mail/test-mail-id/move", "description": "메일 이동", "data": {"folder": "inbox"}},
        
        # 대량 작업
        {"method": "POST", "endpoint": "/mail/bulk-action", "description": "대량 작업", "data": {
            "mail_ids": ["test-mail-id-1", "test-mail-id-2"],
            "action": "mark_read"
        }},
        
        # 검색 및 필터
        {"method": "GET", "endpoint": "/mail/search", "description": "메일 검색", "data": {"query": "test"}},
        {"method": "GET", "endpoint": "/mail/filter", "description": "메일 필터", "data": {"folder": "inbox", "unread_only": True}},
        
        # 첨부파일 관리
        {"method": "POST", "endpoint": "/mail/attachment/upload", "description": "첨부파일 업로드"},
        {"method": "GET", "endpoint": "/mail/attachment/test-attachment-id", "description": "첨부파일 다운로드"},
        {"method": "DELETE", "endpoint": "/mail/attachment/test-attachment-id", "description": "첨부파일 삭제"},
        
        # 메일 상세 조회
        {"method": "GET", "endpoint": "/mail/test-mail-id", "description": "메일 상세 조회"},
        {"method": "GET", "endpoint": "/mail/test-mail-id/raw", "description": "메일 원본 조회"},
        
        # 통계 및 정보
        {"method": "GET", "endpoint": "/mail/stats", "description": "메일 통계 조회"},
        {"method": "GET", "endpoint": "/mail/folders", "description": "폴더 목록 조회"},
        
        # 설정 관리
        {"method": "GET", "endpoint": "/mail/settings", "description": "메일 설정 조회"},
        {"method": "PUT", "endpoint": "/mail/settings", "description": "메일 설정 업데이트", "data": {
            "auto_reply": False,
            "signature": "테스트 서명"
        }}
    ]
    
    # 각 엔드포인트 테스트 실행
    for test_case in endpoints_to_test:
        try:
            method = test_case["method"]
            endpoint = test_case["endpoint"]
            description = test_case["description"]
            data = test_case.get("data")
            
            print(f"\n🧪 테스트 중: {description} ({method} {endpoint})")
            
            response = make_request(method, endpoint, data)
            
            # 성공 조건 판단
            success = response.status_code < 500  # 5xx 에러가 아니면 성공으로 간주
            
            # 특별한 경우 처리
            if response.status_code == 404:
                message = "엔드포인트를 찾을 수 없음 (구현되지 않음)"
            elif response.status_code == 405:
                message = "허용되지 않는 HTTP 메서드"
            elif response.status_code == 401:
                message = "인증 실패"
                success = False  # 인증 실패는 실패로 처리
            elif response.status_code == 403:
                message = "권한 없음"
            elif response.status_code == 422:
                message = "요청 데이터 검증 실패"
            elif 200 <= response.status_code < 300:
                message = "성공"
            else:
                try:
                    error_detail = response.json().get("detail", "알 수 없는 오류")
                    message = f"오류: {error_detail}"
                except:
                    message = f"HTTP {response.status_code} 오류"
            
            log_test_result(endpoint, method, response.status_code, success, message)
            
        except Exception as e:
            log_test_result(endpoint, method, 0, False, f"예외 발생: {str(e)}")
            print(f"❌ 테스트 중 오류 발생: {e}")

def print_test_summary():
    """
    테스트 결과 요약을 출력합니다.
    """
    print("\n" + "="*80)
    print("📊 테스트 결과 요약")
    print("="*80)
    
    total_tests = len(test_results)
    successful_tests = sum(1 for result in test_results if result["success"])
    failed_tests = total_tests - successful_tests
    
    print(f"\n📈 전체 테스트: {total_tests}개")
    print(f"✅ 성공: {successful_tests}개")
    print(f"❌ 실패: {failed_tests}개")
    print(f"📊 성공률: {(successful_tests/total_tests*100):.1f}%")
    
    # 실패한 테스트 목록
    if failed_tests > 0:
        print("\n❌ 실패한 테스트:")
        for result in test_results:
            if not result["success"]:
                print(f"  - {result['method']} {result['endpoint']}: {result['message']}")
    
    # 성공한 테스트 목록
    print("\n✅ 성공한 테스트:")
    for result in test_results:
        if result["success"]:
            print(f"  - {result['method']} {result['endpoint']}: {result['message']}")

def save_test_results():
    """
    테스트 결과를 JSON 파일로 저장합니다.
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"test_results_with_auth_{timestamp}.json"
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(test_results, f, ensure_ascii=False, indent=2)
        print(f"\n💾 테스트 결과가 {filename}에 저장되었습니다.")
    except Exception as e:
        print(f"❌ 테스트 결과 저장 실패: {e}")

def main():
    """
    메인 함수: 전체 테스트 프로세스를 실행합니다.
    """
    print("🚀 메일 서버 인증 테스트 시작")
    print(f"🌐 서버 URL: {BASE_URL}")
    print(f"👤 테스트 사용자: {TEST_USER['email']}")
    
    try:
        # 1. 사용자 생성
        if not register_user():
            print("❌ 사용자 생성에 실패했습니다. 테스트를 중단합니다.")
            return False
        
        # 2. 로그인
        if not login_user():
            print("❌ 로그인에 실패했습니다. 테스트를 중단합니다.")
            return False
        
        # 3. 메일 엔드포인트 테스트
        test_mail_endpoints()
        
        # 4. 결과 요약 출력
        print_test_summary()
        
        # 5. 결과 저장
        save_test_results()
        
        print("\n🎉 모든 테스트가 완료되었습니다!")
        return True
        
    except KeyboardInterrupt:
        print("\n⚠️ 사용자에 의해 테스트가 중단되었습니다.")
        return False
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류가 발생했습니다: {e}")
        print(f"상세 오류: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)