#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
메일 라우터 엔드포인트 테스트 스크립트

이 스크립트는 mail_router.py의 모든 엔드포인트를 테스트하고
결과를 체크리스트에 업데이트합니다.
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, List, Any

# 기본 설정
BASE_URL = "http://localhost:8000"
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}

# 테스트 결과 저장
test_results = []

def log_test_result(endpoint: str, method: str, status_code: int, success: bool, error_msg: str = ""):
    """테스트 결과를 로깅합니다."""
    result = {
        "endpoint": endpoint,
        "method": method,
        "status_code": status_code,
        "success": success,
        "error_msg": error_msg,
        "timestamp": datetime.now().isoformat()
    }
    test_results.append(result)
    
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} {method} {endpoint} - Status: {status_code}")
    if error_msg:
        print(f"   Error: {error_msg}")

def test_endpoint(method: str, endpoint: str, data: Dict = None, auth_token: str = None):
    """개별 엔드포인트를 테스트합니다."""
    url = f"{BASE_URL}{endpoint}"
    headers = HEADERS.copy()
    
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=10)
        elif method.upper() == "PUT":
            response = requests.put(url, headers=headers, json=data, timeout=10)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=headers, timeout=10)
        else:
            log_test_result(endpoint, method, 0, False, f"Unsupported method: {method}")
            return None
        
        # 성공 조건: 2xx 상태코드 또는 인증 관련 401/403
        success = (200 <= response.status_code < 300) or response.status_code in [401, 403]
        error_msg = "" if success else f"HTTP {response.status_code}: {response.text[:200]}"
        
        log_test_result(endpoint, method, response.status_code, success, error_msg)
        return response
        
    except requests.exceptions.RequestException as e:
        log_test_result(endpoint, method, 0, False, str(e))
        return None

def test_all_endpoints():
    """모든 엔드포인트를 테스트합니다."""
    print("🚀 메일 라우터 엔드포인트 테스트 시작")
    print("=" * 50)
    
    # 1. 받은 메일함 관련 엔드포인트
    print("\n📥 받은 메일함 테스트")
    test_endpoint("GET", "/mail/inbox")
    test_endpoint("GET", "/mail/inbox/test-mail-id")
    test_endpoint("PUT", "/mail/inbox/test-mail-id/read")
    test_endpoint("PUT", "/mail/inbox/test-mail-id/unread")
    
    # 2. 보낸 메일함 관련 엔드포인트
    print("\n📤 보낸 메일함 테스트")
    test_endpoint("GET", "/mail/sent")
    test_endpoint("GET", "/mail/sent/test-mail-id")
    
    # 3. 메일 작성 및 발송
    print("\n✍️ 메일 작성/발송 테스트")
    test_data = {
        "subject": "테스트 메일",
        "content": "테스트 내용",
        "recipients": [{"email": "test@example.com", "name": "테스트", "type": "TO"}]
    }
    test_endpoint("POST", "/mail/send", test_data)
    
    # 4. 임시보관함
    print("\n📝 임시보관함 테스트")
    test_endpoint("GET", "/mail/drafts")
    test_endpoint("POST", "/mail/drafts", test_data)
    test_endpoint("GET", "/mail/drafts/test-draft-id")
    test_endpoint("PUT", "/mail/drafts/test-draft-id", test_data)
    test_endpoint("DELETE", "/mail/drafts/test-draft-id")
    
    # 5. 휴지통
    print("\n🗑️ 휴지통 테스트")
    test_endpoint("GET", "/mail/trash")
    test_endpoint("GET", "/mail/trash/test-mail-id")
    test_endpoint("PUT", "/mail/test-mail-id/trash")
    test_endpoint("PUT", "/mail/test-mail-id/restore")
    test_endpoint("DELETE", "/mail/test-mail-id/permanent")
    
    # 6. 폴더 관리
    print("\n📁 폴더 관리 테스트")
    test_endpoint("GET", "/mail/folders")
    folder_data = {"name": "테스트 폴더", "description": "테스트용 폴더"}
    test_endpoint("POST", "/mail/folders", folder_data)
    test_endpoint("GET", "/mail/folders/test-folder-id")
    test_endpoint("PUT", "/mail/folders/test-folder-id", folder_data)
    test_endpoint("DELETE", "/mail/folders/test-folder-id")
    
    # 7. 메일 이동
    print("\n📦 메일 이동 테스트")
    move_data = {"folder_id": "test-folder-id"}
    test_endpoint("PUT", "/mail/test-mail-id/move", move_data)
    
    # 8. 첨부파일
    print("\n📎 첨부파일 테스트")
    test_endpoint("GET", "/mail/test-mail-id/attachments")
    test_endpoint("GET", "/mail/attachments/test-attachment-id/download")
    
    # 9. 검색
    print("\n🔍 검색 테스트")
    search_data = {"keyword": "테스트"}
    test_endpoint("POST", "/mail/search", search_data)
    
    # 10. 통계
    print("\n📊 통계 테스트")
    test_endpoint("GET", "/mail/stats")
    
    # 11. 대량 작업
    print("\n📋 대량 작업 테스트")
    bulk_data = {"mail_ids": ["test-id-1", "test-id-2"], "action": "read"}
    test_endpoint("POST", "/mail/bulk", bulk_data)
    
    print("\n" + "=" * 50)
    print("🏁 테스트 완료")
    
    # 결과 요약
    total_tests = len(test_results)
    passed_tests = sum(1 for r in test_results if r["success"])
    failed_tests = total_tests - passed_tests
    
    print(f"\n📈 테스트 결과 요약:")
    print(f"   총 테스트: {total_tests}")
    print(f"   성공: {passed_tests} ✅")
    print(f"   실패: {failed_tests} ❌")
    print(f"   성공률: {(passed_tests/total_tests*100):.1f}%")
    
    return test_results

def save_results_to_file(results: List[Dict]):
    """테스트 결과를 파일로 저장합니다."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"test_results_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 테스트 결과가 {filename}에 저장되었습니다.")

if __name__ == "__main__":
    try:
        # 서버 연결 확인
        print("🔗 서버 연결 확인 중...")
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        if response.status_code == 200:
            print("✅ 서버 연결 성공")
        else:
            print(f"❌ 서버 연결 실패: HTTP {response.status_code}")
            sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"❌ 서버에 연결할 수 없습니다: {e}")
        print("💡 서버가 실행 중인지 확인해주세요: http://localhost:8000")
        sys.exit(1)
    
    # 테스트 실행
    results = test_all_endpoints()
    save_results_to_file(results)