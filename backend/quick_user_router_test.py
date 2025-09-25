#!/usr/bin/env python3
"""
User Router 빠른 테스트 스크립트
기본적인 엔드포인트 연결성과 응답 확인
"""

import requests
import json
from datetime import datetime

class QuickUserRouterTester:
    def __init__(self):
        self.base_url = "http://127.0.0.1:8000"
        self.api_prefix = "/api/v1/users"
        self.results = []
        
    def test_endpoint(self, method: str, endpoint: str, description: str, 
                     headers: dict = None, json_data: dict = None, 
                     expected_status: list = None):
        """엔드포인트 테스트 실행"""
        if expected_status is None:
            expected_status = [200, 401, 403, 404, 422]  # 허용 가능한 상태 코드들
            
        url = f"{self.base_url}{self.api_prefix}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, timeout=5)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=json_data, timeout=5)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=headers, json=json_data, timeout=5)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers, timeout=5)
            else:
                raise ValueError(f"지원하지 않는 HTTP 메서드: {method}")
            
            success = response.status_code in expected_status
            status_msg = "✅ PASS" if success else "❌ FAIL"
            
            result = {
                "endpoint": f"{method.upper()} {endpoint}",
                "description": description,
                "status_code": response.status_code,
                "success": success,
                "response_size": len(response.text),
                "timestamp": datetime.now().isoformat()
            }
            
            self.results.append(result)
            print(f"{status_msg} {method.upper()} {endpoint} - {description} (상태: {response.status_code})")
            
            return response
            
        except requests.exceptions.Timeout:
            print(f"❌ TIMEOUT {method.upper()} {endpoint} - {description} (5초 초과)")
            self.results.append({
                "endpoint": f"{method.upper()} {endpoint}",
                "description": description,
                "status_code": "TIMEOUT",
                "success": False,
                "error": "Request timeout",
                "timestamp": datetime.now().isoformat()
            })
            return None
            
        except Exception as e:
            print(f"❌ ERROR {method.upper()} {endpoint} - {description} (오류: {e})")
            self.results.append({
                "endpoint": f"{method.upper()} {endpoint}",
                "description": description,
                "status_code": "ERROR",
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            return None
    
    def run_quick_tests(self):
        """빠른 테스트 실행"""
        print("🚀 User Router 빠른 테스트 시작...")
        print("=" * 60)
        
        # 1. 서버 연결 확인
        try:
            response = requests.get(f"{self.base_url}/", timeout=3)
            print(f"✅ 서버 연결 확인: {response.status_code}")
        except Exception as e:
            print(f"❌ 서버 연결 실패: {e}")
            return
        
        # 2. 기본 엔드포인트 테스트 (인증 없이)
        print("\n📋 기본 엔드포인트 연결성 테스트:")
        
        # 사용자 생성 (POST /)
        self.test_endpoint("POST", "/", "사용자 생성", 
                          json_data={"email": "test@example.com", "password": "test123"})
        
        # 사용자 목록 조회 (GET /)
        self.test_endpoint("GET", "/", "사용자 목록 조회")
        
        # 현재 사용자 정보 (GET /me)
        self.test_endpoint("GET", "/me", "현재 사용자 정보")
        
        # 특정 사용자 조회 (GET /{user_id})
        self.test_endpoint("GET", "/1", "특정 사용자 조회")
        
        # 사용자 정보 수정 (PUT /{user_id})
        self.test_endpoint("PUT", "/1", "사용자 정보 수정",
                          json_data={"name": "수정된 이름"})
        
        # 사용자 삭제 (DELETE /{user_id})
        self.test_endpoint("DELETE", "/1", "사용자 삭제")
        
        # 비밀번호 변경 (POST /{user_id}/change-password)
        self.test_endpoint("POST", "/1/change-password", "비밀번호 변경",
                          json_data={"current_password": "old", "new_password": "new"})
        
        # 사용자 통계 (GET /stats/overview)
        self.test_endpoint("GET", "/stats/overview", "사용자 통계 조회")
        
        # 사용자 활성화 (POST /{user_id}/activate)
        self.test_endpoint("POST", "/1/activate", "사용자 활성화")
        
        # 사용자 비활성화 (POST /{user_id}/deactivate)
        self.test_endpoint("POST", "/1/deactivate", "사용자 비활성화")
        
        # 3. 결과 요약
        self.print_summary()
        self.save_results()
    
    def print_summary(self):
        """테스트 결과 요약"""
        total = len(self.results)
        success = sum(1 for r in self.results if r["success"])
        failed = total - success
        
        print("\n" + "=" * 60)
        print("📊 테스트 결과 요약")
        print("=" * 60)
        print(f"총 테스트: {total}")
        print(f"✅ 연결 성공: {success}")
        print(f"❌ 연결 실패: {failed}")
        print(f"연결률: {(success/total*100):.1f}%")
        
        if failed > 0:
            print("\n❌ 연결 실패한 엔드포인트:")
            for result in self.results:
                if not result["success"]:
                    print(f"  - {result['endpoint']}: {result.get('error', result.get('status_code'))}")
    
    def save_results(self):
        """결과를 JSON 파일로 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"quick_test_results_{timestamp}.json"
        
        summary = {
            "test_summary": {
                "total_tests": len(self.results),
                "successful_connections": sum(1 for r in self.results if r["success"]),
                "failed_connections": sum(1 for r in self.results if not r["success"]),
                "connection_rate": f"{(sum(1 for r in self.results if r['success'])/len(self.results)*100):.1f}%"
            },
            "test_results": self.results,
            "test_timestamp": datetime.now().isoformat()
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            print(f"\n📄 테스트 결과가 {filename}에 저장되었습니다.")
        except Exception as e:
            print(f"❌ 결과 저장 오류: {e}")

def main():
    """메인 실행 함수"""
    print("🧪 User Router 빠른 연결성 테스트")
    print("각 엔드포인트의 기본 연결성과 응답을 확인합니다.")
    print("(인증 토큰 없이 기본 응답 상태만 확인)")
    
    tester = QuickUserRouterTester()
    tester.run_quick_tests()

if __name__ == "__main__":
    main()