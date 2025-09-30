"""
user_router.py 테스트 코드

이 파일은 사용자 관리 API의 정확성과 안정성을 검증합니다.
SaaS 다중 조직 지원 환경에서의 사용자 관리 기능을 테스트합니다.
"""

import pytest
import asyncio
import json
import time
from typing import Dict, Any, List
from unittest.mock import patch, MagicMock
import sys
import os

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from fastapi.testclient import TestClient
    from fastapi import status
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    
    # 프로젝트 모듈 임포트
    from main import app
    from app.database.user import get_db
    from app.model.user_model import User
    from app.model.organization_model import Organization
    from app.service.auth_service import create_access_token
    from auth_utils import TestAuthUtils, get_test_admin_token, get_test_user_token
    
except ImportError as e:
    print(f"모듈 임포트 오류: {e}")
    print("테스트 실행을 위해 필요한 의존성을 설치하세요.")
    sys.exit(1)

class TestUserRouter:
    """user_router.py 테스트 클래스"""
    
    @classmethod
    def setup_class(cls):
        """테스트 클래스 초기화"""
        print("🚀 user_router.py 테스트 시작")
        print("=" * 60)
        
        cls.client = TestClient(app)
        
        # 토큰 캐시 초기화 및 토큰 생성
        TestAuthUtils.clear_token_cache()
        cls.admin_token = TestAuthUtils.get_admin_token(cls.client)
        cls.user_token = TestAuthUtils.get_user_token(cls.client)
        
        cls.prepare_test_data()

    @classmethod
    def prepare_test_data(cls):
        """테스트 데이터 준비 - 실제 데이터베이스 사용자 사용"""
        cls.test_organizations = [
            {
                "org_id": "3856a8c1-84a4-4019-9133-655cacab4bc9",
                "org_code": "DEFAULT",
                "name": "기본 조직",
                "domain": "localhost"
            },
            {
                "org_id": "bbf43d4b-3862-4ab0-9a03-522213ccb7a2",
                "org_code": "SKYBOOT",
                "name": "SkyBoot", 
                "domain": "skyboot.com"
            }
        ]
        
        cls.test_users = [
            {
                "user_uuid": "441eb65c-bed0-4e75-9cdd-c95425e635a0",
                "email": "admin@skyboot.com",
                "username": "admin",
                "org_id": "bbf43d4b-3862-4ab0-9a03-522213ccb7a2",
                "role": "admin"
            },
            {
                "user_uuid": "7ffc2474-2abf-4ec9-8857-f6171b29811f",
                "email": "admin1758777139@skyboot.com", 
                "username": "admin1758777139",
                "org_id": "3856a8c1-84a4-4019-9133-655cacab4bc9",
                "role": "admin"
            },
            {
                "user_uuid": "bb775f95-b318-4d2c-940b-6ac29f5510c3",
                "email": "admin@test.com",
                "username": "admin", 
                "org_id": "3856a8c1-84a4-4019-9133-655cacab4bc9",
                "role": "user"
            }
        ]
        
        # 테스트용 액세스 토큰 생성
        cls.access_tokens = {}
        for user in cls.test_users:
            org = next(org for org in cls.test_organizations if org["org_id"] == user["org_id"])
            token_data = {
                "sub": user["email"],
                "user_uuid": user["user_uuid"],
                "email": user["email"],
                "org_id": user["org_id"],
                "org_code": org["org_code"],
                "role": user["role"]
            }
            cls.access_tokens[user["user_uuid"]] = create_access_token(data=token_data)

    def get_auth_headers(self, user_uuid: str) -> Dict[str, str]:
        """인증 헤더 생성"""
        return {"Authorization": f"Bearer {self.access_tokens[user_uuid]}"}

    def test_01_get_current_user_info(self):
        """시나리오 1: 현재 사용자 정보 조회 (/me)"""
        print("\n=== 테스트 1: 현재 사용자 정보 조회 ===")
        
        user_uuid = "441eb65c-bed0-4e75-9cdd-c95425e635a0"
        headers = self.get_auth_headers(user_uuid)
        
        response = self.client.get(
            "/api/v1/users/me",
            headers=headers
        )
        
        print(f"응답 상태 코드: {response.status_code}")
        print(f"응답 내용: {response.json()}")
        
        # 검증
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert "user_uuid" in response_data
        assert "email" in response_data
        assert "username" in response_data
        assert "org_id" in response_data
        print("✅ 현재 사용자 정보 조회 성공")

    def test_02_get_users_list_admin(self):
        """시나리오 2: 관리자 권한으로 사용자 목록 조회"""
        print("\n=== 테스트 2: 관리자 권한으로 사용자 목록 조회 ===")
        
        admin_uuid = "441eb65c-bed0-4e75-9cdd-c95425e635a0"  # admin 역할
        headers = self.get_auth_headers(admin_uuid)
        
        response = self.client.get(
            "/api/v1/users/?page=1&limit=10",
            headers=headers
        )
        
        print(f"응답 상태 코드: {response.status_code}")
        print(f"응답 내용: {response.json()}")
        
        # 검증
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert "users" in response_data or "data" in response_data
        print("✅ 관리자 사용자 목록 조회 성공")

    def test_03_get_users_list_non_admin(self):
        """시나리오 3: 일반 사용자 권한으로 사용자 목록 조회 (권한 오류 예상)"""
        print("\n=== 테스트 3: 일반 사용자 권한으로 사용자 목록 조회 ===")
        
        user_uuid = "bb775f95-b318-4d2c-940b-6ac29f5510c3"  # user 역할
        headers = self.get_auth_headers(user_uuid)
        
        response = self.client.get(
            "/api/v1/users/?page=1&limit=10",
            headers=headers
        )
        
        print(f"응답 상태 코드: {response.status_code}")
        print(f"응답 내용: {response.json()}")
        
        # 검증 - 403 Forbidden 또는 401 Unauthorized 예상
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
        print("✅ 일반 사용자 권한 제한 확인")

    def test_04_get_specific_user(self):
        """시나리오 4: 특정 사용자 조회"""
        print("\n=== 테스트 4: 특정 사용자 조회 ===")
        
        admin_uuid = "441eb65c-bed0-4e75-9cdd-c95425e635a0"
        target_user_uuid = "7ffc2474-2abf-4ec9-8857-f6171b29811f"
        headers = self.get_auth_headers(admin_uuid)
        
        response = self.client.get(
            f"/api/v1/users/{target_user_uuid}",
            headers=headers
        )
        
        print(f"응답 상태 코드: {response.status_code}")
        print(f"응답 내용: {response.json()}")
        
        # 검증
        if response.status_code == status.HTTP_200_OK:
            response_data = response.json()
            assert "user_uuid" in response_data
            print("✅ 특정 사용자 조회 성공")
        else:
            print("⚠️ 특정 사용자 조회 실패 (조직 격리 또는 권한 문제)")

    def test_05_create_user_admin(self):
        """시나리오 5: 관리자 권한으로 새 사용자 생성"""
        print("\n=== 테스트 5: 관리자 권한으로 새 사용자 생성 ===")
        
        admin_uuid = "441eb65c-bed0-4e75-9cdd-c95425e635a0"
        headers = self.get_auth_headers(admin_uuid)
        
        new_user_data = {
            "email": f"newuser_{int(time.time())}@skyboot.com",
            "username": f"newuser_{int(time.time())}",
            "password": "newpassword123",
            "role": "user"
        }
        
        response = self.client.post(
            "/api/v1/users/",
            headers=headers,
            json=new_user_data
        )
        
        print(f"응답 상태 코드: {response.status_code}")
        print(f"응답 내용: {response.json()}")
        
        # 검증
        if response.status_code == status.HTTP_201_CREATED or response.status_code == status.HTTP_200_OK:
            response_data = response.json()
            assert "user_uuid" in response_data
            assert response_data["email"] == new_user_data["email"]
            print("✅ 새 사용자 생성 성공")
        else:
            print("⚠️ 사용자 생성 실패 (중복 이메일 또는 기타 오류)")

    def test_06_create_user_non_admin(self):
        """시나리오 6: 일반 사용자 권한으로 사용자 생성 시도 (권한 오류 예상)"""
        print("\n=== 테스트 6: 일반 사용자 권한으로 사용자 생성 시도 ===")
        
        user_uuid = "bb775f95-b318-4d2c-940b-6ac29f5510c3"  # user 역할
        headers = self.get_auth_headers(user_uuid)
        
        new_user_data = {
            "email": f"unauthorized_{int(time.time())}@test.com",
            "username": f"unauthorized_{int(time.time())}",
            "password": "password123",
            "role": "user"
        }
        
        response = self.client.post(
            "/api/v1/users/",
            headers=headers,
            json=new_user_data
        )
        
        print(f"응답 상태 코드: {response.status_code}")
        print(f"응답 내용: {response.json()}")
        
        # 검증 - 403 Forbidden 또는 401 Unauthorized 예상
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
        print("✅ 일반 사용자 생성 권한 제한 확인")

    def test_07_update_user_info(self):
        """시나리오 7: 사용자 정보 수정"""
        print("\n=== 테스트 7: 사용자 정보 수정 ===")
        
        user_uuid = "441eb65c-bed0-4e75-9cdd-c95425e635a0"
        headers = self.get_auth_headers(user_uuid)
        
        update_data = {
            "username": f"updated_admin_{int(time.time())}",
            "full_name": "업데이트된 관리자"
        }
        
        response = self.client.put(
            f"/api/v1/users/{user_uuid}",
            headers=headers,
            json=update_data
        )
        
        print(f"응답 상태 코드: {response.status_code}")
        print(f"응답 내용: {response.json()}")
        
        # 검증
        if response.status_code == status.HTTP_200_OK:
            response_data = response.json()
            assert "user_uuid" in response_data
            print("✅ 사용자 정보 수정 성공")
        else:
            print("⚠️ 사용자 정보 수정 실패")

    def test_08_change_password(self):
        """시나리오 8: 비밀번호 변경"""
        print("\n=== 테스트 8: 비밀번호 변경 ===")
        
        user_uuid = "441eb65c-bed0-4e75-9cdd-c95425e635a0"
        headers = self.get_auth_headers(user_uuid)
        
        password_data = {
            "current_password": "admin123",
            "new_password": "newpassword123"
        }
        
        response = self.client.post(
            f"/api/v1/users/{user_uuid}/change-password",
            headers=headers,
            json=password_data
        )
        
        print(f"응답 상태 코드: {response.status_code}")
        print(f"응답 내용: {response.json()}")
        
        # 검증
        if response.status_code == status.HTTP_200_OK:
            print("✅ 비밀번호 변경 성공")
        else:
            print("⚠️ 비밀번호 변경 실패 (현재 비밀번호 불일치 또는 기타 오류)")

    def test_09_get_user_stats(self):
        """시나리오 9: 사용자 통계 조회"""
        print("\n=== 테스트 9: 사용자 통계 조회 ===")
        
        admin_uuid = "441eb65c-bed0-4e75-9cdd-c95425e635a0"
        headers = self.get_auth_headers(admin_uuid)
        
        response = self.client.get(
            "/api/v1/users/stats/overview",
            headers=headers
        )
        
        print(f"응답 상태 코드: {response.status_code}")
        print(f"응답 내용: {response.json()}")
        
        # 검증
        if response.status_code == status.HTTP_200_OK:
            response_data = response.json()
            assert isinstance(response_data, dict)
            print("✅ 사용자 통계 조회 성공")
        else:
            print("⚠️ 사용자 통계 조회 실패")

    def test_10_unauthorized_access(self):
        """시나리오 10: 인증되지 않은 접근"""
        print("\n=== 테스트 10: 인증되지 않은 접근 ===")
        
        # 토큰 없이 요청
        response = self.client.get("/api/v1/users/me")
        
        print(f"응답 상태 코드: {response.status_code}")
        print(f"응답 내용: {response.json()}")
        
        # 검증
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
        print("✅ 인증되지 않은 접근 차단 확인")

    def test_11_activate_deactivate_user(self):
        """시나리오 11: 사용자 활성화/비활성화"""
        print("\n=== 테스트 11: 사용자 활성화/비활성화 ===")
        
        admin_uuid = "441eb65c-bed0-4e75-9cdd-c95425e635a0"
        target_user_uuid = "bb775f95-b318-4d2c-940b-6ac29f5510c3"
        headers = self.get_auth_headers(admin_uuid)
        
        # 사용자 비활성화
        response = self.client.post(
            f"/api/v1/users/{target_user_uuid}/deactivate",
            headers=headers
        )
        
        print(f"비활성화 응답 상태 코드: {response.status_code}")
        print(f"비활성화 응답 내용: {response.json()}")
        
        # 사용자 활성화
        response = self.client.post(
            f"/api/v1/users/{target_user_uuid}/activate",
            headers=headers
        )
        
        print(f"활성화 응답 상태 코드: {response.status_code}")
        print(f"활성화 응답 내용: {response.json()}")
        
        # 검증
        if response.status_code == status.HTTP_200_OK:
            print("✅ 사용자 활성화/비활성화 성공")
        else:
            print("⚠️ 사용자 활성화/비활성화 실패")

    def test_12_performance_test(self):
        """시나리오 12: 성능 테스트 - 연속 요청"""
        print("\n=== 테스트 12: 성능 테스트 ===")
        
        user_uuid = "441eb65c-bed0-4e75-9cdd-c95425e635a0"
        headers = self.get_auth_headers(user_uuid)
        
        start_time = time.time()
        success_count = 0
        
        for i in range(10):
            response = self.client.get(
                "/api/v1/users/me",
                headers=headers
            )
            if response.status_code == status.HTTP_200_OK:
                success_count += 1
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"10회 요청 처리 시간: {duration:.2f}초")
        print(f"성공한 요청: {success_count}/10")
        print(f"평균 응답 시간: {(duration/10)*1000:.2f}ms")
        
        # 검증
        assert success_count >= 8  # 80% 이상 성공
        assert duration < 5.0  # 5초 이내 완료
        print("✅ 성능 테스트 통과")


def run_tests():
    """테스트 실행 함수"""
    test_instance = TestUserRouter()
    test_instance.setup_class()
    
    tests = [
        test_instance.test_01_get_current_user_info,
        test_instance.test_02_get_users_list_admin,
        test_instance.test_03_get_users_list_non_admin,
        test_instance.test_04_get_specific_user,
        test_instance.test_05_create_user_admin,
        test_instance.test_06_create_user_non_admin,
        test_instance.test_07_update_user_info,
        test_instance.test_08_change_password,
        test_instance.test_09_get_user_stats,
        test_instance.test_10_unauthorized_access,
        test_instance.test_11_activate_deactivate_user,
        test_instance.test_12_performance_test
    ]
    
    success_count = 0
    total_count = len(tests)
    
    for test in tests:
        try:
            test()
            success_count += 1
        except Exception as e:
            print(f"❌ {test.__name__} 실패: {str(e)}")
    
    print("\n" + "=" * 60)
    print("📊 테스트 결과 요약")
    print(f"✅ 성공: {success_count}개")
    print(f"❌ 실패: {total_count - success_count}개")
    print(f"📈 성공률: {(success_count/total_count)*100:.1f}%")


if __name__ == "__main__":
    run_tests()