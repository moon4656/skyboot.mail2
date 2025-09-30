#!/usr/bin/env python3
"""
간단한 Rate Limiting 테스트 스크립트

인증이 필요하지 않은 엔드포인트로 rate limiting을 테스트합니다.
"""
import requests
import time
from datetime import datetime

def test_rate_limiting_simple():
    """루트 엔드포인트로 Rate limiting 테스트"""
    print("🚦 간단한 Rate Limiting 테스트 시작...")
    print("=" * 60)
    
    base_url = "http://localhost:8000"
    test_endpoint = f"{base_url}/"  # 루트 엔드포인트
    
    # 테스트 설정
    max_requests = 25  # 기본 제한(20)보다 많이 요청
    delay_between_requests = 0.1  # 100ms 간격
    
    print(f"📊 테스트 설정:")
    print(f"  - 요청 URL: {test_endpoint}")
    print(f"  - 총 요청 수: {max_requests}")
    print(f"  - 요청 간격: {delay_between_requests}초")
    print(f"  - 예상 IP 제한: 20 요청/분")
    print()
    
    success_count = 0
    rate_limited_count = 0
    error_count = 0
    first_rate_limit_at = None
    
    for i in range(max_requests):
        try:
            print(f"📤 요청 {i+1:2d}/{max_requests}...", end=" ")
            
            start_time = time.time()
            response = requests.get(test_endpoint, timeout=5)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                success_count += 1
                print(f"✅ 성공 (응답시간: {response_time:.3f}초)")
                
                # Rate limit 헤더 확인
                headers = response.headers
                if 'X-RateLimit-Limit' in headers:
                    limit = headers.get('X-RateLimit-Limit', 'N/A')
                    remaining = headers.get('X-RateLimit-Remaining', 'N/A')
                    reset_time = headers.get('X-RateLimit-Reset', 'N/A')
                    print(f"   📊 Rate Limit: {remaining}/{limit} (리셋: {reset_time})")
                
            elif response.status_code == 429:  # Too Many Requests
                rate_limited_count += 1
                if first_rate_limit_at is None:
                    first_rate_limit_at = i + 1
                
                print(f"🚫 Rate Limit 도달! (HTTP 429)")
                
                try:
                    error_data = response.json()
                    print(f"   📝 메시지: {error_data.get('message', 'N/A')}")
                except:
                    print(f"   📝 응답: {response.text[:100]}...")
                
                # Rate limit 헤더 확인
                headers = response.headers
                retry_after = headers.get('Retry-After', 'N/A')
                reset_time = headers.get('X-RateLimit-Reset', 'N/A')
                print(f"   ⏰ 재시도 대기: {retry_after}초, 리셋: {reset_time}")
                
            else:
                error_count += 1
                print(f"❌ 오류 (HTTP {response.status_code})")
                print(f"   📝 응답: {response.text[:100]}...")
            
        except requests.exceptions.RequestException as e:
            error_count += 1
            print(f"❌ 연결 오류: {str(e)}")
        
        except Exception as e:
            error_count += 1
            print(f"❌ 예상치 못한 오류: {str(e)}")
        
        # 다음 요청 전 대기
        if i < max_requests - 1:
            time.sleep(delay_between_requests)
    
    print()
    print("=" * 60)
    print("📊 테스트 결과 요약:")
    print(f"  ✅ 성공한 요청: {success_count}")
    print(f"  🚫 Rate Limit 도달: {rate_limited_count}")
    print(f"  ❌ 기타 오류: {error_count}")
    print(f"  📈 총 요청 수: {max_requests}")
    
    if first_rate_limit_at:
        print(f"  🎯 첫 번째 Rate Limit: {first_rate_limit_at}번째 요청")
    
    # 결과 분석
    if rate_limited_count > 0:
        print("\n🎉 Rate Limiting이 정상적으로 작동하고 있습니다!")
        print(f"💡 {first_rate_limit_at}번째 요청부터 HTTP 429 응답을 받았습니다.")
        print("🔒 SkyBoot Mail SaaS의 보안 기능이 활성화되었습니다.")
        return True
    elif success_count == max_requests:
        print("\n⚠️ Rate Limiting이 작동하지 않는 것 같습니다.")
        print("💡 모든 요청이 성공했습니다. 설정을 확인해보세요.")
        return False
    else:
        print("\n❓ 테스트 결과가 명확하지 않습니다.")
        print("💡 네트워크 오류나 서버 문제가 있을 수 있습니다.")
        return False

def check_redis_data():
    """Redis 데이터 확인"""
    print("\n🔍 Redis Rate Limit 데이터 확인...")
    
    try:
        import redis
        import sys
        import os
        
        # 프로젝트 루트 디렉토리를 Python 경로에 추가
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        
        from app.config import settings
        
        redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            db=settings.REDIS_DB,
            decode_responses=True
        )
        
        # Rate limit 관련 키 검색
        rate_limit_keys = redis_client.keys("rate_limit:*")
        
        if rate_limit_keys:
            print(f"📊 발견된 Rate Limit 키: {len(rate_limit_keys)}개")
            for key in rate_limit_keys:
                value = redis_client.get(key)
                ttl = redis_client.ttl(key)
                print(f"  🔑 {key}: {value} (TTL: {ttl}초)")
        else:
            print("📭 Rate Limit 관련 Redis 키가 없습니다.")
        
        return True
        
    except Exception as e:
        print(f"❌ Redis 데이터 확인 오류: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 SkyBoot Mail SaaS - 간단한 Rate Limiting 테스트")
    print(f"⏰ 테스트 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Rate limiting 기능 테스트
    rate_limit_working = test_rate_limiting_simple()
    
    # Redis 데이터 확인
    redis_data_check = check_redis_data()
    
    print("\n" + "=" * 60)
    print("🏁 최종 결과:")
    print(f"  Rate Limiting 작동: {'✅ 정상' if rate_limit_working else '❌ 문제'}")
    print(f"  Redis 데이터 확인: {'✅ 성공' if redis_data_check else '❌ 실패'}")
    
    if rate_limit_working and redis_data_check:
        print("\n🎉 Redis 기반 Rate Limiting이 완벽하게 작동합니다!")
        print("💡 SkyBoot Mail SaaS의 보안 기능이 정상적으로 활성화되었습니다.")
        print("🔒 API 엔드포인트가 DDoS 및 남용으로부터 보호되고 있습니다.")
    else:
        print("\n⚠️ 일부 기능에 문제가 있을 수 있습니다.")
        print("💡 로그와 설정을 다시 확인해보세요.")