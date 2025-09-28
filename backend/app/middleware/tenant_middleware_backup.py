"""
테넌트 미들웨어 - 서브도메인 기반 조직 식별
"""
import re
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session
from ..database.user import get_db
from ..model.organization_model import Organization
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class TenantMiddleware(BaseHTTPMiddleware):
    """
    테넌트 미들웨어
    서브도메인을 기반으로 조직을 식별하고 요청 컨텍스트에 추가
    """
    
    def __init__(self, app, default_org_code: str = "default"):
        super().__init__(app)
        self.default_org_code = default_org_code
        
        # API 문서 및 정적 파일 경로는 테넌트 검증 제외
        self.excluded_paths = {
            "/docs", "/redoc", "/openapi.json", "/favicon.ico",
            "/static", "/health", "/api/system"
        }
    
    async def dispatch(self, request: Request, call_next):
        """요청 처리 전 테넌트 식별"""
        
        # 제외 경로 확인
        if any(request.url.path.startswith(path) for path in self.excluded_paths):
            return await call_next(request)
        
        try:
            # 테넌트 식별
            org_code = self._extract_tenant_from_request(request)
            
            # 조직 정보 조회 및 검증
            organization = await self._get_organization(org_code)
            
            if not organization:
                logger.warning(f"🏢 조직을 찾을 수 없음 - org_code: {org_code}")
                return JSONResponse(
                    status_code=404,
                    content={
                        "error": "ORGANIZATION_NOT_FOUND",
                        "message": "조직을 찾을 수 없습니다.",
                        "org_code": org_code
                    }
                )
            
            # 조직 상태 확인
            if organization.status != "active":
                logger.warning(f"🚫 비활성 조직 접근 시도 - org_code: {org_code}, status: {organization.status}")
                return JSONResponse(
                    status_code=403,
                    content={
                        "error": "ORGANIZATION_INACTIVE",
                        "message": "비활성화된 조직입니다.",
                        "status": organization.status
                    }
                )
            
            # 요청 상태에 조직 정보 추가
            request.state.organization = organization
            request.state.org_id = organization.org_id
            request.state.org_code = organization.org_code
            
            logger.info(f"🏢 테넌트 식별 완료 - org_code: {org_code}, org_id: {organization.org_id}")
            
            # 다음 미들웨어/핸들러로 전달
            response = await call_next(request)
            
            # 응답 헤더에 조직 정보 추가
            response.headers["X-Organization-Code"] = organization.org_code
            response.headers["X-Organization-ID"] = organization.org_id
            
            return response
            
        except Exception as e:
            logger.error(f"❌ 테넌트 미들웨어 오류: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={
                    "error": "TENANT_MIDDLEWARE_ERROR",
                    "message": "테넌트 처리 중 오류가 발생했습니다."
                }
            )
    
    def _extract_tenant_from_request(self, request: Request) -> str:
        """
        요청에서 테넌트(조직 코드) 추출
        우선순위: 1) 서브도메인 2) 헤더 3) 쿼리 파라미터 4) 기본값
        """
        
        # 1. 서브도메인에서 추출
        host = request.headers.get("host", "")
        subdomain = self._extract_subdomain(host)
        if subdomain and subdomain != "www":
            logger.debug(f"🌐 서브도메인에서 테넌트 추출: {subdomain}")
            return subdomain
        
        # 2. X-Organization-Code 헤더에서 추출
        org_code_header = request.headers.get("X-Organization-Code")
        if org_code_header:
            logger.debug(f"📋 헤더에서 테넌트 추출: {org_code_header}")
            return org_code_header
        
        # 3. 쿼리 파라미터에서 추출
        org_code_param = request.query_params.get("org_code")
        if org_code_param:
            logger.debug(f"🔗 쿼리 파라미터에서 테넌트 추출: {org_code_param}")
            return org_code_param
        
        # 4. 기본값 사용
        logger.debug(f"🏠 기본 테넌트 사용: {self.default_org_code}")
        return self.default_org_code
    
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
    
    async def _get_organization(self, org_code: str) -> Optional[Organization]:
        """조직 코드로 조직 정보 조회"""
        try:
            # 데이터베이스 세션 생성
            db_gen = get_db()
            db: Session = next(db_gen)
            
            try:
                # 조직 조회
                organization = db.query(Organization).filter(
                    Organization.org_code == org_code,
                    Organization.deleted_at.is_(None)
                ).first()
                
                return organization
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"❌ 조직 조회 오류: {str(e)}")
            return None

# 테넌트 정보 가져오기 헬퍼 함수
def get_current_organization(request: Request) -> Organization:
    """현재 요청의 조직 정보 반환"""
    if not hasattr(request.state, 'organization'):
        raise HTTPException(
            status_code=500,
            detail="조직 정보가 설정되지 않았습니다. 테넌트 미들웨어를 확인하세요."
        )
    return request.state.organization

def get_current_org_id(request: Request) -> str:
    """현재 요청의 조직 ID 반환"""
    if not hasattr(request.state, 'org_id'):
        raise HTTPException(
            status_code=500,
            detail="조직 ID가 설정되지 않았습니다. 테넌트 미들웨어를 확인하세요."
        )
    return request.state.org_id

def get_current_org_code(request: Request) -> str:
    """현재 요청의 조직 코드 반환"""
    if not hasattr(request.state, 'org_code'):
        raise HTTPException(
            status_code=500,
            detail="조직 코드가 설정되지 않았습니다. 테넌트 미들웨어를 확인하세요."
        )
    return request.state.org_code