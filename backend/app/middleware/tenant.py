"""
SaaS 테넌트 미들웨어

다중 조직 지원을 위한 테넌트 격리 및 컨텍스트 관리
"""
import logging
import re
from typing import Optional, Dict, Any
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session
from contextvars import ContextVar
import time

from ..database.base import get_db
from ..model import Organization
from ..config import settings

# 로거 설정
logger = logging.getLogger(__name__)

# 컨텍스트 변수 - 현재 요청의 조직 정보 저장
current_org_context: ContextVar[Optional[Dict[str, Any]]] = ContextVar('current_org', default=None)
current_user_context: ContextVar[Optional[Dict[str, Any]]] = ContextVar('current_user', default=None)


class TenantMiddleware(BaseHTTPMiddleware):
    """
    테넌트 미들웨어
    
    모든 요청에 대해 조직 컨텍스트를 설정하고 데이터 격리를 보장합니다.
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
            "/docs", "/redoc", "/openapi.json", "/health", "/info",
            "/api/v1/auth/login", "/api/v1/auth/register", "/api/v1/organizations/create"
        ]
        self.default_org_code = default_org_code
        logger.info("🏢 테넌트 미들웨어 초기화 완료")
    
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
                return await call_next(request)
                
                logger.info(f"🏢 테넌트 검증 필요 경로: {request.url.path}")
                
                # 조직 정보 추출 및 설정
                org_info = await self._extract_organization_info(request)
                if org_info:
                    # 조직 컨텍스트 설정
                    current_org_context.set(org_info)
                    logger.debug(f"🏢 조직 컨텍스트 설정: {org_info['name']} (ID: {org_info['id']})")
                    
                    # 요청 state에 조직 정보 추가 (기존 라우터 호환성)
                    request.state.org_id = str(org_info['id'])
                    request.state.org_code = org_info.get('org_code', self.default_org_code)
                    request.state.organization = org_info
                
                # 다음 미들웨어/핸들러 호출
                response = await call_next(request)
                
                # 응답 헤더에 조직 정보 추가 (ASCII 안전한 값만)
                if org_info:
                    response.headers["X-Organization-ID"] = str(org_info['id'])
                    # 한국어 조직명은 헤더에 추가하지 않음 (인코딩 오류 방지)
                    if org_info.get('org_code'):
                        response.headers["X-Organization-Code"] = org_info['org_code']
                
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
                    "error": "internal_server_error",
                    "message": "테넌트 처리 중 오류가 발생했습니다.",
                    "details": str(e) if settings.is_development() else None
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
        2. X-Organization-Code/X-Organization-ID 헤더
        3. 도메인/서브도메인 기반 조직 식별
        4. 쿼리 파라미터 (org_code, org_id)
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
                return org_info
            
            # 2. 헤더에서 조직 정보 추출
            org_info = await self._extract_from_header(request)
            if org_info:
                return org_info
            
            # 3. 도메인 기반 조직 식별
            org_info = await self._extract_from_domain(request)
            if org_info:
                return org_info
            
            # 4. 쿼리 파라미터에서 추출
            org_info = await self._extract_from_query(request)
            if org_info:
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
            
            # JWT 토큰 디코딩은 auth.py에서 처리
            # 여기서는 토큰이 있다는 것만 확인
            token = auth_header.split(" ")[1]
            if token:
                # 실제 JWT 디코딩 및 조직 정보 추출은 별도 함수에서 처리
                # 현재는 기본 조직 반환 (개발용)
                return await self._get_default_organization()
            
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
                logger.debug(f"📋 헤더에서 조직 코드 추출: {org_code}")
                return await self._get_organization_by_code(org_code)
            
            # X-Organization-ID 헤더 확인
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
                logger.debug(f"🌐 서브도메인에서 조직 추출: {subdomain}")
                return await self._get_organization_by_subdomain(subdomain)
            
            return None
            
        except Exception as e:
            logger.error(f"❌ 도메인에서 조직 정보 추출 오류: {str(e)}")
            return None
    
    def _extract_subdomain(self, host: str) -> Optional[str]:
        """호스트에서 서브도메인 추출"""
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
                logger.debug(f"🔗 쿼리 파라미터에서 조직 코드 추출: {org_code}")
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
        조직 코드로 조직 정보 조회
        
        Args:
            org_code: 조직 코드
            
        Returns:
            조직 정보 또는 None
        """
        try:
            db = next(get_db())
            
            org = db.query(Organization).filter(
                Organization.org_code == org_code,
                Organization.is_active == True
            ).first()
            
            if org:
                return {
                    "id": org.org_id,
                    "org_code": org.org_code,
                    "name": org.name,
                    "domain": org.domain,
                    "subdomain": org.subdomain,
                    "is_active": org.is_active,
                    "max_users": org.max_users,
                    "max_storage_gb": org.max_storage_gb,
                    "settings": org.settings or {}
                }
            
            return None
            
        except Exception as e:
            logger.error(f"❌ 조직 코드 조회 오류: {str(e)}")
            return None
    
    async def _get_organization_by_id_or_uuid(self, org_id: Optional[str], org_uuid: Optional[str]) -> Optional[Dict[str, Any]]:
        """
        ID 또는 UUID로 조직 정보 조회
        
        Args:
            org_id: 조직 ID
            org_uuid: 조직 UUID
            
        Returns:
            조직 정보 또는 None
        """
        try:
            db = next(get_db())
            
            query = db.query(Organization)
            if org_uuid:
                query = query.filter(Organization.org_id == org_uuid)
            elif org_id:
                query = query.filter(Organization.org_id == org_id)
            else:
                return None
            
            org = query.filter(Organization.is_active == True).first()
            if org:
                return {
                    "id": org.org_id,
                    "org_code": org.org_code,
                    "name": org.name,
                    "domain": org.domain,
                    "subdomain": org.subdomain,
                    "is_active": org.is_active,
                    "max_users": org.max_users,
                    "max_storage_gb": org.max_storage_gb,
                    "settings": org.settings or {}
                }
            
            return None
            
        except Exception as e:
            logger.error(f"❌ 조직 조회 오류: {str(e)}")
            return None
    
    async def _get_organization_by_subdomain(self, subdomain: str) -> Optional[Dict[str, Any]]:
        """
        서브도메인으로 조직 정보 조회
        
        Args:
            subdomain: 서브도메인
            
        Returns:
            조직 정보 또는 None
        """
        try:
            db = next(get_db())
            
            # 서브도메인을 조직 코드 또는 서브도메인 필드로 매칭
            org = db.query(Organization).filter(
                Organization.is_active == True,
                (Organization.org_code == subdomain) | (Organization.subdomain == subdomain)
            ).first()
            
            if org:
                return {
                    "id": org.org_id,
                    "org_code": org.org_code,
                    "name": org.name,
                    "domain": org.domain,
                    "subdomain": org.subdomain,
                    "is_active": org.is_active,
                    "max_users": org.max_users,
                    "max_storage_gb": org.max_storage_gb,
                    "settings": org.settings or {}
                }
            
            return None
            
        except Exception as e:
            logger.error(f"❌ 서브도메인 조직 조회 오류: {str(e)}")
            return None
    
    async def _get_default_organization(self) -> Optional[Dict[str, Any]]:
        """
        기본 조직 정보 조회
        
        Returns:
            기본 조직 정보 또는 None
        """
        try:
            db = next(get_db())
            
            # 기본 조직 코드로 조직 찾기
            org = db.query(Organization).filter(
                Organization.org_code == self.default_org_code,
                Organization.is_active == True
            ).first()
            
            # 기본 조직이 없으면 첫 번째 활성 조직 사용
            if not org:
                org = db.query(Organization).filter(
                    Organization.is_active == True
                ).first()
            
            if org:
                return {
                    "id": org.org_id,
                    "org_code": org.org_code,
                    "name": org.name,
                    "domain": org.domain,
                    "subdomain": org.subdomain,
                    "is_active": org.is_active,
                    "max_users": org.max_users,
                    "max_storage_gb": org.max_storage_gb,
                    "settings": org.settings or {}
                }
            
            return None
            
        except Exception as e:
            logger.error(f"❌ 기본 조직 조회 오류: {str(e)}")
            return None


# ContextVar 기반 헬퍼 함수들 (기존 tenant.py 호환성)
def get_current_org() -> Optional[Dict[str, Any]]:
    """
    현재 요청의 조직 정보 반환
    
    Returns:
        조직 정보 딕셔너리 또는 None
    """
    return current_org_context.get()


def get_current_user() -> Optional[Dict[str, Any]]:
    """
    현재 요청의 사용자 정보 반환
    
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


# Request.state 기반 헬퍼 함수들 (기존 tenant_middleware.py 호환성)
def get_current_organization(request: Request) -> Dict[str, Any]:
    """현재 요청의 조직 정보 반환 (request.state 기반)"""
    if not hasattr(request.state, 'organization'):
        raise HTTPException(
            status_code=500,
            detail="조직 정보가 설정되지 않았습니다. 테넌트 미들웨어를 확인하세요."
        )
    return request.state.organization


def get_current_org_id(request: Request) -> str:
    """현재 요청의 조직 ID 반환 (request.state 기반)"""
    if not hasattr(request.state, 'org_id'):
        raise HTTPException(
            status_code=500,
            detail="조직 ID가 설정되지 않았습니다. 테넌트 미들웨어를 확인하세요."
        )
    return request.state.org_id


def get_current_org_code(request: Request) -> str:
    """현재 요청의 조직 코드 반환 (request.state 기반)"""
    if not hasattr(request.state, 'org_code'):
        raise HTTPException(
            status_code=500,
            detail="조직 코드가 설정되지 않았습니다. 테넌트 미들웨어를 확인하세요."
        )
    return request.state.org_code