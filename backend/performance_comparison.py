"""
조직 사용량 업데이트 성능 비교 스크립트

기존 방식 vs 새로운 UPSERT 방식의 성능을 비교합니다.
"""

import asyncio
import time
import statistics
from typing import List
import sys
import os

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.mail import get_db
from app.service.mail_service import MailService


class PerformanceComparator:
    """성능 비교 클래스"""
    
    def __init__(self):
        self.db = next(get_db())
        self.mail_service = MailService(self.db)
        self.test_org_id = "test_org_performance"
    
    async def test_upsert_method(self, iterations: int = 100) -> List[float]:
        """새로운 UPSERT 방식 테스트"""
        print(f"🔄 UPSERT 방식 테스트 시작 ({iterations}회)")
        
        durations = []
        
        for i in range(iterations):
            start_time = time.time()
            
            try:
                await self.mail_service._update_organization_usage(
                    org_id=self.test_org_id,
                    email_count=1
                )
                
                end_time = time.time()
                duration = end_time - start_time
                durations.append(duration)
                
                if (i + 1) % 20 == 0:
                    print(f"   진행률: {i + 1}/{iterations} ({duration:.4f}초)")
                    
            except Exception as e:
                print(f"❌ UPSERT 테스트 오류 (반복 {i + 1}): {str(e)}")
        
        return durations
    
    async def test_redis_lock_method(self, iterations: int = 100) -> List[float]:
        """Redis 락 방식 테스트"""
        print(f"🔒 Redis 락 방식 테스트 시작 ({iterations}회)")
        
        durations = []
        
        for i in range(iterations):
            start_time = time.time()
            
            try:
                await self.mail_service._update_organization_usage_with_redis_lock(
                    org_id=self.test_org_id,
                    email_count=1
                )
                
                end_time = time.time()
                duration = end_time - start_time
                durations.append(duration)
                
                if (i + 1) % 20 == 0:
                    print(f"   진행률: {i + 1}/{iterations} ({duration:.4f}초)")
                    
            except Exception as e:
                print(f"❌ Redis 락 테스트 오류 (반복 {i + 1}): {str(e)}")
        
        return durations
    
    async def test_concurrent_upsert(self, concurrent_tasks: int = 10, iterations_per_task: int = 10) -> List[float]:
        """동시 UPSERT 테스트"""
        print(f"⚡ 동시 UPSERT 테스트 시작 ({concurrent_tasks}개 작업, 각 {iterations_per_task}회)")
        
        async def single_task(task_id: int) -> List[float]:
            task_durations = []
            for i in range(iterations_per_task):
                start_time = time.time()
                
                try:
                    await self.mail_service._update_organization_usage(
                        org_id=f"{self.test_org_id}_{task_id}",
                        email_count=1
                    )
                    
                    end_time = time.time()
                    duration = end_time - start_time
                    task_durations.append(duration)
                    
                except Exception as e:
                    print(f"❌ 동시 UPSERT 오류 (작업 {task_id}, 반복 {i + 1}): {str(e)}")
            
            return task_durations
        
        # 동시 작업 실행
        tasks = [single_task(task_id) for task_id in range(concurrent_tasks)]
        results = await asyncio.gather(*tasks)
        
        # 모든 결과 합치기
        all_durations = []
        for task_durations in results:
            all_durations.extend(task_durations)
        
        return all_durations
    
    def analyze_performance(self, method_name: str, durations: List[float]):
        """성능 분석"""
        if not durations:
            print(f"❌ {method_name}: 측정 데이터 없음")
            return
        
        print(f"\n📊 {method_name} 성능 분석:")
        print(f"   총 실행 횟수: {len(durations)}")
        print(f"   평균 시간: {statistics.mean(durations):.4f}초")
        print(f"   중간값: {statistics.median(durations):.4f}초")
        print(f"   최소 시간: {min(durations):.4f}초")
        print(f"   최대 시간: {max(durations):.4f}초")
        
        if len(durations) > 1:
            print(f"   표준편차: {statistics.stdev(durations):.4f}초")
        
        # 성능 등급
        avg_time = statistics.mean(durations)
        if avg_time < 0.01:
            grade = "A+ (매우 빠름)"
        elif avg_time < 0.05:
            grade = "A (빠름)"
        elif avg_time < 0.1:
            grade = "B (보통)"
        elif avg_time < 0.5:
            grade = "C (느림)"
        else:
            grade = "D (매우 느림)"
        
        print(f"   성능 등급: {grade}")
    
    def compare_methods(self, upsert_durations: List[float], redis_durations: List[float]):
        """방식 간 비교"""
        if not upsert_durations or not redis_durations:
            print("❌ 비교할 데이터가 부족합니다.")
            return
        
        upsert_avg = statistics.mean(upsert_durations)
        redis_avg = statistics.mean(redis_durations)
        
        print(f"\n🔍 성능 비교:")
        print(f"   UPSERT 방식 평균: {upsert_avg:.4f}초")
        print(f"   Redis 락 방식 평균: {redis_avg:.4f}초")
        
        if upsert_avg < redis_avg:
            improvement = ((redis_avg - upsert_avg) / redis_avg) * 100
            print(f"   ✅ UPSERT 방식이 {improvement:.1f}% 더 빠름")
        elif redis_avg < upsert_avg:
            improvement = ((upsert_avg - redis_avg) / upsert_avg) * 100
            print(f"   ✅ Redis 락 방식이 {improvement:.1f}% 더 빠름")
        else:
            print(f"   ⚖️ 두 방식의 성능이 비슷함")
    
    async def run_performance_tests(self):
        """전체 성능 테스트 실행"""
        print("🚀 조직 사용량 업데이트 성능 테스트 시작")
        print("=" * 60)
        
        # 1. UPSERT 방식 테스트
        upsert_durations = await self.test_upsert_method(100)
        self.analyze_performance("UPSERT 방식", upsert_durations)
        
        # 2. Redis 락 방식 테스트
        redis_durations = await self.test_redis_lock_method(100)
        self.analyze_performance("Redis 락 방식", redis_durations)
        
        # 3. 동시 실행 테스트
        concurrent_durations = await self.test_concurrent_upsert(10, 10)
        self.analyze_performance("동시 UPSERT (10개 작업)", concurrent_durations)
        
        # 4. 방식 간 비교
        self.compare_methods(upsert_durations, redis_durations)
        
        print("\n" + "=" * 60)
        print("✅ 성능 테스트 완료")
        
        # 권장사항 제시
        print(f"\n💡 권장사항:")
        if upsert_durations and redis_durations:
            upsert_avg = statistics.mean(upsert_durations)
            redis_avg = statistics.mean(redis_durations)
            
            if upsert_avg < redis_avg * 1.5:  # UPSERT가 50% 이상 빠르지 않으면
                print("   - 일반적인 상황에서는 PostgreSQL UPSERT 방식 사용 권장")
                print("   - 매우 높은 동시성이 예상되는 경우에만 Redis 락 방식 고려")
            else:
                print("   - PostgreSQL UPSERT 방식을 기본으로 사용")
                print("   - Redis 락은 특별한 경우에만 사용")
        
        print("   - 정기적인 성능 모니터링 필요")
        print("   - 실제 운영 환경에서의 추가 테스트 권장")


async def main():
    """메인 함수"""
    try:
        comparator = PerformanceComparator()
        await comparator.run_performance_tests()
    except Exception as e:
        print(f"❌ 테스트 실행 중 오류: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())