import requests
import json
from datetime import datetime, timedelta
import time

# 테스트 설정
BASE_URL = "http://localhost:8000"
MAIL_CONVENIENCE_URL = f"{BASE_URL}/mail"

# 테스트 결과 저장용 딕셔너리
test_results = {
    "timestamp": datetime.now().isoformat(),
    "total_tests": 0,
    "passed_tests": 0,
    "failed_tests": 0,
    "results": []
}

# 테스트용 메일 ID 저장
test_mail_id_global = None

# 체크리스트
checklist = {
    "login_and_auth": False,
    "search_mails": False,
    "get_stats": False,
    "get_unread": False,
    "get_starred": False,
    "mark_read": False,
    "mark_unread": False,
    "mark_all_read": False,
    "star_mail": False,
    "unstar_mail": False,
    "search_suggestions": False
}

def log_test_result(test_name, success, response_data=None, error_message=None):
    """테스트 결과 로깅"""
    test_results["total_tests"] += 1
    if success:
        test_results["passed_tests"] += 1
        print(f"✅ {test_name}: PASSED")
    else:
        test_results["failed_tests"] += 1
        print(f"❌ {test_name}: FAILED - {error_message}")
    
    test_results["results"].append({
        "test_name": test_name,
        "success": success,
        "response_data": response_data,
        "error_message": error_message,
        "timestamp": datetime.now().isoformat()
    })

def save_test_results():
    """테스트 결과 저장"""
    filename = f"mail_convenience_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(test_results, f, ensure_ascii=False, indent=2)
    print(f"\n테스트 결과가 {filename}에 저장되었습니다.")

def print_checklist():
    """체크리스트 출력"""
    print("\n=== 테스트 체크리스트 ===")
    for test_name, completed in checklist.items():
        status = "✅" if completed else "⬜"
        print(f"{status} {test_name}")

def test_login_and_get_token():
    """로그인 후 인증 토큰 획득"""
    print("\n=== 1. 로그인 및 인증 토큰 획득 ===")
    
    try:
        # 로그인 요청
        login_data = {
            "email": "test@skyboot.com",
            "password": "test123456"
        }
        
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get("access_token")
            
            if access_token:
                headers = {"Authorization": f"Bearer {access_token}"}
                log_test_result("로그인 및 토큰 획득", True, {"token_acquired": True})
                checklist["login_and_auth"] = True
                return headers
            else:
                log_test_result("로그인 및 토큰 획득", False, error_message="토큰이 응답에 없음")
                return None
        else:
            log_test_result("로그인 및 토큰 획득", False, error_message=f"HTTP {response.status_code}: {response.text}")
            return None
            
    except Exception as e:
        log_test_result("로그인 및 토큰 획득", False, error_message=str(e))
        return None

def test_search_mails(headers):
    """메일 검색 테스트"""
    print("\n=== 2. 메일 검색 테스트 ===")
    
    try:
        # 기본 검색
        search_data = {
            "query": "test",
            "page": 1,
            "limit": 10
        }
        
        response = requests.post(f"{MAIL_CONVENIENCE_URL}/search", 
                               json=search_data, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            log_test_result("메일 검색", True, {"total_found": data.get("total", 0)})
            checklist["search_mails"] = True
        else:
            log_test_result("메일 검색", False, error_message=f"HTTP {response.status_code}: {response.text}")
            
    except Exception as e:
        log_test_result("메일 검색", False, error_message=str(e))

def test_get_stats(headers):
    """메일 통계 조회 테스트"""
    print("\n=== 3. 메일 통계 조회 테스트 ===")
    
    try:
        response = requests.get(f"{MAIL_CONVENIENCE_URL}/stats", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            stats = data.get("data", {})
            log_test_result("메일 통계 조회", True, stats)
            checklist["get_stats"] = True
        else:
            log_test_result("메일 통계 조회", False, error_message=f"HTTP {response.status_code}: {response.text}")
            
    except Exception as e:
        log_test_result("메일 통계 조회", False, error_message=str(e))

def test_get_unread(headers):
    """읽지 않은 메일 조회 테스트"""
    print("\n=== 4. 읽지 않은 메일 조회 테스트 ===")
    
    try:
        response = requests.get(f"{MAIL_CONVENIENCE_URL}/unread?page=1&limit=10", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            mail_data = data.get("data", {})
            log_test_result("읽지 않은 메일 조회", True, {"total": mail_data.get("total", 0)})
            checklist["get_unread"] = True
        else:
            log_test_result("읽지 않은 메일 조회", False, error_message=f"HTTP {response.status_code}: {response.text}")
            
    except Exception as e:
        log_test_result("읽지 않은 메일 조회", False, error_message=str(e))

def test_get_starred(headers):
    """중요 표시된 메일 조회 테스트"""
    print("\n=== 5. 중요 표시된 메일 조회 테스트 ===")
    
    try:
        response = requests.get(f"{MAIL_CONVENIENCE_URL}/starred?page=1&limit=10", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            mail_data = data.get("data", {})
            log_test_result("중요 표시된 메일 조회", True, {"total": mail_data.get("total", 0)})
            checklist["get_starred"] = True
        else:
            log_test_result("중요 표시된 메일 조회", False, error_message=f"HTTP {response.status_code}: {response.text}")
            
    except Exception as e:
        log_test_result("중요 표시된 메일 조회", False, error_message=str(e))

def send_test_mail(headers):
    """테스트용 메일 발송"""
    global test_mail_id_global
    try:
        print("📧 테스트용 메일 발송 중...")
        mail_data = {
            "to_emails": "test@skyboot.com",
            "subject": "테스트 메일 - 편의 기능 테스트용",
            "content": "이 메일은 편의 기능 엔드포인트 테스트를 위해 발송된 메일입니다.",
            "priority": "normal"
        }
        
        response = requests.post(f"{BASE_URL}/mail/send", data=mail_data, headers=headers)
        if response.status_code == 200:
            data = response.json()
            mail_id = data.get("mail_uuid")
            test_mail_id_global = mail_id  # 전역 변수에 저장
            print(f"✅ 테스트용 메일 발송 성공: {mail_id}")
            return mail_id
        else:
            print(f"❌ 테스트용 메일 발송 실패: {response.status_code}")
            print(f"오류 응답: {response.text}")
            return None
    except Exception as e:
        print(f"❌ 테스트용 메일 발송 오류: {str(e)}")
        return None

def get_test_mail_id(headers):
    """테스트용 메일 ID 획득"""
    global test_mail_id_global
    
    # 전역 변수에 저장된 메일 ID가 있으면 우선 사용
    if test_mail_id_global:
        print(f"🔍 저장된 테스트 메일 ID 사용: {test_mail_id_global}")
        return test_mail_id_global
    
    try:
        # 메일 검색을 통해 방금 발송한 테스트 메일 찾기
        search_params = {
            "query": "테스트 메일 - 편의 기능 테스트용",
            "page": 1,
            "limit": 10
        }
        
        response = requests.get(f"{MAIL_CONVENIENCE_URL}/search", params=search_params, headers=headers)
        if response.status_code == 200:
            data = response.json()
            mails = data.get("data", {}).get("mails", [])
            if mails:
                # 가장 최근 메일 반환
                mail_id = mails[0].get("id")
                print(f"🔍 검색으로 찾은 메일 ID: {mail_id}")
                return mail_id
        
        # 검색으로 찾지 못한 경우 받은 메일함에서 조회
        response = requests.get(f"{BASE_URL}/mail/inbox?page=1&limit=5", headers=headers)
        if response.status_code == 200:
            data = response.json()
            mails = data.get("data", {}).get("mails", [])
            if mails:
                mail_id = mails[0].get("id")
                print(f"🔍 받은 메일함에서 찾은 메일 ID: {mail_id}")
                return mail_id
        
        # 보낸 메일함에서 메일 조회
        response = requests.get(f"{BASE_URL}/mail/sent?page=1&limit=5", headers=headers)
        if response.status_code == 200:
            data = response.json()
            mails = data.get("data", {}).get("mails", [])
            if mails:
                mail_id = mails[0].get("id")
                print(f"🔍 보낸 메일함에서 찾은 메일 ID: {mail_id}")
                return mail_id
                
        print("❌ 어떤 메일함에서도 메일을 찾을 수 없음")
        return None
    except Exception as e:
        print(f"메일 ID 조회 오류: {str(e)}")
        return None

def test_mark_read(headers):
    """메일 읽음 처리 테스트"""
    print("\n=== 6. 메일 읽음 처리 테스트 ===")
    
    mail_id = get_test_mail_id(headers)
    if not mail_id:
        log_test_result("메일 읽음 처리", False, error_message="테스트할 메일 ID를 찾을 수 없음")
        return
    
    try:
        response = requests.post(f"{MAIL_CONVENIENCE_URL}/{mail_id}/read", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            log_test_result("메일 읽음 처리", True, {"mail_id": mail_id})
            checklist["mark_read"] = True
        else:
            log_test_result("메일 읽음 처리", False, error_message=f"HTTP {response.status_code}: {response.text}")
            
    except Exception as e:
        log_test_result("메일 읽음 처리", False, error_message=str(e))

def test_mark_unread(headers):
    """메일 읽지 않음 처리 테스트"""
    print("\n=== 7. 메일 읽지 않음 처리 테스트 ===")
    
    mail_id = get_test_mail_id(headers)
    if not mail_id:
        log_test_result("메일 읽지 않음 처리", False, error_message="테스트할 메일 ID를 찾을 수 없음")
        return
    
    try:
        response = requests.post(f"{MAIL_CONVENIENCE_URL}/{mail_id}/unread", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            log_test_result("메일 읽지 않음 처리", True, {"mail_id": mail_id})
            checklist["mark_unread"] = True
        else:
            log_test_result("메일 읽지 않음 처리", False, error_message=f"HTTP {response.status_code}: {response.text}")
            
    except Exception as e:
        log_test_result("메일 읽지 않음 처리", False, error_message=str(e))

def test_mark_all_read(headers):
    """모든 메일 읽음 처리 테스트"""
    print("\n=== 8. 모든 메일 읽음 처리 테스트 ===")
    
    try:
        response = requests.post(f"{MAIL_CONVENIENCE_URL}/mark-all-read?folder_type=inbox", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            log_test_result("모든 메일 읽음 처리", True, data.get("data", {}))
            checklist["mark_all_read"] = True
        else:
            log_test_result("모든 메일 읽음 처리", False, error_message=f"HTTP {response.status_code}: {response.text}")
            
    except Exception as e:
        log_test_result("모든 메일 읽음 처리", False, error_message=str(e))

def test_star_mail(headers):
    """메일 중요 표시 테스트"""
    print("\n=== 9. 메일 중요 표시 테스트 ===")
    
    mail_id = get_test_mail_id(headers)
    if not mail_id:
        log_test_result("메일 중요 표시", False, error_message="테스트할 메일 ID를 찾을 수 없음")
        return
    
    try:
        response = requests.post(f"{MAIL_CONVENIENCE_URL}/{mail_id}/star", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            log_test_result("메일 중요 표시", True, {"mail_id": mail_id})
            checklist["star_mail"] = True
        else:
            log_test_result("메일 중요 표시", False, error_message=f"HTTP {response.status_code}: {response.text}")
            
    except Exception as e:
        log_test_result("메일 중요 표시", False, error_message=str(e))

def test_unstar_mail(headers):
    """메일 중요 표시 해제 테스트"""
    print("\n=== 10. 메일 중요 표시 해제 테스트 ===")
    
    mail_id = get_test_mail_id(headers)
    if not mail_id:
        log_test_result("메일 중요 표시 해제", False, error_message="테스트할 메일 ID를 찾을 수 없음")
        return
    
    try:
        response = requests.delete(f"{MAIL_CONVENIENCE_URL}/{mail_id}/star", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            log_test_result("메일 중요 표시 해제", True, {"mail_id": mail_id})
            checklist["unstar_mail"] = True
        else:
            log_test_result("메일 중요 표시 해제", False, error_message=f"HTTP {response.status_code}: {response.text}")
            
    except Exception as e:
        log_test_result("메일 중요 표시 해제", False, error_message=str(e))

def test_search_suggestions(headers):
    """검색 자동완성 테스트"""
    print("\n=== 11. 검색 자동완성 테스트 ===")
    
    try:
        response = requests.get(f"{MAIL_CONVENIENCE_URL}/search/suggestions?query=test&limit=5", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            suggestions = data.get("data", {}).get("suggestions", [])
            log_test_result("검색 자동완성", True, {"suggestions_count": len(suggestions)})
            checklist["search_suggestions"] = True
        else:
            log_test_result("검색 자동완성", False, error_message=f"HTTP {response.status_code}: {response.text}")
            
    except Exception as e:
        log_test_result("검색 자동완성", False, error_message=str(e))

def main():
    """메인 테스트 실행"""
    print("=== Mail Convenience Router 엔드포인트 테스트 시작 ===")
    
    # 1. 로그인 및 인증 토큰 획득
    headers = test_login_and_get_token()
    if not headers:
        print("❌ 로그인 실패로 테스트를 중단합니다.")
        return
    
    # 2. 테스트용 메일 발송 (메일 ID가 필요한 테스트를 위해)
    test_mail_id = send_test_mail(headers)
    if test_mail_id:
        print(f"📧 테스트용 메일 ID: {test_mail_id}")
    
    # 메일 발송 후 시스템 반영을 위해 대기
    print("⏳ 메일 시스템 반영 대기 중...")
    time.sleep(5)
    
    # 3. 각 엔드포인트 테스트
    test_search_mails(headers)
    test_get_stats(headers)
    test_get_unread(headers)
    test_get_starred(headers)
    test_mark_read(headers)
    test_mark_unread(headers)
    test_mark_all_read(headers)
    test_star_mail(headers)
    test_unstar_mail(headers)
    test_search_suggestions(headers)
    
    # 결과 출력
    print(f"\n=== 테스트 완료 ===")
    print(f"총 테스트: {test_results['total_tests']}")
    print(f"성공: {test_results['passed_tests']}")
    print(f"실패: {test_results['failed_tests']}")
    print(f"성공률: {(test_results['passed_tests']/test_results['total_tests']*100):.1f}%")
    
    # 체크리스트 출력
    print_checklist()
    
    # 결과 저장
    save_test_results()

if __name__ == "__main__":
    main()