"""
조직 관리 라우터

SaaS 다중 조직 지원을 위한 조직 관리 API 엔드포인트
"""
import logging
import traceback
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status, Path
from sqlalchemy.orm import Session
from pydantic import ValidationError

from ..database import get_db
from ..service.auth_service import get_current_user, get_current_admin_user
from ..model import User
from ..schemas.organization_schema import (
    OrganizationCreate, OrganizationUpdate, OrganizationResponse,
    OrganizationStats, OrganizationCreateRequest,
    OrganizationListResponse, OrganizationStatsResponse,
    OrganizationSettingsResponse, OrganizationSettingsUpdate
)
from ..service.organization_service import get_organization_service, OrganizationService
from ..middleware.tenant_middleware import get_current_org, get_current_org_id_from_context, require_org

# 로거 설정
logger = logging.getLogger(__name__)

# 라우터 생성
router = APIRouter(
    tags=["organizations"],
    responses={404: {"description": "조직을 찾을 수 없습니다"}}
)


@router.post(
    "/",
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="조직 생성",
    description="새로운 조직을 생성하고 관리자 계정을 설정합니다."
)
async def create_organization(
    org_request: OrganizationCreateRequest,
    db: Session = Depends(get_db),
    org_service: OrganizationService = Depends(get_organization_service)
):
    """
    새 조직 생성
    
    - **name**: 조직명 (필수)
    - **domain**: 조직 도메인 (선택사항)
    - **description**: 조직 설명 (선택사항)
    - **max_users**: 최대 사용자 수 (선택사항)
    - **max_storage_gb**: 최대 저장 공간 (GB) (선택사항)
    - **admin_email**: 관리자 이메일 (필수)
    - **admin_password**: 관리자 비밀번호 (필수)
    - **admin_name**: 관리자 이름 (선택사항)
    """
    try:
        logger.info(f"🏢 조직 생성 요청: {org_request.organization.name}")
        logger.info(f"📋 요청 데이터 - org_code: {org_request.organization.org_code}, subdomain: {org_request.organization.subdomain}")
        
        result = await org_service.create_organization(
            org_data=org_request.organization,
            admin_email=org_request.admin_email,
            admin_password=org_request.admin_password,
            admin_name=org_request.admin_name
        )
        
        logger.info(f"✅ 조직 생성 완료: {result.name}")
        return result
        
    except HTTPException:
        raise
    except ValidationError as e:
        logger.error(f"❌ 조직 생성 검증 오류: {e.errors()}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"입력 데이터 검증 오류: {e.errors()}"
        )
    except Exception as e:
        logger.error(f"❌ 조직 생성 API 오류: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="조직 생성 중 오류가 발생했습니다."
        )


@router.get(
    "/list",
    response_model=OrganizationListResponse,
    summary="조직 목록 조회",
    description="조직 목록을 조회합니다. (시스템 관리자만 접근 가능)"
)
async def list_organizations(
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    search: Optional[str] = Query(None, description="검색어 (조직명, 도메인)"),
    is_active: Optional[bool] = Query(None, description="활성 상태 필터"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
    org_service: OrganizationService = Depends(get_organization_service)
):
    """
    조직 목록 조회 (시스템 관리자 전용)
    
    - **page**: 페이지 번호 (기본값: 1)
    - **limit**: 페이지당 항목 수 (기본값: 20, 최대: 100)
    - **search**: 검색어 (조직명, 도메인에서 검색)
    - **is_active**: 활성 상태 필터 (true/false)
    """
    try:
        logger.info(f"📋 조직 목록 조회 요청 - 사용자: {current_user.email}, 페이지: {page}")
        
        # skip 계산
        skip = (page - 1) * limit
        
        # 성능 최적화: 단일 쿼리로 목록과 개수를 함께 조회
        organizations = await org_service.list_organizations(
            skip=skip,
            limit=limit + 1,  # 다음 페이지 존재 여부 확인을 위해 +1
            search=search,
            is_active=is_active
        )
        
        # 다음 페이지 존재 여부 확인 및 실제 결과 조정
        has_more = len(organizations) > limit
        if has_more:
            organizations = organizations[:limit]
        
        # 전체 개수는 첫 페이지에서만 정확히 계산, 나머지는 추정
        if skip == 0:
            total = await org_service.count_organizations(search=search, is_active=is_active)
        else:
            # 추정값 계산 (정확하지 않지만 성능상 이점)
            total = skip + len(organizations) + (1 if has_more else 0)
        
        total_pages = (total + limit - 1) // limit
        
        logger.info(f"✅ 조직 목록 조회 완료: {len(organizations)}개 (전체: {total}개)")
        
        return OrganizationListResponse(
            organizations=organizations,
            total=total,
            page=page,
            limit=limit,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(f"❌ 조직 목록 조회 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="조직 목록 조회 중 오류가 발생했습니다."
        )


@router.get(
    "/current",
    response_model=OrganizationResponse,
    summary="현재 조직 정보 조회",
    description="현재 사용자가 속한 조직의 정보를 조회합니다."
)
async def get_current_organization(
    current_user: User = Depends(get_current_user),
    current_org: str = Depends(get_current_org_id_from_context),
    db: Session = Depends(get_db),
    org_service: OrganizationService = Depends(get_organization_service)
):
    """
    현재 조직 정보 조회
    
    현재 사용자가 속한 조직의 상세 정보를 반환합니다.
    """
    try:
        logger.info(f"🏢 현재 조직 정보 조회 - 사용자: {current_user.email}, 조직: {current_org}")
        
        organization = await org_service.get_organization_by_id(current_org)
        
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="조직을 찾을 수 없습니다."
            )
        
        logger.info(f"✅ 현재 조직 정보 조회 완료: {organization.name}")
        return organization
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 현재 조직 정보 조회 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="조직 정보 조회 중 오류가 발생했습니다."
        )


@router.get(
    "/{org_id}",
    response_model=OrganizationResponse,
    summary="조직 정보 조회",
    description="특정 조직의 정보를 조회합니다."
)
async def get_organization(
    org_id: str = Path(..., pattern=r"^[A-Za-z0-9_-]+$", min_length=1, max_length=50, description="조직 ID (영숫자, 언더스코어, 하이픈만 허용)"),
    current_user: User = Depends(get_current_user),
    current_org: str = Depends(require_org),
    db: Session = Depends(get_db),
    org_service: OrganizationService = Depends(get_organization_service)
):
    """
    조직 정보 조회
    
    - **org_id**: 조직 ID
    
    일반 사용자는 자신이 속한 조직만 조회 가능하며,
    시스템 관리자는 모든 조직을 조회할 수 있습니다.
    """
    try:
        logger.info(f"🏢 조직 정보 조회 - 요청 org_id: {org_id}")
        logger.info(f"👤 사용자 정보 - 이메일: {current_user.email}, 역할: {current_user.role}")
        logger.info(f"🏢 사용자 소속 조직 - user.org_id: {getattr(current_user, 'org_id', 'None')}")
        logger.info(f"🔍 미들웨어에서 추출한 current_org: {current_org}")
        
        # 입력 검증: 빈 문자열 확인
        if not org_id or org_id.strip() == "":
            logger.warning(f"⚠️ 빈 조직 ID 요청")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="조직을 찾을 수 없습니다."
            )
        
        # 권한 확인: 일반 사용자는 자신의 조직만 조회 가능
        logger.info(f"🔐 권한 검증 - 사용자 역할: {current_user.role}, 요청 org_id: {org_id}, 현재 org: {current_org}")
        
        # current_org가 딕셔너리인 경우 'id' 키에서 조직 ID 추출
        current_org_id = current_org.get('id') if isinstance(current_org, dict) else current_org
        
        if current_user.role not in ["system_admin", "admin"] and org_id != current_org_id:
            logger.warning(f"❌ 권한 없음 - 사용자({current_user.email})가 다른 조직({org_id}) 접근 시도, 허용된 조직 ID: {current_org_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="다른 조직의 정보에 접근할 권한이 없습니다."
            )
        
        organization = await org_service.get_organization_by_id(org_id)
        
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="조직을 찾을 수 없습니다."
            )
        
        logger.info(f"✅ 조직 정보 조회 완료: {organization.name}")
        return organization
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 조직 정보 조회 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="조직 정보 조회 중 오류가 발생했습니다."
        )


@router.put(
    "/{org_id}",
    response_model=OrganizationResponse,
    summary="조직 정보 수정",
    description="조직 정보를 수정합니다. (조직 관리자 권한 필요)"
)
async def update_organization(
    org_update: OrganizationUpdate,
    org_id: str = Path(..., pattern=r"^[A-Za-z0-9_-]+$", min_length=1, max_length=50, description="조직 ID (영숫자, 언더스코어, 하이픈만 허용)"),
    current_user: User = Depends(get_current_user),
    current_org: str = Depends(require_org),
    db: Session = Depends(get_db),
    org_service: OrganizationService = Depends(get_organization_service)
):
    """
    조직 정보 수정
    
    - **org_id**: 조직 ID
    - **name**: 조직명 (선택사항)
    - **domain**: 조직 도메인 (선택사항)
    - **description**: 조직 설명 (선택사항)
    - **max_users**: 최대 사용자 수 (선택사항)
    - **max_storage_gb**: 최대 저장 공간 (GB) (선택사항)
    - **settings**: 조직 설정 (선택사항)
    
    조직 관리자 또는 시스템 관리자만 수정할 수 있습니다.
    """
    try:
        logger.info(f"✏️ 조직 정보 수정 요청 - ID: {org_id}, 사용자: {current_user.email}")
        
        # 권한 확인: 조직 관리자 또는 시스템 관리자만 수정 가능
        current_org_id = current_org.get('id') if isinstance(current_org, dict) else current_org
        if current_user.role not in ["admin", "system_admin"] and org_id != current_org_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="조직 정보를 수정할 권한이 없습니다."
            )
        
        result = await org_service.update_organization(org_id, org_update)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="조직을 찾을 수 없습니다."
            )
        
        logger.info(f"✅ 조직 정보 수정 완료: {result.name}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 조직 정보 수정 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="조직 정보 수정 중 오류가 발생했습니다."
        )


@router.delete(
    "/{org_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="조직 삭제",
    description="조직을 삭제합니다. (시스템 관리자 권한 필요)"
)
async def delete_organization(
    org_id: str = Path(..., pattern=r"^[A-Za-z0-9_-]+$", min_length=1, max_length=50, description="조직 ID (영숫자, 언더스코어, 하이픈만 허용)"),
    force: bool = Query(False, description="강제 삭제 여부 (하드 삭제)"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
    org_service: OrganizationService = Depends(get_organization_service)
):
    """
    조직 삭제 (시스템 관리자 전용)
    
    - **org_id**: 조직 ID
    - **force**: 강제 삭제 여부 (기본값: false)
        - false: 소프트 삭제 (비활성화)
        - true: 하드 삭제 (완전 삭제)
    
    주의: 강제 삭제 시 모든 관련 데이터가 영구적으로 삭제됩니다.
    """
    try:
        logger.info(f"🗑️ 조직 삭제 요청 - ID: {org_id}, 강제: {force}, 사용자: {current_user.email}")
        
        success = await org_service.delete_organization(org_id, force)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="조직을 찾을 수 없습니다."
            )
        
        logger.info(f"✅ 조직 삭제 완료 - ID: {org_id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 조직 삭제 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="조직 삭제 중 오류가 발생했습니다."
        )


@router.get(
    "/{org_id}/stats",
    response_model=OrganizationStatsResponse,
    summary="조직 통계 조회",
    description="조직의 사용량 및 통계 정보를 조회합니다."
)
async def get_organization_stats(
    org_id: str = Path(..., pattern=r"^[A-Za-z0-9_-]+$", min_length=1, max_length=50, description="조직 ID (영숫자, 언더스코어, 하이픈만 허용)"),
    current_user: User = Depends(get_current_user),
    current_org: str = Depends(require_org),
    db: Session = Depends(get_db),
    org_service: OrganizationService = Depends(get_organization_service)
):
    """
    조직 통계 정보 조회
    
    - **org_id**: 조직 ID
    
    조직의 사용자 수, 저장 공간 사용량, 메일 통계 등의 상세 정보를 반환합니다.
    조직 관리자 또는 시스템 관리자만 조회할 수 있습니다.
    """
    try:
        logger.info(f"📊 조직 통계 조회 - ID: {org_id}, 사용자: {current_user.email}")
        
        # 권한 확인: 조직 관리자 또는 시스템 관리자만 조회 가능
        current_org_id = current_org.get('id') if isinstance(current_org, dict) else current_org
        if current_user.role not in ["admin", "system_admin"] and org_id != current_org_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="조직 통계에 접근할 권한이 없습니다."
            )
        
        stats = await org_service.get_detailed_organization_stats(org_id)
        
        if not stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="조직을 찾을 수 없습니다."
            )
        
        logger.info(f"✅ 조직 통계 조회 완료 - ID: {org_id}")
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 조직 통계 조회 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="조직 통계 조회 중 오류가 발생했습니다."
        )


@router.get(
    "/current/stats",
    response_model=OrganizationStatsResponse,
    summary="현재 조직 통계 조회",
    description="현재 사용자가 속한 조직의 통계 정보를 조회합니다."
)
async def get_current_organization_stats(
    current_user: User = Depends(get_current_user),
    current_org: str = Depends(get_current_org_id_from_context),
    db: Session = Depends(get_db),
    org_service: OrganizationService = Depends(get_organization_service)
):
    """
    현재 조직 통계 정보 조회
    
    현재 사용자가 속한 조직의 사용량, 메일 통계 등의 상세 정보를 반환합니다.
    """
    try:
        logger.info(f"📊 현재 조직 통계 조회 - 사용자: {current_user.email}, 조직: {current_org}")
        
        stats = await org_service.get_detailed_organization_stats(current_org)
        
        if not stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="조직을 찾을 수 없습니다."
            )
        
        logger.info(f"✅ 현재 조직 통계 조회 완료 - 조직: {current_org}")
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 현재 조직 통계 조회 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="조직 통계 조회 중 오류가 발생했습니다."
        )


# 조직 설정 관리
@router.get(
    "/{org_id}/settings",
    response_model=OrganizationSettingsResponse,
    summary="조직 설정 조회",
    description="조직의 설정 정보를 조회합니다."
)
async def get_organization_settings(
    org_id: str = Path(..., pattern=r"^[A-Za-z0-9_-]+$", min_length=1, max_length=50, description="조직 ID (영숫자, 언더스코어, 하이픈만 허용)"),
    current_user: User = Depends(get_current_user),
    current_org: str = Depends(require_org),
    db: Session = Depends(get_db),
    org_service: OrganizationService = Depends(get_organization_service)
):
    """
    조직 설정 조회
    
    - **org_id**: 조직 ID
    
    조직의 메일 설정, 보안 설정 등을 조회합니다.
    조직 관리자 또는 시스템 관리자만 조회할 수 있습니다.
    """
    try:
        logger.info(f"⚙️ 조직 설정 조회 - ID: {org_id}, 사용자: {current_user.email}")
        
        # 권한 확인: 조직 관리자 또는 시스템 관리자만 조회 가능
        current_org_id = current_org.get('id') if isinstance(current_org, dict) else current_org
        if current_user.role not in ["admin", "system_admin"] and org_id != current_org_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="조직 설정에 접근할 권한이 없습니다."
            )
        
        settings = await org_service.get_organization_settings(org_id)
        
        if not settings:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="조직 설정을 찾을 수 없습니다."
            )
        
        logger.info(f"✅ 조직 설정 조회 완료 - ID: {org_id}")
        return settings
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 조직 설정 조회 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="조직 설정 조회 중 오류가 발생했습니다."
        )


@router.put(
    "/{org_id}/settings",
    response_model=OrganizationSettingsResponse,
    summary="조직 설정 수정",
    description="조직의 설정 정보를 수정합니다."
)
async def update_organization_settings(
    settings_update: OrganizationSettingsUpdate,
    org_id: str = Path(..., pattern=r"^[A-Za-z0-9_-]+$", min_length=1, max_length=50, description="조직 ID (영숫자, 언더스코어, 하이픈만 허용)"),
    current_user: User = Depends(get_current_user),
    current_org: str = Depends(require_org),
    db: Session = Depends(get_db),
    org_service: OrganizationService = Depends(get_organization_service)
):
    """
    조직 설정 수정
    
    - **org_id**: 조직 ID
    - **max_mail_size_mb**: 최대 메일 크기 (MB) (선택사항)
    - **max_attachment_size_mb**: 최대 첨부파일 크기 (MB) (선택사항)
    - **allow_external_mail**: 외부 메일 허용 여부 (선택사항)
    - **spam_filter_enabled**: 스팸 필터 활성화 여부 (선택사항)
    - **require_2fa**: 2FA 필수 여부 (선택사항)
    - **session_timeout_minutes**: 세션 타임아웃 (분) (선택사항)
    - **custom_domain**: 커스텀 도메인 (선택사항)
    - **password_policy**: 비밀번호 정책 (선택사항)
    - **features_enabled**: 활성화된 기능들 (선택사항)
    
    조직 관리자 또는 시스템 관리자만 수정할 수 있습니다.
    """
    try:
        logger.info(f"⚙️ 조직 설정 수정 요청 - ID: {org_id}, 사용자: {current_user.email}")
        
        # 권한 확인: 조직 관리자 또는 시스템 관리자만 수정 가능
        current_org_id = current_org.get('id') if isinstance(current_org, dict) else current_org
        if current_user.role not in ["admin", "system_admin"] and org_id != current_org_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="조직 설정을 수정할 권한이 없습니다."
            )
        
        result = await org_service.update_organization_settings(org_id, settings_update)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="조직 설정을 찾을 수 없습니다."
            )
        
        logger.info(f"✅ 조직 설정 수정 완료 - ID: {org_id}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 조직 설정 수정 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="조직 설정 수정 중 오류가 발생했습니다."
        )


@router.get(
    "/current/settings",
    response_model=OrganizationSettingsResponse,
    summary="현재 조직 설정 조회",
    description="현재 사용자가 속한 조직의 설정 정보를 조회합니다."
)
async def get_current_organization_settings(
    current_user: User = Depends(get_current_user),
    current_org: str = Depends(get_current_org_id_from_context),
    db: Session = Depends(get_db),
    org_service: OrganizationService = Depends(get_organization_service)
):
    """
    현재 조직 설정 조회
    
    현재 사용자가 속한 조직의 메일 설정, 보안 설정 등을 조회합니다.
    """
    try:
        logger.info(f"⚙️ 현재 조직 설정 조회 - 사용자: {current_user.email}, 조직: {current_org}")
        
        settings = await org_service.get_organization_settings(current_org)
        
        if not settings:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="조직 설정을 찾을 수 없습니다."
            )
        
        logger.info(f"✅ 현재 조직 설정 조회 완료 - 조직: {current_org}")
        return settings
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 현재 조직 설정 조회 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="조직 설정 조회 중 오류가 발생했습니다."
        )