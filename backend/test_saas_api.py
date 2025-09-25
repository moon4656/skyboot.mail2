#!/usr/bin/env python3
"""
SaaS 구조 API 엔드포인트 테스트 스크립트

이 스크립트는 다중 조직 지원 SaaS 구조로 업데이트된 API들을 테스트합니다.
"""

import requests
import json
import time
from typing import Dict, Any, Optional

# 테스트 설정
BASE_URL = "http://localhost:8000"
TEST_ORG_DOMAIN = "test-org.example.com"
TEST_ADMIN_EMAIL = "admin@test-org.example.com"
TEST_ADMIN_PASSWORD = "admin123"
TEST_USER_EMAIL = "user@test-org.example.com"
TEST_USER_PASSWORD = "user123"

class SaaSAPITester:
    """SaaS API 테스터 클래스"""
    
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.user_token = None
        self.org_id = None
        
    def log_test(self, test_name: str, success: bool, message: str = ""):
        """테스트 결과 로깅"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        
    def make_request(self, method: str, endpoint: str, headers: Dict = None, 
                    data: Dict = None, token: str = None) -> requests.Response:
        """API 요청 헬퍼"""
        url = f"{BASE_URL}{endpoint}"
        
        # 기본 헤더 설정
        request_headers = {
            "Content-Type": "application/json",
            "Host": TEST_ORG_DOMAIN  # 조직 식별을 위한 Host 헤더
        }
        
        if headers:
            request_headers.update(headers)
            
        if token:
            request_headers["Authorization"] = f"Bearer {token}"
            
        # 요청 실행
        if method.upper() == "GET":
            return self.session.get(url, headers=request_headers, params=data)
        elif method.upper() == "POST":
            return self.session.post(url, headers=request_headers, 
                                   json=data if data else {})
        elif method.upper() == "PUT":
            return self.session.put(url, headers=request_headers, 
                                  json=data if data else {})
        elif method.upper() == "DELETE":
            return self.session.delete(url, headers=request_headers)
            
    def test_health_check(self):
        """헬스체크 테스트"""
        try:
            response = self.make_request("GET", "/health")
            success = response.status_code == 200
            self.log_test("헬스체크", success, f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("헬스체크", False, f"Error: {str(e)}")
            return False
            
    def test_admin_login(self):
        """관리자 로그인 테스트"""
        try:
            login_data = {
                "email": TEST_ADMIN_EMAIL,
                "password": TEST_ADMIN_PASSWORD
            }
            
            response = self.make_request("POST", "/api/auth/login", data=login_data)
            
            if response.status_code == 200:
                result = response.json()
                self.admin_token = result.get("access_token")
                self.org_id = result.get("user", {}).get("org_id")
                
                success = self.admin_token is not None
                self.log_test("관리자 로그인", success, 
                            f"Token: {'획득' if self.admin_token else '실패'}")
                return success
            else:
                self.log_test("관리자 로그인", False, 
                            f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("관리자 로그인", False, f"Error: {str(e)}")
            return False
            
    def test_organization_info(self):
        """조직 정보 조회 테스트"""
        if not self.admin_token:
            self.log_test("조직 정보 조회", False, "관리자 토큰 없음")
            return False
            
        try:
            response = self.make_request("GET", "/api/organizations/current", 
                                       token=self.admin_token)
            
            success = response.status_code == 200
            if success:
                org_info = response.json()
                self.log_test("조직 정보 조회", True, 
                            f"조직명: {org_info.get('name', 'N/A')}")
            else:
                self.log_test("조직 정보 조회", False, 
                            f"Status: {response.status_code}")
            return success
            
        except Exception as e:
            self.log_test("조직 정보 조회", False, f"Error: {str(e)}")
            return False
            
    def test_user_creation(self):
        """사용자 생성 테스트"""
        if not self.admin_token:
            self.log_test("사용자 생성", False, "관리자 토큰 없음")
            return False
            
        try:
            user_data = {
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD,
                "username": "testuser",
                "full_name": "테스트 사용자",
                "role": "user"
            }
            
            response = self.make_request("POST", "/api/users", 
                                       data=user_data, token=self.admin_token)
            
            success = response.status_code in [200, 201]
            if success:
                user_info = response.json()
                self.log_test("사용자 생성", True, 
                            f"사용자 ID: {user_info.get('user_id', 'N/A')}")
            else:
                self.log_test("사용자 생성", False, 
                            f"Status: {response.status_code}, Response: {response.text}")
            return success
            
        except Exception as e:
            self.log_test("사용자 생성", False, f"Error: {str(e)}")
            return False
            
    def test_user_login(self):
        """일반 사용자 로그인 테스트"""
        try:
            login_data = {
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD
            }
            
            response = self.make_request("POST", "/api/auth/login", data=login_data)
            
            if response.status_code == 200:
                result = response.json()
                self.user_token = result.get("access_token")
                
                success = self.user_token is not None
                self.log_test("사용자 로그인", success, 
                            f"Token: {'획득' if self.user_token else '실패'}")
                return success
            else:
                self.log_test("사용자 로그인", False, 
                            f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("사용자 로그인", False, f"Error: {str(e)}")
            return False
            
    def test_user_list(self):
        """사용자 목록 조회 테스트"""
        if not self.admin_token:
            self.log_test("사용자 목록 조회", False, "관리자 토큰 없음")
            return False
            
        try:
            response = self.make_request("GET", "/api/users", 
                                       token=self.admin_token)
            
            success = response.status_code == 200
            if success:
                users = response.json()
                user_count = len(users.get("users", []))
                self.log_test("사용자 목록 조회", True, 
                            f"사용자 수: {user_count}")
            else:
                self.log_test("사용자 목록 조회", False, 
                            f"Status: {response.status_code}")
            return success
            
        except Exception as e:
            self.log_test("사용자 목록 조회", False, f"Error: {str(e)}")
            return False
            
    def test_current_user_info(self):
        """현재 사용자 정보 조회 테스트"""
        if not self.user_token:
            self.log_test("현재 사용자 정보", False, "사용자 토큰 없음")
            return False
            
        try:
            response = self.make_request("GET", "/api/users/me", 
                                       token=self.user_token)
            
            success = response.status_code == 200
            if success:
                user_info = response.json()
                self.log_test("현재 사용자 정보", True, 
                            f"이메일: {user_info.get('email', 'N/A')}")
            else:
                self.log_test("현재 사용자 정보", False, 
                            f"Status: {response.status_code}")
            return success
            
        except Exception as e:
            self.log_test("현재 사용자 정보", False, f"Error: {str(e)}")
            return False
            
    def test_mail_send(self):
        """메일 발송 테스트"""
        if not self.user_token:
            self.log_test("메일 발송", False, "사용자 토큰 없음")
            return False
            
        try:
            mail_data = {
                "recipients": ["test@example.com"],
                "subject": "SaaS 테스트 메일",
                "content": "이것은 SaaS 구조 테스트를 위한 메일입니다.",
                "content_type": "text"
            }
            
            response = self.make_request("POST", "/api/mail/send", 
                                       data=mail_data, token=self.user_token)
            
            success = response.status_code in [200, 201]
            if success:
                result = response.json()
                self.log_test("메일 발송", True, 
                            f"메일 ID: {result.get('mail_id', 'N/A')}")
            else:
                self.log_test("메일 발송", False, 
                            f"Status: {response.status_code}, Response: {response.text}")
            return success
            
        except Exception as e:
            self.log_test("메일 발송", False, f"Error: {str(e)}")
            return False
            
    def test_mail_inbox(self):
        """받은 메일함 조회 테스트"""
        if not self.user_token:
            self.log_test("받은 메일함 조회", False, "사용자 토큰 없음")
            return False
            
        try:
            response = self.make_request("GET", "/api/mail/inbox", 
                                       token=self.user_token)
            
            success = response.status_code == 200
            if success:
                inbox = response.json()
                mail_count = len(inbox.get("mails", []))
                self.log_test("받은 메일함 조회", True, 
                            f"메일 수: {mail_count}")
            else:
                self.log_test("받은 메일함 조회", False, 
                            f"Status: {response.status_code}")
            return success
            
        except Exception as e:
            self.log_test("받은 메일함 조회", False, f"Error: {str(e)}")
            return False
            
    def test_cross_organization_access(self):
        """조직 간 접근 제어 테스트"""
        if not self.user_token:
            self.log_test("조직 간 접근 제어", False, "사용자 토큰 없음")
            return False
            
        try:
            # 다른 조직 도메인으로 요청
            headers = {"Host": "other-org.example.com"}
            response = self.make_request("GET", "/api/users/me", 
                                       headers=headers, token=self.user_token)
            
            # 403 Forbidden이 반환되어야 함
            success = response.status_code == 403
            self.log_test("조직 간 접근 제어", success, 
                        f"Status: {response.status_code} (403 기대)")
            return success
            
        except Exception as e:
            self.log_test("조직 간 접근 제어", False, f"Error: {str(e)}")
            return False
            
    def run_all_tests(self):
        """모든 테스트 실행"""
        print("🚀 SaaS API 테스트 시작")
        print("=" * 50)
        
        tests = [
            ("헬스체크", self.test_health_check),
            ("관리자 로그인", self.test_admin_login),
            ("조직 정보 조회", self.test_organization_info),
            ("사용자 생성", self.test_user_creation),
            ("사용자 로그인", self.test_user_login),
            ("사용자 목록 조회", self.test_user_list),
            ("현재 사용자 정보", self.test_current_user_info),
            ("메일 발송", self.test_mail_send),
            ("받은 메일함 조회", self.test_mail_inbox),
            ("조직 간 접근 제어", self.test_cross_organization_access)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n📋 {test_name} 테스트 실행 중...")
            if test_func():
                passed += 1
            time.sleep(0.5)  # 테스트 간 간격
            
        print("\n" + "=" * 50)
        print(f"🏁 테스트 완료: {passed}/{total} 통과")
        
        if passed == total:
            print("🎉 모든 테스트가 성공했습니다!")
        else:
            print(f"⚠️  {total - passed}개의 테스트가 실패했습니다.")
            
        return passed == total

if __name__ == "__main__":
    tester = SaaSAPITester()
    success = tester.run_all_tests()
    
    if not success:
        exit(1)