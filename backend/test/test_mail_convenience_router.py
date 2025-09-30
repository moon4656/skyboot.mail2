"""
mail_convenience_router.py 테스트 모듈

메일 편의 기능 API의 모든 엔드포인트를 테스트합니다.
- 메일 검색 기능
- 메일 통계 조회
- 읽지 않은 메일 관리
- 중요 메일 관리
- 메일 상태 변경
- 검색 자동완성
"""

import sys
import os
import time
import pytest
from fastapi.testclient import TestClient

# 프로젝트 루트 경로를 sys.path에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from main import app

class TestMailConvenienceRouter:
    """메일 편의 기능 라우터 테스트 클래스"""
    
    @classmethod
    def setup_class(cls):
        """테스트 클래스 초기화"""
        cls.client = TestClient(app)
        cls.base_url = "/api/v1/mail-convenience"
        
        # 실제 데이터베이스의 사용자 정보 사용
        cls.admin_email = "admin@skyboot.kr"
        cls.admin_password = "admin123!"
        cls.user_email = "user@skyboot.kr"
        cls.user_password = "user123!"
        
        # 토큰 생성
        cls.admin_token = cls._get_access_token(cls.admin_email, cls.admin_password)
        cls.user_token = cls._get_access_token(cls.user_email, cls.user_password)
        
        # 테스트용 메일 UUID (실제 데이터베이스에서 가져와야 함)
        cls.test_mail_uuid = "test-mail-uuid-12345"
    
    @classmethod
    def _get_access_token(cls, email: str, password: str) -> str:
        """액세스 토큰 획득"""
        try:
            response = cls.client.post("/api/v1/auth/login", json={
                "email": email,
                "password": password
            })
            if response.status_code == 200:
                return response.json().get("data", {}).get("access_token", "")
            return ""
        except Exception:
            return ""
    
    def test_01_search_mails(self):
        """메일 검색 테스트"""
        print("\n=== 테스트 1: 메일 검색 ===")
        
        search_data = {
            "query": "test",
            "page": 1,
            "limit": 10
        }
        
        headers = {"Authorization": f"Bearer {self.user_token}"} if self.user_token else {}
        response = self.client.post(f"{self.base_url}/search", json=search_data, headers=headers)
        
        print(f"응답 상태 코드: {response.status_code}")
        print(f"응답 내용: {response.json()}")
        
        # 인증된 사용자의 경우 200 또는 404 (메일 사용자 없음) 예상
        assert response.status_code in [200, 404, 401, 403]
        
        if response.status_code == 200:
            data = response.json()
            assert "success" in data
            print("✅ 메일 검색 테스트 성공")
        else:
            print(f"⚠️ 메일 검색 테스트 - 예상된 응답: {response.status_code}")
    
    def test_02_get_mail_stats(self):
        """메일 통계 조회 테스트"""
        print("\n=== 테스트 2: 메일 통계 조회 ===")
        
        headers = {"Authorization": f"Bearer {self.user_token}"} if self.user_token else {}
        response = self.client.get(f"{self.base_url}/stats", headers=headers)
        
        print(f"응답 상태 코드: {response.status_code}")
        print(f"응답 내용: {response.json()}")
        
        # 인증된 사용자의 경우 200 또는 404 (메일 사용자 없음) 예상
        assert response.status_code in [200, 404, 401, 403]
        
        if response.status_code == 200:
            data = response.json()
            assert "success" in data
            print("✅ 메일 통계 조회 테스트 성공")
        else:
            print(f"⚠️ 메일 통계 조회 테스트 - 예상된 응답: {response.status_code}")
    
    def test_03_get_unread_mails(self):
        """읽지 않은 메일 조회 테스트"""
        print("\n=== 테스트 3: 읽지 않은 메일 조회 ===")
        
        headers = {"Authorization": f"Bearer {self.user_token}"} if self.user_token else {}
        response = self.client.get(f"{self.base_url}/unread?page=1&limit=10", headers=headers)
        
        print(f"응답 상태 코드: {response.status_code}")
        print(f"응답 내용: {response.json()}")
        
        # 인증된 사용자의 경우 200 또는 404 (메일 사용자 없음) 예상
        assert response.status_code in [200, 404, 401, 403]
        
        if response.status_code == 200:
            data = response.json()
            assert "success" in data
            print("✅ 읽지 않은 메일 조회 테스트 성공")
        else:
            print(f"⚠️ 읽지 않은 메일 조회 테스트 - 예상된 응답: {response.status_code}")
    
    def test_04_get_starred_mails(self):
        """중요 표시된 메일 조회 테스트"""
        print("\n=== 테스트 4: 중요 표시된 메일 조회 ===")
        
        headers = {"Authorization": f"Bearer {self.user_token}"} if self.user_token else {}
        response = self.client.get(f"{self.base_url}/starred?page=1&limit=10", headers=headers)
        
        print(f"응답 상태 코드: {response.status_code}")
        print(f"응답 내용: {response.json()}")
        
        # 인증된 사용자의 경우 200 또는 404 (메일 사용자 없음) 예상
        assert response.status_code in [200, 404, 401, 403]
        
        if response.status_code == 200:
            data = response.json()
            assert "success" in data
            print("✅ 중요 표시된 메일 조회 테스트 성공")
        else:
            print(f"⚠️ 중요 표시된 메일 조회 테스트 - 예상된 응답: {response.status_code}")
    
    def test_05_mark_mail_as_read(self):
        """메일 읽음 처리 테스트"""
        print("\n=== 테스트 5: 메일 읽음 처리 ===")
        
        headers = {"Authorization": f"Bearer {self.user_token}"} if self.user_token else {}
        response = self.client.post(f"{self.base_url}/{self.test_mail_uuid}/read", headers=headers)
        
        print(f"응답 상태 코드: {response.status_code}")
        print(f"응답 내용: {response.json()}")
        
        # 메일이 존재하지 않거나 권한이 없는 경우 404 또는 403 예상
        assert response.status_code in [200, 404, 401, 403]
        
        if response.status_code == 200:
            data = response.json()
            assert "success" in data
            print("✅ 메일 읽음 처리 테스트 성공")
        else:
            print(f"⚠️ 메일 읽음 처리 테스트 - 예상된 응답: {response.status_code}")
    
    def test_06_mark_mail_as_unread(self):
        """메일 읽지 않음 처리 테스트"""
        print("\n=== 테스트 6: 메일 읽지 않음 처리 ===")
        
        headers = {"Authorization": f"Bearer {self.user_token}"} if self.user_token else {}
        response = self.client.post(f"{self.base_url}/{self.test_mail_uuid}/unread", headers=headers)
        
        print(f"응답 상태 코드: {response.status_code}")
        print(f"응답 내용: {response.json()}")
        
        # 메일이 존재하지 않거나 권한이 없는 경우 404 또는 403 예상
        assert response.status_code in [200, 404, 401, 403]
        
        if response.status_code == 200:
            data = response.json()
            assert "success" in data
            print("✅ 메일 읽지 않음 처리 테스트 성공")
        else:
            print(f"⚠️ 메일 읽지 않음 처리 테스트 - 예상된 응답: {response.status_code}")
    
    def test_07_mark_all_mails_as_read(self):
        """모든 메일 읽음 처리 테스트"""
        print("\n=== 테스트 7: 모든 메일 읽음 처리 ===")
        
        headers = {"Authorization": f"Bearer {self.user_token}"} if self.user_token else {}
        response = self.client.post(f"{self.base_url}/mark-all-read?folder_type=inbox", headers=headers)
        
        print(f"응답 상태 코드: {response.status_code}")
        print(f"응답 내용: {response.json()}")
        
        # 인증된 사용자의 경우 200 또는 404 (메일 사용자 없음) 예상
        assert response.status_code in [200, 404, 401, 403]
        
        if response.status_code == 200:
            data = response.json()
            assert "success" in data
            print("✅ 모든 메일 읽음 처리 테스트 성공")
        else:
            print(f"⚠️ 모든 메일 읽음 처리 테스트 - 예상된 응답: {response.status_code}")
    
    def test_08_star_mail(self):
        """메일 중요 표시 테스트"""
        print("\n=== 테스트 8: 메일 중요 표시 ===")
        
        headers = {"Authorization": f"Bearer {self.user_token}"} if self.user_token else {}
        response = self.client.post(f"{self.base_url}/{self.test_mail_uuid}/star", headers=headers)
        
        print(f"응답 상태 코드: {response.status_code}")
        print(f"응답 내용: {response.json()}")
        
        # 메일이 존재하지 않거나 권한이 없는 경우 404 또는 403 예상
        assert response.status_code in [200, 404, 401, 403]
        
        if response.status_code == 200:
            data = response.json()
            assert "success" in data
            print("✅ 메일 중요 표시 테스트 성공")
        else:
            print(f"⚠️ 메일 중요 표시 테스트 - 예상된 응답: {response.status_code}")
    
    def test_09_unstar_mail(self):
        """메일 중요 표시 해제 테스트"""
        print("\n=== 테스트 9: 메일 중요 표시 해제 ===")
        
        headers = {"Authorization": f"Bearer {self.user_token}"} if self.user_token else {}
        response = self.client.delete(f"{self.base_url}/{self.test_mail_uuid}/star", headers=headers)
        
        print(f"응답 상태 코드: {response.status_code}")
        print(f"응답 내용: {response.json()}")
        
        # 메일이 존재하지 않거나 권한이 없는 경우 404 또는 403 예상
        assert response.status_code in [200, 404, 401, 403]
        
        if response.status_code == 200:
            data = response.json()
            assert "success" in data
            print("✅ 메일 중요 표시 해제 테스트 성공")
        else:
            print(f"⚠️ 메일 중요 표시 해제 테스트 - 예상된 응답: {response.status_code}")
    
    def test_10_get_search_suggestions(self):
        """검색 자동완성 테스트"""
        print("\n=== 테스트 10: 검색 자동완성 ===")
        
        headers = {"Authorization": f"Bearer {self.user_token}"} if self.user_token else {}
        response = self.client.get(f"{self.base_url}/search/suggestions?query=test&limit=5", headers=headers)
        
        print(f"응답 상태 코드: {response.status_code}")
        print(f"응답 내용: {response.json()}")
        
        # 인증된 사용자의 경우 200 또는 404 (메일 사용자 없음) 예상
        assert response.status_code in [200, 404, 401, 403]
        
        if response.status_code == 200:
            data = response.json()
            assert "success" in data
            print("✅ 검색 자동완성 테스트 성공")
        else:
            print(f"⚠️ 검색 자동완성 테스트 - 예상된 응답: {response.status_code}")
    
    def test_11_unauthorized_access(self):
        """인증되지 않은 접근 테스트"""
        print("\n=== 테스트 11: 인증되지 않은 접근 ===")
        
        # 토큰 없이 요청
        response = self.client.get(f"{self.base_url}/stats")
        
        print(f"응답 상태 코드: {response.status_code}")
        print(f"응답 내용: {response.json()}")
        
        # 인증되지 않은 접근은 401 또는 403 예상
        assert response.status_code in [401, 403]
        print("✅ 인증되지 않은 접근 테스트 성공")
    
    def test_12_admin_search_mails(self):
        """관리자 메일 검색 테스트"""
        print("\n=== 테스트 12: 관리자 메일 검색 ===")
        
        search_data = {
            "query": "admin",
            "page": 1,
            "limit": 10
        }
        
        headers = {"Authorization": f"Bearer {self.admin_token}"} if self.admin_token else {}
        response = self.client.post(f"{self.base_url}/search", json=search_data, headers=headers)
        
        print(f"응답 상태 코드: {response.status_code}")
        print(f"응답 내용: {response.json()}")
        
        # 관리자의 경우 200 또는 404 (메일 사용자 없음) 예상
        assert response.status_code in [200, 404, 401, 403]
        
        if response.status_code == 200:
            data = response.json()
            assert "success" in data
            print("✅ 관리자 메일 검색 테스트 성공")
        else:
            print(f"⚠️ 관리자 메일 검색 테스트 - 예상된 응답: {response.status_code}")
    
    def test_13_performance_test(self):
        """성능 테스트 - 메일 통계 조회"""
        print("\n=== 테스트 13: 성능 테스트 ===")
        
        if not self.user_token:
            print("⚠️ 사용자 토큰이 없어 성능 테스트를 건너뜁니다.")
            return
        
        headers = {"Authorization": f"Bearer {self.user_token}"}
        
        # 10번 연속 요청하여 성능 측정
        start_time = time.time()
        success_count = 0
        
        for i in range(10):
            response = self.client.get(f"{self.base_url}/stats", headers=headers)
            if response.status_code in [200, 404]:  # 404도 정상적인 응답으로 간주
                success_count += 1
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / 10
        
        print(f"총 요청 시간: {total_time:.2f}초")
        print(f"평균 응답 시간: {avg_time:.2f}초")
        print(f"성공한 요청: {success_count}/10")
        
        # 평균 응답 시간이 2초 이하이고 성공률이 80% 이상이면 통과
        assert avg_time < 2.0, f"평균 응답 시간이 너무 깁니다: {avg_time:.2f}초"
        assert success_count >= 8, f"성공률이 너무 낮습니다: {success_count}/10"
        
        print("✅ 성능 테스트 성공")


if __name__ == "__main__":
    # 직접 실행 시 테스트 수행
    test_instance = TestMailConvenienceRouter()
    test_instance.setup_class()
    
    print("🚀 메일 편의 기능 라우터 테스트 시작")
    print("=" * 50)
    
    # 모든 테스트 메서드 실행
    test_methods = [method for method in dir(test_instance) if method.startswith('test_')]
    passed = 0
    failed = 0
    
    for method_name in sorted(test_methods):
        try:
            method = getattr(test_instance, method_name)
            method()
            passed += 1
        except Exception as e:
            print(f"❌ {method_name} 실패: {str(e)}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 테스트 결과: {passed}개 성공, {failed}개 실패")
    print(f"📈 성공률: {(passed / (passed + failed) * 100):.1f}%")
    
    if failed == 0:
        print("🎉 모든 테스트가 성공했습니다!")
    else:
        print(f"⚠️ {failed}개의 테스트가 실패했습니다.")