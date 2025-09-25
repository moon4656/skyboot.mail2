#!/usr/bin/env python3
"""
조직 라우터 엔드포인트 테스트 스크립트

organization_router.py의 모든 엔드포인트를 체계적으로 테스트합니다.
"""
import asyncio
import json
import sys
import traceback
from datetime import datetime
from typing import Dict, Any, Optional

import httpx
import pytest


class OrganizationRouterTester:
    """조직 라우터 테스트 클래스"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
        self.admin_token = None
        self.user_token = None
        self.test_org_id = None
        self.test_results = []
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    def log_test(self, test_name: str, success: bool, details: str = "", response_data: Any = None):
        """테스트 결과 로깅"""
        result = {
            "test_name": test_name,
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "details": details,
            "response_data": response_data
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   📝 {details}")
        if not success and response_data:
            print(f"   📄 Response: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
        print()
    
    async def test_server_health(self):
        """서버 상태 확인"""
        try:
            response = await self.client.get(f"{self.base_url}/docs")
            success = response.status_code == 200
            self.log_test(
                "서버 상태 확인",
                success,
                f"Status: {response.status_code}"
            )
            return success
        except Exception as e:
            self.log_test("서버 상태 확인", False, f"Error: {str(e)}")
            return False
    
    async def create_test_admin_user(self):
        """테스트용 관리자 사용자 생성"""
        try:
            # 먼저 기존 사용자가 있는지 확인
            login_data = {
                "email": "admin@test.com",
                "password": "testpassword123"
            }
            
            response = await self.client.post(
                 f"{self.base_url}/api/v1/auth/login",
                 json=login_data
             )
            
            if response.status_code == 200:
                token_data = response.json()
                self.admin_token = token_data.get("access_token")
                self.log_test(
                    "기존 관리자 로그인",
                    True,
                    "기존 관리자 계정으로 로그인 성공"
                )
                return True
            
            # 기존 사용자가 없으면 회원가입 시도
            register_data = {
                "user_id": "admin",
                "username": "admin",
                "email": "admin@test.com",
                "password": "testpassword123"
            }
            
            response = await self.client.post(
                 f"{self.base_url}/api/v1/auth/register",
                 json=register_data
             )
            
            if response.status_code in [200, 201]:
                # 회원가입 후 로그인
                response = await self.client.post(
                     f"{self.base_url}/api/v1/auth/login",
                     json=login_data
                 )
                
                if response.status_code == 200:
                    token_data = response.json()
                    self.admin_token = token_data.get("access_token")
                    self.log_test(
                        "관리자 사용자 생성 및 로그인",
                        True,
                        "새 관리자 계정 생성 및 로그인 성공"
                    )
                    return True
            
            self.log_test(
                "관리자 사용자 생성",
                False,
                f"Status: {response.status_code}",
                response.json() if response.status_code != 500 else {"error": "Server error"}
            )
            return False
            
        except Exception as e:
            self.log_test("관리자 사용자 생성", False, f"Error: {str(e)}")
            return False
    
    def get_auth_headers(self, token: Optional[str] = None) -> Dict[str, str]:
        """인증 헤더 생성"""
        if not token:
            token = self.admin_token
        
        if token:
            return {"Authorization": f"Bearer {token}"}
        return {}
    
    async def test_create_organization(self):
        """조직 생성 테스트"""
        try:
            org_data = {
                "organization": {
                    "name": "테스트 조직",
                    "domain": "test.example.com",
                    "description": "테스트용 조직입니다",
                    "max_users": 100,
                    "max_storage_gb": 1000
                },
                "admin_email": "org_admin@test.com",
                "admin_password": "orgpassword123",
                "admin_name": "조직 관리자"
            }
            
            response = await self.client.post(
                f"{self.base_url}/api/v1/organizations/",
                json=org_data,
                headers=self.get_auth_headers()
            )
            
            success = response.status_code == 201
            response_data = response.json() if response.status_code != 500 else {"error": "Server error"}
            
            if success and "id" in response_data:
                self.test_org_id = response_data["id"]
            
            self.log_test(
                "조직 생성",
                success,
                f"Status: {response.status_code}, Org ID: {self.test_org_id}",
                response_data
            )
            return success
            
        except Exception as e:
            self.log_test("조직 생성", False, f"Error: {str(e)}")
            return False
    
    async def test_list_organizations(self):
        """조직 목록 조회 테스트"""
        try:
            response = await self.client.get(
                f"{self.base_url}/api/v1/organizations/",
                headers=self.get_auth_headers()
            )
            
            success = response.status_code == 200
            response_data = response.json() if response.status_code != 500 else {"error": "Server error"}
            
            details = f"Status: {response.status_code}"
            if success and "organizations" in response_data:
                details += f", Count: {len(response_data['organizations'])}"
            
            self.log_test("조직 목록 조회", success, details, response_data)
            return success
            
        except Exception as e:
            self.log_test("조직 목록 조회", False, f"Error: {str(e)}")
            return False
    
    async def test_get_organization(self):
        """조직 정보 조회 테스트"""
        if not self.test_org_id:
            self.log_test("조직 정보 조회", False, "테스트 조직 ID가 없습니다")
            return False
        
        try:
            response = await self.client.get(
                f"{self.base_url}/api/v1/organizations/{self.test_org_id}",
                headers=self.get_auth_headers()
            )
            
            success = response.status_code == 200
            response_data = response.json() if response.status_code != 500 else {"error": "Server error"}
            
            self.log_test(
                "조직 정보 조회",
                success,
                f"Status: {response.status_code}, Org ID: {self.test_org_id}",
                response_data
            )
            return success
            
        except Exception as e:
            self.log_test("조직 정보 조회", False, f"Error: {str(e)}")
            return False
    
    async def test_update_organization(self):
        """조직 정보 수정 테스트"""
        if not self.test_org_id:
            self.log_test("조직 정보 수정", False, "테스트 조직 ID가 없습니다")
            return False
        
        try:
            update_data = {
                "name": "수정된 테스트 조직",
                "description": "수정된 설명입니다",
                "max_users": 150
            }
            
            response = await self.client.put(
                f"{self.base_url}/api/v1/organizations/{self.test_org_id}",
                json=update_data,
                headers=self.get_auth_headers()
            )
            
            success = response.status_code == 200
            response_data = response.json() if response.status_code != 500 else {"error": "Server error"}
            
            self.log_test(
                "조직 정보 수정",
                success,
                f"Status: {response.status_code}",
                response_data
            )
            return success
            
        except Exception as e:
            self.log_test("조직 정보 수정", False, f"Error: {str(e)}")
            return False
    
    async def test_organization_stats(self):
        """조직 통계 조회 테스트"""
        if not self.test_org_id:
            self.log_test("조직 통계 조회", False, "테스트 조직 ID가 없습니다")
            return False
        
        try:
            response = await self.client.get(
                f"{self.base_url}/api/v1/organizations/{self.test_org_id}/stats",
                headers=self.get_auth_headers()
            )
            
            success = response.status_code == 200
            response_data = response.json() if response.status_code != 500 else {"error": "Server error"}
            
            self.log_test(
                "조직 통계 조회",
                success,
                f"Status: {response.status_code}",
                response_data
            )
            return success
            
        except Exception as e:
            self.log_test("조직 통계 조회", False, f"Error: {str(e)}")
            return False
    
    async def test_organization_settings(self):
        """조직 설정 조회 테스트"""
        if not self.test_org_id:
            self.log_test("조직 설정 조회", False, "테스트 조직 ID가 없습니다")
            return False
        
        try:
            response = await self.client.get(
                f"{self.base_url}/api/v1/organizations/{self.test_org_id}/settings",
                headers=self.get_auth_headers()
            )
            
            success = response.status_code == 200
            response_data = response.json() if response.status_code != 500 else {"error": "Server error"}
            
            self.log_test(
                "조직 설정 조회",
                success,
                f"Status: {response.status_code}",
                response_data
            )
            return success
            
        except Exception as e:
            self.log_test("조직 설정 조회", False, f"Error: {str(e)}")
            return False
    
    async def test_update_organization_settings(self):
        """조직 설정 수정 테스트"""
        if not self.test_org_id:
            self.log_test("조직 설정 수정", False, "테스트 조직 ID가 없습니다")
            return False
        
        try:
            settings_data = {
                "mail_retention_days": 180,
                "max_attachment_size_mb": 50,
                "enable_spam_filter": True,
                "enable_virus_scan": True
            }
            
            response = await self.client.put(
                f"{self.base_url}/api/v1/organizations/{self.test_org_id}/settings",
                json=settings_data,
                headers=self.get_auth_headers()
            )
            
            success = response.status_code == 200
            response_data = response.json() if response.status_code != 500 else {"error": "Server error"}
            
            self.log_test(
                "조직 설정 수정",
                success,
                f"Status: {response.status_code}",
                response_data
            )
            return success
            
        except Exception as e:
            self.log_test("조직 설정 수정", False, f"Error: {str(e)}")
            return False
    
    async def test_current_organization_endpoints(self):
        """현재 조직 관련 엔드포인트 테스트"""
        try:
            # 현재 조직 정보 조회
            response = await self.client.get(
                f"{self.base_url}/api/v1/organizations/current",
                headers=self.get_auth_headers()
            )
            
            success1 = response.status_code == 200
            self.log_test(
                "현재 조직 정보 조회",
                success1,
                f"Status: {response.status_code}",
                response.json() if response.status_code != 500 else {"error": "Server error"}
            )
            
            # 현재 조직 통계 조회
            response = await self.client.get(
                f"{self.base_url}/api/v1/organizations/current/stats",
                headers=self.get_auth_headers()
            )
            
            success2 = response.status_code == 200
            self.log_test(
                "현재 조직 통계 조회",
                success2,
                f"Status: {response.status_code}",
                response.json() if response.status_code != 500 else {"error": "Server error"}
            )
            
            # 현재 조직 설정 조회
            response = await self.client.get(
                f"{self.base_url}/api/v1/organizations/current/settings",
                headers=self.get_auth_headers()
            )
            
            success3 = response.status_code == 200
            self.log_test(
                "현재 조직 설정 조회",
                success3,
                f"Status: {response.status_code}",
                response.json() if response.status_code != 500 else {"error": "Server error"}
            )
            
            return success1 and success2 and success3
            
        except Exception as e:
            self.log_test("현재 조직 엔드포인트", False, f"Error: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """모든 테스트 실행"""
        print("🚀 조직 라우터 엔드포인트 테스트 시작\n")
        
        # 1. 서버 상태 확인
        if not await self.test_server_health():
            print("❌ 서버에 연결할 수 없습니다. 테스트를 중단합니다.")
            return
        
        # 2. 관리자 사용자 생성/로그인
        if not await self.create_test_admin_user():
            print("❌ 관리자 사용자를 생성할 수 없습니다. 테스트를 중단합니다.")
            return
        
        # 3. 기본 CRUD 테스트
        await self.test_create_organization()
        await self.test_list_organizations()
        await self.test_get_organization()
        await self.test_update_organization()
        
        # 4. 통계 및 설정 테스트
        await self.test_organization_stats()
        await self.test_organization_settings()
        await self.test_update_organization_settings()
        
        # 5. 현재 조직 엔드포인트 테스트
        await self.test_current_organization_endpoints()
        
        # 6. 결과 요약
        self.print_summary()
    
    def print_summary(self):
        """테스트 결과 요약 출력"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print("\n" + "="*60)
        print("📊 테스트 결과 요약")
        print("="*60)
        print(f"총 테스트: {total_tests}")
        print(f"성공: {passed_tests} ✅")
        print(f"실패: {failed_tests} ❌")
        print(f"성공률: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ 실패한 테스트:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test_name']}: {result['details']}")
        
        # 결과를 파일로 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"organization_router_test_results_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 상세 결과가 {filename}에 저장되었습니다.")


async def main():
    """메인 함수"""
    try:
        async with OrganizationRouterTester() as tester:
            await tester.run_all_tests()
    except KeyboardInterrupt:
        print("\n⚠️ 사용자에 의해 테스트가 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류가 발생했습니다: {str(e)}")
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())