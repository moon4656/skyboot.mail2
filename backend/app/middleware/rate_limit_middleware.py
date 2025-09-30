"""
SaaS 속도 제한 미들웨어

API 요청 속도 제한 및 DDoS 방지를 위한 미들웨어
"""
import logging
import time
import json
import traceback
from typing import Dict, Optional, Tuple, Callable
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
import redis
from datetime import datetime, timedelta

from ..config import settings

# 로거 설정
logger = logging.getLogger(__name__)

# Redis 연결 (캐시 및 속도 제한용)
try:
    redis_client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        password=settings.REDIS_PASSWORD,
        db=settings.REDIS_DB,
        decode_responses=True
    )
    redis_client.ping()
    logger.info("✅ Redis 연결 성공")
except Exception as e:
    logger.warning(f"⚠️ Redis 연결 실패: {str(e)}")
    redis_client = None


class RateLimitService:
    """속도 제한 서비스 클래스"""
    
    def __init__(self):
        # 기본 제한 설정 (분당 요청 수)
        self.default_limits = {
            "per_ip": 100,          # IP당 분당 100회
            "per_user": 200,        # 사용자당 분당 200회
            "per_org": 1000,        # 조직당 분당 1000회
            "auth_endpoints": 10,   # 인증 엔드포인트 분당 10회
            "mail_send": 50,        # 메일 발송 분당 50회
            "mail_read": 500        # 메일 읽기 분당 500회
        }
        
        # 제외 경로 설정
        self.excluded_paths = [
            "/docs", "/redoc", "/openapi.json", "/health", "/info"
        ]
        
        # 엔드포인트별 특별 제한
        self.endpoint_limits = {
            "/api/auth/login": self.default_limits["auth_endpoints"],
            "/api/auth/register": self.default_limits["auth_endpoints"],
            "/api/mail/send": self.default_limits["mail_send"],
            "/api/mail/bulk-send": 10,  # 대량 발송은 더 엄격하게
        }
        
        logger.info("🚦 속도 제한 서비스 초기화 완료")
    
    def _is_excluded_path(self, path: str) -> bool:
        """제외 경로 확인"""
        return any(path.startswith(excluded) for excluded in self.excluded_paths)
    
    def _extract_client_info(self, request: Request) -> Dict[str, str]:
        """클라이언트 정보 추출"""
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        return {
            "ip": client_ip,
            "user_agent": user_agent,
            "path": request.url.path,
            "method": request.method
        }
    
    def _check_rate_limits(self, request: Request, client_info: Dict[str, str]) -> Tuple[bool, Dict]:
        """속도 제한 검사"""
        if not redis_client:
            return True, {}
        
        current_time = int(time.time())
        window_start = current_time - 60  # 1분 윈도우
        
        # IP 기반 제한 검사
        ip_key = f"rate_limit:ip:{client_info['ip']}:{window_start // 60}"
        
        try:
            current_count = redis_client.get(ip_key) or 0
            current_count = int(current_count)
            
            limit = self.endpoint_limits.get(request.url.path, self.default_limits["per_ip"])
            
            if current_count >= limit:
                return False, {
                    "limit": limit,
                    "current": current_count,
                    "reset_time": (window_start // 60 + 1) * 60
                }
            
            return True, {
                "limit": limit,
                "current": current_count,
                "reset_time": (window_start // 60 + 1) * 60
            }
            
        except Exception as e:
            logger.error(f"❌ Redis 속도 제한 검사 오류: {str(e)}")
            return True, {}
    
    def _increment_counters(self, request: Request, client_info: Dict[str, str]):
        """요청 카운터 증가"""
        if not redis_client:
            return
        
        current_time = int(time.time())
        window_start = current_time - 60
        
        ip_key = f"rate_limit:ip:{client_info['ip']}:{window_start // 60}"
        
        try:
            redis_client.incr(ip_key)
            redis_client.expire(ip_key, 120)  # 2분 후 만료
        except Exception as e:
            logger.error(f"❌ Redis 카운터 증가 오류: {str(e)}")
    
    def _create_rate_limit_response(self, limit_info: Dict) -> JSONResponse:
        """속도 제한 응답 생성"""
        return JSONResponse(
            status_code=429,
            content={
                "error": "Rate limit exceeded",
                "message": "요청 한도를 초과했습니다. 잠시 후 다시 시도해주세요.",
                "limit": limit_info.get("limit"),
                "reset_time": limit_info.get("reset_time")
            },
            headers={
                "X-RateLimit-Limit": str(limit_info.get("limit", 0)),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(limit_info.get("reset_time", 0)),
                "Retry-After": "60"
            }
        )
    
    def _add_rate_limit_headers(self, response: Response, limit_info: Dict):
        """응답에 속도 제한 헤더 추가"""
        if limit_info:
            response.headers["X-RateLimit-Limit"] = str(limit_info.get("limit", 0))
            response.headers["X-RateLimit-Remaining"] = str(
                max(0, limit_info.get("limit", 0) - limit_info.get("current", 0))
            )
            response.headers["X-RateLimit-Reset"] = str(limit_info.get("reset_time", 0))


# 전역 서비스 인스턴스
rate_limit_service = RateLimitService()


async def rate_limit_middleware(request: Request, call_next: Callable):
    """
    속도 제한 미들웨어
    
    IP 주소, 사용자, 조직별로 요청 속도를 제한합니다.
    """
    start_time = time.time()
    
    try:
        # Redis가 사용 불가능한 경우 제한 없이 통과
        if not redis_client:
            logger.warning("⚠️ Redis 연결 없음 - 속도 제한 비활성화")
            response = await call_next(request)
            return response
        
        # 제외 경로 확인
        if rate_limit_service._is_excluded_path(request.url.path):
            response = await call_next(request)
            return response
        
        # 클라이언트 정보 추출
        client_info = rate_limit_service._extract_client_info(request)
        
        # 속도 제한 확인
        is_allowed, limit_info = rate_limit_service._check_rate_limits(request, client_info)
        
        if not is_allowed:
            # 제한 초과 시 429 응답 반환
            logger.warning(f"🚫 속도 제한 초과 - IP: {client_info['ip']}, 경로: {request.url.path}")
            return rate_limit_service._create_rate_limit_response(limit_info)
        
        # 요청 처리
        response = await call_next(request)
        
        # 카운터 증가
        rate_limit_service._increment_counters(request, client_info)
        
        # 응답 헤더에 제한 정보 추가
        rate_limit_service._add_rate_limit_headers(response, limit_info)
        
        # 처리 시간 로깅 (DEBUG 레벨)
        processing_time = time.time() - start_time
        logger.debug(f"⚡ 요청 처리 완료 - {request.method} {request.url.path} ({processing_time:.3f}초)")
        
        return response
        
    except Exception as e:
        logger.error(f"❌ 속도 제한 미들웨어 오류: {str(e)}")
        # 오류 발생 시 제한 없이 통과
        response = await call_next(request)
        return response


# 호환성을 위한 클래스 (사용하지 않음)
class RateLimitMiddleware:
    """호환성을 위한 더미 클래스"""
    def __init__(self, app):
        pass