"""
사용자 관리 라우터

SaaS 다중 조직 지원을 위한 사용자 관리 API 엔드포인트
"""
import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..database.base import get_db
from ..model.user_model import User
from ..schemas.base_schema import UserCreate, UserResponse
from ..service.user_service import UserService
from ..middleware.tenant import get_current_org, get_current_user, require_org
from ..service.auth_service import get_current_user as auth_get_current_user

# 로거 설정
logger = logging.getLogger(__name__)

# 라우터 초기화
router = APIRouter(tags=["사용자 관리"])


@router.post("/", response_model=UserResponse, summary="사용자 생성")
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(auth_get_current_user),
    current_org = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """
    조직 내에 새 사용자를 생성합니다.
    
    - **관리자 권한 필요**
    - 조직의 최대 사용자 수 제한 확인
    - 이메일 및 사용자명 중복 확인 (조직 내)
    """
    logger.info(f"👤 사용자 생성 요청 - 조직: {current_org.name}, 요청자: {current_user.email}")
    
    # 관리자 권한 확인
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다."
        )
    
    user_service = UserService(db)
    return await user_service.create_user(
        org_id=current_org.id,
        user_data=user_data,
        created_by_admin=True
    )


@router.get("/", response_model=Dict[str, Any], summary="사용자 목록 조회")
async def get_users(
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    search: Optional[str] = Query(None, description="검색어 (이메일, 사용자명)"),
    is_active: Optional[bool] = Query(None, description="활성 상태 필터"),
    current_user: User = Depends(auth_get_current_user),
    current_org = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """
    조직의 사용자 목록을 조회합니다.
    
    - **관리자 권한 필요**
    - 페이지네이션 지원
    - 검색 및 필터링 지원
    """
    logger.info(f"👥 사용자 목록 조회 - 조직: {current_org.name}, 요청자: {current_user.email}")
    
    # 관리자 권한 확인
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다."
        )
    
    user_service = UserService(db)
    return await user_service.get_users_by_org(
        org_id=current_org.id,
        page=page,
        limit=limit,
        search=search,
        is_active=is_active
    )


@router.get("/me", response_model=UserResponse, summary="현재 사용자 정보 조회")
async def get_current_user_info(
    current_user: User = Depends(auth_get_current_user),
    current_org = Depends(get_current_org)
):
    """
    현재 로그인한 사용자의 정보를 조회합니다.
    """
    logger.info(f"👤 현재 사용자 정보 조회 - 조직: {current_org.name}, 사용자: {current_user.email}")
    
    return UserResponse(
        id=current_user.id,
        user_uuid=current_user.user_uuid,
        email=current_user.email,
        username=current_user.username,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at
    )


@router.get("/{user_id}", response_model=UserResponse, summary="특정 사용자 조회")
async def get_user(
    user_id: int,
    current_user: User = Depends(auth_get_current_user),
    current_org = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """
    조직 내 특정 사용자의 정보를 조회합니다.
    
    - **관리자 권한 필요** (본인 조회는 제외)
    """
    logger.info(f"👤 사용자 조회 - 조직: {current_org.name}, 대상 ID: {user_id}, 요청자: {current_user.email}")
    
    # 본인 조회가 아닌 경우 관리자 권한 확인
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다."
        )
    
    user_service = UserService(db)
    user = await user_service.get_user_by_id(current_org.id, user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다."
        )
    
    return user


@router.put("/{user_id}", response_model=UserResponse, summary="사용자 정보 수정")
async def update_user(
    user_id: int,
    update_data: Dict[str, Any],
    current_user: User = Depends(auth_get_current_user),
    current_org = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """
    조직 내 사용자 정보를 수정합니다.
    
    - **관리자 권한 필요** (본인 수정은 제외)
    - 수정 가능한 필드: username, full_name, is_active
    """
    logger.info(f"👤 사용자 수정 - 조직: {current_org.name}, 대상 ID: {user_id}, 요청자: {current_user.email}")
    
    # 본인 수정이 아닌 경우 관리자 권한 확인
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다."
        )
    
    # 일반 사용자는 is_active 필드 수정 불가
    if not current_user.is_admin and 'is_active' in update_data:
        del update_data['is_active']
    
    user_service = UserService(db)
    return await user_service.update_user(
        org_id=current_org.id,
        user_id=user_id,
        update_data=update_data
    )


@router.delete("/{user_id}", summary="사용자 삭제")
async def delete_user(
    user_id: int,
    current_user: User = Depends(auth_get_current_user),
    current_org = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """
    조직 내 사용자를 삭제합니다 (소프트 삭제).
    
    - **관리자 권한 필요**
    - 본인 삭제 불가
    """
    logger.info(f"👤 사용자 삭제 - 조직: {current_org.name}, 대상 ID: {user_id}, 요청자: {current_user.email}")
    
    # 관리자 권한 확인
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다."
        )
    
    # 본인 삭제 방지
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="본인 계정은 삭제할 수 없습니다."
        )
    
    user_service = UserService(db)
    success = await user_service.delete_user(current_org.id, user_id)
    
    if success:
        return {"message": "사용자가 성공적으로 삭제되었습니다."}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 삭제 중 오류가 발생했습니다."
        )


@router.post("/{user_id}/change-password", summary="비밀번호 변경")
async def change_password(
    user_id: int,
    password_data: Dict[str, str],
    current_user: User = Depends(auth_get_current_user),
    current_org = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """
    사용자 비밀번호를 변경합니다.
    
    - **본인 또는 관리자 권한 필요**
    - 필수 필드: current_password, new_password
    """
    logger.info(f"🔑 비밀번호 변경 - 조직: {current_org.name}, 대상 ID: {user_id}, 요청자: {current_user.email}")
    
    # 본인 또는 관리자 권한 확인
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="본인 또는 관리자 권한이 필요합니다."
        )
    
    # 필수 필드 확인
    if 'current_password' not in password_data or 'new_password' not in password_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="current_password와 new_password가 필요합니다."
        )
    
    user_service = UserService(db)
    success = await user_service.change_password(
        org_id=current_org.id,
        user_id=user_id,
        current_password=password_data['current_password'],
        new_password=password_data['new_password']
    )
    
    if success:
        return {"message": "비밀번호가 성공적으로 변경되었습니다."}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="비밀번호 변경 중 오류가 발생했습니다."
        )


@router.get("/stats/overview", response_model=Dict[str, Any], summary="사용자 통계 조회")
async def get_user_stats(
    current_user: User = Depends(auth_get_current_user),
    current_org = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """
    조직의 사용자 통계를 조회합니다.
    
    - **관리자 권한 필요**
    - 전체/활성/관리자/최근 사용자 수 등 제공
    """
    logger.info(f"📊 사용자 통계 조회 - 조직: {current_org.name}, 요청자: {current_user.email}")
    
    # 관리자 권한 확인
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다."
        )
    
    user_service = UserService(db)
    return await user_service.get_user_stats(current_org.id)


@router.post("/{user_id}/activate", summary="사용자 활성화")
async def activate_user(
    user_id: int,
    current_user: User = Depends(auth_get_current_user),
    current_org = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """
    비활성화된 사용자를 활성화합니다.
    
    - **관리자 권한 필요**
    """
    logger.info(f"✅ 사용자 활성화 - 조직: {current_org.name}, 대상 ID: {user_id}, 요청자: {current_user.email}")
    
    # 관리자 권한 확인
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다."
        )
    
    user_service = UserService(db)
    user = await user_service.update_user(
        org_id=current_org.id,
        user_id=user_id,
        update_data={"is_active": True}
    )
    
    if user:
        return {"message": "사용자가 성공적으로 활성화되었습니다."}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다."
        )


@router.post("/{user_id}/deactivate", summary="사용자 비활성화")
async def deactivate_user(
    user_id: int,
    current_user: User = Depends(auth_get_current_user),
    current_org = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """
    사용자를 비활성화합니다.
    
    - **관리자 권한 필요**
    - 본인 비활성화 불가
    """
    logger.info(f"❌ 사용자 비활성화 - 조직: {current_org.name}, 대상 ID: {user_id}, 요청자: {current_user.email}")
    
    # 관리자 권한 확인
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다."
        )
    
    # 본인 비활성화 방지
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="본인 계정은 비활성화할 수 없습니다."
        )
    
    user_service = UserService(db)
    user = await user_service.update_user(
        org_id=current_org.id,
        user_id=user_id,
        update_data={"is_active": False}
    )
    
    if user:
        return {"message": "사용자가 성공적으로 비활성화되었습니다."}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다."
        )