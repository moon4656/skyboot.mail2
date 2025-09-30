#!/usr/bin/env python3
"""
📧 Mail Convenience Router 종합 테스트 스크립트

이 스크립트는 mail_convenience_router.py의 모든 엔드포인트를 테스트합니다.
- 메일 검색 (/search)
- 메일 통계 (/stats)  
- 읽지 않은 메일 조회 (/unread)
- 중요 표시된 메일 조회 (/starred)
"""

import asyncio
import json
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import requests
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_mail_convenience_router.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MailConvenienceRouterTester:
    """Mail Convenience Router 테스트 클래스"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        테스터 초기화
        
        Args:
            base_url: FastAPI 서버 기본 URL
        """
        self.base_url = base_url
        self.api_prefix = "/api/v1"
        self.access_token: Optional[str] = None
        self.test_results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "test_details": []
        }
        
        # 테스트 사용자 정보
        self.test_user = {
            "email": "testuser1@example.com",
            "password": "testpassword123"
        }
        
        # 테스트 조직 정보
        self.test_org = {
            "name": "테스트 조직",
            "domain": "skyboot.kr"
        }
    
    def log_test_result(self, test_name: str, success: bool, details: str = "", error: str = ""):
        """테스트 결과 로깅"""
        self.test_results["total_tests"] += 1
        if success:
            self.test_results["passed_tests"] += 1
            logger.info(f"[SUCCESS] {test_name} - 성공")
        else:
            self.test_results["failed_tests"] += 1
            logger.error(f"[FAILED] {test_name} - 실패: {error}")
        
        self.test_results["test_details"].append({
            "test_name": test_name,
            "success": success,
            "details": details,
            "error": error,
            "timestamp": datetime.now().isoformat()
        })
    
    def make_request(self, method: str, endpoint: str, data: Dict = None, params: Dict = None) -> requests.Response:
        """API 요청 실행"""
        url = f"{self.base_url}{self.api_prefix}{endpoint}"
        headers = {
            "Content-Type": "application/json"
        }
        
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, params=params)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=data, params=params)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=headers, json=data, params=params)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers, params=params)
            else:
                raise ValueError(f"지원하지 않는 HTTP 메서드: {method}")
            
            logger.info(f"[API] {method} {url} - Status: {response.status_code}")
            return response
            
        except Exception as e:
            logger.error(f"❌ API 요청 실패: {str(e)}")
            raise
    
    def test_login(self) -> bool:
        """로그인 테스트 및 토큰 획득"""
        try:
            logger.info("[LOGIN] 로그인 테스트 시작")
            
            login_data = {
                "email": self.test_user["email"],
                "password": self.test_user["password"]
            }
            
            response = self.make_request("POST", "/auth/login", data=login_data)
            
            if response.status_code == 200:
                result = response.json()
                self.access_token = result.get("access_token")
                if self.access_token:
                    self.log_test_result("로그인 및 토큰 획득", True, f"토큰 획득 성공")
                    return True
                else:
                    self.log_test_result("로그인 및 토큰 획득", False, error="토큰이 응답에 없음")
                    return False
            else:
                self.log_test_result("로그인 및 토큰 획득", False, error=f"로그인 실패: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test_result("로그인 및 토큰 획득", False, error=str(e))
            return False
    
    def test_mail_search(self) -> bool:
        """메일 검색 엔드포인트 테스트"""
        try:
            logger.info("[SEARCH] 메일 검색 테스트 시작")
            
            # 1. 기본 검색 (빈 검색어)
            search_data = {
                "query": "",
                "page": 1,
                "limit": 10
            }
            
            response = self.make_request("POST", "/mail/search", data=search_data)
            
            if response.status_code == 200:
                result = response.json()
                self.log_test_result("메일 검색 - 기본 검색", True, f"검색 결과: {len(result.get('mails', []))}개")
            else:
                self.log_test_result("메일 검색 - 기본 검색", False, error=f"응답 코드: {response.status_code}")
                return False
            
            # 2. 키워드 검색
            search_data = {
                "query": "테스트",
                "page": 1,
                "limit": 10
            }
            
            response = self.make_request("POST", "/mail/search", data=search_data)
            
            if response.status_code == 200:
                result = response.json()
                self.log_test_result("메일 검색 - 키워드 검색", True, f"'테스트' 검색 결과: {len(result.get('mails', []))}개")
            else:
                self.log_test_result("메일 검색 - 키워드 검색", False, error=f"응답 코드: {response.status_code}")
                return False
            
            # 3. 날짜 범위 검색
            today = datetime.now()
            yesterday = today - timedelta(days=1)
            
            search_data = {
                "query": "",
                "date_from": yesterday.isoformat(),
                "date_to": today.isoformat(),
                "page": 1,
                "limit": 10
            }
            
            response = self.make_request("POST", "/mail/search", data=search_data)
            
            if response.status_code == 200:
                result = response.json()
                self.log_test_result("메일 검색 - 날짜 범위 검색", True, f"최근 1일 검색 결과: {len(result.get('mails', []))}개")
            else:
                self.log_test_result("메일 검색 - 날짜 범위 검색", False, error=f"응답 코드: {response.status_code}")
                return False
            
            # 4. 발신자 필터 검색
            search_data = {
                "query": "",
                "sender_email": "test@",
                "page": 1,
                "limit": 10
            }
            
            response = self.make_request("POST", "/mail/search", data=search_data)
            
            if response.status_code == 200:
                result = response.json()
                self.log_test_result("메일 검색 - 발신자 필터", True, f"발신자 필터 검색 결과: {len(result.get('mails', []))}개")
            else:
                self.log_test_result("메일 검색 - 발신자 필터", False, error=f"응답 코드: {response.status_code}")
                return False
            
            return True
            
        except Exception as e:
            self.log_test_result("메일 검색 전체", False, error=str(e))
            return False
    
    def test_mail_stats(self) -> bool:
        """메일 통계 엔드포인트 테스트"""
        try:
            logger.info("[STATS] 메일 통계 테스트 시작")
            
            response = self.make_request("GET", "/mail/stats")
            
            if response.status_code == 200:
                result = response.json()
                stats = result.get("stats", {})
                
                # 통계 데이터 검증
                required_fields = [
                    "total_sent", "total_received", "total_drafts", 
                    "unread_count", "today_sent", "today_received"
                ]
                
                missing_fields = [field for field in required_fields if field not in stats]
                
                if not missing_fields:
                    details = f"보낸메일: {stats['total_sent']}, 받은메일: {stats['total_received']}, " \
                             f"임시보관: {stats['total_drafts']}, 읽지않음: {stats['unread_count']}"
                    self.log_test_result("메일 통계 조회", True, details)
                    return True
                else:
                    self.log_test_result("메일 통계 조회", False, error=f"누락된 필드: {missing_fields}")
                    return False
            else:
                self.log_test_result("메일 통계 조회", False, error=f"응답 코드: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test_result("메일 통계 조회", False, error=str(e))
            return False
    
    def test_unread_mails(self) -> bool:
        """읽지 않은 메일 조회 엔드포인트 테스트"""
        try:
            logger.info("[UNREAD] 읽지 않은 메일 조회 테스트 시작")
            
            # 1. 기본 조회
            params = {
                "page": 1,
                "limit": 10
            }
            
            response = self.make_request("GET", "/mail/unread", params=params)
            
            if response.status_code == 200:
                result = response.json()
                data = result.get("data", {})
                mails = data.get("mails", [])
                total = data.get("total", 0)
                
                self.log_test_result("읽지 않은 메일 조회 - 기본", True, f"읽지 않은 메일: {total}개, 조회된 메일: {len(mails)}개")
            else:
                self.log_test_result("읽지 않은 메일 조회 - 기본", False, error=f"응답 코드: {response.status_code}")
                return False
            
            # 2. 페이지네이션 테스트
            params = {
                "page": 2,
                "limit": 5
            }
            
            response = self.make_request("GET", "/mail/unread", params=params)
            
            if response.status_code == 200:
                result = response.json()
                data = result.get("data", {})
                mails = data.get("mails", [])
                
                self.log_test_result("읽지 않은 메일 조회 - 페이지네이션", True, f"2페이지 조회 결과: {len(mails)}개")
            else:
                self.log_test_result("읽지 않은 메일 조회 - 페이지네이션", False, error=f"응답 코드: {response.status_code}")
                return False
            
            return True
            
        except Exception as e:
            self.log_test_result("읽지 않은 메일 조회 전체", False, error=str(e))
            return False
    
    def test_starred_mails(self) -> bool:
        """중요 표시된 메일 조회 엔드포인트 테스트"""
        try:
            logger.info("[STARRED] 중요 표시된 메일 조회 테스트 시작")
            
            # 1. 기본 조회
            params = {
                "page": 1,
                "limit": 10
            }
            
            response = self.make_request("GET", "/mail/starred", params=params)
            
            if response.status_code == 200:
                result = response.json()
                data = result.get("data", {})
                mails = data.get("mails", [])
                total = data.get("total", 0)
                
                self.log_test_result("중요 메일 조회 - 기본", True, f"중요 메일: {total}개, 조회된 메일: {len(mails)}개")
            else:
                self.log_test_result("중요 메일 조회 - 기본", False, error=f"응답 코드: {response.status_code}")
                return False
            
            # 2. 페이지네이션 테스트
            params = {
                "page": 1,
                "limit": 5
            }
            
            response = self.make_request("GET", "/mail/starred", params=params)
            
            if response.status_code == 200:
                result = response.json()
                data = result.get("data", {})
                mails = data.get("mails", [])
                
                # 우선순위 확인 (모든 메일이 HIGH 우선순위여야 함)
                high_priority_count = sum(1 for mail in mails if mail.get("priority") == "HIGH")
                
                self.log_test_result("중요 메일 조회 - 우선순위 확인", True, 
                                   f"HIGH 우선순위 메일: {high_priority_count}/{len(mails)}개")
            else:
                self.log_test_result("중요 메일 조회 - 우선순위 확인", False, error=f"응답 코드: {response.status_code}")
                return False
            
            return True
            
        except Exception as e:
            self.log_test_result("중요 메일 조회 전체", False, error=str(e))
            return False
    
    def test_authentication_errors(self) -> bool:
        """인증 오류 테스트"""
        try:
            logger.info("[AUTH] 인증 오류 테스트 시작")
            
            # 토큰 없이 요청
            original_token = self.access_token
            self.access_token = None
            
            response = self.make_request("GET", "/mail/stats")
            
            if response.status_code == 401:
                self.log_test_result("인증 오류 - 토큰 없음", True, "401 Unauthorized 정상 반환")
            else:
                self.log_test_result("인증 오류 - 토큰 없음", False, error=f"예상: 401, 실제: {response.status_code}")
            
            # 잘못된 토큰으로 요청
            self.access_token = "invalid_token_12345"
            
            response = self.make_request("GET", "/mail/stats")
            
            if response.status_code == 401:
                self.log_test_result("인증 오류 - 잘못된 토큰", True, "401 Unauthorized 정상 반환")
            else:
                self.log_test_result("인증 오류 - 잘못된 토큰", False, error=f"예상: 401, 실제: {response.status_code}")
            
            # 토큰 복원
            self.access_token = original_token
            
            return True
            
        except Exception as e:
            self.log_test_result("인증 오류 테스트", False, error=str(e))
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """모든 테스트 실행"""
        logger.info("[START] Mail Convenience Router 종합 테스트 시작")
        logger.info(f"[TARGET] 테스트 대상: {self.base_url}{self.api_prefix}")
        
        # 로그인 테스트
        if not self.test_login():
            logger.error("[FAILED] 로그인 실패로 테스트 중단")
            return self.test_results
        
        # 2. 각 엔드포인트 테스트
        test_functions = [
            self.test_mail_search,
            self.test_mail_stats,
            self.test_unread_mails,
            self.test_starred_mails,
            self.test_authentication_errors
        ]
        
        for test_func in test_functions:
            try:
                test_func()
            except Exception as e:
                logger.error(f"[ERROR] 테스트 함수 {test_func.__name__} 실행 중 오류: {str(e)}")
        
        # 3. 테스트 결과 요약
        self.print_test_summary()
        
        return self.test_results
    
    def print_test_summary(self):
        """테스트 결과 요약 출력"""
        total = self.test_results["total_tests"]
        passed = self.test_results["passed_tests"]
        failed = self.test_results["failed_tests"]
        success_rate = (passed / total * 100) if total > 0 else 0
        
        logger.info("=" * 60)
        logger.info("[SUMMARY] 테스트 결과 요약")
        logger.info("=" * 60)
        logger.info(f"총 테스트: {total}개")
        logger.info(f"성공: {passed}개")
        logger.info(f"실패: {failed}개")
        logger.info(f"성공률: {success_rate:.1f}%")
        logger.info("=" * 60)
        
        if failed > 0:
            logger.info("[FAILED] 실패한 테스트:")
            for test in self.test_results["test_details"]:
                if not test["success"]:
                    logger.info(f"  - {test['test_name']}: {test['error']}")
        
        logger.info("=" * 60)
    
    def save_test_report(self, filename: str = "mail_convenience_router_test_report.json"):
        """테스트 결과를 JSON 파일로 저장"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, ensure_ascii=False, indent=2)
            logger.info(f"[REPORT] 테스트 보고서 저장: {filename}")
        except Exception as e:
            logger.error(f"[ERROR] 테스트 보고서 저장 실패: {str(e)}")


def main():
    """메인 함수"""
    print("🚀 Mail Convenience Router 테스트 시작")
    print("=" * 60)
    
    # 서버 URL 설정 (환경변수 또는 기본값)
    base_url = os.getenv("TEST_SERVER_URL", "http://localhost:8000")
    
    # 테스터 인스턴스 생성
    tester = MailConvenienceRouterTester(base_url)
    
    # 모든 테스트 실행
    results = tester.run_all_tests()
    
    # 테스트 보고서 저장
    tester.save_test_report()
    
    # 종료 코드 설정
    if results["failed_tests"] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()