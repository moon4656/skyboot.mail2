#!/usr/bin/env python3
"""
Rate Limiting 최종 테스트

실제로 rate limiting이 작동하는지 확인합니다.
"""
import requests
import time
from datetime import datetime

def test_rate_limiting():
    """Rate limiting 테스트"""
    print("🚀 Rate Limiting 최종 테스트 시작")
    print(f"⏰ 시작 시간: {datetime.now().strftime('%H:%M:%S')}")
    
    base_url = "http://localhost:8000"
    test_endpoint = f"{base_url}/"
    
    # 현재 기본 제한은 100 요청/분이므로, 매우 빠르게 요청을 보내서 테스트
    max_requests = 110  # 제한을 초과하도록
    delay = 0.001  # 1ms 간격으로 매우 빠르게
    
    print(f"📊 테스트 설정:")
    print(f"  - 요청 수: {max_requests}")
    print(f"  - 간격: {delay}초")
    print(f"  - 예상 제한: 100 요청/분")
    print()
    
    success_count = 0
    rate_limited_count = 0
    error_count = 0
    
    for i in range(max_requests):
        try:
            start_time = time.time()
            response = requests.get(test_endpoint, timeout=1)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                success_count += 1
                status_emoji = "✅"
            elif response.status_code == 429:
                rate_limited_count += 1
                status_emoji = "🚫"
                print(f"{status_emoji} 요청 {i+1:3d}: HTTP {response.status_code} - Rate Limit 도달!")
                
                # Rate limit 헤더 확인
                if 'x-ratelimit-limit' in response.headers:
                    limit = response.headers.get('x-ratelimit-limit')
                    remaining = response.headers.get('x-ratelimit-remaining', 'N/A')
                    reset_time = response.headers.get('x-ratelimit-reset', 'N/A')
                    print(f"    📊 Limit: {limit}, Remaining: {remaining}, Reset: {reset_time}")
                
                # 몇 개 더 테스트한 후 중단
                if rate_limited_count >= 5:
                    print(f"🎯 충분한 Rate Limit 테스트 완료!")
                    break
            else:
                error_count += 1
                status_emoji = "❌"
            
            # 10개마다 진행 상황 출력
            if (i + 1) % 10 == 0 and rate_limited_count == 0:
                print(f"📈 진행: {i+1}/{max_requests} - 성공: {success_count}, 제한: {rate_limited_count}")
            
            time.sleep(delay)
            
        except Exception as e:
            error_count += 1
            print(f"❌ 요청 {i+1} 실패: {str(e)}")
            break
    
    print()
    print("=" * 50)
    print("📊 최종 결과:")
    print(f"  ✅ 성공한 요청: {success_count}")
    print(f"  🚫 Rate Limit 도달: {rate_limited_count}")
    print(f"  ❌ 오류 발생: {error_count}")
    print(f"  📊 총 요청: {success_count + rate_limited_count + error_count}")
    
    if rate_limited_count > 0:
        print()
        print("🎉 Rate Limiting이 정상적으로 작동합니다!")
        print(f"   - {success_count}개 요청 후 제한이 활성화되었습니다.")
    else:
        print()
        print("⚠️ Rate Limiting이 예상대로 작동하지 않습니다.")
        print("   - 가능한 원인: 제한 설정이 너무 높거나 시간 윈도우가 다를 수 있습니다.")

if __name__ == "__main__":
    test_rate_limiting()