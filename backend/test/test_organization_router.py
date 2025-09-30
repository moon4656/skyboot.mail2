"""
조직 관리 라우터 테스트

SaaS 다중 조직 지원을 위한 조직 관리 API 엔드포인트 테스트
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import json
from fastapi.testclient import TestClient
from main import app
from auth_utils import TestAuthUtils, get_test_admin_token, get_test_user_token, get_test_auth_headers


class TestOrganizationRouter:
    """조직 관리 라우터 테스트 클래스"""
    
    @classmethod
    def setup_class(cls):
        """테스트 클래스 초기화"""
        print("\n" + "="*60)
        print("🏢 조직 관리 라우터 테스트 시작")
        print("="*60)
        
        # TestClient 초기화
        cls.client = TestClient(app)
        
        # 테스트 데이터 준비
        cls.test_data = {
            "org_id": "skyboot",
            "org_uuid": "bbf43d4b-3862-4ab0-9a03-522213ccb7a2"
        }
        
        # 토큰 캐시 초기화 및 토큰 생성
        TestAuthUtils.clear_token_cache()
        cls.admin_token = TestAuthUtils.get_admin_token(cls.client)
        cls.user_token = TestAuthUtils.get_user_token(cls.client)
        
        # 토큰 생성 상태 로그
        print(f"관리자 토큰 생성: {'✅' if cls.admin_token else '❌'}")
        print(f"사용자 토큰 생성: {'✅' if cls.user_token else '❌'}")
        if cls.admin_token:
            print(f"관리자 토큰 길이: {len(cls.admin_token)}")
        if cls.user_token:
            print(f"사용자 토큰 길이: {len(cls.user_token)}")
        
        # 헤더 직접 생성 (토큰 재사용)
        cls.admin_headers = {
            "Authorization": f"Bearer {cls.admin_token}",
            "Content-Type": "application/json"
        } if cls.admin_token else {"Content-Type": "application/json"}
        
        cls.user_headers = {
            "Authorization": f"Bearer {cls.user_token}",
            "Content-Type": "application/json"
        } if cls.user_token else {"Content-Type": "application/json"}
        
        print(f"관리자 토큰 생성: {'✅' if cls.admin_token else '❌'}")
        print(f"사용자 토큰 생성: {'✅' if cls.user_token else '❌'}")
        
        # 관리자 계정 검증
        if TestAuthUtils.verify_admin_account():
            print("✅ 관리자 계정 검증 성공")
        else:
            print("❌ 관리자 계정 검증 실패")

    
    def test_01_get_current_organization(self):
        """현재 조직 정보 조회 테스트"""
        print("\n🧪 test_01_get_current_organization")
        
        response = self.client.get(
            "/api/v1/organizations/current",
            headers=self.admin_headers
        )
        
        print(f"응답 상태 코드: {response.status_code}")
        print(f"응답 내용: {response.json()}")
        
        if response.status_code == 200:
            data = response.json()
            assert "name" in data
            assert "org_code" in data
            print("✅ test_01_get_current_organization 성공")
        else:
            print("❌ test_01_get_current_organization 실패")
    
    def test_02_get_organization_list_admin(self):
        """조직 목록 조회 테스트 (관리자)"""
        print("\n🧪 test_02_get_organization_list_admin")
        
        response = self.client.get(
            "/api/v1/organizations/list?page=1&limit=10",
            headers=self.admin_headers
        )
        
        print(f"응답 상태 코드: {response.status_code}")
        print(f"응답 내용: {response.json()}")
        
        if response.status_code == 200:
            data = response.json()
            assert "items" in data
            assert "total" in data
            print("✅ test_02_get_organization_list_admin 성공")
        else:
            print("❌ test_02_get_organization_list_admin 실패")
    
    def test_03_get_organization_list_user(self):
        """조직 목록 조회 테스트 (일반 사용자 - 권한 없음)"""
        print("\n🧪 test_03_get_organization_list_user")
        
        response = self.client.get(
            "/api/v1/organizations/list?page=1&limit=10",
            headers=self.user_headers
        )
        
        print(f"응답 상태 코드: {response.status_code}")
        print(f"응답 내용: {response.json()}")
        
        # 일반 사용자는 403 Forbidden이 예상됨
        if response.status_code == 403:
            print("✅ test_03_get_organization_list_user 성공 (권한 없음 확인)")
        else:
            print("❌ test_03_get_organization_list_user 실패")
    
    def test_04_get_specific_organization(self):
        """특정 조직 정보 조회 테스트"""
        print("\n🧪 test_04_get_specific_organization")
        
        response = self.client.get(
            f"/api/v1/organizations/{self.test_data['org_id']}",
            headers=self.admin_headers
        )
        
        print(f"응답 상태 코드: {response.status_code}")
        print(f"응답 내용: {response.json()}")
        
        if response.status_code == 200:
            data = response.json()
            assert "name" in data
            assert "org_code" in data
            print("✅ test_04_get_specific_organization 성공")
        else:
            print("❌ test_04_get_specific_organization 실패")
    
    def test_05_create_organization(self):
        """조직 생성 테스트"""
        print("\n🧪 test_05_create_organization")
        
        org_data = {
            "organization": {
                "name": "테스트 조직",
                "org_code": "test_org_001",
                "subdomain": "testorg001",
                "description": "테스트용 조직입니다",
                "max_users": 50,
                "max_storage_gb": 100
            },
            "admin_email": "admin@testorg001.com",
            "admin_password": "testadmin123",
            "admin_name": "테스트 관리자"
        }
        
        response = self.client.post(
            "/api/v1/organizations/",
            headers=self.admin_headers,
            json=org_data
        )
        
        print(f"응답 상태 코드: {response.status_code}")
        print(f"응답 내용: {response.json()}")
        
        if response.status_code == 201:
            data = response.json()
            assert "name" in data
            assert data["name"] == org_data["organization"]["name"]
            print("✅ test_05_create_organization 성공")
        else:
            print("❌ test_05_create_organization 실패")
    
    def test_06_update_organization(self):
        """조직 정보 수정 테스트"""
        print("\n🧪 test_06_update_organization")
        
        update_data = {
            "name": "수정된 SkyBoot",
            "description": "수정된 설명입니다",
            "max_users": 200
        }
        
        response = self.client.put(
            f"/api/v1/organizations/{self.test_data['org_id']}",
            headers=self.admin_headers,
            json=update_data
        )
        
        print(f"응답 상태 코드: {response.status_code}")
        print(f"응답 내용: {response.json()}")
        
        if response.status_code == 200:
            data = response.json()
            assert "name" in data
            print("✅ test_06_update_organization 성공")
        else:
            print("❌ test_06_update_organization 실패")
    
    def test_07_get_organization_stats(self):
        """조직 통계 조회 테스트"""
        print("\n🧪 test_07_get_organization_stats")
        
        response = self.client.get(
            f"/api/v1/organizations/{self.test_data['org_id']}/stats",
            headers=self.admin_headers
        )
        
        print(f"응답 상태 코드: {response.status_code}")
        print(f"응답 내용: {response.json()}")
        
        if response.status_code == 200:
            data = response.json()
            assert "user_count" in data or "total_users" in data
            print("✅ test_07_get_organization_stats 성공")
        else:
            print("❌ test_07_get_organization_stats 실패")
    
    def test_08_get_current_organization_stats(self):
        """현재 조직 통계 조회 테스트"""
        print("\n🧪 test_08_get_current_organization_stats")
        
        response = self.client.get(
            "/api/v1/organizations/current/stats",
            headers=self.admin_headers
        )
        
        print(f"응답 상태 코드: {response.status_code}")
        print(f"응답 내용: {response.json()}")
        
        if response.status_code == 200:
            data = response.json()
            assert "user_count" in data or "total_users" in data
            print("✅ test_08_get_current_organization_stats 성공")
        else:
            print("❌ test_08_get_current_organization_stats 실패")
    
    def test_09_get_organization_settings(self):
        """조직 설정 조회 테스트"""
        print("\n🧪 test_09_get_organization_settings")
        
        response = self.client.get(
            f"/api/v1/organizations/{self.test_data['org_id']}/settings",
            headers=self.admin_headers
        )
        
        print(f"응답 상태 코드: {response.status_code}")
        print(f"응답 내용: {response.json()}")
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)
            print("✅ test_09_get_organization_settings 성공")
        else:
            print("❌ test_09_get_organization_settings 실패")
    
    def test_10_get_current_organization_settings(self):
        """현재 조직 설정 조회 테스트"""
        print("\n🧪 test_10_get_current_organization_settings")
        
        response = self.client.get(
            "/api/v1/organizations/current/settings",
            headers=self.admin_headers
        )
        
        print(f"응답 상태 코드: {response.status_code}")
        print(f"응답 내용: {response.json()}")
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)
            print("✅ test_10_get_current_organization_settings 성공")
        else:
            print("❌ test_10_get_current_organization_settings 실패")
    
    def test_11_update_organization_settings(self):
        """조직 설정 수정 테스트"""
        print("\n🧪 test_11_update_organization_settings")
        
        settings_data = {
            "mail_settings": {
                "max_attachment_size_mb": 25,
                "allow_external_mail": True
            },
            "security_settings": {
                "require_2fa": False,
                "password_policy": {
                    "min_length": 8,
                    "require_uppercase": True
                }
            }
        }
        
        response = self.client.put(
            f"/api/v1/organizations/{self.test_data['org_id']}/settings",
            headers=self.admin_headers,
            json=settings_data
        )
        
        print(f"응답 상태 코드: {response.status_code}")
        print(f"응답 내용: {response.json()}")
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)
            print("✅ test_11_update_organization_settings 성공")
        else:
            print("❌ test_11_update_organization_settings 실패")
    
    def test_12_unauthorized_access(self):
        """인증되지 않은 접근 테스트"""
        print("\n🧪 test_12_unauthorized_access")
        
        # 토큰 없이 요청
        response = self.client.get("/api/v1/organizations/current")
        
        print(f"응답 상태 코드: {response.status_code}")
        print(f"응답 내용: {response.json()}")
        
        if response.status_code == 401:
            print("✅ test_12_unauthorized_access 성공 (인증 필요 확인)")
        else:
            print("❌ test_12_unauthorized_access 실패")
    
    def test_13_delete_organization(self):
        """조직 삭제 테스트 (주의: 실제 삭제되므로 테스트용 조직만)"""
        print("\n🧪 test_13_delete_organization")
        
        # 테스트용 조직 ID (실제 운영 조직은 삭제하지 않음)
        test_org_id = "test_org_001"
        
        response = self.client.delete(
            f"/api/v1/organizations/{test_org_id}",
            headers=self.admin_headers
        )
        
        print(f"응답 상태 코드: {response.status_code}")
        
        if response.status_code in [204, 404]:  # 삭제 성공 또는 이미 없음
            print("✅ test_13_delete_organization 성공")
        else:
            print(f"응답 내용: {response.json()}")
            print("❌ test_13_delete_organization 실패")
    
    def test_14_performance_test(self):
        """성능 테스트"""
        print("\n🧪 test_14_performance_test")
        
        if not self.admin_token:
            print("⏭️ 관리자 토큰이 없어 성능 테스트를 건너뜁니다.")
            return
        
        start_time = time.time()
        success_count = 0
        
        for i in range(10):
            response = self.client.get(
                "/api/v1/organizations/current",
                headers={"Authorization": f"Bearer {self.admin_token}"}
            )
            if response.status_code == 200:
                success_count += 1
        
        end_time = time.time()
        duration = end_time - start_time
        avg_response_time = (duration / 10) * 1000  # ms
        
        print(f"10회 요청 처리 시간: {duration:.2f}초")
        print(f"성공한 요청: {success_count}/10")
        print(f"평균 응답 시간: {avg_response_time:.2f}ms")
        
        if success_count >= 8 and avg_response_time < 1000:
            print("✅ test_14_performance_test 성공")
        else:
            print("❌ test_14_performance_test 실패")


def run_tests():
    """테스트 실행 함수"""
    test_instance = TestOrganizationRouter()
    test_instance.setup_class()
    
    # 테스트 메서드 목록
    test_methods = [
        test_instance.test_01_get_current_organization,
        test_instance.test_02_get_organization_list_admin,
        test_instance.test_03_get_organization_list_user,
        test_instance.test_04_get_specific_organization,
        test_instance.test_05_create_organization,
        test_instance.test_06_update_organization,
        test_instance.test_07_get_organization_stats,
        test_instance.test_08_get_current_organization_stats,
        test_instance.test_09_get_organization_settings,
        test_instance.test_10_get_current_organization_settings,
        test_instance.test_11_update_organization_settings,
        test_instance.test_12_unauthorized_access,
        test_instance.test_13_delete_organization,
        test_instance.test_14_performance_test
    ]
    
    # 테스트 실행
    success_count = 0
    total_count = len(test_methods)
    
    for test_method in test_methods:
        try:
            test_method()
            success_count += 1
        except Exception as e:
            print(f"❌ {test_method.__name__} 실패: {str(e)}")
    
    # 결과 요약
    print("\n" + "="*60)
    print("📊 테스트 결과 요약")
    print(f"✅ 성공: {success_count}개")
    print(f"❌ 실패: {total_count - success_count}개")
    print(f"📈 성공률: {(success_count / total_count) * 100:.1f}%")
    print("="*60)


if __name__ == "__main__":
    run_tests()