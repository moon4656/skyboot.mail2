"""
User Router 엔드포인트 테스트 스크립트

모든 사용자 관리 API 엔드포인트를 체계적으로 테스트합니다.
"""
import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional

# 테스트 설정
BASE_URL = "http://127.0.0.1:8000"
USER_ROUTER_PREFIX = "/api/v1/users"

class UserRouterTester:
    def __init__(self):
        self.base_url = BASE_URL + USER_ROUTER_PREFIX
        self.admin_token = None
        self.user_token = None
        self.test_results = []
        self.created_user_id = None
        
    def log_test(self, test_name: str, success: bool, details: str = "", response_data: Any = None):
        """테스트 결과 로깅"""
        result = {
            "timestamp": datetime.now().isoformat(),
            "test_name": test_name,
            "success": success,
            "details": details,
            "response_data": response_data
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {details}")
        
    def get_auth_headers(self, token: str) -> Dict[str, str]:
        """인증 헤더 생성"""
        return {"Authorization": f"Bearer {token}"}
    
    def setup_test_tokens(self):
        """테스트용 토큰 설정"""
        print("🔑 테스트용 토큰 설정 중...")
        
        # 관리자 로그인
        admin_login_data = {
            "username": "admin@example.com",
            "password": "admin123"
        }
        
        try:
            response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=admin_login_data)
            if response.status_code == 200:
                self.admin_token = response.json().get("access_token")
                self.log_test("관리자 토큰 획득", True, "관리자 로그인 성공")
            else:
                self.log_test("관리자 토큰 획득", False, f"로그인 실패: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("관리자 토큰 획득", False, f"연결 오류: {str(e)}")
            return False
            
        # 일반 사용자 로그인 (테스트용 사용자가 있다면)
        user_login_data = {
            "username": "user@example.com", 
            "password": "user123"
        }
        
        try:
            response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=user_login_data)
            if response.status_code == 200:
                self.user_token = response.json().get("access_token")
                self.log_test("일반 사용자 토큰 획득", True, "일반 사용자 로그인 성공")
            else:
                self.log_test("일반 사용자 토큰 획득", False, f"로그인 실패: {response.status_code}")
        except Exception as e:
            self.log_test("일반 사용자 토큰 획득", False, f"연결 오류: {str(e)}")
            
        return self.admin_token is not None
    
    def test_create_user(self):
        """사용자 생성 테스트"""
        print("\n📝 사용자 생성 테스트")
        
        # 1. 관리자 권한으로 정상 사용자 생성
        user_data = {
            "email": f"test_user_{int(time.time())}@example.com",
            "username": f"testuser_{int(time.time())}",
            "password": "testpass123",
            "full_name": "테스트 사용자"
        }
        
        try:
            response = requests.post(
                self.base_url + "/",
                json=user_data,
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 200:
                created_user = response.json()
                self.created_user_id = created_user.get("id")
                self.log_test("관리자 권한 사용자 생성", True, f"사용자 ID: {self.created_user_id}")
            else:
                self.log_test("관리자 권한 사용자 생성", False, f"상태코드: {response.status_code}, 응답: {response.text}")
                
        except Exception as e:
            self.log_test("관리자 권한 사용자 생성", False, f"오류: {str(e)}")
        
        # 2. 일반 사용자 권한으로 생성 시도 (403 에러 예상)
        if self.user_token:
            try:
                response = requests.post(
                    self.base_url + "/",
                    json=user_data,
                    headers=self.get_auth_headers(self.user_token)
                )
                
                if response.status_code == 403:
                    self.log_test("일반 사용자 권한 생성 차단", True, "403 Forbidden 정상 반환")
                else:
                    self.log_test("일반 사용자 권한 생성 차단", False, f"예상과 다른 상태코드: {response.status_code}")
                    
            except Exception as e:
                self.log_test("일반 사용자 권한 생성 차단", False, f"오류: {str(e)}")
        
        # 3. 토큰 없이 접근 (401 에러 예상)
        try:
            response = requests.post(self.base_url + "/", json=user_data)
            
            if response.status_code == 401:
                self.log_test("토큰 없이 사용자 생성 차단", True, "401 Unauthorized 정상 반환")
            else:
                self.log_test("토큰 없이 사용자 생성 차단", False, f"예상과 다른 상태코드: {response.status_code}")
                
        except Exception as e:
            self.log_test("토큰 없이 사용자 생성 차단", False, f"오류: {str(e)}")
    
    def test_get_users(self):
        """사용자 목록 조회 테스트"""
        print("\n📋 사용자 목록 조회 테스트")
        
        # 1. 관리자 권한으로 목록 조회
        try:
            response = requests.get(
                self.base_url + "/",
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 200:
                users_data = response.json()
                self.log_test("관리자 권한 사용자 목록 조회", True, f"사용자 수: {len(users_data.get('users', []))}")
            else:
                self.log_test("관리자 권한 사용자 목록 조회", False, f"상태코드: {response.status_code}")
                
        except Exception as e:
            self.log_test("관리자 권한 사용자 목록 조회", False, f"오류: {str(e)}")
        
        # 2. 일반 사용자 권한으로 조회 시도 (403 에러 예상)
        if self.user_token:
            try:
                response = requests.get(
                    self.base_url + "/",
                    headers=self.get_auth_headers(self.user_token)
                )
                
                if response.status_code == 403:
                    self.log_test("일반 사용자 목록 조회 차단", True, "403 Forbidden 정상 반환")
                else:
                    self.log_test("일반 사용자 목록 조회 차단", False, f"예상과 다른 상태코드: {response.status_code}")
                    
            except Exception as e:
                self.log_test("일반 사용자 목록 조회 차단", False, f"오류: {str(e)}")
        
        # 3. 페이지네이션 테스트
        try:
            response = requests.get(
                self.base_url + "/?page=1&limit=5",
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 200:
                self.log_test("페이지네이션 테스트", True, "페이지네이션 파라미터 정상 처리")
            else:
                self.log_test("페이지네이션 테스트", False, f"상태코드: {response.status_code}")
                
        except Exception as e:
            self.log_test("페이지네이션 테스트", False, f"오류: {str(e)}")
    
    def test_get_current_user(self):
        """현재 사용자 정보 조회 테스트"""
        print("\n👤 현재 사용자 정보 조회 테스트")
        
        # 1. 관리자 토큰으로 조회
        try:
            response = requests.get(
                self.base_url + "/me",
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 200:
                user_info = response.json()
                self.log_test("관리자 현재 사용자 정보 조회", True, f"사용자: {user_info.get('email')}")
            else:
                self.log_test("관리자 현재 사용자 정보 조회", False, f"상태코드: {response.status_code}")
                
        except Exception as e:
            self.log_test("관리자 현재 사용자 정보 조회", False, f"오류: {str(e)}")
        
        # 2. 토큰 없이 접근 (401 에러 예상)
        try:
            response = requests.get(self.base_url + "/me")
            
            if response.status_code == 401:
                self.log_test("토큰 없이 현재 사용자 조회 차단", True, "401 Unauthorized 정상 반환")
            else:
                self.log_test("토큰 없이 현재 사용자 조회 차단", False, f"예상과 다른 상태코드: {response.status_code}")
                
        except Exception as e:
            self.log_test("토큰 없이 현재 사용자 조회 차단", False, f"오류: {str(e)}")
    
    def test_get_user_by_id(self):
        """특정 사용자 조회 테스트"""
        print("\n🔍 특정 사용자 조회 테스트")
        
        if not self.created_user_id:
            self.log_test("특정 사용자 조회 테스트", False, "테스트용 사용자 ID가 없음")
            return
        
        # 1. 관리자 권한으로 다른 사용자 조회
        try:
            response = requests.get(
                f"{self.base_url}/{self.created_user_id}",
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 200:
                user_info = response.json()
                self.log_test("관리자 권한 특정 사용자 조회", True, f"사용자: {user_info.get('email')}")
            else:
                self.log_test("관리자 권한 특정 사용자 조회", False, f"상태코드: {response.status_code}")
                
        except Exception as e:
            self.log_test("관리자 권한 특정 사용자 조회", False, f"오류: {str(e)}")
        
        # 2. 존재하지 않는 사용자 ID (404 에러 예상)
        try:
            response = requests.get(
                f"{self.base_url}/99999",
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 404:
                self.log_test("존재하지 않는 사용자 조회", True, "404 Not Found 정상 반환")
            else:
                self.log_test("존재하지 않는 사용자 조회", False, f"예상과 다른 상태코드: {response.status_code}")
                
        except Exception as e:
            self.log_test("존재하지 않는 사용자 조회", False, f"오류: {str(e)}")
    
    def test_update_user(self):
        """사용자 정보 수정 테스트"""
        print("\n✏️ 사용자 정보 수정 테스트")
        
        if not self.created_user_id:
            self.log_test("사용자 정보 수정 테스트", False, "테스트용 사용자 ID가 없음")
            return
        
        # 1. 관리자 권한으로 사용자 정보 수정
        update_data = {
            "username": f"updated_user_{int(time.time())}",
            "full_name": "수정된 사용자"
        }
        
        try:
            response = requests.put(
                f"{self.base_url}/{self.created_user_id}",
                json=update_data,
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 200:
                updated_user = response.json()
                self.log_test("관리자 권한 사용자 정보 수정", True, f"수정된 사용자명: {updated_user.get('username')}")
            else:
                self.log_test("관리자 권한 사용자 정보 수정", False, f"상태코드: {response.status_code}")
                
        except Exception as e:
            self.log_test("관리자 권한 사용자 정보 수정", False, f"오류: {str(e)}")
    
    def test_user_stats(self):
        """사용자 통계 조회 테스트"""
        print("\n📊 사용자 통계 조회 테스트")
        
        # 1. 관리자 권한으로 통계 조회
        try:
            response = requests.get(
                self.base_url + "/stats/overview",
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 200:
                stats = response.json()
                self.log_test("관리자 권한 사용자 통계 조회", True, f"통계 데이터: {stats}")
            else:
                self.log_test("관리자 권한 사용자 통계 조회", False, f"상태코드: {response.status_code}")
                
        except Exception as e:
            self.log_test("관리자 권한 사용자 통계 조회", False, f"오류: {str(e)}")
        
        # 2. 일반 사용자 권한으로 조회 시도 (403 에러 예상)
        if self.user_token:
            try:
                response = requests.get(
                    self.base_url + "/stats/overview",
                    headers=self.get_auth_headers(self.user_token)
                )
                
                if response.status_code == 403:
                    self.log_test("일반 사용자 통계 조회 차단", True, "403 Forbidden 정상 반환")
                else:
                    self.log_test("일반 사용자 통계 조회 차단", False, f"예상과 다른 상태코드: {response.status_code}")
                    
            except Exception as e:
                self.log_test("일반 사용자 통계 조회 차단", False, f"오류: {str(e)}")
    
    def test_user_activation(self):
        """사용자 활성화/비활성화 테스트"""
        print("\n🔄 사용자 활성화/비활성화 테스트")
        
        if not self.created_user_id:
            self.log_test("사용자 활성화/비활성화 테스트", False, "테스트용 사용자 ID가 없음")
            return
        
        # 1. 사용자 비활성화
        try:
            response = requests.post(
                f"{self.base_url}/{self.created_user_id}/deactivate",
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 200:
                self.log_test("관리자 권한 사용자 비활성화", True, "사용자 비활성화 성공")
            else:
                self.log_test("관리자 권한 사용자 비활성화", False, f"상태코드: {response.status_code}")
                
        except Exception as e:
            self.log_test("관리자 권한 사용자 비활성화", False, f"오류: {str(e)}")
        
        # 2. 사용자 활성화
        try:
            response = requests.post(
                f"{self.base_url}/{self.created_user_id}/activate",
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 200:
                self.log_test("관리자 권한 사용자 활성화", True, "사용자 활성화 성공")
            else:
                self.log_test("관리자 권한 사용자 활성화", False, f"상태코드: {response.status_code}")
                
        except Exception as e:
            self.log_test("관리자 권한 사용자 활성화", False, f"오류: {str(e)}")
    
    def test_delete_user(self):
        """사용자 삭제 테스트"""
        print("\n🗑️ 사용자 삭제 테스트")
        
        if not self.created_user_id:
            self.log_test("사용자 삭제 테스트", False, "테스트용 사용자 ID가 없음")
            return
        
        # 관리자 권한으로 사용자 삭제
        try:
            response = requests.delete(
                f"{self.base_url}/{self.created_user_id}",
                headers=self.get_auth_headers(self.admin_token)
            )
            
            if response.status_code == 200:
                self.log_test("관리자 권한 사용자 삭제", True, "사용자 삭제 성공")
            else:
                self.log_test("관리자 권한 사용자 삭제", False, f"상태코드: {response.status_code}")
                
        except Exception as e:
            self.log_test("관리자 권한 사용자 삭제", False, f"오류: {str(e)}")
    
    def run_all_tests(self):
        """모든 테스트 실행"""
        print("🚀 User Router 엔드포인트 테스트 시작")
        print("=" * 50)
        
        # 토큰 설정
        if not self.setup_test_tokens():
            print("❌ 토큰 설정 실패. 테스트를 중단합니다.")
            return
        
        # 각 테스트 실행
        self.test_create_user()
        self.test_get_users()
        self.test_get_current_user()
        self.test_get_user_by_id()
        self.test_update_user()
        self.test_user_stats()
        self.test_user_activation()
        self.test_delete_user()
        
        # 결과 요약
        self.print_summary()
        self.save_results()
    
    def print_summary(self):
        """테스트 결과 요약 출력"""
        print("\n" + "=" * 50)
        print("📊 테스트 결과 요약")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"총 테스트: {total_tests}")
        print(f"성공: {passed_tests} ✅")
        print(f"실패: {failed_tests} ❌")
        print(f"성공률: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print("\n❌ 실패한 테스트:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test_name']}: {result['details']}")
    
    def save_results(self):
        """테스트 결과를 JSON 파일로 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"user_router_test_results_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 테스트 결과가 {filename}에 저장되었습니다.")

if __name__ == "__main__":
    tester = UserRouterTester()
    tester.run_all_tests()