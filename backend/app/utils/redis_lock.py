"""
Redis 분산 락 유틸리티

동시성이 높은 환경에서 조직 사용량 업데이트 시 
추가적인 락 메커니즘을 제공합니다.
"""

import redis
import time
import uuid
import asyncio
import logging
from typing import Optional
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class RedisDistributedLock:
    """Redis를 사용한 분산 락 구현"""
    
    def __init__(self, redis_client: redis.Redis, lock_timeout: int = 10):
        """
        Redis 분산 락 초기화
        
        Args:
            redis_client: Redis 클라이언트 인스턴스
            lock_timeout: 락 타임아웃 (초, 기본값: 10초)
        """
        self.redis_client = redis_client
        self.lock_timeout = lock_timeout
        self.lock_value = str(uuid.uuid4())  # 고유한 락 값
    
    async def acquire_lock(self, lock_key: str, timeout: int = 5) -> bool:
        """
        락을 획득합니다.
        
        Args:
            lock_key: 락 키
            timeout: 락 획득 대기 시간 (초)
            
        Returns:
            락 획득 성공 여부
        """
        end_time = time.time() + timeout
        
        while time.time() < end_time:
            # SET NX EX를 사용하여 원자적으로 락 설정
            if self.redis_client.set(
                lock_key, 
                self.lock_value, 
                nx=True,  # 키가 존재하지 않을 때만 설정
                ex=self.lock_timeout  # 만료 시간 설정
            ):
                logger.info(f"🔒 Redis 락 획득 성공 - 키: {lock_key}, 값: {self.lock_value}")
                return True
            
            # 짧은 시간 대기 후 재시도
            await asyncio.sleep(0.01)
        
        logger.warning(f"⚠️ Redis 락 획득 실패 - 키: {lock_key}, 타임아웃: {timeout}초")
        return False
    
    async def release_lock(self, lock_key: str) -> bool:
        """
        락을 해제합니다.
        
        Args:
            lock_key: 락 키
            
        Returns:
            락 해제 성공 여부
        """
        # Lua 스크립트를 사용하여 원자적으로 락 해제
        # 자신이 설정한 락만 해제할 수 있도록 보장
        lua_script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """
        
        try:
            result = self.redis_client.eval(lua_script, 1, lock_key, self.lock_value)
            if result:
                logger.info(f"🔓 Redis 락 해제 성공 - 키: {lock_key}")
                return True
            else:
                logger.warning(f"⚠️ Redis 락 해제 실패 - 키: {lock_key} (다른 프로세스의 락이거나 이미 만료됨)")
                return False
        except Exception as e:
            logger.error(f"❌ Redis 락 해제 중 오류 - 키: {lock_key}, 오류: {str(e)}")
            return False
    
    @asynccontextmanager
    async def lock_context(self, lock_key: str, timeout: int = 5):
        """
        컨텍스트 매니저를 사용한 락 관리
        
        Args:
            lock_key: 락 키
            timeout: 락 획득 대기 시간 (초)
            
        Usage:
            async with redis_lock.lock_context("org_usage_123") as acquired:
                if acquired:
                    # 락을 획득한 경우의 로직
                    pass
        """
        acquired = await self.acquire_lock(lock_key, timeout)
        try:
            yield acquired
        finally:
            if acquired:
                await self.release_lock(lock_key)


class OrganizationUsageLock:
    """조직 사용량 업데이트를 위한 특화된 락 클래스"""
    
    def __init__(self, redis_client: redis.Redis):
        """
        조직 사용량 락 초기화
        
        Args:
            redis_client: Redis 클라이언트 인스턴스
        """
        self.redis_lock = RedisDistributedLock(redis_client, lock_timeout=30)
    
    def get_usage_lock_key(self, org_id: str) -> str:
        """
        조직 사용량 락 키를 생성합니다.
        
        Args:
            org_id: 조직 ID
            
        Returns:
            락 키
        """
        return f"org_usage_lock:{org_id}"
    
    @asynccontextmanager
    async def lock_organization_usage(self, org_id: str, timeout: int = 3):
        """
        조직 사용량 업데이트를 위한 락을 획득합니다.
        
        Args:
            org_id: 조직 ID
            timeout: 락 획득 대기 시간 (초)
            
        Usage:
            async with usage_lock.lock_organization_usage("org_123") as acquired:
                if acquired:
                    # 조직 사용량 업데이트 로직
                    pass
        """
        lock_key = self.get_usage_lock_key(org_id)
        async with self.redis_lock.lock_context(lock_key, timeout) as acquired:
            yield acquired


# Redis 클라이언트 팩토리
def create_redis_client(host: str = "localhost", port: int = 6379, db: int = 0) -> redis.Redis:
    """
    Redis 클라이언트를 생성합니다.
    
    Args:
        host: Redis 서버 호스트
        port: Redis 서버 포트
        db: Redis 데이터베이스 번호
        
    Returns:
        Redis 클라이언트 인스턴스
    """
    try:
        client = redis.Redis(
            host=host,
            port=port,
            db=db,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True
        )
        
        # 연결 테스트
        client.ping()
        logger.info(f"✅ Redis 연결 성공 - {host}:{port}/{db}")
        return client
        
    except Exception as e:
        logger.error(f"❌ Redis 연결 실패 - {host}:{port}/{db}, 오류: {str(e)}")
        raise


# 전역 Redis 클라이언트 (선택적 사용)
_redis_client: Optional[redis.Redis] = None

def get_redis_client() -> Optional[redis.Redis]:
    """전역 Redis 클라이언트를 반환합니다."""
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = create_redis_client()
        except Exception:
            logger.warning("⚠️ Redis 클라이언트 초기화 실패 - 분산 락 기능 비활성화")
    return _redis_client