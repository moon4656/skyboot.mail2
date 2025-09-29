#!/usr/bin/env python3
"""
SkyBoot Mail SaaS - 로그인 API 테스트 케이스
===========================================

/api/v1/auth/login 엔드포인트에 대한 종합적인 테스트 케이스

작성일: 2024년 12월
작성자: SkyBoot Mail 개발팀
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional

# 테스트 설정
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"

class LoginAPITester:
    """로그인 API 테스트 클래스"""
    
    def __init__(self):
        self.base_url = f"{BASE_URL}{API_PREFIX}"
        self.test_results = {}
        self.session = requests.Session()
        
    def log_test_result(self, test_name: str, success: bool, details: Dict[str, Any]):
        """테스트 결과 로깅"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.test_results[test_name] = {
            "timestamp": timestamp,
            "success": success,
            "details": details
        }
        
        status = "✅ 성공" if success else "❌ 실패"
        print(f"[{timestamp}] {status} - {test_name}")
        if not success:
            print(f"  상세: {details.get('error', 'Unknown error')}")
    
    def test_login_success(self) -> bool:
        """정상 로그인 테스트"""
        print("\n=== 1. 정상 로그인 테스트 ===")
        
        # 테스트 데이터
        login_data = {
            "email": "admin@skyboot.kr",
            "password": "admin123"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"}
            )
            
            # 응답 상태 코드 확인
            if response.status_code != 200:
                self.log_test_result(
                    "정상_로그인", 
                    False, 
                    {
                        "status_code": response.status_code,
                        "response": response.text,
                        "error": f"예상 상태 코드: 200, 실제: {response.status_code}"
                    }
                )
                return False
            
            # 응답 데이터 확인
            response_data = response.json()
            required_fields = ["access_token", "refresh_token", "token_type", "expires_in"]
            
            for field in required_fields:
                if field not in response_data:
                    self.log_test_result(
                        "정상_로그인", 
                        False, 
                        {
                            "error": f"응답에 필수 필드 '{field}'가 없습니다",
                            "response": response_data
                        }
                    )
                    return False
            
            # 토큰 타입 확인
            if response_data["token_type"] != "bearer":
                self.log_test_result(
                    "정상_로그인", 
                    False, 
                    {
                        "error": f"토큰 타입이 'bearer'가 아닙니다: {response_data['token_type']}",
                        "response": response_data
                    }
                )
                return False
            
            # 만료 시간 확인 (30분 = 1800초)
            if response_data["expires_in"] != 1800:
                print(f"⚠️ 경고: 예상 만료 시간(1800초)과 다릅니다: {response_data['expires_in']}초")
            
            self.log_test_result(
                "정상_로그인", 
                True, 
                {
                    "status_code": response.status_code,
                    "token_type": response_data["token_type"],
                    "expires_in": response_data["expires_in"],
                    "access_token_length": len(response_data["access_token"]),
                    "refresh_token_length": len(response_data["refresh_token"])
                }
            )
            
            # 토큰 저장 (후속 테스트용)
            self.access_token = response_data["access_token"]
            self.refresh_token = response_data["refresh_token"]
            
            return True
            
        except Exception as e:
            self.log_test_result(
                "정상_로그인", 
                False, 
                {"error": f"예외 발생: {str(e)}"}
            )
            return False
    
    def test_login_invalid_credentials(self) -> bool:
        """잘못된 자격증명 테스트"""
        print("\n=== 2. 잘못된 자격증명 테스트 ===")
        
        test_cases = [
            {
                "name": "잘못된_비밀번호",
                "data": {"email": "admin@skyboot.kr", "password": "wrongpassword"},
                "expected_status": 401,
                "expected_error": "Incorrect email or password"
            },
            {
                "name": "존재하지_않는_이메일",
                "data": {"email": "nonexistent@example.com", "password": "admin123"},
                "expected_status": 401,
                "expected_error": "Incorrect email or password"
            },
            {
                "name": "빈_이메일",
                "data": {"email": "", "password": "admin123"},
                "expected_status": 422,
                "expected_error": "validation error"
            },
            {
                "name": "빈_비밀번호",
                "data": {"email": "admin@skyboot.kr", "password": ""},
                "expected_status": 422,
                "expected_error": "validation error"
            }
        ]
        
        all_passed = True
        
        for test_case in test_cases:
            try:
                response = self.session.post(
                    f"{self.base_url}/auth/login",
                    json=test_case["data"],
                    headers={"Content-Type": "application/json"}
                )
                
                success = response.status_code == test_case["expected_status"]
                
                if success and test_case["expected_status"] == 401:
                    # 401 에러의 경우 에러 메시지도 확인
                    response_data = response.json()
                    if "detail" in response_data:
                        success = test_case["expected_error"] in str(response_data["detail"])
                
                self.log_test_result(
                    test_case["name"],
                    success,
                    {
                        "expected_status": test_case["expected_status"],
                        "actual_status": response.status_code,
                        "response": response.text[:200] if response.text else None
                    }
                )
                
                if not success:
                    all_passed = False
                    
            except Exception as e:
                self.log_test_result(
                    test_case["name"],
                    False,
                    {"error": f"예외 발생: {str(e)}"}
                )
                all_passed = False
        
        return all_passed
    
    def test_login_validation_errors(self) -> bool:
        """입력 검증 오류 테스트"""
        print("\n=== 3. 입력 검증 오류 테스트 ===")
        
        test_cases = [
            {
                "name": "필수_필드_누락_이메일",
                "data": {"password": "admin123"},
                "expected_status": 422
            },
            {
                "name": "필수_필드_누락_비밀번호",
                "data": {"email": "admin@skyboot.kr"},
                "expected_status": 422
            },
            {
                "name": "잘못된_JSON_형식",
                "data": "invalid json",
                "expected_status": 422
            },
            {
                "name": "빈_요청_본문",
                "data": {},
                "expected_status": 422
            }
        ]
        
        all_passed = True
        
        for test_case in test_cases:
            try:
                if isinstance(test_case["data"], str):
                    # 잘못된 JSON 형식 테스트
                    response = self.session.post(
                        f"{self.base_url}/auth/login",
                        data=test_case["data"],
                        headers={"Content-Type": "application/json"}
                    )
                else:
                    response = self.session.post(
                        f"{self.base_url}/auth/login",
                        json=test_case["data"],
                        headers={"Content-Type": "application/json"}
                    )
                
                success = response.status_code == test_case["expected_status"]
                
                self.log_test_result(
                    test_case["name"],
                    success,
                    {
                        "expected_status": test_case["expected_status"],
                        "actual_status": response.status_code,
                        "response": response.text[:200] if response.text else None
                    }
                )
                
                if not success:
                    all_passed = False
                    
            except Exception as e:
                self.log_test_result(
                    test_case["name"],
                    False,
                    {"error": f"예외 발생: {str(e)}"}
                )
                all_passed = False
        
        return all_passed
    
    def test_token_validation(self) -> bool:
        """토큰 검증 테스트"""
        print("\n=== 4. 토큰 검증 테스트 ===")
        
        if not hasattr(self, 'access_token'):
            print("❌ 이전 테스트에서 토큰을 얻지 못했습니다. 정상 로그인 테스트를 먼저 실행하세요.")
            return False
        
        try:
            # 발급받은 토큰으로 사용자 정보 조회
            response = self.session.get(
                f"{self.base_url}/auth/me",
                headers={"Authorization": f"Bearer {self.access_token}"}
            )
            
            success = response.status_code == 200
            
            if success:
                user_data = response.json()
                required_fields = ["user_id", "user_uuid", "email", "username", "org_id", "is_active"]
                
                for field in required_fields:
                    if field not in user_data:
                        success = False
                        break
            
            self.log_test_result(
                "토큰_검증",
                success,
                {
                    "status_code": response.status_code,
                    "response": response.json() if success else response.text[:200]
                }
            )
            
            return success
            
        except Exception as e:
            self.log_test_result(
                "토큰_검증",
                False,
                {"error": f"예외 발생: {str(e)}"}
            )
            return False
    
    def test_concurrent_logins(self) -> bool:
        """동시 로그인 테스트"""
        print("\n=== 5. 동시 로그인 테스트 ===")
        
        login_data = {
            "email": "admin@skyboot.kr",
            "password": "admin123"
        }
        
        try:
            # 첫 번째 로그인
            response1 = self.session.post(
                f"{self.base_url}/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"}
            )
            
            # 두 번째 로그인 (같은 사용자)
            response2 = self.session.post(
                f"{self.base_url}/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"}
            )
            
            success = (response1.status_code == 200 and response2.status_code == 200)
            
            if success:
                token1 = response1.json()["access_token"]
                token2 = response2.json()["access_token"]
                
                # 두 토큰이 다른지 확인
                tokens_different = token1 != token2
                
                self.log_test_result(
                    "동시_로그인",
                    success and tokens_different,
                    {
                        "first_login_status": response1.status_code,
                        "second_login_status": response2.status_code,
                        "tokens_different": tokens_different
                    }
                )
                
                return success and tokens_different
            else:
                self.log_test_result(
                    "동시_로그인",
                    False,
                    {
                        "first_login_status": response1.status_code,
                        "second_login_status": response2.status_code,
                        "error": "로그인 실패"
                    }
                )
                return False
                
        except Exception as e:
            self.log_test_result(
                "동시_로그인",
                False,
                {"error": f"예외 발생: {str(e)}"}
            )
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """모든 테스트 실행"""
        print("🚀 SkyBoot Mail SaaS - 로그인 API 테스트 시작")
        print("=" * 60)
        
        start_time = time.time()
        
        # 테스트 실행
        tests = [
            ("정상 로그인", self.test_login_success),
            ("잘못된 자격증명", self.test_login_invalid_credentials),
            ("입력 검증 오류", self.test_login_validation_errors),
            ("토큰 검증", self.test_token_validation),
            ("동시 로그인", self.test_concurrent_logins)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed_tests += 1
            except Exception as e:
                print(f"❌ {test_name} 테스트 중 예외 발생: {str(e)}")
        
        end_time = time.time()
        duration = end_time - start_time
        
        # 결과 요약
        print("\n" + "=" * 60)
        print("📊 테스트 결과 요약")
        print("=" * 60)
        print(f"총 테스트: {total_tests}")
        print(f"성공: {passed_tests}")
        print(f"실패: {total_tests - passed_tests}")
        print(f"성공률: {(passed_tests/total_tests)*100:.1f}%")
        print(f"실행 시간: {duration:.2f}초")
        
        # 상세 결과 저장
        summary = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "success_rate": (passed_tests/total_tests)*100,
            "duration": duration,
            "detailed_results": self.test_results
        }
        
        # JSON 파일로 저장
        with open("login_api_test_results.json", "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n📄 상세 결과가 'login_api_test_results.json' 파일에 저장되었습니다.")
        
        return summary

def main():
    """메인 함수"""
    tester = LoginAPITester()
    results = tester.run_all_tests()
    
    # 테스트 실패 시 종료 코드 1 반환
    if results["failed_tests"] > 0:
        exit(1)
    else:
        print("\n🎉 모든 테스트가 성공적으로 완료되었습니다!")
        exit(0)

if __name__ == "__main__":
    main()