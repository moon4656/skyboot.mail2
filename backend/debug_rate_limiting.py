#!/usr/bin/env python3
"""
Rate Limiting 디버깅 스크립트

Rate limiting이 작동하지 않는 이유를 진단합니다.
"""
import requests
import time
import redis
import sys
import os
from datetime import datetime

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.config import settings

def check_redis_connection():
    """Redis 연결 상태 확인"""
    print("🔍 Redis 연결 상태 확인...")
    
    try:
        redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            db=settings.REDIS_DB,
            decode_responses=True
        )
        
        # 연결 테스트
        pong = redis_client.ping()
        print(f"✅ Redis 연결 성공: {pong}")
        
        # 현재 키 확인
        all_keys = redis_client.keys("*")
        print(f"📊 현재 Redis 키 개수: {len(all_keys)}")
        
        if all_keys:
            print("🔑 현재 Redis 키들:")
            for key in all_keys[:10]:  # 최대 10개만 표시
                value = redis_client.get(key)
                ttl = redis_client.ttl(key)
                print(f"  - {key}: {value} (TTL: {ttl}초)")
        
        return redis_client
        
    except Exception as e:
        print(f"❌ Redis 연결 실패: {str(e)}")
        return None

def test_single_request():
    """단일 요청으로 rate limiting 테스트"""
    print("\n🚦 단일 요청 테스트...")
    
    base_url = "http://localhost:8000"
    test_endpoint = f"{base_url}/"
    
    try:
        print(f"📤 요청 URL: {test_endpoint}")
        
        start_time = time.time()
        response = requests.get(test_endpoint, timeout=5)
        response_time = time.time() - start_time
        
        print(f"📊 응답 정보:")
        print(f"  - 상태 코드: {response.status_code}")
        print(f"  - 응답 시간: {response_time:.3f}초")
        print(f"  - 응답 크기: {len(response.content)} bytes")
        
        # 헤더 확인
        print(f"📋 응답 헤더:")
        for header, value in response.headers.items():
            if 'rate' in header.lower() or 'limit' in header.lower():
                print(f"  - {header}: {value}")
        
        # 응답 내용 확인
        print(f"📝 응답 내용 (처음 200자):")
        print(f"  {response.text[:200]}...")
        
        return response
        
    except Exception as e:
        print(f"❌ 요청 실패: {str(e)}")
        return None

def test_rapid_requests():
    """빠른 연속 요청으로 rate limiting 테스트"""
    print("\n🚀 빠른 연속 요청 테스트...")
    
    base_url = "http://localhost:8000"
    test_endpoint = f"{base_url}/"
    
    # 매우 빠른 속도로 요청 (10ms 간격)
    max_requests = 30
    delay = 0.01  # 10ms
    
    print(f"📊 테스트 설정:")
    print(f"  - 요청 수: {max_requests}")
    print(f"  - 간격: {delay}초")
    print(f"  - 예상 제한: 20 요청/분")
    
    results = []
    
    for i in range(max_requests):
        try:
            start_time = time.time()
            response = requests.get(test_endpoint, timeout=2)
            response_time = time.time() - start_time
            
            result = {
                'request_num': i + 1,
                'status_code': response.status_code,
                'response_time': response_time,
                'headers': dict(response.headers)
            }
            results.append(result)
            
            status_emoji = "✅" if response.status_code == 200 else "🚫" if response.status_code == 429 else "❌"
            print(f"{status_emoji} 요청 {i+1:2d}: HTTP {response.status_code} ({response_time:.3f}초)")
            
            # Rate limit에 걸리면 중단
            if response.status_code == 429:
                print(f"🎯 Rate Limit 도달! {i+1}번째 요청에서 제한됨")
                break
            
            time.sleep(delay)
            
        except Exception as e:
            print(f"❌ 요청 {i+1} 실패: {str(e)}")
            break
    
    return results

def check_redis_after_requests(redis_client):
    """요청 후 Redis 상태 확인"""
    print("\n🔍 요청 후 Redis 상태 확인...")
    
    if not redis_client:
        print("❌ Redis 클라이언트가 없습니다.")
        return
    
    try:
        # Rate limit 관련 키 검색
        rate_limit_keys = redis_client.keys("rate_limit:*")
        
        if rate_limit_keys:
            print(f"📊 Rate Limit 키 발견: {len(rate_limit_keys)}개")
            for key in rate_limit_keys:
                value = redis_client.get(key)
                ttl = redis_client.ttl(key)
                print(f"  🔑 {key}: {value} (TTL: {ttl}초)")
        else:
            print("📭 Rate Limit 키가 없습니다.")
            
            # 전체 키 확인
            all_keys = redis_client.keys("*")
            if all_keys:
                print(f"🗂️ 전체 키: {len(all_keys)}개")
                for key in all_keys[:5]:
                    value = redis_client.get(key)
                    print(f"  🔑 {key}: {value}")
            else:
                print("📭 Redis에 키가 전혀 없습니다.")
        
    except Exception as e:
        print(f"❌ Redis 상태 확인 실패: {str(e)}")

def check_middleware_configuration():
    """미들웨어 설정 확인"""
    print("\n⚙️ 미들웨어 설정 확인...")
    
    try:
        from app.middleware.rate_limit_middleware import rate_limit_service, redis_client
        
        print(f"📊 Rate Limit 서비스 설정:")
        print(f"  - 기본 제한: {rate_limit_service.default_limits}")
        print(f"  - 제외 경로: {rate_limit_service.excluded_paths}")
        print(f"  - 엔드포인트 제한: {rate_limit_service.endpoint_limits}")
        
        print(f"🔗 Redis 클라이언트 상태:")
        if redis_client:
            try:
                redis_client.ping()
                print("  ✅ Redis 연결 정상")
            except Exception as e:
                print(f"  ❌ Redis 연결 오류: {str(e)}")
        else:
            print("  ❌ Redis 클라이언트가 None입니다.")
        
        # 루트 경로가 제외되는지 확인
        is_excluded = rate_limit_service._is_excluded_path("/")
        print(f"🚫 루트 경로(/) 제외 여부: {is_excluded}")
        
    except Exception as e:
        print(f"❌ 미들웨어 설정 확인 실패: {str(e)}")

if __name__ == "__main__":
    print("🔧 SkyBoot Mail SaaS - Rate Limiting 디버깅")
    print(f"⏰ 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 1. Redis 연결 확인
    redis_client = check_redis_connection()
    
    # 2. 미들웨어 설정 확인
    check_middleware_configuration()
    
    # 3. 단일 요청 테스트
    single_response = test_single_request()
    
    # 4. 빠른 연속 요청 테스트
    rapid_results = test_rapid_requests()
    
    # 5. 요청 후 Redis 상태 확인
    check_redis_after_requests(redis_client)
    
    print("\n" + "=" * 60)
    print("🏁 디버깅 완료")
    
    # 결과 분석
    if rapid_results:
        rate_limited_count = sum(1 for r in rapid_results if r['status_code'] == 429)
        success_count = sum(1 for r in rapid_results if r['status_code'] == 200)
        
        print(f"📊 최종 결과:")
        print(f"  - 성공한 요청: {success_count}")
        print(f"  - Rate Limit 도달: {rate_limited_count}")
        print(f"  - 총 요청: {len(rapid_results)}")
        
        if rate_limited_count > 0:
            print("🎉 Rate Limiting이 작동합니다!")
        else:
            print("⚠️ Rate Limiting이 작동하지 않습니다.")
            print("💡 가능한 원인:")
            print("  - 미들웨어가 등록되지 않음")
            print("  - Redis 연결 문제")
            print("  - 제한 설정이 너무 높음")
            print("  - 경로가 제외 목록에 포함됨")