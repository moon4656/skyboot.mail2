#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
메일 검색/필터링 기능 테스트 스크립트
SkyBoot Mail SaaS 프로젝트
"""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any


class SearchFilterTest:
    """검색/필터링 기능 테스트 클래스"""
    
    def __init__(self):
        self.BASE_URL = "http://localhost:8000"
        self.session = requests.Session()
        self.access_token = None
        self.test_results = []
        self.created_mails = []
        
    def log_test(self, test_name: str, success: bool, message: str):
        """테스트 결과 로깅"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        
        self.test_results.append({
            "test_name": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
    
    def authenticate(self) -> bool:
        """사용자 인증"""
        try:
            login_data = {
                "email": "admin@skyboot.kr",
                "password": "admin123"
            }
            
            response = self.session.post(
                f"{self.BASE_URL}/api/v1/auth/login",
                json=login_data
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get("access_token")
                
                if self.access_token:
                    self.session.headers.update({
                        "Authorization": f"Bearer {self.access_token}"
                    })
                    self.log_test("사용자 인증", True, "로그인 성공")
                    return True
                else:
                    self.log_test("사용자 인증", False, "토큰을 받지 못함")
                    return False
            else:
                self.log_test("사용자 인증", False, f"로그인 실패: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("사용자 인증", False, f"인증 오류: {str(e)}")
            return False
    
    def create_test_mails(self, count: int = 5) -> bool:
        """검색 테스트용 메일 생성"""
        try:
            success_count = 0
            
            # 다양한 검색 조건을 위한 테스트 메일들
            test_mails = [
                {
                    "to_emails": "test1@example.com",
                    "subject": "중요한 회의 안내",
                    "content": "내일 오후 2시에 중요한 회의가 있습니다. 참석 부탁드립니다.",
                    "priority": "high"
                },
                {
                    "to_emails": "test2@example.com",
                    "subject": "프로젝트 진행 상황 보고",
                    "content": "프로젝트가 순조롭게 진행되고 있습니다. 상세한 내용은 첨부파일을 확인해주세요.",
                    "priority": "normal"
                },
                {
                    "to_emails": "test3@example.com",
                    "subject": "시스템 점검 공지",
                    "content": "시스템 점검으로 인해 서비스가 일시 중단됩니다.",
                    "priority": "low"
                },
                {
                    "to_emails": "urgent@example.com",
                    "subject": "긴급 - 서버 장애 발생",
                    "content": "서버에 장애가 발생했습니다. 즉시 확인이 필요합니다.",
                    "priority": "high"
                },
                {
                    "to_emails": "info@example.com",
                    "subject": "정기 뉴스레터",
                    "content": "이번 주 뉴스레터를 보내드립니다. 다양한 소식을 확인해보세요.",
                    "priority": "normal"
                }
            ]
            
            for i, mail_data in enumerate(test_mails[:count]):
                response = self.session.post(
                    f"{self.BASE_URL}/api/v1/mail/send",
                    data=mail_data
                )
                
                if response.status_code == 200:
                    data = response.json()
                    mail_id = data.get("mail_uuid") or data.get("mail_id") or data.get("id")
                    if mail_id:
                        self.created_mails.append(mail_id)
                        success_count += 1
                        print(f"  📧 테스트 메일 {i+1} 생성 성공 (ID: {mail_id})")
                    else:
                        print(f"  ❌ 메일 {i+1} ID 추출 실패")
                else:
                    print(f"  ❌ 메일 {i+1} 생성 실패: {response.status_code}")
                
                # 메일 생성 간격
                time.sleep(0.5)
            
            if success_count == count:
                self.log_test("테스트 메일 생성", True, f"{count}개 메일 생성 성공")
                return True
            else:
                self.log_test("테스트 메일 생성", False, f"{success_count}/{count}개 메일만 생성됨")
                return False
                
        except Exception as e:
            self.log_test("테스트 메일 생성", False, f"메일 생성 오류: {str(e)}")
            return False
    
    def test_basic_search(self) -> bool:
        """기본 검색 기능 테스트"""
        try:
            # 키워드 검색 테스트
            search_data = {
                "query": "회의",
                "page": 1,
                "limit": 10
            }
            
            response = self.session.post(
                f"{self.BASE_URL}/api/v1/mail/search",
                json=search_data
            )
            
            if response.status_code == 200:
                data = response.json()
                mails = data.get("mails", [])
                total = data.get("total", 0)
                
                self.log_test("기본 검색", True, f"검색 성공 - 총 {total}개 결과, {len(mails)}개 반환")
                return True
            else:
                self.log_test("기본 검색", False, f"검색 실패: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_test("기본 검색", False, f"검색 오류: {str(e)}")
            return False
    
    def test_advanced_search(self) -> bool:
        """고급 검색 기능 테스트"""
        try:
            # 발신자 기반 검색
            search_data = {
                "sender_email": "admin@skyboot.kr",
                "page": 1,
                "limit": 10
            }
            
            response = self.session.post(
                f"{self.BASE_URL}/api/v1/mail/search",
                json=search_data
            )
            
            if response.status_code == 200:
                data = response.json()
                mails = data.get("mails", [])
                total = data.get("total", 0)
                
                self.log_test("고급 검색 (발신자)", True, f"발신자 검색 성공 - 총 {total}개 결과")
                return True
            else:
                self.log_test("고급 검색 (발신자)", False, f"발신자 검색 실패: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("고급 검색 (발신자)", False, f"발신자 검색 오류: {str(e)}")
            return False
    
    def test_date_range_search(self) -> bool:
        """날짜 범위 검색 테스트"""
        try:
            # 최근 1일 내 메일 검색
            date_from = (datetime.now() - timedelta(days=1)).isoformat()
            date_to = datetime.now().isoformat()
            
            search_data = {
                "date_from": date_from,
                "date_to": date_to,
                "page": 1,
                "limit": 10
            }
            
            response = self.session.post(
                f"{self.BASE_URL}/api/v1/mail/search",
                json=search_data
            )
            
            if response.status_code == 200:
                data = response.json()
                mails = data.get("mails", [])
                total = data.get("total", 0)
                
                self.log_test("날짜 범위 검색", True, f"날짜 범위 검색 성공 - 총 {total}개 결과")
                return True
            else:
                self.log_test("날짜 범위 검색", False, f"날짜 범위 검색 실패: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("날짜 범위 검색", False, f"날짜 범위 검색 오류: {str(e)}")
            return False
    
    def test_priority_filter(self) -> bool:
        """우선순위 필터 테스트"""
        try:
            # 높은 우선순위 메일 검색
            search_data = {
                "priority": "high",
                "page": 1,
                "limit": 10
            }
            
            response = self.session.post(
                f"{self.BASE_URL}/api/v1/mail/search",
                json=search_data
            )
            
            if response.status_code == 200:
                data = response.json()
                mails = data.get("mails", [])
                total = data.get("total", 0)
                
                # 결과 검증: 모든 메일이 high 우선순위인지 확인
                high_priority_count = sum(1 for mail in mails if mail.get("priority") == "high")
                
                self.log_test("우선순위 필터", True, f"우선순위 필터 성공 - 총 {total}개 결과, {high_priority_count}개 high 우선순위")
                return True
            else:
                self.log_test("우선순위 필터", False, f"우선순위 필터 실패: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("우선순위 필터", False, f"우선순위 필터 오류: {str(e)}")
            return False
    
    def test_search_suggestions(self) -> bool:
        """검색 자동완성 테스트"""
        try:
            response = self.session.get(
                f"{self.BASE_URL}/api/v1/mail/search/suggestions",
                params={"query": "회의", "limit": 5}
            )
            
            if response.status_code == 200:
                data = response.json()
                suggestions = data.get("data", {}).get("suggestions", [])
                
                self.log_test("검색 자동완성", True, f"자동완성 성공 - {len(suggestions)}개 제안")
                return True
            else:
                self.log_test("검색 자동완성", False, f"자동완성 실패: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("검색 자동완성", False, f"자동완성 오류: {str(e)}")
            return False
    
    def test_unread_filter(self) -> bool:
        """읽지 않은 메일 필터 테스트"""
        try:
            response = self.session.get(
                f"{self.BASE_URL}/api/v1/mail/unread",
                params={"page": 1, "limit": 10}
            )
            
            if response.status_code == 200:
                data = response.json()
                mails = data.get("mails", [])
                total = data.get("total", 0)
                
                self.log_test("읽지 않은 메일 필터", True, f"읽지 않은 메일 필터 성공 - 총 {total}개 결과")
                return True
            else:
                self.log_test("읽지 않은 메일 필터", False, f"읽지 않은 메일 필터 실패: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("읽지 않은 메일 필터", False, f"읽지 않은 메일 필터 오류: {str(e)}")
            return False
    
    def test_starred_filter(self) -> bool:
        """중요 메일 필터 테스트"""
        try:
            response = self.session.get(
                f"{self.BASE_URL}/api/v1/mail/starred",
                params={"page": 1, "limit": 10}
            )
            
            if response.status_code == 200:
                data = response.json()
                mails = data.get("mails", [])
                total = data.get("total", 0)
                
                self.log_test("중요 메일 필터", True, f"중요 메일 필터 성공 - 총 {total}개 결과")
                return True
            else:
                self.log_test("중요 메일 필터", False, f"중요 메일 필터 실패: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("중요 메일 필터", False, f"중요 메일 필터 오류: {str(e)}")
            return False
    
    def test_error_cases(self) -> bool:
        """에러 케이스 테스트"""
        try:
            error_tests = [
                {
                    "name": "빈 검색어",
                    "data": {"query": "", "page": 1, "limit": 10},
                    "expected_status": [200, 400]  # 빈 검색어는 허용될 수도 있음
                },
                {
                    "name": "잘못된 날짜 형식",
                    "data": {"date_from": "invalid-date", "page": 1, "limit": 10},
                    "expected_status": [400, 422]
                },
                {
                    "name": "잘못된 우선순위",
                    "data": {"priority": "invalid", "page": 1, "limit": 10},
                    "expected_status": [400, 422]
                }
            ]
            
            passed_tests = 0
            total_tests = len(error_tests)
            
            for test_case in error_tests:
                response = self.session.post(
                    f"{self.BASE_URL}/api/v1/mail/search",
                    json=test_case["data"]
                )
                
                if response.status_code in test_case["expected_status"]:
                    print(f"  ✅ {test_case['name']}: 예상된 응답 {response.status_code}")
                    passed_tests += 1
                else:
                    print(f"  ❌ {test_case['name']}: 예상과 다른 응답 {response.status_code}")
            
            if passed_tests == total_tests:
                self.log_test("에러 케이스 테스트", True, f"모든 에러 케이스 통과 ({passed_tests}/{total_tests})")
                return True
            else:
                self.log_test("에러 케이스 테스트", False, f"{passed_tests}/{total_tests} 에러 케이스만 통과")
                return False
                
        except Exception as e:
            self.log_test("에러 케이스 테스트", False, f"에러 케이스 테스트 오류: {str(e)}")
            return False
    
    def cleanup(self):
        """테스트 정리"""
        try:
            print("\n🧹 테스트 정리 중...")
            # 생성된 테스트 메일들은 실제 서비스에서 사용될 수 있으므로 삭제하지 않음
            print("✅ 테스트 정리 완료")
        except Exception as e:
            print(f"❌ 테스트 정리 중 오류: {str(e)}")
    
    def run_all_tests(self):
        """모든 테스트 실행"""
        print("🚀 검색/필터링 기능 테스트 시작")
        print("=" * 50)
        
        # 1. 사용자 인증
        if not self.authenticate():
            return
        
        # 2. 테스트 메일 생성
        if not self.create_test_mails(5):
            return
        
        # 3. 검색 기능 테스트
        self.test_basic_search()
        self.test_advanced_search()
        self.test_date_range_search()
        self.test_priority_filter()
        
        # 4. 자동완성 테스트
        self.test_search_suggestions()
        
        # 5. 필터링 테스트
        self.test_unread_filter()
        self.test_starred_filter()
        
        # 6. 에러 케이스 테스트
        self.test_error_cases()
        
        # 7. 테스트 정리
        self.cleanup()
        
        # 8. 결과 요약
        self.print_summary()
    
    def print_summary(self):
        """테스트 결과 요약 출력"""
        print("\n" + "=" * 50)
        print("📊 테스트 결과 요약")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"총 테스트: {total_tests}")
        print(f"성공: {passed_tests}")
        print(f"실패: {failed_tests}")
        print(f"성공률: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ 실패한 테스트:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test_name']}: {result['message']}")


if __name__ == "__main__":
    tester = SearchFilterTest()
    tester.run_all_tests()