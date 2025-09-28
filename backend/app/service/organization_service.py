"""
조직 관리 서비스

SaaS 다중 조직 지원을 위한 조직 관리 기능
"""
import logging
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
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
            
            # 1. org_id 자동 생성 (UUID)
            org_id = str(uuid.uuid4())
            logger.info(f"📋 자동 생성된 조직 ID: {org_id}")
            
            # 2. 조직명 중복 확인
            existing_org = self.db.query(Organization).filter(
                Organization.name == org_data.name
            ).first()
            
            if existing_org:
                raise HTTPException(
                    status_code=400,
                    detail=f"조직명 '{org_data.name}'이 이미 존재합니다."
                )
            
            # 3. org_code 중복 확인
            existing_org_code = self.db.query(Organization).filter(
                Organization.org_code == org_data.org_code
            ).first()
            
            if existing_org_code:
                raise HTTPException(
                    status_code=400,
                    detail=f"조직 코드 '{org_data.org_code}'가 이미 존재합니다."
                )
            
            # 4. subdomain 중복 확인
            existing_subdomain = self.db.query(Organization).filter(
                Organization.subdomain == org_data.subdomain
            ).first()
            
            if existing_subdomain:
                raise HTTPException(
                    status_code=400,
                    detail=f"서브도메인 '{org_data.subdomain}'이 이미 존재합니다."
                )
            
            # 5. 도메인 중복 확인 (도메인이 제공된 경우)
            if org_data.domain:
                existing_domain = self.db.query(Organization).filter(
                    Organization.domain == org_data.domain
                ).first()
                
                if existing_domain:
                    raise HTTPException(
                        status_code=400,
                        detail=f"도메인 '{org_data.domain}'이 이미 사용 중입니다."
                    )
            
            # 6. 조직 생성 (한글 문자열 UTF-8 처리)
            # 한글 문자열을 명시적으로 UTF-8로 인코딩/디코딩하여 처리
            org_name = org_data.name.encode('utf-8').decode('utf-8') if org_data.name else None
            org_description = org_data.description.encode('utf-8').decode('utf-8') if org_data.description else None
            admin_name_utf8 = admin_name.encode('utf-8').decode('utf-8') if admin_name else None
            
            new_org = Organization(
                org_id=org_id,
                org_code=org_data.org_code,
                subdomain=org_data.subdomain,
                name=org_name,
                domain=org_data.domain,
                description=org_description,
                admin_email=admin_email,
                admin_name=admin_name_utf8,
                max_users=org_data.max_users or settings.DEFAULT_MAX_USERS_PER_ORG,
                max_storage_gb=org_data.max_storage_gb or settings.DEFAULT_MAX_STORAGE_PER_ORG,
                is_active=True
            )
            
            self.db.add(new_org)
            self.db.flush()  # ID 생성을 위해 flush
            
            logger.info(f"✅ 조직 생성 완료: {new_org.name} (ID: {new_org.org_id})")
            
            # 4. 관리자 계정 생성
            admin_user = await self._create_admin_user(
                org_id=new_org.org_id,
                email=admin_email,
                password=admin_password,
                full_name=admin_name or f"{org_data.name} 관리자"
            )
            
            # 5. 기본 메일 사용자 생성
            await self._create_mail_user(
                user_id=admin_user.user_id,
                org_id=new_org.org_id,
                email=admin_email
            )
            
            # 6. 기본 설정 적용
            await self._apply_default_settings(new_org.org_id)
            
            self.db.commit()
            
            logger.info(f"🎉 조직 '{new_org.name}' 생성 및 초기화 완료")
            
            return OrganizationResponse(
                org_id=new_org.org_id,
                org_code=new_org.org_code,
                subdomain=new_org.subdomain,
                admin_email=new_org.admin_email,
                name=new_org.name,
                domain=new_org.domain,
                description=new_org.description,
                is_active=new_org.is_active,
                max_users=new_org.max_users,
                max_storage_gb=new_org.max_storage_gb,
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
    
    async def get_organization(self, org_id: str) -> Optional[OrganizationResponse]:
        """
        조직 정보 조회
        
        Args:
            org_id: 조직 ID
            
        Returns:
            조직 정보 또는 None
        """
        try:
            org = self.db.query(Organization).filter(
                Organization.org_id == org_id,
                Organization.is_active == True
            ).first()
            
            if not org:
                return None
            
            # 설정을 딕셔너리로 변환
            settings_dict = {}
            if hasattr(org, 'settings') and org.settings:
                # org.settings가 리스트인 경우 (OrganizationSettings 객체들)
                if isinstance(org.settings, list):
                    for setting in org.settings:
                        settings_dict[setting.setting_key] = setting.setting_value
                # org.settings가 단일 객체인 경우
                elif hasattr(org.settings, 'setting_key'):
                    settings_dict[org.settings.setting_key] = org.settings.setting_value
                # org.settings가 이미 딕셔너리인 경우
                elif isinstance(org.settings, dict):
                    settings_dict = org.settings
            
            return OrganizationResponse(
                org_id=org.org_id,
                org_code=org.org_code,
                subdomain=org.subdomain,
                admin_email=org.admin_email,
                name=org.name,
                domain=org.domain,
                description=org.description,
                is_active=org.is_active,
                max_users=org.max_users,
                max_storage_gb=org.max_storage_gb,
                settings=settings_dict,
                created_at=org.created_at,
                updated_at=org.updated_at
            )
            
        except Exception as e:
            logger.error(f"❌ 조직 조회 오류: {str(e)}")
            return None
    
    async def get_organization_by_id(self, org_id: str) -> Optional[OrganizationResponse]:
        """
        ID로 조직 정보 조회
        
        Args:
            org_id: 조직 ID
            
        Returns:
            조직 정보 또는 None
        """
        try:
            org = self.db.query(Organization).filter(
                Organization.org_id == org_id,
                Organization.is_active == True
            ).first()
            
            if not org:
                return None
            
            return OrganizationResponse(
                org_id=org.org_id,
                org_code=org.org_code,
                subdomain=org.subdomain,
                admin_email=org.admin_email,
                name=org.name,
                domain=org.domain,
                description=org.description,
                is_active=org.is_active,
                max_users=org.max_users,
                max_storage_gb=org.max_storage_gb,
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
        조직 목록 조회 (성능 최적화)
        
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
            
            # 정렬 및 페이지네이션 (인덱스 활용을 위해 org_id 기준 정렬로 변경)
            orgs = query.order_by(Organization.org_code.desc()).offset(skip).limit(limit).all()
            
            return [
                OrganizationResponse(
                    org_id=org.org_id,
                    org_code=org.org_code,
                    subdomain=org.subdomain,
                    admin_email=org.admin_email,
                    name=org.name,
                    domain=org.domain,
                    description=org.description,
                    is_active=org.is_active,
                    max_users=org.max_users,
                    max_storage_gb=org.max_storage_gb,
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
        org_id: str, 
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
                Organization.org_id == org_id
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
            
            logger.info(f"✅ 조직 수정 완료: {org.name} (ID: {org.org_id})")
            
            return OrganizationResponse(
                org_id=org.org_id,
                org_code=org.org_code,
                subdomain=org.subdomain,
                admin_email=org.admin_email,
                name=org.name,
                domain=org.domain,
                description=org.description,
                is_active=org.is_active,
                max_users=org.max_users,
                max_storage_gb=org.max_storage_gb,
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
    
    async def delete_organization(self, org_id: str, force: bool = False) -> bool:
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
                Organization.org_id == org_id
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
                logger.warning(f"🗑️ 조직 하드 삭제 시작: {org.name} (ID: {org.org_id})")
                
                # 관련 데이터 삭제는 외래 키 CASCADE로 처리됨
                self.db.delete(org)
                
            else:
                # 소프트 삭제 - 비활성화
                logger.info(f"🔒 조직 소프트 삭제: {org.name} (ID: {org.org_id})")
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
    
    async def get_organization_stats(self, org_id: str) -> Optional[OrganizationStats]:
        """
        조직 통계 정보 조회
        
        Args:
            org_id: 조직 ID
            
        Returns:
            조직 통계 정보 또는 None
        """
        try:
            org = self.db.query(Organization).filter(
                Organization.org_id == org_id,
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
                func.sum(MailUser.storage_used_mb).label('total_used')
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

    async def get_detailed_organization_stats(self, org_id: str):
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

    async def get_organization_settings(self, org_id: str):
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
                Organization.org_id == org_id,
                Organization.is_active == True
            ).first()
            
            if not org:
                return None
            
            # 기본 설정 생성
            settings = OrganizationSettings()
            
            # 조직의 settings에서 값이 있으면 덮어쓰기
            if org.settings:
                # org.settings는 OrganizationSettings 객체들의 리스트
                settings_dict = {}
                if isinstance(org.settings, list):
                    for setting in org.settings:
                        if hasattr(setting, 'setting_key') and hasattr(setting, 'setting_value'):
                            settings_dict[setting.setting_key] = setting.setting_value
                
                # 딕셔너리의 값들을 OrganizationSettings 객체의 속성으로 설정
                for key, value in settings_dict.items():
                    if hasattr(settings, key):
                        # 타입 변환 처리
                        if key in ['mail_retention_days', 'max_attachment_size_mb', 'backup_retention_days']:
                            try:
                                setattr(settings, key, int(value))
                            except (ValueError, TypeError):
                                pass  # 기본값 유지
                        elif key in ['spam_filter_enabled', 'virus_scan_enabled', 'mail_encryption_enabled', 
                                   'backup_enabled', 'email_notifications', 'sms_notifications', 
                                   'two_factor_auth', 'ip_whitelist_enabled', 'webmail_enabled', 
                                   'mobile_app_enabled', 'api_access_enabled']:
                            try:
                                setattr(settings, key, str(value).lower() in ['true', '1', 'yes', 'on'])
                            except (ValueError, TypeError):
                                pass  # 기본값 유지
                        else:
                            setattr(settings, key, value)
            
            return OrganizationSettingsResponse(
                organization=org_response,
                settings=settings
            )
            
        except Exception as e:
            logger.error(f"❌ 조직 설정 조회 오류: {str(e)}")
            return None

    async def update_organization_settings(self, org_id: str, settings_update):
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
                Organization.org_id == org_id,
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
        org_id: str, 
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
        user_id = f"admin_{uuid.uuid4().hex[:8]}"  # 관리자 사용자 ID 생성
        password_hash = get_password_hash(password)
        
        admin_user = User(
            user_id=user_id,
            user_uuid=user_uuid,
            org_id=org_id,
            username=email.split('@')[0],  # 이메일의 로컬 부분을 사용자명으로
            email=email,
            hashed_password=password_hash,
            is_active=True,
            role="admin",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        self.db.add(admin_user)
        self.db.flush()
        
        logger.info(f"✅ 관리자 사용자 생성: {email} (ID: {admin_user.user_id})")
        return admin_user
    
    async def _create_mail_user(self, user_id: int, org_id: str, email: str):
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
        user = self.db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise ValueError("사용자를 찾을 수 없습니다.")
        
        mail_user = MailUser(
            user_id=user_id,
            org_id=org_id,
            user_uuid=user.user_uuid,
            email=email,
            password_hash=user.hashed_password,
            display_name=user.username,  # 사용자명을 표시 이름으로 사용
            is_active=True,
            storage_used_mb=0  # 사용 중인 저장 용량 초기화
        )
        
        self.db.add(mail_user)
        self.db.flush()
        
        logger.info(f"✅ 메일 사용자 생성: {email} (ID: {mail_user.user_id})")
        return mail_user
    
    async def _apply_default_settings(self, org_id: str) -> None:
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