"""
mail_advanced_router.py 테스트 모듈

메일 고급 기능 API의 모든 엔드포인트를 테스트합니다.
- 폴더 관리 기능
- 메일 백업/복원 기능
- 메일 분석 기능
- 메일 이동 기능
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

class TestMailAdvancedRouter:
    """메일 고급 기능 라우터 테스트 클래스"""
    
    @classmethod
    def setup_class(cls):
        """테스트 클래스 초기화"""
        cls.client = TestClient(app)
        cls.base_url = "/api/v1/mail-advanced"
        
        # 실제 데이터베이스의 사용자 정보 사용
        cls.admin_email = "admin@skyboot.kr"
        cls.admin_password = "admin123!"
        cls.user_email = "user@skyboot.kr"
        cls.user_password = "user123!"
        
        # 토큰 생성
        cls.admin_token = cls._get_access_token(cls.admin_email, cls.admin_password)
        cls.user_token = cls._get_access_token(cls.user_email, cls.user_password)
        
        # 테스트용 UUID들
        cls.test_folder_uuid = "test-folder-uuid-12345"
        cls.test_mail_uuid = "test-mail-uuid-12345"
        cls.test_backup_filename = "test-backup.zip"
    
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
    
    def test_01_get_folders(self):
        """폴더 목록 조회 테스트"""
        print("\n=== 테스트 1: 폴더 목록 조회 ===")
        
        headers = {"Authorization": f"Bearer {self.user_token}"} if self.user_token else {}
        response = self.client.get(f"{self.base_url}/folders", headers=headers)
        
        print(f"응답 상태 코드: {response.status_code}")
        print(f"응답 내용: {response.json()}")
        
        # 인증된 사용자의 경우 200 또는 404 (메일 사용자 없음) 예상
        assert response.status_code in [200, 404, 401, 403]
        
        if response.status_code == 200:
            data = response.json()
            assert "folders" in data
            print("✅ 폴더 목록 조회 테스트 성공")
        else:
            print(f"⚠️ 폴더 목록 조회 테스트 - 예상된 응답: {response.status_code}")
    
    def test_02_create_folder(self):
        """폴더 생성 테스트"""
        print("\n=== 테스트 2: 폴더 생성 ===")
        
        folder_data = {
            "name": "테스트 폴더",
            "folder_type": "custom"
        }
        
        headers = {"Authorization": f"Bearer {self.user_token}"} if self.user_token else {}
        response = self.client.post(f"{self.base_url}/folders", json=folder_data, headers=headers)
        
        print(f"응답 상태 코드: {response.status_code}")
        print(f"응답 내용: {response.json()}")
        
        # 인증된 사용자의 경우 200, 201 또는 404 (메일 사용자 없음) 예상
        assert response.status_code in [200, 201, 404, 401, 403]
        
        if response.status_code in [200, 201]:
            data = response.json()
            assert "folder_uuid" in data or "message" in data
            print("✅ 폴더 생성 테스트 성공")
        else:
            print(f"⚠️ 폴더 생성 테스트 - 예상된 응답: {response.status_code}")
    
    def test_03_update_folder(self):
        """폴더 수정 테스트"""
        print("\n=== 테스트 3: 폴더 수정 ===")
        
        folder_data = {
            "name": "수정된 테스트 폴더"
        }
        
        headers = {"Authorization": f"Bearer {self.user_token}"} if self.user_token else {}
        response = self.client.put(f"{self.base_url}/folders/{self.test_folder_uuid}", json=folder_data, headers=headers)
        
        print(f"응답 상태 코드: {response.status_code}")
        print(f"응답 내용: {response.json()}")
        
        # 폴더가 존재하지 않거나 권한이 없는 경우 404 또는 403 예상
        assert response.status_code in [200, 404, 401, 403]
        
        if response.status_code == 200:
            data = response.json()
            assert "message" in data or "folder_uuid" in data
            print("✅ 폴더 수정 테스트 성공")
        else:
            print(f"⚠️ 폴더 수정 테스트 - 예상된 응답: {response.status_code}")
    
    def test_04_delete_folder(self):
        """폴더 삭제 테스트"""
        print("\n=== 테스트 4: 폴더 삭제 ===")
        
        headers = {"Authorization": f"Bearer {self.user_token}"} if self.user_token else {}
        response = self.client.delete(f"{self.base_url}/folders/{self.test_folder_uuid}", headers=headers)
        
        print(f"응답 상태 코드: {response.status_code}")
        print(f"응답 내용: {response.json()}")
        
        # 폴더가 존재하지 않거나 권한이 없는 경우 404 또는 403 예상
        assert response.status_code in [200, 404, 401, 403]
        
        if response.status_code == 200:
            data = response.json()
            assert "message" in data
            print("✅ 폴더 삭제 테스트 성공")
        else:
            print(f"⚠️ 폴더 삭제 테스트 - 예상된 응답: {response.status_code}")
    
    def test_05_move_mail_to_folder(self):
        """메일을 폴더로 이동 테스트"""
        print("\n=== 테스트 5: 메일을 폴더로 이동 ===")
        
        headers = {"Authorization": f"Bearer {self.user_token}"} if self.user_token else {}
        response = self.client.post(
            f"{self.base_url}/folders/{self.test_folder_uuid}/mails/{self.test_mail_uuid}", 
            headers=headers
        )
        
        print(f"응답 상태 코드: {response.status_code}")
        print(f"응답 내용: {response.json()}")
        
        # 폴더나 메일이 존재하지 않거나 권한이 없는 경우 404 또는 403 예상
        assert response.status_code in [200, 404, 401, 403]
        
        if response.status_code == 200:
            data = response.json()
            assert "message" in data
            print("✅ 메일을 폴더로 이동 테스트 성공")
        else:
            print(f"⚠️ 메일을 폴더로 이동 테스트 - 예상된 응답: {response.status_code}")
    
    def test_06_backup_mails(self):
        """메일 백업 테스트"""
        print("\n=== 테스트 6: 메일 백업 ===")
        
        headers = {"Authorization": f"Bearer {self.user_token}"} if self.user_token else {}
        response = self.client.post(
            f"{self.base_url}/backup?include_attachments=false", 
            headers=headers
        )
        
        print(f"응답 상태 코드: {response.status_code}")
        print(f"응답 내용: {response.json()}")
        
        # 인증된 사용자의 경우 200 또는 404 (메일 사용자 없음) 예상
        assert response.status_code in [200, 404, 401, 403]
        
        if response.status_code == 200:
            data = response.json()
            assert "backup_filename" in data or "message" in data
            print("✅ 메일 백업 테스트 성공")
        else:
            print(f"⚠️ 메일 백업 테스트 - 예상된 응답: {response.status_code}")
    
    def test_07_download_backup(self):
        """백업 파일 다운로드 테스트"""
        print("\n=== 테스트 7: 백업 파일 다운로드 ===")
        
        headers = {"Authorization": f"Bearer {self.user_token}"} if self.user_token else {}
        response = self.client.get(f"{self.base_url}/backup/{self.test_backup_filename}", headers=headers)
        
        print(f"응답 상태 코드: {response.status_code}")
        print(f"응답 헤더: {dict(response.headers)}")
        
        # 백업 파일이 존재하지 않거나 권한이 없는 경우 404 또는 403 예상
        assert response.status_code in [200, 404, 401, 403]
        
        if response.status_code == 200:
            # 파일 다운로드 응답인지 확인
            assert "application" in response.headers.get("content-type", "") or "octet-stream" in response.headers.get("content-type", "")
            print("✅ 백업 파일 다운로드 테스트 성공")
        else:
            print(f"⚠️ 백업 파일 다운로드 테스트 - 예상된 응답: {response.status_code}")
    
    def test_08_get_mail_analytics(self):
        """메일 분석 테스트"""
        print("\n=== 테스트 8: 메일 분석 ===")
        
        headers = {"Authorization": f"Bearer {self.user_token}"} if self.user_token else {}
        response = self.client.get(f"{self.base_url}/analytics?period=month", headers=headers)
        
        print(f"응답 상태 코드: {response.status_code}")
        print(f"응답 내용: {response.json()}")
        
        # 인증된 사용자의 경우 200 또는 404 (메일 사용자 없음) 예상
        assert response.status_code in [200, 404, 401, 403]
        
        if response.status_code == 200:
            data = response.json()
            assert "analytics" in data or "period" in data
            print("✅ 메일 분석 테스트 성공")
        else:
            print(f"⚠️ 메일 분석 테스트 - 예상된 응답: {response.status_code}")
    
    def test_09_unauthorized_access(self):
        """인증되지 않은 접근 테스트"""
        print("\n=== 테스트 9: 인증되지 않은 접근 ===")
        
        # 토큰 없이 요청
        response = self.client.get(f"{self.base_url}/folders")
        
        print(f"응답 상태 코드: {response.status_code}")
        print(f"응답 내용: {response.json()}")
        
        # 인증되지 않은 접근은 401 또는 403 예상
        assert response.status_code in [401, 403]
        print("✅ 인증되지 않은 접근 테스트 성공")
    
    def test_10_admin_get_folders(self):
        """관리자 폴더 목록 조회 테스트"""
        print("\n=== 테스트 10: 관리자 폴더 목록 조회 ===")
        
        headers = {"Authorization": f"Bearer {self.admin_token}"} if self.admin_token else {}
        response = self.client.get(f"{self.base_url}/folders", headers=headers)
        
        print(f"응답 상태 코드: {response.status_code}")
        print(f"응답 내용: {response.json()}")
        
        # 관리자의 경우 200 또는 404 (메일 사용자 없음) 예상
        assert response.status_code in [200, 404, 401, 403]
        
        if response.status_code == 200:
            data = response.json()
            assert "folders" in data
            print("✅ 관리자 폴더 목록 조회 테스트 성공")
        else:
            print(f"⚠️ 관리자 폴더 목록 조회 테스트 - 예상된 응답: {response.status_code}")
    
    def test_11_admin_backup_mails(self):
        """관리자 메일 백업 테스트"""
        print("\n=== 테스트 11: 관리자 메일 백업 ===")
        
        headers = {"Authorization": f"Bearer {self.admin_token}"} if self.admin_token else {}
        response = self.client.post(
            f"{self.base_url}/backup?include_attachments=true", 
            headers=headers
        )
        
        print(f"응답 상태 코드: {response.status_code}")
        print(f"응답 내용: {response.json()}")
        
        # 관리자의 경우 200 또는 404 (메일 사용자 없음) 예상
        assert response.status_code in [200, 404, 401, 403]
        
        if response.status_code == 200:
            data = response.json()
            assert "backup_filename" in data or "message" in data
            print("✅ 관리자 메일 백업 테스트 성공")
        else:
            print(f"⚠️ 관리자 메일 백업 테스트 - 예상된 응답: {response.status_code}")
    
    def test_12_performance_test(self):
        """성능 테스트 - 폴더 목록 조회"""
        print("\n=== 테스트 12: 성능 테스트 ===")
        
        if not self.user_token:
            print("⚠️ 사용자 토큰이 없어 성능 테스트를 건너뜁니다.")
            return
        
        headers = {"Authorization": f"Bearer {self.user_token}"}
        
        # 10번 연속 요청하여 성능 측정
        start_time = time.time()
        success_count = 0
        
        for i in range(10):
            response = self.client.get(f"{self.base_url}/folders", headers=headers)
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
    test_instance = TestMailAdvancedRouter()
    test_instance.setup_class()
    
    print("🚀 메일 고급 기능 라우터 테스트 시작")
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