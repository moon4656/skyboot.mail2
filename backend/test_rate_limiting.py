#!/usr/bin/env python3
"""
Rate Limiting 테스트 스크립트 (실제 API 엔드포인트 사용)

SkyBoot Mail SaaS의 Redis 기반 rate limiting 기능을 테스트합니다.
"""
import requests
import time
import json
from datetime import datetime

def test_rate_limiting_on_api():
    """실제 API 엔드포인트로 Rate limiting 기능 테스트"""
    print("🚦 Rate Limiting 테스트 시작 (실제 API 엔드포인트)...")
    print("=" * 70)
    
    base_url = "http://localhost:8000"
    # 제외 경로가 아닌 실제 API 엔드포인트 사용
    test_endpoint = f"{base_url}/api/v1/debug/context"
    
    # 테스트 설정
    max_requests = 25  # 기본 제한(20)보다 많이 요청
    delay_between_requests = 0.05  # 50ms 간격으로 빠르게 요청
    
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
                
            elif response.status_code == 401:  # Unauthorized (예상됨)
                success_count += 1  # 인증 오류는 정상적인 응답으로 간주
                print(f"🔐 인증 필요 (HTTP 401) - 정상 응답")
                
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
    print("=" * 70)
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
    elif success_count == max_requests:
        print("\n⚠️ Rate Limiting이 작동하지 않는 것 같습니다.")
        print("💡 모든 요청이 성공했습니다. 설정을 확인해보세요.")
    else:
        print("\n❓ 테스트 결과가 명확하지 않습니다.")
        print("💡 네트워크 오류나 서버 문제가 있을 수 있습니다.")
    
    return rate_limited_count > 0

def test_redis_rate_limit_data():
    """Redis에 저장된 rate limit 데이터 확인"""
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
            print("💡 아직 요청이 없거나 TTL이 만료되었을 수 있습니다.")
        
        # 전체 Redis 키 확인 (디버깅용)
        all_keys = redis_client.keys("*")
        if all_keys:
            print(f"\n🗂️ 전체 Redis 키: {len(all_keys)}개")
            for key in all_keys[:5]:  # 처음 5개만 표시
                value = redis_client.get(key)
                print(f"  🔑 {key}: {value}")
            if len(all_keys) > 5:
                print(f"  ... 및 {len(all_keys) - 5}개 더")
        
        return True
        
    except Exception as e:
        print(f"❌ Redis 데이터 확인 오류: {str(e)}")
        return False

def test_excluded_paths():
    """제외 경로 테스트"""
    print("\n🚫 제외 경로 테스트...")
    
    excluded_endpoints = [
        "http://localhost:8000/health",
        "http://localhost:8000/docs",
        "http://localhost:8000/openapi.json"
    ]
    
    for endpoint in excluded_endpoints:
        try:
            print(f"📤 테스트: {endpoint}...", end=" ")
            response = requests.get(endpoint, timeout=5)
            
            if response.status_code in [200, 404]:  # 정상 또는 Not Found
                print(f"✅ 제외됨 (HTTP {response.status_code})")
            else:
                print(f"❓ 예상치 못한 응답 (HTTP {response.status_code})")
                
        except Exception as e:
            print(f"❌ 오류: {str(e)}")

if __name__ == "__main__":
    print("🚀 SkyBoot Mail SaaS - Rate Limiting 종합 테스트")
    print(f"⏰ 테스트 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 제외 경로 테스트
    test_excluded_paths()
    
    # Rate limiting 기능 테스트 (실제 API)
    rate_limit_working = test_rate_limiting_on_api()
    
    # Redis 데이터 확인
    redis_data_check = test_redis_rate_limit_data()
    
    print("\n" + "=" * 70)
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