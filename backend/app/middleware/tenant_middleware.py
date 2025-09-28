"""
통합 테넌트 미들웨어

다중 조직 지원을 위한 테넌트 격리 및 컨텍스트 관리
tenant_middleware.py와 tenant.py의 최고 기능들을 통합
"""
import logging
import re
import time
from typing import Optional, Dict, Any
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session
from contextvars import ContextVar
from datetime import datetime, timedelta

from ..database.user import get_db
from ..model.organization_model import Organization
from ..config import settings

# 로깅 설정
logger = logging.getLogger(__name__)

# 컨텍스트 변수 (요청별 조직 정보 저장)
current_org_context: ContextVar[Optional[Dict[str, Any]]] = ContextVar('current_org', default=None)
current_user_context: ContextVar[Optional[Dict[str, Any]]] = ContextVar('current_user', default=None)

# 조직 정보 캐시 (메모리 기반)
_organization_cache: Dict[str, Dict[str, Any]] = {}
_cache_timestamps: Dict[str, datetime] = {}
CACHE_EXPIRY_MINUTES = 5  # 5분 캐시 유지


class TenantMiddleware(BaseHTTPMiddleware):
    """
    통합 테넌트 미들웨어
    
    서브도메인, 헤더, JWT 토큰 등 다양한 방법으로 조직을 식별하고
    요청 컨텍스트에 조직 정보를 설정하여 데이터 격리를 보장합니다.
    """
    
    def __init__(self, app, excluded_paths: Optional[list] = None, default_org_code: str = "default"):
        """
        테넌트 미들웨어 초기화
        
        Args:
            app: FastAPI 애플리케이션
            excluded_paths: 테넌트 검증을 제외할 경로 목록
            default_org_code: 기본 조직 코드
        """
        super().__init__(app)
        self.excluded_paths = excluded_paths or [
            "/docs", "/redoc", "/openapi.json", "/favicon.ico",
            "/static", "/health", "/info", "/api/system",
            "/api/v1/auth/login", "/api/v1/auth/register", "/api/v1/organizations/create"
        ]
        self.default_org_code = default_org_code
        logger.info("🏢 통합 테넌트 미들웨어 초기화 완료")
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """
        캐시가 유효한지 확인
        
        Args:
            cache_key: 캐시 키
            
        Returns:
            캐시 유효 여부
        """
        if cache_key not in _cache_timestamps:
            return False
        
        cache_time = _cache_timestamps[cache_key]
        expiry_time = cache_time + timedelta(minutes=CACHE_EXPIRY_MINUTES)
        return datetime.now() < expiry_time
    
    def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        캐시에서 조직 정보 조회
        
        Args:
            cache_key: 캐시 키
            
        Returns:
            캐시된 조직 정보 또는 None
        """
        if self._is_cache_valid(cache_key) and cache_key in _organization_cache:
            logger.debug(f"🚀 캐시에서 조직 정보 조회: {cache_key}")
            return _organization_cache[cache_key]
        return None
    
    def _set_cache(self, cache_key: str, org_info: Dict[str, Any]) -> None:
        """
        캐시에 조직 정보 저장
        
        Args:
            cache_key: 캐시 키
            org_info: 조직 정보
        """
        _organization_cache[cache_key] = org_info
        _cache_timestamps[cache_key] = datetime.now()
        logger.debug(f"💾 캐시에 조직 정보 저장: {cache_key}")
    
    def _clear_expired_cache(self) -> None:
        """
        만료된 캐시 항목 정리
        """
        current_time = datetime.now()
        expired_keys = []
        
        for cache_key, cache_time in _cache_timestamps.items():
            expiry_time = cache_time + timedelta(minutes=CACHE_EXPIRY_MINUTES)
            if current_time >= expiry_time:
                expired_keys.append(cache_key)
        
        for key in expired_keys:
            _organization_cache.pop(key, None)
            _cache_timestamps.pop(key, None)
            logger.debug(f"🗑️ 만료된 캐시 삭제: {key}")
    
    async def dispatch(self, request: Request, call_next):
        """
        요청 처리 및 테넌트 컨텍스트 설정
        
        Args:
            request: HTTP 요청
            call_next: 다음 미들웨어/핸들러
            
        Returns:
            HTTP 응답
        """
        start_time = time.time()
        
        try:
            # 제외 경로 확인
            if self._is_excluded_path(request.url.path):
                logger.debug(f"🚫 테넌트 검증 제외 경로: {request.url.path}")
                return await call_next(request)
            
            logger.debug(f"🏢 테넌트 검증 필요 경로: {request.url.path}")
            
            # 조직 정보 추출 및 설정
            org_info = await self._extract_organization_info(request)
            
            if not org_info:
                logger.warning(f"🏢 조직을 찾을 수 없음 - 개발용 기본 조직 사용 - 경로: {request.url.path}")
                org_info = self._create_development_default_org()
                
            if not org_info:
                logger.error(f"❌ 조직 정보 생성 실패 - 경로: {request.url.path}")
                return JSONResponse(
                    status_code=500,
                    content={
                        "error": "ORGANIZATION_CREATION_FAILED",
                        "message": "조직 정보를 생성할 수 없습니다.",
                        "path": request.url.path
                    }
                )
            
            # 조직 상태 확인
            if not org_info.get('is_active', True):
                logger.warning(f"🚫 비활성 조직 접근 시도 - org_code: {org_info.get('org_code')}")
                return JSONResponse(
                    status_code=403,
                    content={
                        "error": "ORGANIZATION_INACTIVE",
                        "message": "비활성화된 조직입니다.",
                        "org_code": org_info.get('org_code')
                    }
                )
            
            # 컨텍스트 설정
            current_org_context.set(org_info)
            logger.debug(f"🏢 조직 컨텍스트 설정: {org_info.get('name', 'Unknown')} (ID: {org_info.get('id', 'Unknown')})")
            
            # 요청 state에 조직 정보 추가 (기존 라우터 호환성)
            request.state.organization = org_info
            request.state.org_id = str(org_info.get('id', 'unknown'))
            request.state.org_code = org_info.get('org_code', self.default_org_code)
            
            logger.info(f"🏢 테넌트 식별 완료 - org_code: {org_info.get('org_code')}, org_id: {org_info.get('id', 'unknown')}")
            
            # 다음 미들웨어/핸들러 호출
            response = await call_next(request)
            
            # 응답 헤더에 조직 정보 추가 (ASCII 안전한 값만)
            try:
                response.headers["X-Organization-ID"] = str(org_info.get('id', 'unknown'))
                org_code = org_info.get('org_code')
                if org_code:
                    # ASCII 안전한 문자열로 변환
                    org_code_safe = str(org_code).encode('ascii', 'ignore').decode('ascii')
                    if org_code_safe:
                        response.headers["X-Organization-Code"] = org_code_safe
            except (UnicodeEncodeError, UnicodeDecodeError) as e:
                logger.warning(f"⚠️ 조직 정보 헤더 설정 오류 (인코딩): {str(e)}")
            except Exception as e:
                logger.warning(f"⚠️ 조직 정보 헤더 설정 오류: {str(e)}")
            
            # 처리 시간 로깅
            process_time = time.time() - start_time
            response.headers["X-Process-Time"] = str(process_time)
            
            logger.debug(f"✅ 테넌트 미들웨어 처리 완료 - 시간: {process_time:.3f}초")
            return response
            
        except HTTPException as e:
            logger.warning(f"⚠️ 테넌트 미들웨어 HTTP 예외: {e.detail}")
            raise e
            
        except Exception as e:
            logger.error(f"❌ 테넌트 미들웨어 오류: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={
                    "error": "TENANT_MIDDLEWARE_ERROR",
                    "message": "테넌트 처리 중 오류가 발생했습니다.",
                    "details": str(e) if hasattr(settings, 'is_development') and settings.is_development() else None
                }
            )
        
        finally:
            # 컨텍스트 정리
            current_org_context.set(None)
            current_user_context.set(None)
    
    def _is_excluded_path(self, path: str) -> bool:
        """
        제외 경로 확인
        
        Args:
            path: 요청 경로
            
        Returns:
            제외 여부
        """
        return any(path.startswith(excluded) for excluded in self.excluded_paths)
    
    async def _extract_organization_info(self, request: Request) -> Optional[Dict[str, Any]]:
        """
        요청에서 조직 정보 추출
        
        다음 순서로 조직 정보를 찾습니다:
        1. Authorization 헤더의 JWT 토큰
        2. X-Organization-Code/X-Organization-ID/X-Organization-UUID 헤더
        3. 도메인/서브도메인 기반 조직 식별
        4. 쿼리 파라미터 (org_code, org_id, org_uuid)
        5. 기본 조직
        
        Args:
            request: HTTP 요청
            
        Returns:
            조직 정보 딕셔너리 또는 None
        """
        try:
            # 1. JWT 토큰에서 조직 정보 추출
            org_info = await self._extract_from_jwt(request)
            if org_info:
                logger.debug(f"🔑 JWT에서 조직 추출: {org_info.get('org_code')}")
                return org_info
            
            # 2. 헤더에서 조직 정보 추출
            org_info = await self._extract_from_header(request)
            if org_info:
                logger.debug(f"📋 헤더에서 조직 추출: {org_info.get('org_code')}")
                return org_info
            
            # 3. 도메인 기반 조직 식별
            org_info = await self._extract_from_domain(request)
            if org_info:
                logger.debug(f"🌐 도메인에서 조직 추출: {org_info.get('org_code')}")
                return org_info
            
            # 4. 쿼리 파라미터에서 추출
            org_info = await self._extract_from_query(request)
            if org_info:
                logger.debug(f"🔗 쿼리에서 조직 추출: {org_info.get('org_code')}")
                return org_info
            
            # 5. 기본 조직 사용
            logger.debug(f"🏠 기본 조직 사용: {self.default_org_code}")
            return await self._get_default_organization()
            
        except Exception as e:
            logger.error(f"❌ 조직 정보 추출 오류: {str(e)}")
            return await self._get_default_organization()
    
    async def _extract_from_jwt(self, request: Request) -> Optional[Dict[str, Any]]:
        """
        JWT 토큰에서 조직 정보 추출
        
        Args:
            request: HTTP 요청
            
        Returns:
            조직 정보 또는 None
        """
        try:
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return None
            
            token = auth_header.split(" ")[1]
            if not token:
                return None
            
            # JWT 토큰 디코딩
            from ..service.auth_service import AuthService
            payload = AuthService.verify_token(token, "access")
            
            if not payload:
                logger.warning("❌ JWT 토큰 검증 실패")
                return None
            
            # JWT에서 조직 ID 추출
            org_id = payload.get("org_id")
            if not org_id:
                logger.warning("❌ JWT에 조직 ID가 없음")
                return None
            
            # 데이터베이스에서 조직 정보 조회
            org_info = await self._get_organization_by_id_or_uuid(org_id, None)
            if org_info:
                logger.info(f"✅ JWT에서 조직 정보 추출 성공: {org_info['name']} ({org_id})")
                return org_info
            else:
                logger.warning(f"❌ 조직을 찾을 수 없음: {org_id}")
                return None
            
        except Exception as e:
            logger.error(f"❌ JWT에서 조직 정보 추출 오류: {str(e)}")
            return None
    
    async def _extract_from_header(self, request: Request) -> Optional[Dict[str, Any]]:
        """
        헤더에서 조직 정보 추출
        
        Args:
            request: HTTP 요청
            
        Returns:
            조직 정보 또는 None
        """
        try:
            # X-Organization-Code 헤더 우선 확인
            org_code = request.headers.get("X-Organization-Code")
            if org_code:
                return await self._get_organization_by_code(org_code)
            
            # X-Organization-ID/UUID 헤더 확인
            org_id = request.headers.get("X-Organization-ID")
            org_uuid = request.headers.get("X-Organization-UUID")
            
            if org_id or org_uuid:
                return await self._get_organization_by_id_or_uuid(org_id, org_uuid)
            
            return None
            
        except Exception as e:
            logger.error(f"❌ 헤더에서 조직 정보 추출 오류: {str(e)}")
            return None
    
    async def _extract_from_domain(self, request: Request) -> Optional[Dict[str, Any]]:
        """
        도메인 기반 조직 식별
        
        Args:
            request: HTTP 요청
            
        Returns:
            조직 정보 또는 None
        """
        try:
            host = request.headers.get("host", "")
            subdomain = self._extract_subdomain(host)
            
            if subdomain and subdomain != "www":
                return await self._get_organization_by_subdomain(subdomain)
            
            return None
            
        except Exception as e:
            logger.error(f"❌ 도메인에서 조직 정보 추출 오류: {str(e)}")
            return None
    
    def _extract_subdomain(self, host: str) -> Optional[str]:
        """
        호스트에서 서브도메인 추출
        
        Args:
            host: 호스트 문자열
            
        Returns:
            서브도메인 또는 None
        """
        if not host:
            return None
        
        # 포트 번호 제거
        host = host.split(':')[0]
        
        # IP 주소인 경우 서브도메인 없음
        if re.match(r'^\d+\.\d+\.\d+\.\d+$', host):
            return None
        
        # localhost인 경우 서브도메인 없음
        if host in ['localhost', '127.0.0.1']:
            return None
        
        # 도메인 분할
        parts = host.split('.')
        
        # 최소 3개 부분이 있어야 서브도메인 존재 (subdomain.domain.com)
        if len(parts) >= 3:
            return parts[0]
        
        return None
    
    async def _extract_from_query(self, request: Request) -> Optional[Dict[str, Any]]:
        """
        쿼리 파라미터에서 조직 정보 추출
        
        Args:
            request: HTTP 요청
            
        Returns:
            조직 정보 또는 None
        """
        try:
            # org_code 쿼리 파라미터 우선 확인
            org_code = request.query_params.get("org_code")
            if org_code:
                return await self._get_organization_by_code(org_code)
            
            # org_id, org_uuid 쿼리 파라미터 확인
            org_id = request.query_params.get("org_id")
            org_uuid = request.query_params.get("org_uuid")
            
            if org_id or org_uuid:
                return await self._get_organization_by_id_or_uuid(org_id, org_uuid)
            
            return None
            
        except Exception as e:
            logger.error(f"❌ 쿼리에서 조직 정보 추출 오류: {str(e)}")
            return None
    
    async def _get_organization_by_code(self, org_code: str) -> Optional[Dict[str, Any]]:
        """
        조직 코드로 조직 정보 조회 (캐싱 적용)
        
        Args:
            org_code: 조직 코드
            
        Returns:
            조직 정보 또는 None
        """
        try:
            # 캐시 키 생성
            cache_key = f"org_code:{org_code}"
            
            # 만료된 캐시 정리
            self._clear_expired_cache()
            
            # 캐시에서 조직 정보 조회
            cached_org = self._get_from_cache(cache_key)
            if cached_org:
                logger.debug(f"🎯 조직 정보 캐시 히트: {cache_key}")
                return cached_org
            
            # 캐시 미스 - 데이터베이스에서 조회
            logger.debug(f"💾 조직 정보 데이터베이스 조회: {cache_key}")
            
            db_gen = get_db()
            db: Session = next(db_gen)
            
            try:
                org = db.query(Organization).filter(
                    Organization.org_code == org_code,
                    Organization.deleted_at.is_(None)
                ).first()
                
                if org:
                    org_info = self._organization_to_dict(org)
                    # 캐시에 저장
                    self._set_cache(cache_key, org_info)
                    return org_info
                
                return None
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"❌ 조직 코드 조회 오류: {str(e)}")
            return None
    
    async def _get_organization_by_id_or_uuid(self, org_id: Optional[str], org_uuid: Optional[str]) -> Optional[Dict[str, Any]]:
        """
        ID 또는 UUID로 조직 정보 조회 (캐싱 적용)
        
        Args:
            org_id: 조직 ID
            org_uuid: 조직 UUID
            
        Returns:
            조직 정보 또는 None
        """
        try:
            # 캐시 키 생성
            cache_key = f"org_id_uuid:{org_uuid or org_id}"
            
            # 만료된 캐시 정리
            self._clear_expired_cache()
            
            # 캐시에서 조직 정보 조회
            cached_org = self._get_from_cache(cache_key)
            if cached_org:
                logger.debug(f"🎯 조직 정보 캐시 히트: {cache_key}")
                return cached_org
            
            # 캐시 미스 - 데이터베이스에서 조회
            logger.debug(f"💾 조직 정보 데이터베이스 조회: {cache_key}")
            
            db_gen = get_db()
            db: Session = next(db_gen)
            
            try:
                query = db.query(Organization)
                if org_uuid:
                    query = query.filter(Organization.org_id == org_uuid)
                elif org_id:
                    query = query.filter(Organization.org_id == org_id)
                else:
                    return None
                
                org = query.filter(Organization.deleted_at.is_(None)).first()
                if org:
                    org_info = self._organization_to_dict(org)
                    # 캐시에 저장
                    self._set_cache(cache_key, org_info)
                    return org_info
                
                return None
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"❌ 조직 조회 오류: {str(e)}")
            return None
    
    async def _get_organization_by_subdomain(self, subdomain: str) -> Optional[Dict[str, Any]]:
        """
        서브도메인으로 조직 정보 조회 (캐싱 적용)
        
        Args:
            subdomain: 서브도메인
            
        Returns:
            조직 정보 또는 None
        """
        try:
            # 캐시 키 생성
            cache_key = f"org_subdomain:{subdomain}"
            
            # 만료된 캐시 정리
            self._clear_expired_cache()
            
            # 캐시에서 조직 정보 조회
            cached_org = self._get_from_cache(cache_key)
            if cached_org:
                logger.debug(f"🎯 조직 정보 캐시 히트: {cache_key}")
                return cached_org
            
            # 캐시 미스 - 데이터베이스에서 조회
            logger.debug(f"💾 조직 정보 데이터베이스 조회: {cache_key}")
            
            db_gen = get_db()
            db: Session = next(db_gen)
            
            try:
                # 서브도메인을 조직 코드 또는 서브도메인 필드로 매칭
                org = db.query(Organization).filter(
                    Organization.deleted_at.is_(None),
                    (Organization.org_code == subdomain) | 
                    (Organization.subdomain == subdomain if hasattr(Organization, 'subdomain') else False)
                ).first()
                
                if org:
                    org_info = self._organization_to_dict(org)
                    # 캐시에 저장
                    self._set_cache(cache_key, org_info)
                    return org_info
                
                return None
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"❌ 서브도메인 조직 조회 오류: {str(e)}")
            return None
    
    async def _get_default_organization(self) -> Optional[Dict[str, Any]]:
        """
        기본 조직 정보 조회 (캐싱 적용)
        
        Returns:
            기본 조직 정보 또는 None
        """
        # 캐시 키 생성
        cache_key = f"default_org:{self.default_org_code}"
        
        # 만료된 캐시 정리
        self._clear_expired_cache()
        
        # 캐시에서 조회
        cached_org = self._get_from_cache(cache_key)
        if cached_org:
            return cached_org
        
        try:
            db_gen = get_db()
            db: Session = next(db_gen)
            
            try:
                # 기본 조직 코드로 조직 찾기
                org = db.query(Organization).filter(
                    Organization.org_code == self.default_org_code,
                    Organization.deleted_at.is_(None)
                ).first()
                
                # 기본 조직이 없으면 첫 번째 활성 조직 사용
                if not org:
                    org = db.query(Organization).filter(
                        Organization.deleted_at.is_(None)
                    ).first()
                
                if org:
                    org_info = self._organization_to_dict(org)
                    # 캐시에 저장
                    self._set_cache(cache_key, org_info)
                    return org_info
                
                # 데이터베이스에 조직이 없는 경우 개발용 기본 조직 반환
                logger.warning("⚠️ 데이터베이스에 조직이 없어 개발용 기본 조직을 생성합니다.")
                default_org = self._create_development_default_org()
                # 개발용 조직도 캐시에 저장 (짧은 시간)
                self._set_cache(cache_key, default_org)
                return default_org
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"❌ 기본 조직 조회 오류: {str(e)}")
            # 오류 발생 시에도 개발용 기본 조직 반환
            default_org = self._create_development_default_org()
            # 오류 상황에서도 캐시에 저장 (재시도 방지)
            self._set_cache(cache_key, default_org)
            return default_org
    
    def _create_development_default_org(self) -> Dict[str, Any]:
        """
        개발용 기본 조직 정보 생성
        
        Returns:
            기본 조직 정보 딕셔너리
        """
        try:
            # 개발용 기본 조직 정보 (ASCII 안전한 값들)
            default_org = {
                "id": "default-org-001",
                "org_code": self.default_org_code,
                "name": "Default Organization",
                "domain": "localhost",
                "subdomain": None,
                "is_active": True,
                "status": "active",
                "max_users": 1000,
                "max_storage_gb": 100,
                "settings": {}
            }
            logger.info(f"🏢 개발용 기본 조직 정보 생성: {default_org['name']}")
            return default_org
        except Exception as e:
            logger.error(f"❌ 개발용 기본 조직 정보 생성 오류: {str(e)}")
            # 최소한의 안전한 기본값
            return {
                "id": "fallback-org",
                "org_code": "FALLBACK",
                "name": "Fallback Organization",
                "domain": None,
                "subdomain": None,
                "is_active": True,
                "status": "active",
                "max_users": 100,
                "max_storage_gb": 10,
                "settings": {}
            }
    
    def _organization_to_dict(self, org: Organization) -> Dict[str, Any]:
        """
        Organization 모델을 딕셔너리로 변환
        
        Args:
            org: Organization 모델 인스턴스
            
        Returns:
            조직 정보 딕셔너리
        """
        if not org:
            logger.error("❌ 조직 객체가 None입니다.")
            return None
            
        try:
            # 조직 객체가 이미 딕셔너리인 경우 그대로 반환
            if isinstance(org, dict):
                return org
                
            return {
                "id": getattr(org, 'org_id', None),
                "org_code": getattr(org, 'org_code', None),
                "name": getattr(org, 'name', None),
                "domain": getattr(org, 'domain', None),
                "subdomain": getattr(org, 'subdomain', None),
                "is_active": getattr(org, 'is_active', True),
                "status": getattr(org, 'status', 'active'),
                "max_users": getattr(org, 'max_users', None),
                "max_storage_gb": getattr(org, 'max_storage_gb', None),
                "settings": getattr(org, 'settings', {}) or {}
            }
        except Exception as e:
            logger.error(f"❌ 조직 정보 변환 오류: {str(e)}")
            return None


# ContextVar 기반 헬퍼 함수들 (글로벌 컨텍스트)
def get_current_org() -> Optional[Dict[str, Any]]:
    """
    현재 요청의 조직 정보 반환 (ContextVar 기반)
    
    Returns:
        조직 정보 딕셔너리 또는 None
    """
    return current_org_context.get()


def get_current_org_id_from_context() -> Optional[str]:
    """
    현재 요청의 조직 ID 반환 (ContextVar 기반)
    
    Returns:
        조직 ID 문자열 또는 None
    """
    org = current_org_context.get()
    if org:
        return str(org.get('id', ''))
    return None


def get_current_user() -> Optional[Dict[str, Any]]:
    """
    현재 요청의 사용자 정보 반환 (ContextVar 기반)
    
    Returns:
        사용자 정보 딕셔너리 또는 None
    """
    return current_user_context.get()


def require_org() -> Dict[str, Any]:
    """
    조직 정보 필수 반환 (없으면 예외 발생)
    
    Returns:
        조직 정보 딕셔너리
        
    Raises:
        HTTPException: 조직 정보가 없는 경우
    """
    org = get_current_org()
    if not org:
        raise HTTPException(
            status_code=400,
            detail="조직 정보가 필요합니다."
        )
    return org


def set_current_user(user_info: Dict[str, Any]) -> None:
    """
    현재 사용자 컨텍스트 설정
    
    Args:
        user_info: 사용자 정보 딕셔너리
    """
    current_user_context.set(user_info)


# Request.state 기반 헬퍼 함수들 (기존 코드 호환성)
def get_current_organization(request: Request) -> Dict[str, Any]:
    """
    현재 요청의 조직 정보 반환 (request.state 기반)
    
    Args:
        request: HTTP 요청 객체
        
    Returns:
        조직 정보 딕셔너리
        
    Raises:
        HTTPException: 조직 정보가 설정되지 않은 경우
    """
    if not hasattr(request.state, 'organization'):
        raise HTTPException(
            status_code=500,
            detail="조직 정보가 설정되지 않았습니다. 테넌트 미들웨어를 확인하세요."
        )
    return request.state.organization


def get_current_org_id(request: Request) -> str:
    """
    현재 요청의 조직 ID 반환 (request.state 기반)
    
    Args:
        request: HTTP 요청 객체
        
    Returns:
        조직 ID 문자열
        
    Raises:
        HTTPException: 조직 ID가 설정되지 않은 경우
    """
    if not hasattr(request.state, 'org_id'):
        raise HTTPException(
            status_code=500,
            detail="조직 ID가 설정되지 않았습니다. 테넌트 미들웨어를 확인하세요."
        )
    return request.state.org_id


def get_current_org_code(request: Request) -> str:
    """
    현재 요청의 조직 코드 반환 (request.state 기반)
    
    Args:
        request: HTTP 요청 객체
        
    Returns:
        조직 코드 문자열
        
    Raises:
        HTTPException: 조직 코드가 설정되지 않은 경우
    """
    if not hasattr(request.state, 'org_code'):
        raise HTTPException(
            status_code=500,
            detail="조직 코드가 설정되지 않았습니다. 테넌트 미들웨어를 확인하세요."
        )
    return request.state.org_code