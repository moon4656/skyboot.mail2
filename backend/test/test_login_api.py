"""
SkyBoot Mail SaaS 로그인 API 테스트 케이스

/api/v1/auth/login 엔드포인트의 요청/응답 구조를 검증하는 테스트 케이스
"""
import requests
import json
import logging
from datetime import datetime
from typing import Dict, Any

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LoginAPITester:
    """로그인 API 테스트 클래스"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.login_endpoint = f"{base_url}/api/v1/auth/login"
        self.test_results = []
    
    def test_valid_login(self) -> Dict[str, Any]:
        """유효한 로그인 테스트"""
        logger.info("🔐 유효한 로그인 테스트 시작")
        
        test_data = {
            "email": "eldorado@skyboot.co.kr",
            "password": "test123"
        }
        
        try:
            response = requests.post(
                self.login_endpoint,
                json=test_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            result = {
                "test_name": "유효한 로그인",
                "status_code": response.status_code,
                "success": response.status_code == 200,
                "response_data": response.json() if response.status_code == 200 else None,
                "error": response.text if response.status_code != 200 else None,
                "timestamp": datetime.now().isoformat()
            }
            
            if result["success"]:
                # 응답 구조 검증
                data = result["response_data"]
                required_fields = ["access_token", "refresh_token", "token_type", "expires_in"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    result["success"] = False
                    result["error"] = f"응답에서 누락된 필드: {missing_fields}"
                else:
                    logger.info("✅ 유효한 로그인 테스트 성공")
            else:
                logger.error(f"❌ 유효한 로그인 테스트 실패: {result['error']}")
                
        except Exception as e:
            result = {
                "test_name": "유효한 로그인",
                "status_code": None,
                "success": False,
                "response_data": None,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            logger.error(f"❌ 유효한 로그인 테스트 예외: {str(e)}")
        
        self.test_results.append(result)
        return result
    
    def test_invalid_email(self) -> Dict[str, Any]:
        """잘못된 이메일 테스트"""
        logger.info("📧 잘못된 이메일 테스트 시작")
        
        test_data = {
            "email": "nonexistent@skyboot.co.kr",
            "password": "test123"
        }
        
        try:
            response = requests.post(
                self.login_endpoint,
                json=test_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            result = {
                "test_name": "잘못된 이메일",
                "status_code": response.status_code,
                "success": response.status_code == 401,  # 401 Unauthorized 예상
                "response_data": response.json() if response.headers.get('content-type', '').startswith('application/json') else None,
                "error": response.text if response.status_code != 401 else None,
                "timestamp": datetime.now().isoformat()
            }
            
            if result["success"]:
                logger.info("✅ 잘못된 이메일 테스트 성공 (401 반환)")
            else:
                logger.error(f"❌ 잘못된 이메일 테스트 실패: 예상 401, 실제 {response.status_code}")
                
        except Exception as e:
            result = {
                "test_name": "잘못된 이메일",
                "status_code": None,
                "success": False,
                "response_data": None,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            logger.error(f"❌ 잘못된 이메일 테스트 예외: {str(e)}")
        
        self.test_results.append(result)
        return result
    
    def test_invalid_password(self) -> Dict[str, Any]:
        """잘못된 비밀번호 테스트"""
        logger.info("🔑 잘못된 비밀번호 테스트 시작")
        
        test_data = {
            "email": "eldorado@skyboot.co.kr",
            "password": "wrongpassword"
        }
        
        try:
            response = requests.post(
                self.login_endpoint,
                json=test_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            result = {
                "test_name": "잘못된 비밀번호",
                "status_code": response.status_code,
                "success": response.status_code == 401,  # 401 Unauthorized 예상
                "response_data": response.json() if response.headers.get('content-type', '').startswith('application/json') else None,
                "error": response.text if response.status_code != 401 else None,
                "timestamp": datetime.now().isoformat()
            }
            
            if result["success"]:
                logger.info("✅ 잘못된 비밀번호 테스트 성공 (401 반환)")
            else:
                logger.error(f"❌ 잘못된 비밀번호 테스트 실패: 예상 401, 실제 {response.status_code}")
                
        except Exception as e:
            result = {
                "test_name": "잘못된 비밀번호",
                "status_code": None,
                "success": False,
                "response_data": None,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            logger.error(f"❌ 잘못된 비밀번호 테스트 예외: {str(e)}")
        
        self.test_results.append(result)
        return result
    
    def test_missing_fields(self) -> Dict[str, Any]:
        """필수 필드 누락 테스트"""
        logger.info("📝 필수 필드 누락 테스트 시작")
        
        test_data = {
            "email": "eldorado@skyboot.co.kr"
            # password 필드 누락
        }
        
        try:
            response = requests.post(
                self.login_endpoint,
                json=test_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            result = {
                "test_name": "필수 필드 누락",
                "status_code": response.status_code,
                "success": response.status_code == 422,  # 422 Validation Error 예상
                "response_data": response.json() if response.headers.get('content-type', '').startswith('application/json') else None,
                "error": response.text if response.status_code != 422 else None,
                "timestamp": datetime.now().isoformat()
            }
            
            if result["success"]:
                logger.info("✅ 필수 필드 누락 테스트 성공 (422 반환)")
            else:
                logger.error(f"❌ 필수 필드 누락 테스트 실패: 예상 422, 실제 {response.status_code}")
                
        except Exception as e:
            result = {
                "test_name": "필수 필드 누락",
                "status_code": None,
                "success": False,
                "response_data": None,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            logger.error(f"❌ 필수 필드 누락 테스트 예외: {str(e)}")
        
        self.test_results.append(result)
        return result
    
    def test_invalid_json(self) -> Dict[str, Any]:
        """잘못된 JSON 형식 테스트"""
        logger.info("🔧 잘못된 JSON 형식 테스트 시작")
        
        invalid_json = '{"email": "eldorado@skyboot.co.kr", "password": "test123"'  # 닫는 괄호 누락
        
        try:
            response = requests.post(
                self.login_endpoint,
                data=invalid_json,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            result = {
                "test_name": "잘못된 JSON 형식",
                "status_code": response.status_code,
                "success": response.status_code == 422,  # 422 Validation Error 예상
                "response_data": response.json() if response.headers.get('content-type', '').startswith('application/json') else None,
                "error": response.text if response.status_code != 422 else None,
                "timestamp": datetime.now().isoformat()
            }
            
            if result["success"]:
                logger.info("✅ 잘못된 JSON 형식 테스트 성공 (422 반환)")
            else:
                logger.error(f"❌ 잘못된 JSON 형식 테스트 실패: 예상 422, 실제 {response.status_code}")
                
        except Exception as e:
            result = {
                "test_name": "잘못된 JSON 형식",
                "status_code": None,
                "success": False,
                "response_data": None,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            logger.error(f"❌ 잘못된 JSON 형식 테스트 예외: {str(e)}")
        
        self.test_results.append(result)
        return result
    
    def run_all_tests(self) -> Dict[str, Any]:
        """모든 테스트 실행"""
        logger.info("🚀 로그인 API 테스트 시작")
        
        # 모든 테스트 실행
        self.test_valid_login()
        self.test_invalid_email()
        self.test_invalid_password()
        self.test_missing_fields()
        self.test_invalid_json()
        
        # 결과 요약
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        summary = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": f"{(passed_tests / total_tests * 100):.1f}%" if total_tests > 0 else "0%",
            "test_results": self.test_results,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"📊 테스트 완료 - 총 {total_tests}개, 성공 {passed_tests}개, 실패 {failed_tests}개")
        
        return summary
    
    def save_results(self, filename: str = "login_api_test_results.json"):
        """테스트 결과를 파일로 저장"""
        summary = self.run_all_tests()
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        logger.info(f"💾 테스트 결과가 {filename}에 저장되었습니다.")
        return summary

def main():
    """메인 함수"""
    logger.info("🎯 SkyBoot Mail SaaS 로그인 API 테스트 시작")
    
    # 테스터 초기화
    tester = LoginAPITester()
    
    # 테스트 실행 및 결과 저장
    results = tester.save_results()
    
    # 결과 출력
    print("\n" + "="*50)
    print("📋 로그인 API 테스트 결과 요약")
    print("="*50)
    print(f"총 테스트: {results['total_tests']}개")
    print(f"성공: {results['passed_tests']}개")
    print(f"실패: {results['failed_tests']}개")
    print(f"성공률: {results['success_rate']}")
    print("="*50)
    
    # 개별 테스트 결과
    for result in results['test_results']:
        status = "✅ 성공" if result['success'] else "❌ 실패"
        print(f"{status} - {result['test_name']} (상태코드: {result['status_code']})")
        if not result['success'] and result['error']:
            print(f"   오류: {result['error']}")
    
    return results

if __name__ == "__main__":
    main()