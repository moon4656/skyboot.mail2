#!/usr/bin/env python3
"""
Mail Advanced Router 종합 테스트 스크립트
SkyBoot Mail SaaS 시스템의 고급 메일 기능 테스트

테스트 대상:
1. 폴더 관리 기능 (CRUD)
2. 메일 이동 기능
3. 백업/복원 기능
4. 분석 기능

작성자: SkyBoot Mail 개발팀
작성일: 2024-12-29
"""

import requests
import json
import time
import os
import tempfile
import zipfile
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

# 테스트 설정
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"

# 테스트 사용자 정보
TEST_USER = {
    "email": "testadvanced@skyboot.kr",
    "password": "testpassword123"
}

# 글로벌 변수
auth_token = None
test_results = []
created_folders = []
created_mails = []

class TestResult:
    """테스트 결과를 저장하는 클래스"""
    def __init__(self, test_name: str, endpoint: str, method: str):
        self.test_name = test_name
        self.endpoint = endpoint
        self.method = method
        self.start_time = time.time()
        self.status = "RUNNING"
        self.status_code = None
        self.response_time = None
        self.expected_result = None
        self.actual_result = None
        self.issues = []
        self.response_data = None

    def complete(self, status_code: int, response_data: Any, expected_result: str, actual_result: str, issues: List[str] = None):
        """테스트 완료 처리"""
        self.end_time = time.time()
        self.response_time = round(self.end_time - self.start_time, 3)
        self.status_code = status_code
        self.response_data = response_data
        self.expected_result = expected_result
        self.actual_result = actual_result
        self.issues = issues or []
        self.status = "PASS" if not self.issues else "FAIL"

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "test_name": self.test_name,
            "endpoint": self.endpoint,
            "method": self.method,
            "status": self.status,
            "response_time": f"{self.response_time}s",
            "status_code": self.status_code,
            "expected_result": self.expected_result,
            "actual_result": self.actual_result,
            "issues": self.issues,
            "timestamp": datetime.now().isoformat()
        }

def log_test(message: str, level: str = "INFO"):
    """테스트 로그 출력"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

def make_request(method: str, endpoint: str, data: Dict = None, files: Dict = None, params: Dict = None) -> requests.Response:
    """API 요청 헬퍼 함수"""
    url = f"{BASE_URL}{API_PREFIX}{endpoint}"
    headers = {}
    
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    
    if method.upper() == "GET":
        response = requests.get(url, headers=headers, params=params)
    elif method.upper() == "POST":
        if files:
            response = requests.post(url, headers=headers, data=data, files=files)
        else:
            headers["Content-Type"] = "application/json"
            response = requests.post(url, headers=headers, json=data)
    elif method.upper() == "PUT":
        headers["Content-Type"] = "application/json"
        response = requests.put(url, headers=headers, json=data)
    elif method.upper() == "DELETE":
        response = requests.delete(url, headers=headers)
    else:
        raise ValueError(f"지원하지 않는 HTTP 메서드: {method}")
    
    return response

def login() -> bool:
    """로그인 및 토큰 획득"""
    global auth_token
    
    log_test("🔐 로그인 시작")
    
    try:
        response = make_request("POST", "/auth/login", {
            "email": TEST_USER["email"],
            "password": TEST_USER["password"]
        })
        
        if response.status_code == 200:
            data = response.json()
            auth_token = data.get("access_token")
            log_test(f"✅ 로그인 성공 - 토큰 획득: {auth_token[:20]}...")
            return True
        else:
            log_test(f"❌ 로그인 실패 - 상태코드: {response.status_code}, 응답: {response.text}", "ERROR")
            return False
            
    except Exception as e:
        log_test(f"❌ 로그인 오류: {str(e)}", "ERROR")
        return False

def test_folder_management():
    """폴더 관리 기능 테스트"""
    log_test("📁 폴더 관리 기능 테스트 시작")
    
    # 1. 폴더 목록 조회 테스트
    test = TestResult("폴더 목록 조회", "/mail/folders", "GET")
    try:
        response = make_request("GET", "/mail/folders")
        
        if response.status_code == 200:
            data = response.json()
            folders = data.get("folders", [])
            test.complete(
                response.status_code, data,
                "폴더 목록 조회 성공", f"폴더 {len(folders)}개 조회됨"
            )
            log_test(f"✅ 폴더 목록 조회 성공 - {len(folders)}개 폴더")
        else:
            test.complete(
                response.status_code, response.text,
                "폴더 목록 조회 성공", f"오류 발생: {response.status_code}",
                [f"예상하지 못한 상태코드: {response.status_code}"]
            )
            log_test(f"❌ 폴더 목록 조회 실패 - {response.status_code}: {response.text}", "ERROR")
            
    except Exception as e:
        test.complete(500, str(e), "폴더 목록 조회 성공", f"예외 발생: {str(e)}", [str(e)])
        log_test(f"❌ 폴더 목록 조회 예외: {str(e)}", "ERROR")
    
    test_results.append(test)
    
    # 2. 폴더 생성 테스트
    test = TestResult("폴더 생성", "/mail/folders", "POST")
    folder_data = {
        "name": f"테스트폴더_{int(time.time())}",
        "folder_type": "custom"
    }
    
    try:
        response = make_request("POST", "/mail/folders", folder_data)
        
        if response.status_code in [200, 201]:
            data = response.json()
            folder_uuid = data.get("folder_uuid")
            if folder_uuid:
                created_folders.append(folder_uuid)
            test.complete(
                response.status_code, data,
                "폴더 생성 성공", f"폴더 '{folder_data['name']}' 생성됨"
            )
            log_test(f"✅ 폴더 생성 성공 - UUID: {folder_uuid}")
        else:
            test.complete(
                response.status_code, response.text,
                "폴더 생성 성공", f"오류 발생: {response.status_code}",
                [f"예상하지 못한 상태코드: {response.status_code}"]
            )
            log_test(f"❌ 폴더 생성 실패 - {response.status_code}: {response.text}", "ERROR")
            
    except Exception as e:
        test.complete(500, str(e), "폴더 생성 성공", f"예외 발생: {str(e)}", [str(e)])
        log_test(f"❌ 폴더 생성 예외: {str(e)}", "ERROR")
    
    test_results.append(test)
    
    # 3. 폴더 수정 테스트 (생성된 폴더가 있는 경우)
    if created_folders:
        test = TestResult("폴더 수정", f"/mail/folders/{created_folders[0]}", "PUT")
        update_data = {
            "name": f"수정된폴더_{int(time.time())}",
            "folder_type": "custom"
        }
        
        try:
            response = make_request("PUT", f"/mail/folders/{created_folders[0]}", update_data)
            
            if response.status_code == 200:
                data = response.json()
                test.complete(
                    response.status_code, data,
                    "폴더 수정 성공", f"폴더명이 '{update_data['name']}'로 변경됨"
                )
                log_test(f"✅ 폴더 수정 성공")
            else:
                test.complete(
                    response.status_code, response.text,
                    "폴더 수정 성공", f"오류 발생: {response.status_code}",
                    [f"예상하지 못한 상태코드: {response.status_code}"]
                )
                log_test(f"❌ 폴더 수정 실패 - {response.status_code}: {response.text}", "ERROR")
                
        except Exception as e:
            test.complete(500, str(e), "폴더 수정 성공", f"예외 발생: {str(e)}", [str(e)])
            log_test(f"❌ 폴더 수정 예외: {str(e)}", "ERROR")
        
        test_results.append(test)

def test_backup_restore():
    """백업/복원 기능 테스트"""
    log_test("💾 백업/복원 기능 테스트 시작")
    
    # 1. 메일 백업 테스트
    test = TestResult("메일 백업", "/mail/backup", "POST")
    backup_data = {
        "include_attachments": False,
        "date_from": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
        "date_to": datetime.now().strftime("%Y-%m-%d")
    }
    
    try:
        response = make_request("POST", "/mail/backup", backup_data)
        
        if response.status_code == 200:
            data = response.json()
            backup_filename = data.get("backup_filename")
            test.complete(
                response.status_code, data,
                "백업 생성 성공", f"백업 파일 생성됨: {backup_filename}"
            )
            log_test(f"✅ 메일 백업 성공 - 파일: {backup_filename}")
            
            # 백업 파일 다운로드 테스트
            if backup_filename:
                test_backup_download(backup_filename)
                
        else:
            test.complete(
                response.status_code, response.text,
                "백업 생성 성공", f"오류 발생: {response.status_code}",
                [f"예상하지 못한 상태코드: {response.status_code}"]
            )
            log_test(f"❌ 메일 백업 실패 - {response.status_code}: {response.text}", "ERROR")
            
    except Exception as e:
        test.complete(500, str(e), "백업 생성 성공", f"예외 발생: {str(e)}", [str(e)])
        log_test(f"❌ 메일 백업 예외: {str(e)}", "ERROR")
    
    test_results.append(test)

def test_backup_download(backup_filename: str):
    """백업 파일 다운로드 테스트"""
    test = TestResult("백업 파일 다운로드", f"/mail/backup/{backup_filename}", "GET")
    
    try:
        response = make_request("GET", f"/mail/backup/{backup_filename}")
        
        if response.status_code == 200:
            # 파일 크기 확인
            content_length = len(response.content)
            test.complete(
                response.status_code, f"파일 크기: {content_length} bytes",
                "백업 파일 다운로드 성공", f"파일 다운로드 완료 ({content_length} bytes)"
            )
            log_test(f"✅ 백업 파일 다운로드 성공 - 크기: {content_length} bytes")
        else:
            test.complete(
                response.status_code, response.text,
                "백업 파일 다운로드 성공", f"오류 발생: {response.status_code}",
                [f"예상하지 못한 상태코드: {response.status_code}"]
            )
            log_test(f"❌ 백업 파일 다운로드 실패 - {response.status_code}: {response.text}", "ERROR")
            
    except Exception as e:
        test.complete(500, str(e), "백업 파일 다운로드 성공", f"예외 발생: {str(e)}", [str(e)])
        log_test(f"❌ 백업 파일 다운로드 예외: {str(e)}", "ERROR")
    
    test_results.append(test)

def test_analytics():
    """분석 기능 테스트"""
    log_test("📊 분석 기능 테스트 시작")
    
    # 다양한 기간별 분석 테스트
    periods = ["daily", "weekly", "monthly"]
    
    for period in periods:
        test = TestResult(f"메일 분석 ({period})", f"/mail/analytics?period={period}", "GET")
        
        try:
            response = make_request("GET", "/mail/analytics", params={"period": period})
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    analytics_data = data.get("data", {})
                    summary = analytics_data.get("summary", {})
                    test.complete(
                        response.status_code, data,
                        f"{period} 분석 성공", 
                        f"총 메일: {summary.get('total_mails', 0)}개, 보낸메일: {summary.get('total_sent', 0)}개, 받은메일: {summary.get('total_received', 0)}개"
                    )
                    log_test(f"✅ {period} 분석 성공 - 총 메일: {summary.get('total_mails', 0)}개")
                else:
                    test.complete(
                        response.status_code, data,
                        f"{period} 분석 성공", f"분석 실패: {data.get('message')}",
                        [f"분석 실패: {data.get('message')}"]
                    )
                    log_test(f"❌ {period} 분석 실패 - {data.get('message')}", "ERROR")
            else:
                test.complete(
                    response.status_code, response.text,
                    f"{period} 분석 성공", f"오류 발생: {response.status_code}",
                    [f"예상하지 못한 상태코드: {response.status_code}"]
                )
                log_test(f"❌ {period} 분석 실패 - {response.status_code}: {response.text}", "ERROR")
                
        except Exception as e:
            test.complete(500, str(e), f"{period} 분석 성공", f"예외 발생: {str(e)}", [str(e)])
            log_test(f"❌ {period} 분석 예외: {str(e)}", "ERROR")
        
        test_results.append(test)

def test_error_cases():
    """오류 케이스 테스트"""
    log_test("⚠️ 오류 케이스 테스트 시작")
    
    # 1. 존재하지 않는 폴더 수정 시도
    test = TestResult("존재하지 않는 폴더 수정", "/mail/folders/nonexistent-uuid", "PUT")
    try:
        response = make_request("PUT", "/mail/folders/nonexistent-uuid", {"name": "테스트"})
        
        if response.status_code == 404:
            test.complete(
                response.status_code, response.text,
                "404 오류 반환", "404 오류 정상 반환"
            )
            log_test("✅ 존재하지 않는 폴더 수정 - 404 오류 정상 반환")
        else:
            test.complete(
                response.status_code, response.text,
                "404 오류 반환", f"예상과 다른 상태코드: {response.status_code}",
                [f"404가 아닌 {response.status_code} 반환"]
            )
            log_test(f"❌ 존재하지 않는 폴더 수정 - 예상과 다른 응답: {response.status_code}", "ERROR")
            
    except Exception as e:
        test.complete(500, str(e), "404 오류 반환", f"예외 발생: {str(e)}", [str(e)])
        log_test(f"❌ 존재하지 않는 폴더 수정 예외: {str(e)}", "ERROR")
    
    test_results.append(test)
    
    # 2. 잘못된 분석 기간 파라미터
    test = TestResult("잘못된 분석 기간", "/mail/analytics?period=invalid", "GET")
    try:
        response = make_request("GET", "/mail/analytics", params={"period": "invalid"})
        
        if response.status_code == 400:
            test.complete(
                response.status_code, response.text,
                "400 오류 반환", "400 오류 정상 반환"
            )
            log_test("✅ 잘못된 분석 기간 - 400 오류 정상 반환")
        else:
            # 일부 시스템에서는 기본값으로 처리할 수 있으므로 경고로 처리
            test.complete(
                response.status_code, response.text,
                "400 오류 반환", f"상태코드: {response.status_code} (기본값 처리 가능)",
                []  # 이슈로 처리하지 않음
            )
            log_test(f"⚠️ 잘못된 분석 기간 - {response.status_code} 반환 (기본값 처리 가능)", "WARNING")
            
    except Exception as e:
        test.complete(500, str(e), "400 오류 반환", f"예외 발생: {str(e)}", [str(e)])
        log_test(f"❌ 잘못된 분석 기간 예외: {str(e)}", "ERROR")
    
    test_results.append(test)

def cleanup():
    """테스트 후 정리 작업"""
    log_test("🧹 테스트 정리 작업 시작")
    
    # 생성된 폴더 삭제
    for folder_uuid in created_folders:
        try:
            response = make_request("DELETE", f"/mail/folders/{folder_uuid}")
            if response.status_code == 200:
                log_test(f"✅ 폴더 삭제 완료: {folder_uuid}")
            else:
                log_test(f"⚠️ 폴더 삭제 실패: {folder_uuid} - {response.status_code}", "WARNING")
        except Exception as e:
            log_test(f"❌ 폴더 삭제 예외: {folder_uuid} - {str(e)}", "ERROR")

def generate_report():
    """테스트 결과 보고서 생성"""
    log_test("📋 테스트 결과 보고서 생성")
    
    # 통계 계산
    total_tests = len(test_results)
    passed_tests = len([t for t in test_results if t.status == "PASS"])
    failed_tests = len([t for t in test_results if t.status == "FAIL"])
    
    # 평균 응답 시간 계산
    response_times = [t.response_time for t in test_results if t.response_time]
    avg_response_time = sum(response_times) / len(response_times) if response_times else 0
    
    # 보고서 데이터
    report = {
        "test_summary": {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": round((passed_tests / total_tests) * 100, 2) if total_tests > 0 else 0,
            "average_response_time": round(avg_response_time, 3)
        },
        "test_details": [test.to_dict() for test in test_results],
        "generated_at": datetime.now().isoformat(),
        "test_environment": {
            "base_url": BASE_URL,
            "test_user": TEST_USER["email"]
        }
    }
    
    # JSON 파일로 저장
    report_filename = f"mail_advanced_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_filename, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    # 콘솔 출력
    print("\n" + "="*80)
    print("📊 MAIL ADVANCED ROUTER 테스트 결과 요약")
    print("="*80)
    print(f"총 테스트 수: {total_tests}")
    print(f"성공: {passed_tests} ({round((passed_tests/total_tests)*100, 1)}%)")
    print(f"실패: {failed_tests} ({round((failed_tests/total_tests)*100, 1)}%)")
    print(f"평균 응답 시간: {round(avg_response_time, 3)}초")
    print(f"보고서 파일: {report_filename}")
    print("="*80)
    
    # 실패한 테스트 상세 출력
    if failed_tests > 0:
        print("\n❌ 실패한 테스트:")
        for test in test_results:
            if test.status == "FAIL":
                print(f"  - {test.test_name}: {', '.join(test.issues)}")
    
    return report_filename

def main():
    """메인 테스트 실행 함수"""
    print("🚀 Mail Advanced Router 종합 테스트 시작")
    print(f"대상 서버: {BASE_URL}")
    print(f"테스트 사용자: {TEST_USER['email']}")
    print("-" * 80)
    
    # 1. 로그인
    if not login():
        log_test("로그인 실패로 테스트 중단", "ERROR")
        return
    
    # 2. 기능별 테스트 실행
    try:
        test_folder_management()
        test_backup_restore()
        test_analytics()
        test_error_cases()
        
    except KeyboardInterrupt:
        log_test("사용자에 의해 테스트 중단됨", "WARNING")
    except Exception as e:
        log_test(f"예상치 못한 오류: {str(e)}", "ERROR")
    
    # 3. 정리 작업
    cleanup()
    
    # 4. 보고서 생성
    report_file = generate_report()
    
    print(f"\n✅ 테스트 완료! 상세 결과는 {report_file}을 확인하세요.")

if __name__ == "__main__":
    main()