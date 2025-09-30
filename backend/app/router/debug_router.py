"""
디버그 라우터 (임시)

조직 컨텍스트 디버깅을 위한 임시 엔드포인트
"""
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from ..database import get_db
from ..service.auth_service import get_current_user, get_password_hash
from ..model import User, Organization
from ..middleware.tenant_middleware import (
    get_current_org, 
    get_current_org_id_from_context, 
    current_org_context,
    current_user_context
)

# Pydantic 모델
class OrganizationCreateRequest(BaseModel):
    """조직 생성 요청 모델"""
    name: str
    org_code: str
    domain: str
    max_users: int = 100
    is_active: bool = True

class UserCreateRequest(BaseModel):
    """사용자 생성 요청 모델"""
    email: EmailStr
    password: str
    full_name: str
    org_id: str
    role: str = "user"
    is_active: bool = True

# 로거 설정
logger = logging.getLogger(__name__)

# 라우터 생성
router = APIRouter(
    prefix="/debug",
    tags=["debug"],
    responses={404: {"description": "디버그 정보를 찾을 수 없습니다"}}
)


@router.get(
    "/context",
    summary="컨텍스트 디버그 정보",
    description="현재 요청의 컨텍스트 정보를 디버깅합니다."
)
async def get_context_debug_info(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    컨텍스트 디버그 정보 조회
    
    현재 요청의 조직 및 사용자 컨텍스트 정보를 반환합니다.
    """
    try:
        logger.info(f"🔍 컨텍스트 디버그 정보 조회 - 사용자: {current_user.email}")
        
        # 1. ContextVar에서 조직 정보 가져오기
        org_context = current_org_context.get()
        user_context = current_user_context.get()
        
        # 2. 헬퍼 함수들로 정보 가져오기
        current_org = get_current_org()
        current_org_id = get_current_org_id_from_context()
        
        # 3. request.state에서 정보 가져오기
        request_state_info = {}
        if hasattr(request.state, 'org_id'):
            request_state_info['org_id'] = request.state.org_id
        if hasattr(request.state, 'org_code'):
            request_state_info['org_code'] = request.state.org_code
        if hasattr(request.state, 'org_info'):
            request_state_info['org_info'] = request.state.org_info
        if hasattr(request.state, 'user_info'):
            request_state_info['user_info'] = request.state.user_info
        
        # 4. 헤더 정보
        headers_info = {
            'host': request.headers.get('host'),
            'x-org-id': request.headers.get('x-org-id'),
            'x-org-code': request.headers.get('x-org-code'),
            'authorization': 'Bearer ***' if request.headers.get('authorization') else None
        }
        
        # 5. 쿼리 파라미터
        query_params = dict(request.query_params)
        
        debug_info = {
            "timestamp": str(logger.handlers[0].formatter.formatTime(logger.makeRecord(
                name="debug", level=logging.INFO, pathname="", lineno=0,
                msg="", args=(), exc_info=None
            )) if logger.handlers else "N/A"),
            "current_user": {
                "email": current_user.email,
                "user_uuid": current_user.user_uuid,
                "org_id": current_user.org_id,
                "role": current_user.role,
                "is_active": current_user.is_active
            },
            "context_vars": {
                "org_context": org_context,
                "user_context": user_context,
                "current_org_from_helper": current_org,
                "current_org_id_from_helper": current_org_id
            },
            "request_state": request_state_info,
            "headers": headers_info,
            "query_params": query_params,
            "url": {
                "path": request.url.path,
                "query": request.url.query,
                "scheme": request.url.scheme,
                "hostname": request.url.hostname,
                "port": request.url.port
            }
        }
        
        logger.info(f"✅ 컨텍스트 디버그 정보 조회 완료")
        return debug_info
        
    except Exception as e:
        logger.error(f"❌ 컨텍스트 디버그 정보 조회 오류: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"컨텍스트 디버그 정보 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.post(
    "/create-organization",
    summary="조직 생성 (디버그용)",
    description="디버그 목적으로 새로운 조직을 생성합니다."
)
async def create_organization_debug(
    org_data: OrganizationCreateRequest,
    db: Session = Depends(get_db)
):
    """
    조직 생성 (디버그용)
    
    디버그 목적으로 새로운 조직을 생성합니다.
    """
    try:
        logger.info(f"🏢 조직 생성 시작 - 이름: {org_data.name}, 도메인: {org_data.domain}")
        
        # 중복 확인
        existing_org = db.query(Organization).filter(
            (Organization.name == org_data.name) | 
            (Organization.domain == org_data.domain) |
            (Organization.org_code == org_data.org_code)
        ).first()
        
        if existing_org:
            logger.warning(f"⚠️ 중복된 조직 정보 - 이름: {existing_org.name}")
            raise HTTPException(
                status_code=400,
                detail=f"이미 존재하는 조직입니다: {existing_org.name}"
            )
        
        # 새 조직 생성 (실제 DB 스키마에 맞게)
        new_org = Organization(
            org_id=str(uuid.uuid4()),
            org_code=org_data.org_code,
            name=org_data.name,
            domain=org_data.domain,
            subdomain=org_data.org_code.lower(),
            admin_email=f"admin@{org_data.domain}",
            max_users=org_data.max_users,
            is_active=org_data.is_active
        )
        
        db.add(new_org)
        db.commit()
        db.refresh(new_org)
        
        logger.info(f"✅ 조직 생성 완료 - ID: {new_org.org_id}")
        
        return {
            "id": new_org.org_id,
            "org_id": new_org.org_id,
            "name": new_org.name,
            "org_code": new_org.org_code,
            "domain": new_org.domain,
            "subdomain": new_org.subdomain,
            "admin_email": new_org.admin_email,
            "max_users": new_org.max_users,
            "is_active": new_org.is_active,
            "created_at": new_org.created_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 조직 생성 오류: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"조직 생성 중 오류가 발생했습니다: {str(e)}"
        )


@router.post(
    "/create-user",
    summary="사용자 생성 (디버그용)",
    description="디버그 목적으로 새로운 사용자를 생성합니다."
)
async def create_user_debug(
    user_data: UserCreateRequest,
    db: Session = Depends(get_db)
):
    """
    사용자 생성 (디버그용)
    
    디버그 목적으로 새로운 사용자를 생성합니다.
    """
    try:
        logger.info(f"👤 사용자 생성 시작 - 이메일: {user_data.email}, 조직ID: {user_data.organization_id}")
        
        # 조직 존재 확인
        organization = db.query(Organization).filter(Organization.org_id == user_data.organization_id).first()
        if not organization:
            logger.warning(f"⚠️ 존재하지 않는 조직 - ID: {user_data.organization_id}")
            raise HTTPException(
                status_code=404,
                detail=f"조직을 찾을 수 없습니다: {user_data.organization_id}"
            )
        
        # 중복 확인
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            logger.warning(f"⚠️ 중복된 사용자 이메일 - {user_data.email}")
            raise HTTPException(
                status_code=400,
                detail=f"이미 존재하는 이메일입니다: {user_data.email}"
            )
        
        # 비밀번호 해시화
        hashed_password = get_password_hash(user_data.password)
        
        # 새 사용자 생성
        new_user = User(
            user_id=str(uuid.uuid4()),
            user_uuid=str(uuid.uuid4()),
            email=user_data.email,
            username=user_data.full_name,
            hashed_password=hashed_password,
            org_id=user_data.organization_id,
            role=user_data.role,
            is_active=user_data.is_active
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        logger.info(f"✅ 사용자 생성 완료 - ID: {new_user.user_id}, UUID: {new_user.user_uuid}")
        
        return {
            "id": new_user.user_id,
            "user_id": new_user.user_id,
            "user_uuid": new_user.user_uuid,
            "email": new_user.email,
            "username": new_user.username,
            "org_id": new_user.org_id,
            "role": new_user.role,
            "is_active": new_user.is_active,
            "created_at": new_user.created_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 사용자 생성 오류: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"사용자 생성 중 오류가 발생했습니다: {str(e)}"
        )