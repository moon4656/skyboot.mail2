#!/usr/bin/env python3
"""
Mail Core Router 엔드포인트 테스트 스크립트
"""

import requests
import json
import os
import time
from datetime import datetime
from typing import Dict, Any, Optional

# 테스트 설정
BASE_URL = "http://localhost:8000"
TEST_USER_EMAIL = "test@example.com"
TEST_USER_PASSWORD = "testpassword123"

class MailCoreEndpointTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.access_token = None
        self.test_results = []
        self.mail_ids = []  # 테스트 중 생성된 메일 ID 저장
        
    def log_test_result(self, test_name: str, success: bool, details: str = "", response_data: Any = None):
        """테스트 결과 로깅"""
        result = {
            "test_name": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "response_data": response_data
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   Details: {details}")
        if not success and response_data:
            print(f"   Response: {response_data}")
        print()
    
    def authenticate(self) -> bool:
        """사용자 인증"""
        print("🔐 사용자 인증 중...")
        
        # 먼저 사용자 등록 시도
        register_data = {
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD,
            "name": "Test User"
        }
        
        try:
            response = requests.post(f"{self.base_url}/auth/register", json=register_data)
            if response.status_code == 201:
                print("✅ 새 사용자 등록 성공")
            elif response.status_code == 400:
                print("ℹ️ 사용자가 이미 존재함")
            else:
                print(f"⚠️ 사용자 등록 응답: {response.status_code}")
        except Exception as e:
            print(f"⚠️ 사용자 등록 중 오류: {e}")
        
        # 로그인
        login_data = {
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        }
        
        try:
            response = requests.post(f"{self.base_url}/auth/login", json=login_data)
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get("access_token")
                print("✅ 로그인 성공")
                return True
            else:
                print(f"❌ 로그인 실패: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ 로그인 중 오류: {e}")
            return False
    
    def get_headers(self) -> Dict[str, str]:
        """인증 헤더 반환"""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    def test_send_mail_basic(self):
        """기본 메일 발송 테스트"""
        print("📧 기본 메일 발송 테스트...")
        
        # Form data로 전송
        data = {
            "to_emails": "recipient@example.com",
            "subject": "테스트 메일",
            "content": "이것은 테스트 메일입니다.",
            "priority": "normal"
        }
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        try:
            response = requests.post(f"{self.base_url}/mail/send", data=data, headers=headers)
            
            if response.status_code == 200:
                response_data = response.json()
                if response_data.get("success"):
                    mail_id = response_data.get("mail_id")
                    if mail_id:
                        self.mail_ids.append(mail_id)
                    self.log_test_result(
                        "기본 메일 발송",
                        True,
                        f"메일 ID: {mail_id}",
                        response_data
                    )
                else:
                    self.log_test_result(
                        "기본 메일 발송",
                        False,
                        "응답에서 success=False",
                        response_data
                    )
            else:
                self.log_test_result(
                    "기본 메일 발송",
                    False,
                    f"HTTP {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_test_result("기본 메일 발송", False, f"예외 발생: {e}")
    
    def test_send_mail_with_cc_bcc(self):
        """CC, BCC 포함 메일 발송 테스트"""
        print("📧 CC, BCC 포함 메일 발송 테스트...")
        
        data = {
            "to_emails": "recipient1@example.com,recipient2@example.com",
            "cc_emails": "cc1@example.com,cc2@example.com",
            "bcc_emails": "bcc1@example.com",
            "subject": "CC, BCC 테스트 메일",
            "content": "이것은 CC, BCC가 포함된 테스트 메일입니다.",
            "priority": "high"
        }
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        try:
            response = requests.post(f"{self.base_url}/mail/send", data=data, headers=headers)
            
            if response.status_code == 200:
                response_data = response.json()
                if response_data.get("success"):
                    mail_id = response_data.get("mail_id")
                    if mail_id:
                        self.mail_ids.append(mail_id)
                    self.log_test_result(
                        "CC, BCC 포함 메일 발송",
                        True,
                        f"메일 ID: {mail_id}",
                        response_data
                    )
                else:
                    self.log_test_result(
                        "CC, BCC 포함 메일 발송",
                        False,
                        "응답에서 success=False",
                        response_data
                    )
            else:
                self.log_test_result(
                    "CC, BCC 포함 메일 발송",
                    False,
                    f"HTTP {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_test_result("CC, BCC 포함 메일 발송", False, f"예외 발생: {e}")
    
    def test_send_mail_missing_fields(self):
        """필수 필드 누락 테스트"""
        print("📧 필수 필드 누락 테스트...")
        
        # 제목 누락
        data = {
            "to_emails": "recipient@example.com",
            "content": "제목이 없는 메일입니다."
        }
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        try:
            response = requests.post(f"{self.base_url}/mail/send", data=data, headers=headers)
            
            if response.status_code == 422:  # Validation error expected
                self.log_test_result(
                    "필수 필드 누락 (제목)",
                    True,
                    "예상된 422 Validation Error",
                    response.status_code
                )
            else:
                self.log_test_result(
                    "필수 필드 누락 (제목)",
                    False,
                    f"예상과 다른 응답: HTTP {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_test_result("필수 필드 누락 (제목)", False, f"예외 발생: {e}")
    
    def test_get_inbox(self):
        """받은 메일함 조회 테스트"""
        print("📥 받은 메일함 조회 테스트...")
        
        headers = self.get_headers()
        
        try:
            response = requests.get(f"{self.base_url}/mail/inbox", headers=headers)
            
            if response.status_code == 200:
                response_data = response.json()
                # 새로운 스키마 형식: mails, pagination 필드 사용
                if "mails" in response_data and "pagination" in response_data:
                    mails = response_data.get("mails", [])
                    pagination = response_data.get("pagination", {})
                    self.log_test_result(
                        "받은 메일함 조회",
                        True,
                        f"메일 수: {len(mails)}, 총 개수: {pagination.get('total', 0)}",
                        {"mail_count": len(mails), "pagination": pagination}
                    )
                else:
                    self.log_test_result(
                        "받은 메일함 조회",
                        False,
                        "응답 형식이 올바르지 않음",
                        response_data
                    )
            else:
                self.log_test_result(
                    "받은 메일함 조회",
                    False,
                    f"HTTP {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_test_result("받은 메일함 조회", False, f"예외 발생: {e}")
    
    def test_get_sent_mails(self):
        """보낸 메일함 조회 테스트"""
        print("📤 보낸 메일함 조회 테스트...")
        
        headers = self.get_headers()
        
        try:
            response = requests.get(f"{self.base_url}/mail/sent", headers=headers)
            
            if response.status_code == 200:
                response_data = response.json()
                # 새로운 스키마 형식: mails, pagination 필드 사용
                if "mails" in response_data and "pagination" in response_data:
                    mails = response_data.get("mails", [])
                    pagination = response_data.get("pagination", {})
                    self.log_test_result(
                        "보낸 메일함 조회",
                        True,
                        f"메일 수: {len(mails)}, 총 개수: {pagination.get('total', 0)}",
                        {"mail_count": len(mails), "pagination": pagination}
                    )
                else:
                    self.log_test_result(
                        "보낸 메일함 조회",
                        False,
                        "응답 형식이 올바르지 않음",
                        response_data
                    )
            else:
                self.log_test_result(
                    "보낸 메일함 조회",
                    False,
                    f"HTTP {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_test_result("보낸 메일함 조회", False, f"예외 발생: {e}")
    
    def test_get_sent_mail_detail(self):
        """보낸 메일 상세 조회 테스트"""
        if not self.mail_ids:
            self.log_test_result("보낸 메일 상세 조회", False, "테스트할 메일 ID가 없음")
            return
        
        print("📤 보낸 메일 상세 조회 테스트...")
        
        mail_id = self.mail_ids[0]  # 첫 번째 메일 ID 사용
        headers = self.get_headers()
        
        try:
            response = requests.get(f"{self.base_url}/mail/sent/{mail_id}", headers=headers)
            
            if response.status_code == 200:
                response_data = response.json()
                if response_data.get("success"):
                    data = response_data.get("data", {})
                    self.log_test_result(
                        "보낸 메일 상세 조회",
                        True,
                        f"메일 제목: {data.get('subject', 'N/A')}",
                        {"mail_id": mail_id, "subject": data.get("subject")}
                    )
                else:
                    self.log_test_result(
                        "보낸 메일 상세 조회",
                        False,
                        "응답에서 success=False",
                        response_data
                    )
            else:
                self.log_test_result(
                    "보낸 메일 상세 조회",
                    False,
                    f"HTTP {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_test_result("보낸 메일 상세 조회", False, f"예외 발생: {e}")
    
    def test_get_drafts(self):
        """임시보관함 조회 테스트"""
        print("📝 임시보관함 조회 테스트...")
        
        headers = self.get_headers()
        
        try:
            response = requests.get(f"{self.base_url}/mail/drafts", headers=headers)
            
            if response.status_code == 200:
                response_data = response.json()
                # 새로운 스키마 형식: mails, pagination 필드 사용
                if "mails" in response_data and "pagination" in response_data:
                    mails = response_data.get("mails", [])
                    pagination = response_data.get("pagination", {})
                    self.log_test_result(
                        "임시보관함 조회",
                        True,
                        f"임시보관 메일 수: {len(mails)}, 총 개수: {pagination.get('total', 0)}",
                        {"draft_count": len(mails), "pagination": pagination}
                    )
                else:
                    self.log_test_result(
                        "임시보관함 조회",
                        False,
                        "응답 형식이 올바르지 않음",
                        response_data
                    )
            else:
                self.log_test_result(
                    "임시보관함 조회",
                    False,
                    f"HTTP {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_test_result("임시보관함 조회", False, f"예외 발생: {e}")
    
    def test_get_trash(self):
        """휴지통 조회 테스트"""
        print("🗑️ 휴지통 조회 테스트...")
        
        headers = self.get_headers()
        
        try:
            response = requests.get(f"{self.base_url}/mail/trash", headers=headers)
            
            if response.status_code == 200:
                response_data = response.json()
                # 새로운 스키마 형식: mails, pagination 필드 사용
                if "mails" in response_data and "pagination" in response_data:
                    mails = response_data.get("mails", [])
                    pagination = response_data.get("pagination", {})
                    self.log_test_result(
                        "휴지통 조회",
                        True,
                        f"삭제된 메일 수: {len(mails)}, 총 개수: {pagination.get('total', 0)}",
                        {"trash_count": len(mails), "pagination": pagination}
                    )
                else:
                    self.log_test_result(
                        "휴지통 조회",
                        False,
                        "응답 형식이 올바르지 않음",
                        response_data
                    )
            else:
                self.log_test_result(
                    "휴지통 조회",
                    False,
                    f"HTTP {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_test_result("휴지통 조회", False, f"예외 발생: {e}")
    
    def test_unauthorized_access(self):
        """인증 없는 접근 테스트"""
        print("🔒 인증 없는 접근 테스트...")
        
        try:
            response = requests.get(f"{self.base_url}/mail/inbox")
            
            # 401 또는 403 모두 인증 오류로 간주
            if response.status_code in [401, 403]:
                self.log_test_result(
                    "인증 없는 접근 차단",
                    True,
                    f"예상된 인증 오류: HTTP {response.status_code}",
                    response.status_code
                )
            else:
                self.log_test_result(
                    "인증 없는 접근 차단",
                    False,
                    f"예상과 다른 응답: HTTP {response.status_code}",
                    response.text
                )
        except Exception as e:
            self.log_test_result("인증 없는 접근 차단", False, f"예외 발생: {e}")
    
    def run_all_tests(self):
        """모든 테스트 실행"""
        print("🚀 Mail Core Router 엔드포인트 테스트 시작")
        print("=" * 60)
        
        # 인증
        if not self.authenticate():
            print("❌ 인증 실패로 테스트를 중단합니다.")
            return
        
        # 테스트 실행
        self.test_unauthorized_access()
        self.test_send_mail_basic()
        self.test_send_mail_with_cc_bcc()
        self.test_send_mail_missing_fields()
        
        # 메일 발송 후 잠시 대기
        time.sleep(1)
        
        self.test_get_sent_mails()
        self.test_get_sent_mail_detail()
        self.test_get_inbox()
        self.test_get_drafts()
        self.test_get_trash()
        
        # 결과 요약
        self.print_summary()
        self.save_results()
    
    def print_summary(self):
        """테스트 결과 요약 출력"""
        print("\n" + "=" * 60)
        print("📊 테스트 결과 요약")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"총 테스트 수: {total_tests}")
        print(f"성공: {passed_tests}")
        print(f"실패: {failed_tests}")
        print(f"성공률: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print("\n❌ 실패한 테스트:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test_name']}: {result['details']}")
    
    def save_results(self):
        """테스트 결과를 파일로 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"mail_core_test_results_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 테스트 결과가 저장되었습니다: {filename}")

if __name__ == "__main__":
    tester = MailCoreEndpointTester()
    tester.run_all_tests()