"""
SkyBoot Mail SaaS 로그인 API 테스트 케이스

/api/v1/auth/login 엔드포인트에 대한 종합적인 테스트 계획 및 실행
"""
import pytest
import requests
import json
from datetime import datetime
from typing import Dict, Any

# 테스트 설정
BASE_URL = "http://localhost:8000"
LOGIN_ENDPOINT = f"{BASE_URL}/api/v1/auth/login"

class LoginAPITestSuite:
    """로그인 API 테스트 스위트"""
    
    def __init__(self):
        self.test_results = []
        self.session = requests.Session()
    
    def log_test_result(self, test_name: str, success: bool, details: Dict[str, Any]):
        """테스트 결과 로깅"""
        result = {
            "test_name": test_name,
            "timestamp": datetime.now().isoformat(),
            "success": success,
            "details": details
        }
        self.test_results.append(result)
        print(f"{'✅' if success else '❌'} {test_name}: {details.get('message', '')}")
    
    def test_valid_login(self):
        """정상 로그인 테스트"""
        test_data = {
            "email": "test@skyboot.kr",
            "password": "test123"
        }
        
        try:
            response = self.session.post(LOGIN_ENDPOINT, json=test_data)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["access_token", "refresh_token", "token_type", "expires_in"]
                
                if all(field in data for field in required_fields):
                    self.log_test_result(
                        "정상 로그인 테스트",
                        True,
                        {
                            "message": "로그인 성공",
                            "status_code": response.status_code,
                            "token_type": data.get("token_type"),
                            "expires_in": data.get("expires_in")
                        }
                    )
                    return data
                else:
                    missing_fields = [f for f in required_fields if f not in data]
                    self.log_test_result(
                        "정상 로그인 테스트",
                        False,
                        {
                            "message": f"응답에 필수 필드 누락: {missing_fields}",
                            "response": data
                        }
                    )
            else:
                self.log_test_result(
                    "정상 로그인 테스트",
                    False,
                    {
                        "message": f"예상하지 못한 상태 코드: {response.status_code}",
                        "response": response.text
                    }
                )
        except Exception as e:
            self.log_test_result(
                "정상 로그인 테스트",
                False,
                {"message": f"요청 실패: {str(e)}"}
            )
        
        return None
    
    def test_invalid_email(self):
        """잘못된 이메일 테스트"""
        test_data = {
            "email": "nonexistent@example.com",
            "password": "test123"
        }
        
        try:
            response = self.session.post(LOGIN_ENDPOINT, json=test_data)
            
            if response.status_code == 401:
                self.log_test_result(
                    "잘못된 이메일 테스트",
                    True,
                    {
                        "message": "올바른 401 응답",
                        "status_code": response.status_code
                    }
                )
            else:
                self.log_test_result(
                    "잘못된 이메일 테스트",
                    False,
                    {
                        "message": f"예상 상태 코드 401, 실제: {response.status_code}",
                        "response": response.text
                    }
                )
        except Exception as e:
            self.log_test_result(
                "잘못된 이메일 테스트",
                False,
                {"message": f"요청 실패: {str(e)}"}
            )
    
    def test_invalid_password(self):
        """잘못된 비밀번호 테스트"""
        test_data = {
            "email": "test@skyboot.kr",
            "password": "wrongpassword"
        }
        
        try:
            response = self.session.post(LOGIN_ENDPOINT, json=test_data)
            
            if response.status_code == 401:
                self.log_test_result(
                    "잘못된 비밀번호 테스트",
                    True,
                    {
                        "message": "올바른 401 응답",
                        "status_code": response.status_code
                    }
                )
            else:
                self.log_test_result(
                    "잘못된 비밀번호 테스트",
                    False,
                    {
                        "message": f"예상 상태 코드 401, 실제: {response.status_code}",
                        "response": response.text
                    }
                )
        except Exception as e:
            self.log_test_result(
                "잘못된 비밀번호 테스트",
                False,
                {"message": f"요청 실패: {str(e)}"}
            )
    
    def test_missing_fields(self):
        """필수 필드 누락 테스트"""
        test_cases = [
            {"email": "test@skyboot.kr"},  # password 누락
            {"password": "test123"},       # email 누락
            {}                             # 모든 필드 누락
        ]
        
        for i, test_data in enumerate(test_cases):
            try:
                response = self.session.post(LOGIN_ENDPOINT, json=test_data)
                
                if response.status_code == 422:  # Validation Error
                    self.log_test_result(
                        f"필수 필드 누락 테스트 {i+1}",
                        True,
                        {
                            "message": "올바른 422 응답 (Validation Error)",
                            "status_code": response.status_code,
                            "test_data": test_data
                        }
                    )
                else:
                    self.log_test_result(
                        f"필수 필드 누락 테스트 {i+1}",
                        False,
                        {
                            "message": f"예상 상태 코드 422, 실제: {response.status_code}",
                            "response": response.text,
                            "test_data": test_data
                        }
                    )
            except Exception as e:
                self.log_test_result(
                    f"필수 필드 누락 테스트 {i+1}",
                    False,
                    {"message": f"요청 실패: {str(e)}", "test_data": test_data}
                )
    
    def test_invalid_json(self):
        """잘못된 JSON 형식 테스트"""
        try:
            response = self.session.post(
                LOGIN_ENDPOINT, 
                data="invalid json",
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 422:
                self.log_test_result(
                    "잘못된 JSON 형식 테스트",
                    True,
                    {
                        "message": "올바른 422 응답",
                        "status_code": response.status_code
                    }
                )
            else:
                self.log_test_result(
                    "잘못된 JSON 형식 테스트",
                    False,
                    {
                        "message": f"예상 상태 코드 422, 실제: {response.status_code}",
                        "response": response.text
                    }
                )
        except Exception as e:
            self.log_test_result(
                "잘못된 JSON 형식 테스트",
                False,
                {"message": f"요청 실패: {str(e)}"}
            )
    
    def test_token_validation(self, token_data: Dict[str, Any]):
        """토큰 유효성 검증 테스트"""
        if not token_data:
            self.log_test_result(
                "토큰 유효성 검증 테스트",
                False,
                {"message": "토큰 데이터가 없음"}
            )
            return
        
        # /api/v1/auth/me 엔드포인트로 토큰 검증
        headers = {
            "Authorization": f"Bearer {token_data['access_token']}"
        }
        
        try:
            response = self.session.get(f"{BASE_URL}/api/v1/auth/me", headers=headers)
            
            if response.status_code == 200:
                user_data = response.json()
                required_fields = ["user_id", "email", "org_id", "role"]
                
                if all(field in user_data for field in required_fields):
                    self.log_test_result(
                        "토큰 유효성 검증 테스트",
                        True,
                        {
                            "message": "토큰으로 사용자 정보 조회 성공",
                            "user_email": user_data.get("email"),
                            "user_role": user_data.get("role")
                        }
                    )
                else:
                    missing_fields = [f for f in required_fields if f not in user_data]
                    self.log_test_result(
                        "토큰 유효성 검증 테스트",
                        False,
                        {
                            "message": f"사용자 정보에 필수 필드 누락: {missing_fields}",
                            "response": user_data
                        }
                    )
            else:
                self.log_test_result(
                    "토큰 유효성 검증 테스트",
                    False,
                    {
                        "message": f"토큰 검증 실패: {response.status_code}",
                        "response": response.text
                    }
                )
        except Exception as e:
            self.log_test_result(
                "토큰 유효성 검증 테스트",
                False,
                {"message": f"요청 실패: {str(e)}"}
            )
    
    def run_all_tests(self):
        """모든 테스트 실행"""
        print("🚀 로그인 API 테스트 시작")
        print("=" * 50)
        
        # 1. 정상 로그인 테스트 (토큰 획득)
        token_data = self.test_valid_login()
        
        # 2. 인증 실패 테스트들
        self.test_invalid_email()
        self.test_invalid_password()
        
        # 3. 입력 검증 테스트들
        self.test_missing_fields()
        self.test_invalid_json()
        
        # 4. 토큰 유효성 검증 (정상 로그인이 성공한 경우)
        if token_data:
            self.test_token_validation(token_data)
        
        # 결과 요약
        self.print_summary()
    
    def print_summary(self):
        """테스트 결과 요약 출력"""
        print("\n" + "=" * 50)
        print("📊 테스트 결과 요약")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"총 테스트: {total_tests}")
        print(f"성공: {passed_tests}")
        print(f"실패: {failed_tests}")
        print(f"성공률: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print("\n❌ 실패한 테스트:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test_name']}: {result['details'].get('message', '')}")
        
        # 결과를 JSON 파일로 저장
        with open("login_api_test_results.json", "w", encoding="utf-8") as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 상세 결과가 'login_api_test_results.json'에 저장되었습니다.")

def main():
    """메인 실행 함수"""
    print("🔐 SkyBoot Mail SaaS 로그인 API 테스트")
    print("서버가 http://localhost:8000에서 실행 중인지 확인하세요.")
    
    # 서버 연결 확인
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        if response.status_code == 200:
            print("✅ 서버 연결 확인됨")
        else:
            print(f"⚠️ 서버 응답 이상: {response.status_code}")
    except Exception as e:
        print(f"❌ 서버 연결 실패: {str(e)}")
        print("서버를 먼저 시작해주세요: uvicorn main:app --reload")
        return
    
    # 테스트 실행
    test_suite = LoginAPITestSuite()
    test_suite.run_all_tests()

if __name__ == "__main__":
    main()