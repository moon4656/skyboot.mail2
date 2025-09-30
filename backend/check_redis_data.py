#!/usr/bin/env python3
"""
Redis Rate Limit 데이터 확인 스크립트
"""
import redis
import sys
import os
from datetime import datetime

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.config import settings

def check_redis_rate_limit_data():
    """Redis에서 rate limit 데이터 확인"""
    print("🔍 Redis Rate Limit 데이터 확인")
    print(f"⏰ 확인 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    try:
        # Redis 연결
        redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            db=settings.REDIS_DB,
            decode_responses=True
        )
        
        # 연결 테스트
        redis_client.ping()
        print("✅ Redis 연결 성공")
        
        # Rate limit 키 검색
        rate_limit_keys = redis_client.keys("rate_limit:*")
        
        if rate_limit_keys:
            print(f"📊 Rate Limit 키 발견: {len(rate_limit_keys)}개")
            print()
            
            for key in rate_limit_keys:
                value = redis_client.get(key)
                ttl = redis_client.ttl(key)
                
                print(f"🔑 키: {key}")
                print(f"   값: {value}")
                print(f"   TTL: {ttl}초 ({ttl//60}분 {ttl%60}초)")
                print()
        else:
            print("📭 Rate Limit 키가 없습니다.")
            
            # 전체 키 확인
            all_keys = redis_client.keys("*")
            if all_keys:
                print(f"🗂️ 전체 키: {len(all_keys)}개")
                for key in all_keys[:10]:  # 최대 10개만 표시
                    value = redis_client.get(key)
                    ttl = redis_client.ttl(key)
                    print(f"  🔑 {key}: {value} (TTL: {ttl}초)")
            else:
                print("📭 Redis에 키가 전혀 없습니다.")
        
        print("=" * 50)
        print("🏁 Redis 데이터 확인 완료")
        
    except Exception as e:
        print(f"❌ Redis 연결 실패: {str(e)}")

if __name__ == "__main__":
    check_redis_rate_limit_data()