"""
조직 관리 서비스

SaaS 다중 조직 지원을 위한 조직 관리 기능
"""
import logging
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from fastapi import HTTPException, Depends

from ..model import Organization, User, MailUser
from ..schemas.organization_schema import (
    OrganizationCreate, OrganizationUpdate, OrganizationResponse,
    OrganizationSettings, OrganizationStats
)
from ..service.auth_service import get_password_hash
from ..config import settings
from ..database import get_db

# 로거 설정
logger = logging.getLogger(__name__)


class OrganizationService:
    """
    조직 관리 서비스 클래스
    
    조직 생성, 수정, 삭제, 조회 및 관련 기능을 제공합니다.
    """
    
    def __init__(self, db: Session):
        """
        조직 서비스 초기화
        
        Args:
            db: 데이터베이스 세션
        """
        self.db = db
        logger.debug("🏢 조직 서비스 초기화")
    
    async def create_organization(
        self, 
        org_data: OrganizationCreate,
        admin_email: str,
        admin_password: str,
        admin_name: Optional[str] = None
    ) -> OrganizationResponse:
        """
        새 조직 생성
        
        Args:
            org_data: 조직 생성 데이터
            admin_email: 관리자 이메일
            admin_password: 관리자 비밀번호
            admin_name: 관리자 이름
            
        Returns:
            생성된 조직 정보
            
        Raises:
            HTTPException: 조직 생성 실패 시
        """
        try:
            logger.info(f"🏢 조직 생성 시작: {org_data.name}")
            
            # 1. 조직명 중복 확인
            existing_org = self.db.query(Organization).filter(
                Organization.name == org_data.name
            ).first()
            
            if existing_org:
                raise HTTPException(
                    status_code=400,
                    detail=f"조직명 '{org_data.name}'이 이미 존재합니다."
                )
            
            # 2. 도메인 중복 확인 (도메인이 제공된 경우)
            if org_data.domain:
                existing_domain = self.db.query(Organization).filter(
                    Organization.domain == org_data.domain
                ).first()
                
                if existing_domain:
                    raise HTTPException(
                        status_code=400,
                        detail=f"도메인 '{org_data.domain}'이 이미 사용 중입니다."
                    )
            
            # 3. 조직 생성
            org_uuid = str(uuid.uuid4())
            new_org = Organization(
                org_uuid=org_uuid,
                name=org_data.name,
                domain=org_data.domain,
                description=org_data.description,
                max_users=org_data.max_users or settings.DEFAULT_MAX_USERS_PER_ORG,
                max_storage_gb=org_data.max_storage_gb or settings.DEFAULT_MAX_STORAGE_PER_ORG,
                settings=org_data.settings or {},
                is_active=True,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            
            self.db.add(new_org)
            self.db.flush()  # ID 생성을 위해 flush
            
            logger.info(f"✅ 조직 생성 완료: {new_org.name} (ID: {new_org.id})")
            
            # 4. 관리자 계정 생성
            admin_user = await self._create_admin_user(
                org_id=new_org.id,
                email=admin_email,
                password=admin_password,
                full_name=admin_name or f"{org_data.name} 관리자"
            )
            
            # 5. 기본 메일 사용자 생성
            await self._create_mail_user(
                user_id=admin_user.id,
                org_id=new_org.id,
                email=admin_email
            )
            
            # 6. 기본 설정 적용
            await self._apply_default_settings(new_org.id)
            
            self.db.commit()
            
            logger.info(f"🎉 조직 '{new_org.name}' 생성 및 초기화 완료")
            
            return OrganizationResponse(
                id=new_org.id,
                org_uuid=new_org.org_uuid,
                name=new_org.name,
                domain=new_org.domain,
                description=new_org.description,
                is_active=new_org.is_active,
                max_users=new_org.max_users,
                max_storage_gb=new_org.max_storage_gb,
                settings=new_org.settings,
                created_at=new_org.created_at,
                updated_at=new_org.updated_at
            )
            
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ 조직 생성 오류: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"조직 생성 중 오류가 발생했습니다: {str(e)}"
            )
    
    async def get_organization(self, org_id: int) -> Optional[OrganizationResponse]:
        """
        조직 정보 조회
        
        Args:
            org_id: 조직 ID
            
        Returns:
            조직 정보 또는 None
        """
        try:
            org = self.db.query(Organization).filter(
                Organization.id == org_id,
                Organization.is_active == True
            ).first()
            
            if not org:
                return None
            
            return OrganizationResponse(
                id=org.id,
                org_uuid=org.org_uuid,
                name=org.name,
                domain=org.domain,
                description=org.description,
                is_active=org.is_active,
                max_users=org.max_users,
                max_storage_gb=org.max_storage_gb,
                settings=org.settings,
                created_at=org.created_at,
                updated_at=org.updated_at
            )
            
        except Exception as e:
            logger.error(f"❌ 조직 조회 오류: {str(e)}")
            return None
    
    async def get_organization_by_uuid(self, org_uuid: str) -> Optional[OrganizationResponse]:
        """
        UUID로 조직 정보 조회
        
        Args:
            org_uuid: 조직 UUID
            
        Returns:
            조직 정보 또는 None
        """
        try:
            org = self.db.query(Organization).filter(
                Organization.org_uuid == org_uuid,
                Organization.is_active == True
            ).first()
            
            if not org:
                return None
            
            return OrganizationResponse(
                id=org.id,
                org_uuid=org.org_uuid,
                name=org.name,
                domain=org.domain,
                description=org.description,
                is_active=org.is_active,
                max_users=org.max_users,
                max_storage_gb=org.max_storage_gb,
                settings=org.settings,
                created_at=org.created_at,
                updated_at=org.updated_at
            )
            
        except Exception as e:
            logger.error(f"❌ 조직 UUID 조회 오류: {str(e)}")
            return None
    
    async def list_organizations(
        self, 
        skip: int = 0, 
        limit: int = 100,
        search: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[OrganizationResponse]:
        """
        조직 목록 조회
        
        Args:
            skip: 건너뛸 개수
            limit: 조회할 개수
            search: 검색어 (조직명, 도메인)
            is_active: 활성 상태 필터
            
        Returns:
            조직 목록
        """
        try:
            query = self.db.query(Organization)
            
            # 활성 상태 필터
            if is_active is not None:
                query = query.filter(Organization.is_active == is_active)
            
            # 검색 필터
            if search:
                search_filter = or_(
                    Organization.name.ilike(f"%{search}%"),
                    Organization.domain.ilike(f"%{search}%"),
                    Organization.description.ilike(f"%{search}%")
                )
                query = query.filter(search_filter)
            
            # 정렬 및 페이지네이션
            orgs = query.order_by(Organization.created_at.desc()).offset(skip).limit(limit).all()
            
            return [
                OrganizationResponse(
                    id=org.id,
                    org_uuid=org.org_uuid,
                    name=org.name,
                    domain=org.domain,
                    description=org.description,
                    is_active=org.is_active,
                    max_users=org.max_users,
                    max_storage_gb=org.max_storage_gb,
                    settings=org.settings,
                    created_at=org.created_at,
                    updated_at=org.updated_at
                )
                for org in orgs
            ]
            
        except Exception as e:
            logger.error(f"❌ 조직 목록 조회 오류: {str(e)}")
            return []
    
    async def update_organization(
        self, 
        org_id: int, 
        org_data: OrganizationUpdate
    ) -> Optional[OrganizationResponse]:
        """
        조직 정보 수정
        
        Args:
            org_id: 조직 ID
            org_data: 수정할 데이터
            
        Returns:
            수정된 조직 정보 또는 None
            
        Raises:
            HTTPException: 수정 실패 시
        """
        try:
            org = self.db.query(Organization).filter(
                Organization.id == org_id
            ).first()
            
            if not org:
                raise HTTPException(
                    status_code=404,
                    detail="조직을 찾을 수 없습니다."
                )
            
            # 수정 가능한 필드 업데이트
            update_data = org_data.dict(exclude_unset=True)
            
            for field, value in update_data.items():
                if hasattr(org, field):
                    setattr(org, field, value)
            
            org.updated_at = datetime.now(timezone.utc)
            
            self.db.commit()
            
            logger.info(f"✅ 조직 수정 완료: {org.name} (ID: {org.id})")
            
            return OrganizationResponse(
                id=org.id,
                org_uuid=org.org_uuid,
                name=org.name,
                domain=org.domain,
                description=org.description,
                is_active=org.is_active,
                max_users=org.max_users,
                max_storage_gb=org.max_storage_gb,
                settings=org.settings,
                created_at=org.created_at,
                updated_at=org.updated_at
            )
            
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ 조직 수정 오류: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"조직 수정 중 오류가 발생했습니다: {str(e)}"
            )
    
    async def delete_organization(self, org_id: int, force: bool = False) -> bool:
        """
        조직 삭제 (소프트 삭제 또는 하드 삭제)
        
        Args:
            org_id: 조직 ID
            force: 강제 삭제 여부 (하드 삭제)
            
        Returns:
            삭제 성공 여부
            
        Raises:
            HTTPException: 삭제 실패 시
        """
        try:
            org = self.db.query(Organization).filter(
                Organization.id == org_id
            ).first()
            
            if not org:
                raise HTTPException(
                    status_code=404,
                    detail="조직을 찾을 수 없습니다."
                )
            
            # 사용자 수 확인
            user_count = self.db.query(User).filter(User.org_id == org_id).count()
            
            if user_count > 1 and not force:  # 관리자 제외하고 사용자가 있으면
                raise HTTPException(
                    status_code=400,
                    detail="조직에 사용자가 있어 삭제할 수 없습니다. 강제 삭제를 원하면 force=true를 사용하세요."
                )
            
            if force:
                # 하드 삭제 - 모든 관련 데이터 삭제
                logger.warning(f"🗑️ 조직 하드 삭제 시작: {org.name} (ID: {org.id})")
                
                # 관련 데이터 삭제는 외래 키 CASCADE로 처리됨
                self.db.delete(org)
                
            else:
                # 소프트 삭제 - 비활성화
                logger.info(f"🔒 조직 소프트 삭제: {org.name} (ID: {org.id})")
                org.is_active = False
                org.updated_at = datetime.now(timezone.utc)
            
            self.db.commit()
            
            logger.info(f"✅ 조직 삭제 완료: {org.name}")
            return True
            
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ 조직 삭제 오류: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"조직 삭제 중 오류가 발생했습니다: {str(e)}"
            )
    
    async def get_organization_stats(self, org_id: int) -> Optional[OrganizationStats]:
        """
        조직 통계 정보 조회
        
        Args:
            org_id: 조직 ID
            
        Returns:
            조직 통계 정보 또는 None
        """
        try:
            org = self.db.query(Organization).filter(
                Organization.id == org_id,
                Organization.is_active == True
            ).first()
            
            if not org:
                return None
            
            # 사용자 수 조회
            total_users = self.db.query(User).filter(User.org_id == org_id).count()
            active_users = self.db.query(User).filter(
                User.org_id == org_id,
                User.is_active == True
            ).count()
            
            # 메일 사용자 수 조회
            mail_users = self.db.query(MailUser).filter(MailUser.org_id == org_id).count()
            
            # 저장 공간 사용량 조회
            storage_used = self.db.query(MailUser).filter(
                MailUser.org_id == org_id
            ).with_entities(
                self.db.func.sum(MailUser.used_mb).label('total_used')
            ).scalar() or 0
            
            return OrganizationStats(
                org_id=org_id,
                total_users=total_users,
                active_users=active_users,
                mail_users=mail_users,
                storage_used_mb=int(storage_used),
                storage_limit_mb=org.max_storage_gb * 1024,
                storage_usage_percent=round((storage_used / (org.max_storage_gb * 1024)) * 100, 2) if org.max_storage_gb > 0 else 0,
                user_usage_percent=round((total_users / org.max_users) * 100, 2) if org.max_users > 0 else 0
            )
            
        except Exception as e:
            logger.error(f"❌ 조직 통계 조회 오류: {str(e)}")
            return None

    async def count_organizations(
        self, 
        search: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> int:
        """
        조직 개수 조회
        
        Args:
            search: 검색어
            is_active: 활성 상태 필터
            
        Returns:
            조직 개수
        """
        try:
            query = self.db.query(Organization)
            
            # 검색 조건 적용
            if search:
                search_filter = or_(
                    Organization.name.ilike(f"%{search}%"),
                    Organization.domain.ilike(f"%{search}%")
                )
                query = query.filter(search_filter)
            
            # 활성 상태 필터
            if is_active is not None:
                query = query.filter(Organization.is_active == is_active)
            
            return query.count()
            
        except Exception as e:
            logger.error(f"❌ 조직 개수 조회 오류: {str(e)}")
            return 0

    async def get_detailed_organization_stats(self, org_id: int):
        """
        상세 조직 통계 정보 조회
        
        Args:
            org_id: 조직 ID
            
        Returns:
            상세 통계 정보 (OrganizationStatsResponse 형태)
        """
        try:
            # 조직 정보 조회
            org_response = await self.get_organization(org_id)
            if not org_response:
                return None
            
            # 통계 정보 조회
            stats = await self.get_organization_stats(org_id)
            if not stats:
                return None
            
            from ..schemas.organization_schema import OrganizationStatsResponse
            return OrganizationStatsResponse(
                organization=org_response,
                stats=stats
            )
            
        except Exception as e:
            logger.error(f"❌ 상세 조직 통계 조회 오류: {str(e)}")
            return None

    async def get_organization_settings(self, org_id: int):
        """
        조직 설정 조회
        
        Args:
            org_id: 조직 ID
            
        Returns:
            조직 설정 정보 (OrganizationSettingsResponse 형태)
        """
        try:
            # 조직 정보 조회
            org_response = await self.get_organization(org_id)
            if not org_response:
                return None
            
            # 설정 정보는 조직의 settings 필드에서 가져오거나 기본값 사용
            from ..schemas.organization_schema import OrganizationSettings, OrganizationSettingsResponse
            
            org = self.db.query(Organization).filter(
                Organization.id == org_id,
                Organization.is_active == True
            ).first()
            
            if not org:
                return None
            
            # 기본 설정 생성
            settings = OrganizationSettings()
            
            # 조직의 settings에서 값이 있으면 덮어쓰기
            if org.settings:
                for key, value in org.settings.items():
                    if hasattr(settings, key):
                        setattr(settings, key, value)
            
            return OrganizationSettingsResponse(
                organization=org_response,
                settings=settings
            )
            
        except Exception as e:
            logger.error(f"❌ 조직 설정 조회 오류: {str(e)}")
            return None

    async def update_organization_settings(self, org_id: int, settings_update):
        """
        조직 설정 수정
        
        Args:
            org_id: 조직 ID
            settings_update: 수정할 설정 정보
            
        Returns:
            수정된 설정 정보 (OrganizationSettingsResponse 형태)
        """
        try:
            org = self.db.query(Organization).filter(
                Organization.id == org_id,
                Organization.is_active == True
            ).first()
            
            if not org:
                return None
            
            # 현재 설정 가져오기
            current_settings = org.settings or {}
            
            # 업데이트할 설정 적용
            update_data = settings_update.dict(exclude_unset=True)
            current_settings.update(update_data)
            
            # 설정 저장
            org.settings = current_settings
            org.updated_at = datetime.now(timezone.utc)
            
            self.db.commit()
            
            # 업데이트된 설정 반환
            return await self.get_organization_settings(org_id)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ 조직 설정 수정 오류: {str(e)}")
            return None
    
    async def _create_admin_user(
        self, 
        org_id: int, 
        email: str, 
        password: str, 
        full_name: str
    ):
        """
        관리자 사용자 생성
        
        Args:
            org_id: 조직 ID
            email: 이메일
            password: 비밀번호
            full_name: 전체 이름
            
        Returns:
            생성된 사용자
        """
        user_uuid = str(uuid.uuid4())
        password_hash = get_password_hash(password)
        
        admin_user = User(
            user_uuid=user_uuid,
            org_id=org_id,
            username=email.split('@')[0],  # 이메일의 로컬 부분을 사용자명으로
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            is_active=True,
            is_admin=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        self.db.add(admin_user)
        self.db.flush()
        
        logger.info(f"✅ 관리자 사용자 생성: {email} (ID: {admin_user.id})")
        return admin_user
    
    async def _create_mail_user(self, user_id: int, org_id: int, email: str):
        """
        메일 사용자 생성
        
        Args:
            user_id: 사용자 ID
            org_id: 조직 ID
            email: 이메일
            
        Returns:
            생성된 메일 사용자
        """
        # 사용자 정보 조회
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("사용자를 찾을 수 없습니다.")
        
        mail_user = MailUser(
            user_id=user_id,
            org_id=org_id,
            user_uuid=user.user_uuid,
            email=email,
            password_hash=user.password_hash,  # 동일한 비밀번호 해시 사용
            quota_mb=settings.DEFAULT_MAIL_QUOTA_MB,
            used_mb=0,
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        self.db.add(mail_user)
        self.db.flush()
        
        logger.info(f"✅ 메일 사용자 생성: {email} (ID: {mail_user.id})")
        return mail_user
    
    async def _apply_default_settings(self, org_id: int) -> None:
        """
        기본 설정 적용
        
        Args:
            org_id: 조직 ID
        """
        try:
            # 기본 메일 폴더 생성 등의 초기화 작업
            # 실제 구현은 메일 서비스에서 처리
            logger.info(f"✅ 조직 기본 설정 적용 완료: {org_id}")
            
        except Exception as e:
            logger.error(f"❌ 기본 설정 적용 오류: {str(e)}")


def get_organization_service(db: Session = Depends(get_db)) -> OrganizationService:
    """
    조직 서비스 인스턴스 반환
    
    Args:
        db: 데이터베이스 세션
        
    Returns:
        조직 서비스 인스턴스
    """
    return OrganizationService(db)