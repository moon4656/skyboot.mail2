"""
조직 사용량 업데이트 동시성 성능 테스트

많은 사용자가 동시에 메일을 발송할 때의 성능과 데이터 일관성을 테스트합니다.
"""

import asyncio
import time
import random
import statistics
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any
import requests
import json
from datetime import datetime

# 테스트 설정
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"
TEST_ORG_ID = "3856a8c1-84a4-4019-9133-655cacab4bc9"
CONCURRENT_USERS = 50  # 동시 사용자 수
EMAILS_PER_USER = 10   # 사용자당 메일 발송 수
TEST_DURATION = 60     # 테스트 지속 시간 (초)


class ConcurrencyTester:
    """동시성 테스트 클래스"""
    
    def __init__(self):
        self.access_token = None
        self.results = []
        self.errors = []
        self.start_time = None
        self.end_time = None
    
    def login_admin(self) -> bool:
        """관리자 로그인"""
        try:
            login_data = {
                "username": "admin01",
                "password": "admin123!"
            }
            
            response = requests.post(f"{BASE_URL}{API_PREFIX}/auth/login", data=login_data)
            if response.status_code == 200:
                result = response.json()
                self.access_token = result["access_token"]
                print("✅ 관리자 로그인 성공")
                return True
            else:
                print(f"❌ 로그인 실패: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 로그인 오류: {str(e)}")
            return False
    
    def get_organization_usage(self) -> Dict[str, Any]:
        """조직 사용량 조회"""
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "X-Organization-ID": TEST_ORG_ID
            }
            
            response = requests.get(
                f"{BASE_URL}{API_PREFIX}/organization/usage",
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"⚠️ 사용량 조회 실패: {response.status_code}")
                return {}
        except Exception as e:
            print(f"❌ 사용량 조회 오류: {str(e)}")
            return {}
    
    def send_test_email(self, user_id: int, email_id: int) -> Dict[str, Any]:
        """테스트 메일 발송"""
        start_time = time.time()
        
        try:
            mail_data = {
                "to": [f"test{user_id}_{email_id}@example.com"],
                "subject": f"동시성 테스트 메일 - 사용자{user_id}_메일{email_id}",
                "body_text": f"동시성 테스트용 메일입니다.\n사용자: {user_id}\n메일 번호: {email_id}\n발송 시간: {datetime.now()}",
                "priority": "normal"
            }
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "X-Organization-ID": TEST_ORG_ID,
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                f"{BASE_URL}{API_PREFIX}/mail/send-json",
                json=mail_data,
                headers=headers,
                timeout=30
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            result = {
                "user_id": user_id,
                "email_id": email_id,
                "status_code": response.status_code,
                "duration": duration,
                "success": response.status_code == 200,
                "timestamp": datetime.now().isoformat()
            }
            
            if response.status_code == 200:
                mail_result = response.json()
                result["mail_uuid"] = mail_result.get("mail_uuid")
            else:
                result["error"] = response.text
                self.errors.append(result)
            
            return result
            
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            
            error_result = {
                "user_id": user_id,
                "email_id": email_id,
                "status_code": 0,
                "duration": duration,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            
            self.errors.append(error_result)
            return error_result
    
    def simulate_user(self, user_id: int) -> List[Dict[str, Any]]:
        """사용자 시뮬레이션 (여러 메일 발송)"""
        user_results = []
        
        for email_id in range(EMAILS_PER_USER):
            # 랜덤 지연 (실제 사용자 행동 시뮬레이션)
            delay = random.uniform(0.1, 2.0)
            time.sleep(delay)
            
            result = self.send_test_email(user_id, email_id)
            user_results.append(result)
            
            # 진행 상황 출력 (일부만)
            if user_id % 10 == 0 and email_id % 5 == 0:
                status = "✅" if result["success"] else "❌"
                print(f"{status} 사용자{user_id} - 메일{email_id} ({result['duration']:.2f}초)")
        
        return user_results
    
    async def run_concurrency_test(self):
        """동시성 테스트 실행"""
        print(f"🚀 동시성 테스트 시작")
        print(f"   동시 사용자 수: {CONCURRENT_USERS}")
        print(f"   사용자당 메일 수: {EMAILS_PER_USER}")
        print(f"   총 메일 수: {CONCURRENT_USERS * EMAILS_PER_USER}")
        print("=" * 60)
        
        # 로그인
        if not self.login_admin():
            return
        
        # 테스트 시작 전 사용량 확인
        print("📊 테스트 시작 전 조직 사용량:")
        initial_usage = self.get_organization_usage()
        if initial_usage:
            print(f"   오늘 발송: {initial_usage.get('emails_sent_today', 0)}")
            print(f"   총 발송: {initial_usage.get('total_emails_sent', 0)}")
        
        # 동시성 테스트 실행
        self.start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=CONCURRENT_USERS) as executor:
            print(f"\n🔄 {CONCURRENT_USERS}명의 사용자가 동시에 메일 발송 시작...")
            
            # 모든 사용자 작업 제출
            futures = [
                executor.submit(self.simulate_user, user_id)
                for user_id in range(CONCURRENT_USERS)
            ]
            
            # 결과 수집
            for future in futures:
                try:
                    user_results = future.result(timeout=120)  # 2분 타임아웃
                    self.results.extend(user_results)
                except Exception as e:
                    print(f"❌ 사용자 작업 실패: {str(e)}")
        
        self.end_time = time.time()
        
        # 테스트 완료 후 사용량 확인
        print("\n📊 테스트 완료 후 조직 사용량:")
        final_usage = self.get_organization_usage()
        if final_usage:
            print(f"   오늘 발송: {final_usage.get('emails_sent_today', 0)}")
            print(f"   총 발송: {final_usage.get('total_emails_sent', 0)}")
        
        # 결과 분석
        self.analyze_results(initial_usage, final_usage)
    
    def analyze_results(self, initial_usage: Dict, final_usage: Dict):
        """결과 분석 및 리포트 생성"""
        total_duration = self.end_time - self.start_time
        total_requests = len(self.results)
        successful_requests = len([r for r in self.results if r["success"]])
        failed_requests = len(self.errors)
        
        # 성능 메트릭 계산
        durations = [r["duration"] for r in self.results if r["success"]]
        
        print("\n" + "=" * 60)
        print("📈 동시성 테스트 결과 분석")
        print("=" * 60)
        
        # 기본 통계
        print(f"🕐 총 테스트 시간: {total_duration:.2f}초")
        print(f"📧 총 요청 수: {total_requests}")
        print(f"✅ 성공한 요청: {successful_requests}")
        print(f"❌ 실패한 요청: {failed_requests}")
        print(f"📊 성공률: {(successful_requests/total_requests*100):.1f}%")
        
        if durations:
            print(f"\n⏱️ 응답 시간 통계:")
            print(f"   평균: {statistics.mean(durations):.3f}초")
            print(f"   중간값: {statistics.median(durations):.3f}초")
            print(f"   최소: {min(durations):.3f}초")
            print(f"   최대: {max(durations):.3f}초")
            print(f"   표준편차: {statistics.stdev(durations):.3f}초")
        
        # 처리량 계산
        if total_duration > 0:
            throughput = successful_requests / total_duration
            print(f"\n🚀 처리량: {throughput:.2f} 요청/초")
        
        # 데이터 일관성 검증
        print(f"\n🔍 데이터 일관성 검증:")
        if initial_usage and final_usage:
            expected_increase = successful_requests
            actual_increase = (
                final_usage.get('emails_sent_today', 0) - 
                initial_usage.get('emails_sent_today', 0)
            )
            
            print(f"   예상 증가량: {expected_increase}")
            print(f"   실제 증가량: {actual_increase}")
            
            if expected_increase == actual_increase:
                print("   ✅ 데이터 일관성 유지됨")
            else:
                print("   ❌ 데이터 불일치 발생!")
                print(f"   차이: {abs(expected_increase - actual_increase)}")
        
        # 오류 분석
        if self.errors:
            print(f"\n❌ 오류 분석:")
            error_types = {}
            for error in self.errors:
                error_key = error.get('error', 'Unknown')
                error_types[error_key] = error_types.get(error_key, 0) + 1
            
            for error_type, count in error_types.items():
                print(f"   {error_type}: {count}회")
        
        # 성능 등급 평가
        print(f"\n🏆 성능 등급:")
        if durations:
            avg_duration = statistics.mean(durations)
            success_rate = successful_requests / total_requests * 100
            
            if avg_duration < 1.0 and success_rate > 99:
                grade = "A+ (우수)"
            elif avg_duration < 2.0 and success_rate > 95:
                grade = "A (양호)"
            elif avg_duration < 5.0 and success_rate > 90:
                grade = "B (보통)"
            elif success_rate > 80:
                grade = "C (개선 필요)"
            else:
                grade = "D (심각한 문제)"
            
            print(f"   등급: {grade}")
        
        # 결과를 파일로 저장
        self.save_results_to_file()
    
    def save_results_to_file(self):
        """결과를 JSON 파일로 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"concurrency_test_results_{timestamp}.json"
        
        report_data = {
            "test_config": {
                "concurrent_users": CONCURRENT_USERS,
                "emails_per_user": EMAILS_PER_USER,
                "total_emails": CONCURRENT_USERS * EMAILS_PER_USER,
                "test_duration": self.end_time - self.start_time if self.start_time else 0
            },
            "results": self.results,
            "errors": self.errors,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            print(f"\n💾 결과가 {filename}에 저장되었습니다.")
        except Exception as e:
            print(f"❌ 결과 저장 실패: {str(e)}")


async def main():
    """메인 함수"""
    print("🧪 조직 사용량 업데이트 동시성 테스트")
    print("=" * 60)
    
    tester = ConcurrencyTester()
    await tester.run_concurrency_test()


if __name__ == "__main__":
    asyncio.run(main())