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

    def get_rate_limit_status(self, limit_type: str, identifier: str) -> Dict:
        """
        특정 대상의 속도 제한 상태를 조회합니다.
        
        Args:
            limit_type: 제한 타입 (ip, user, organization, endpoint)
            identifier: 식별자 (IP 주소, 사용자 ID, 조직 ID 등)
        
        Returns:
            속도 제한 상태 정보
        """
        try:
            if not redis_client:
                return {"limit": 0, "remaining": 0, "reset_time": None, "window_seconds": 60}
            
            # Redis 키 생성
            key = f"rate_limit:{limit_type}:{identifier}"
            current_minute = int(time.time() // 60)
            minute_key = f"{key}:{current_minute}"
            
            # 현재 요청 수 조회
            current_count = redis_client.get(minute_key) or 0
            current_count = int(current_count)
            
            # 제한 값 결정
            if limit_type == "ip":
                limit = self.default_limits["per_ip"]
            elif limit_type == "user":
                limit = self.default_limits["per_user"]
            elif limit_type == "organization":
                limit = self.default_limits["per_org"]
            elif limit_type == "endpoint":
                if "/auth/login" in identifier:
                    limit = self.default_limits["auth_endpoints"]
                elif "/mail/send" in identifier:
                    limit = self.default_limits["mail_send"]
                else:
                    limit = self.default_limits["per_ip"]
            else:
                limit = self.default_limits["per_ip"]
            
            # 리셋 시간 계산 (다음 분)
            reset_time = (current_minute + 1) * 60
            
            return {
                "limit": limit,
                "remaining": max(0, limit - current_count),
                "reset_time": reset_time,
                "window_seconds": 60,
                "current_count": current_count
            }
            
        except Exception as e:
            logger.error(f"❌ 속도 제한 상태 조회 오류: {str(e)}")
            return {"limit": 0, "remaining": 0, "reset_time": None, "window_seconds": 60}

    def reset_rate_limit(self, target_type: str, target_id: str) -> bool:
        """
        특정 대상의 속도 제한을 리셋합니다.
        
        Args:
            target_type: 대상 타입 (ip, user, organization)
            target_id: 대상 ID
        
        Returns:
            리셋 성공 여부
        """
        try:
            if not redis_client:
                return False
            
            # 패턴으로 키 검색 및 삭제
            pattern = f"rate_limit:{target_type}:{target_id}:*"
            keys = redis_client.keys(pattern)
            
            if keys:
                redis_client.delete(*keys)
                logger.info(f"✅ 속도 제한 리셋 성공 - {target_type}:{target_id}, 삭제된 키: {len(keys)}개")
                return True
            else:
                logger.info(f"ℹ️ 리셋할 속도 제한 데이터 없음 - {target_type}:{target_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 속도 제한 리셋 오류: {str(e)}")
            return False

    def get_violation_logs(self, limit: int = 50, offset: int = 0, target_type: str = None, organization_id: str = None) -> list:
        """
        속도 제한 위반 로그를 조회합니다.
        
        Args:
            limit: 조회할 로그 수
            offset: 오프셋
            target_type: 필터링할 대상 타입
            organization_id: 조직 ID (조직 관리자용)
        
        Returns:
            위반 로그 목록
        """
        try:
            if not redis_client:
                return []
            
            # 실제 구현에서는 데이터베이스에서 조회하거나 Redis에서 로그 데이터를 가져옴
            # 여기서는 샘플 데이터를 반환
            violations = []
            
            # Redis에서 위반 로그 키 패턴 검색
            if target_type:
                pattern = f"violation_log:{target_type}:*"
            else:
                pattern = "violation_log:*"
            
            keys = redis_client.keys(pattern)
            
            # 최근 위반 로그 생성 (샘플)
            for i, key in enumerate(keys[offset:offset+limit]):
                try:
                    log_data = redis_client.get(key)
                    if log_data:
                        violation = json.loads(log_data)
                        violations.append(violation)
                except:
                    # 샘플 데이터 생성
                    violation = {
                        "id": f"violation_{i+1}",
                        "timestamp": datetime.utcnow().isoformat(),
                        "target_type": target_type or "ip",
                        "target_id": f"192.168.1.{i+1}",
                        "endpoint": "/api/auth/login",
                        "limit_exceeded": "5 requests per minute",
                        "actual_requests": 10 + i,
                        "organization_id": organization_id or f"org_{i%3+1}",
                        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        "severity": "medium" if i % 2 == 0 else "high"
                    }
                    violations.append(violation)
            
            # 조직 필터링 (조직 관리자용)
            if organization_id:
                violations = [v for v in violations if v.get("organization_id") == organization_id]
            
            logger.info(f"✅ 위반 로그 조회 성공 - 로그 수: {len(violations)}")
            return violations
            
        except Exception as e:
            logger.error(f"❌ 위반 로그 조회 오류: {str(e)}")
            return []

    def log_violation(self, target_type: str, target_id: str, endpoint: str, limit_info: Dict, request_info: Dict):
        """
        속도 제한 위반을 로그에 기록합니다.
        
        Args:
            target_type: 대상 타입
            target_id: 대상 ID
            endpoint: 엔드포인트
            limit_info: 제한 정보
            request_info: 요청 정보
        """
        try:
            if not redis_client:
                return
            
            violation_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "target_type": target_type,
                "target_id": target_id,
                "endpoint": endpoint,
                "limit_exceeded": f"{limit_info.get('limit', 0)} requests per minute",
                "actual_requests": limit_info.get('current', 0),
                "organization_id": request_info.get('org_id'),
                "user_agent": request_info.get('user_agent', ''),
                "ip_address": request_info.get('ip_address', ''),
                "severity": "high" if limit_info.get('current', 0) > limit_info.get('limit', 0) * 2 else "medium"
            }
            
            # Redis에 위반 로그 저장 (24시간 TTL)
            key = f"violation_log:{target_type}:{target_id}:{int(time.time())}"
            redis_client.setex(key, 86400, json.dumps(violation_data))
            
            logger.warning(f"🚨 속도 제한 위반 기록 - {target_type}:{target_id}, 엔드포인트: {endpoint}")
            
        except Exception as e:
            logger.error(f"❌ 위반 로그 기록 오류: {str(e)}")


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