"""
User Router 종합 테스트 스크립트

모든 엔드포인트의 기능, 권한, 데이터 검증을 테스트합니다.
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import aiohttp
import sys
import os

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UserRouterTester:
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url
        self.session = None
        self.admin_token = None
        self.user_token = None
        self.test_results = []
        self.created_user_id = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
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
        logger.info(f"{status} {test_name}: {details}")
    
    async def make_request(self, method: str, endpoint: str, token: str = None, 
                          data: Dict = None, params: Dict = None) -> tuple:
        """HTTP 요청 실행"""
        url = f"{self.base_url}{endpoint}"
        headers = {}
        
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        try:
            async with self.session.request(
                method, url, json=data, params=params, headers=headers
            ) as response:
                try:
                    response_data = await response.json()
                except:
                    response_data = await response.text()
                
                return response.status, response_data
        except Exception as e:
            return 0, str(e)
    
    async def setup_test_environment(self):
        """테스트 환경 설정 - 관리자 및 일반 사용자 토큰 획득"""
        logger.info("🔧 테스트 환경 설정 중...")
        
        # 관리자 로그인 시도
        admin_login_data = {
            "email": "admin@test.com",
            "password": "testpassword123"
        }
        
        status, response = await self.make_request("POST", "/api/v1/auth/login", data=admin_login_data)
        if status == 200 and "access_token" in response:
            self.admin_token = response["access_token"]
            self.log_test_result("관리자 로그인", True, "기존 관리자 계정으로 로그인 성공")
        else:
            # 관리자 계정이 없으면 생성
            logger.info("🔧 관리자 계정 생성 중...")
            import time
            unique_suffix = str(int(time.time()))
            admin_register_data = {
                "user_id": f"admin_test_{unique_suffix}",
                "username": f"admin_test_{unique_suffix}",
                "email": "admin@test.com",
                "password": "testpassword123"
            }
            
            status, response = await self.make_request("POST", "/api/v1/auth/register", data=admin_register_data)
            if status in [200, 201]:
                # 회원가입 후 로그인
                status, response = await self.make_request("POST", "/api/v1/auth/login", data=admin_login_data)
                if status == 200 and "access_token" in response:
                    self.admin_token = response["access_token"]
                    self.log_test_result("관리자 계정 생성 및 로그인", True, "새 관리자 계정 생성 및 로그인 성공")
                else:
                    self.log_test_result("관리자 로그인", False, f"Status: {status}, Response: {response}")
                    return False
            else:
                self.log_test_result("관리자 계정 생성", False, f"Status: {status}, Response: {response}")
                return False
        
        # 일반 사용자 생성 및 로그인
        user_create_data = {
            "email": "testuser@test.com",
            "username": "testuser",
            "password": "testpass123",
            "full_name": "테스트 사용자"
        }
        
        # 기존 사용자 삭제 시도 (있을 경우)
        await self.make_request("DELETE", "/api/users/999", token=self.admin_token)
        
        # 새 사용자 생성
        status, response = await self.make_request("POST", "/api/users/", token=self.admin_token, data=user_create_data)
        if status == 201:
            self.created_user_id = response.get("id")
            self.log_test_result("테스트 사용자 생성", True, f"사용자 ID: {self.created_user_id}")
        else:
            self.log_test_result("테스트 사용자 생성", False, f"Status: {status}, Response: {response}")
        
        # 일반 사용자 로그인
        user_login_data = {
            "email": "testuser@test.com",
            "password": "testpass123"
        }
        
        status, response = await self.make_request("POST", "/api/v1/auth/login", data=user_login_data)
        if status == 200 and "access_token" in response:
            self.user_token = response["access_token"]
            self.log_test_result("일반 사용자 로그인", True, "사용자 토큰 획득 성공")
        else:
            self.log_test_result("일반 사용자 로그인", False, f"Status: {status}, Response: {response}")
        
        return self.admin_token and self.user_token
    
    async def test_authentication_and_authorization(self):
        """인증 및 권한 테스트"""
        logger.info("🔐 인증 및 권한 테스트 시작")
        
        # 1. 무인증 요청 테스트
        status, response = await self.make_request("GET", "/api/users/")
        self.log_test_result(
            "무인증 사용자 목록 조회", 
            status == 401, 
            f"예상: 401, 실제: {status}"
        )
        
        # 2. 일반 사용자의 관리자 기능 접근
        status, response = await self.make_request("GET", "/api/users/", token=self.user_token)
        self.log_test_result(
            "일반 사용자 관리자 기능 접근", 
            status == 403, 
            f"예상: 403, 실제: {status}"
        )
        
        # 3. 관리자 권한 확인
        status, response = await self.make_request("GET", "/api/users/", token=self.admin_token)
        self.log_test_result(
            "관리자 사용자 목록 조회", 
            status == 200, 
            f"예상: 200, 실제: {status}"
        )
        
        # 4. 본인 정보 조회 (일반 사용자)
        status, response = await self.make_request("GET", "/api/users/me", token=self.user_token)
        self.log_test_result(
            "본인 정보 조회", 
            status == 200, 
            f"예상: 200, 실제: {status}"
        )
    
    async def test_user_crud_operations(self):
        """사용자 CRUD 작업 테스트"""
        logger.info("📝 사용자 CRUD 작업 테스트 시작")
        
        # 1. 사용자 생성 테스트
        new_user_data = {
            "email": "newuser@test.com",
            "username": "newuser",
            "password": "newpass123",
            "full_name": "새로운 사용자"
        }
        
        status, response = await self.make_request("POST", "/api/users/", token=self.admin_token, data=new_user_data)
        new_user_id = None
        if status == 201:
            new_user_id = response.get("id")
            self.log_test_result("새 사용자 생성", True, f"사용자 ID: {new_user_id}")
        else:
            self.log_test_result("새 사용자 생성", False, f"Status: {status}, Response: {response}")
        
        # 2. 중복 이메일 테스트
        status, response = await self.make_request("POST", "/api/users/", token=self.admin_token, data=new_user_data)
        self.log_test_result(
            "중복 이메일 사용자 생성", 
            status == 400, 
            f"예상: 400, 실제: {status}"
        )
        
        # 3. 사용자 정보 수정 테스트
        if new_user_id:
            update_data = {
                "username": "updated_user",
                "full_name": "수정된 사용자"
            }
            
            status, response = await self.make_request("PUT", f"/api/users/{new_user_id}", token=self.admin_token, data=update_data)
            self.log_test_result(
                "사용자 정보 수정", 
                status == 200, 
                f"예상: 200, 실제: {status}"
            )
        
        # 4. 특정 사용자 조회 테스트
        if new_user_id:
            status, response = await self.make_request("GET", f"/api/users/{new_user_id}", token=self.admin_token)
            self.log_test_result(
                "특정 사용자 조회", 
                status == 200, 
                f"예상: 200, 실제: {status}"
            )
        
        # 5. 사용자 삭제 테스트
        if new_user_id:
            status, response = await self.make_request("DELETE", f"/api/users/{new_user_id}", token=self.admin_token)
            self.log_test_result(
                "사용자 삭제", 
                status == 200, 
                f"예상: 200, 실제: {status}"
            )
    
    async def test_password_management(self):
        """비밀번호 관리 테스트"""
        logger.info("🔑 비밀번호 관리 테스트 시작")
        
        if not self.created_user_id:
            self.log_test_result("비밀번호 테스트 스킵", False, "테스트 사용자 ID 없음")
            return
        
        # 1. 비밀번호 변경 테스트
        password_data = {
            "current_password": "testpass123",
            "new_password": "newpass456"
        }
        
        status, response = await self.make_request(
            "POST", 
            f"/api/users/{self.created_user_id}/change-password", 
            token=self.user_token, 
            data=password_data
        )
        self.log_test_result(
            "비밀번호 변경", 
            status == 200, 
            f"예상: 200, 실제: {status}"
        )
        
        # 2. 잘못된 현재 비밀번호 테스트
        wrong_password_data = {
            "current_password": "wrongpass",
            "new_password": "newpass789"
        }
        
        status, response = await self.make_request(
            "POST", 
            f"/api/users/{self.created_user_id}/change-password", 
            token=self.user_token, 
            data=wrong_password_data
        )
        self.log_test_result(
            "잘못된 현재 비밀번호", 
            status == 400, 
            f"예상: 400, 실제: {status}"
        )
    
    async def test_user_status_management(self):
        """사용자 상태 관리 테스트"""
        logger.info("🔄 사용자 상태 관리 테스트 시작")
        
        if not self.created_user_id:
            self.log_test_result("상태 관리 테스트 스킵", False, "테스트 사용자 ID 없음")
            return
        
        # 1. 사용자 비활성화 테스트
        status, response = await self.make_request(
            "POST", 
            f"/api/users/{self.created_user_id}/deactivate", 
            token=self.admin_token
        )
        self.log_test_result(
            "사용자 비활성화", 
            status == 200, 
            f"예상: 200, 실제: {status}"
        )
        
        # 2. 사용자 활성화 테스트
        status, response = await self.make_request(
            "POST", 
            f"/api/users/{self.created_user_id}/activate", 
            token=self.admin_token
        )
        self.log_test_result(
            "사용자 활성화", 
            status == 200, 
            f"예상: 200, 실제: {status}"
        )
        
        # 3. 본인 비활성화 방지 테스트
        # 관리자 사용자 ID 가져오기
        status, response = await self.make_request("GET", "/api/users/me", token=self.admin_token)
        if status == 200:
            admin_user_id = response.get("id")
            status, response = await self.make_request(
                "POST", 
                f"/api/users/{admin_user_id}/deactivate", 
                token=self.admin_token
            )
            self.log_test_result(
                "본인 비활성화 방지", 
                status == 400, 
                f"예상: 400, 실제: {status}"
            )
    
    async def test_user_statistics(self):
        """사용자 통계 테스트"""
        logger.info("📊 사용자 통계 테스트 시작")
        
        # 1. 관리자 통계 조회
        status, response = await self.make_request("GET", "/api/users/stats/overview", token=self.admin_token)
        self.log_test_result(
            "사용자 통계 조회", 
            status == 200, 
            f"예상: 200, 실제: {status}",
            response
        )
        
        # 2. 일반 사용자 통계 접근 차단
        status, response = await self.make_request("GET", "/api/users/stats/overview", token=self.user_token)
        self.log_test_result(
            "일반 사용자 통계 접근 차단", 
            status == 403, 
            f"예상: 403, 실제: {status}"
        )
    
    async def test_pagination_and_filtering(self):
        """페이지네이션 및 필터링 테스트"""
        logger.info("📄 페이지네이션 및 필터링 테스트 시작")
        
        # 1. 기본 페이지네이션
        params = {"page": 1, "limit": 10}
        status, response = await self.make_request("GET", "/api/users/", token=self.admin_token, params=params)
        self.log_test_result(
            "기본 페이지네이션", 
            status == 200, 
            f"예상: 200, 실제: {status}"
        )
        
        # 2. 검색 기능
        params = {"search": "test"}
        status, response = await self.make_request("GET", "/api/users/", token=self.admin_token, params=params)
        self.log_test_result(
            "사용자 검색", 
            status == 200, 
            f"예상: 200, 실제: {status}"
        )
        
        # 3. 활성 상태 필터
        params = {"is_active": True}
        status, response = await self.make_request("GET", "/api/users/", token=self.admin_token, params=params)
        self.log_test_result(
            "활성 사용자 필터", 
            status == 200, 
            f"예상: 200, 실제: {status}"
        )
    
    async def test_data_validation(self):
        """데이터 검증 테스트"""
        logger.info("🔍 데이터 검증 테스트 시작")
        
        # 1. 잘못된 이메일 형식
        invalid_user_data = {
            "email": "invalid-email",
            "username": "testuser2",
            "password": "testpass123"
        }
        
        status, response = await self.make_request("POST", "/api/users/", token=self.admin_token, data=invalid_user_data)
        self.log_test_result(
            "잘못된 이메일 형식", 
            status == 422, 
            f"예상: 422, 실제: {status}"
        )
        
        # 2. 필수 필드 누락
        incomplete_user_data = {
            "email": "incomplete@test.com"
        }
        
        status, response = await self.make_request("POST", "/api/users/", token=self.admin_token, data=incomplete_user_data)
        self.log_test_result(
            "필수 필드 누락", 
            status == 422, 
            f"예상: 422, 실제: {status}"
        )
        
        # 3. 존재하지 않는 사용자 조회
        status, response = await self.make_request("GET", "/api/users/99999", token=self.admin_token)
        self.log_test_result(
            "존재하지 않는 사용자 조회", 
            status == 404, 
            f"예상: 404, 실제: {status}"
        )
    
    async def run_all_tests(self):
        """모든 테스트 실행"""
        logger.info("🚀 User Router 종합 테스트 시작")
        
        # 테스트 환경 설정
        if not await self.setup_test_environment():
            logger.error("❌ 테스트 환경 설정 실패")
            return
        
        # 모든 테스트 실행
        await self.test_authentication_and_authorization()
        await self.test_user_crud_operations()
        await self.test_password_management()
        await self.test_user_status_management()
        await self.test_user_statistics()
        await self.test_pagination_and_filtering()
        await self.test_data_validation()
        
        # 결과 요약
        self.print_test_summary()
        
        # 결과 파일 저장
        await self.save_test_results()
    
    def print_test_summary(self):
        """테스트 결과 요약 출력"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        logger.info("=" * 60)
        logger.info("📊 테스트 결과 요약")
        logger.info("=" * 60)
        logger.info(f"총 테스트: {total_tests}")
        logger.info(f"성공: {passed_tests} ✅")
        logger.info(f"실패: {failed_tests} ❌")
        logger.info(f"성공률: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            logger.info("\n❌ 실패한 테스트:")
            for result in self.test_results:
                if not result["success"]:
                    logger.info(f"  - {result['test_name']}: {result['details']}")
    
    async def save_test_results(self):
        """테스트 결과를 JSON 파일로 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"user_router_test_results_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"📄 테스트 결과가 {filename}에 저장되었습니다.")

async def main():
    """메인 실행 함수"""
    async with UserRouterTester() as tester:
        await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())