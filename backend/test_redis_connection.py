#!/usr/bin/env python3
"""
Redis 연결 테스트 스크립트

SkyBoot Mail SaaS 프로젝트의 Redis 연결을 테스트합니다.
"""
import redis
import sys
import os

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.config import settings

def test_redis_connection():
    """Redis 연결 테스트"""
    print("🔍 Redis 연결 테스트 시작...")
    print(f"📍 Redis 설정: {settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}")
    
    try:
        # Redis 클라이언트 생성
        redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            db=settings.REDIS_DB,
            decode_responses=True
        )
        
        # 연결 테스트
        print("🔗 Redis 서버에 연결 중...")
        response = redis_client.ping()
        print(f"✅ Redis PING 응답: {response}")
        
        # 기본 읽기/쓰기 테스트
        print("📝 Redis 읽기/쓰기 테스트...")
        test_key = "skyboot_test_key"
        test_value = "SkyBoot Mail SaaS Redis Test"
        
        # 데이터 쓰기
        redis_client.set(test_key, test_value, ex=60)  # 60초 후 만료
        print(f"✅ 데이터 쓰기 성공: {test_key} = {test_value}")
        
        # 데이터 읽기
        retrieved_value = redis_client.get(test_key)
        print(f"✅ 데이터 읽기 성공: {test_key} = {retrieved_value}")
        
        # 데이터 검증
        if retrieved_value == test_value:
            print("✅ 데이터 무결성 확인 완료")
        else:
            print("❌ 데이터 무결성 오류")
            return False
        
        # 카운터 테스트 (rate limiting에 사용)
        print("🔢 카운터 테스트 (rate limiting 기능)...")
        counter_key = "skyboot_rate_limit_test"
        
        # 카운터 증가
        for i in range(5):
            count = redis_client.incr(counter_key)
            print(f"  카운터 {i+1}: {count}")
        
        # TTL 설정
        redis_client.expire(counter_key, 60)
        ttl = redis_client.ttl(counter_key)
        print(f"✅ TTL 설정 완료: {ttl}초")
        
        # 정리
        redis_client.delete(test_key, counter_key)
        print("🧹 테스트 데이터 정리 완료")
        
        print("🎉 Redis 연결 테스트 모든 항목 통과!")
        return True
        
    except redis.ConnectionError as e:
        print(f"❌ Redis 연결 오류: {str(e)}")
        print("💡 Redis 서버가 실행 중인지 확인하세요.")
        return False
        
    except redis.AuthenticationError as e:
        print(f"❌ Redis 인증 오류: {str(e)}")
        print("💡 Redis 비밀번호 설정을 확인하세요.")
        return False
        
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {str(e)}")
        return False

def test_rate_limit_middleware():
    """Rate limit 미들웨어 관련 Redis 기능 테스트"""
    print("\n🚦 Rate Limit 미들웨어 Redis 기능 테스트...")
    
    try:
        from app.middleware.rate_limit_middleware import redis_client
        
        if redis_client is None:
            print("❌ Rate limit 미들웨어의 Redis 클라이언트가 None입니다.")
            return False
        
        # 미들웨어의 Redis 클라이언트 테스트
        response = redis_client.ping()
        print(f"✅ Rate limit 미들웨어 Redis 연결 성공: {response}")
        
        # 실제 rate limiting 시뮬레이션
        test_ip = "192.168.1.100"
        rate_limit_key = f"rate_limit:ip:{test_ip}"
        
        # 요청 카운터 증가
        current_count = redis_client.incr(rate_limit_key)
        redis_client.expire(rate_limit_key, 60)  # 1분 TTL
        
        print(f"✅ Rate limiting 시뮬레이션 성공: IP {test_ip}, 카운트: {current_count}")
        
        # 정리
        redis_client.delete(rate_limit_key)
        
        return True
        
    except Exception as e:
        print(f"❌ Rate limit 미들웨어 테스트 오류: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 SkyBoot Mail SaaS - Redis 연결 테스트")
    print("=" * 50)
    
    # 기본 Redis 연결 테스트
    basic_test_result = test_redis_connection()
    
    # Rate limit 미들웨어 테스트
    middleware_test_result = test_rate_limit_middleware()
    
    print("\n" + "=" * 50)
    print("📊 테스트 결과 요약:")
    print(f"  기본 Redis 연결: {'✅ 성공' if basic_test_result else '❌ 실패'}")
    print(f"  Rate Limit 미들웨어: {'✅ 성공' if middleware_test_result else '❌ 실패'}")
    
    if basic_test_result and middleware_test_result:
        print("\n🎉 모든 Redis 테스트가 성공했습니다!")
        print("💡 이제 SkyBoot Mail SaaS에서 Redis 기반 rate limiting을 사용할 수 있습니다.")
        sys.exit(0)
    else:
        print("\n❌ 일부 테스트가 실패했습니다.")
        print("💡 Redis 서버 상태와 설정을 다시 확인해주세요.")
        sys.exit(1)