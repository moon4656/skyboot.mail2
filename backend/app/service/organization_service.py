"""
조직 관리 서비스

SaaS 다중 조직 지원을 위한 조직 관리 기능
"""
import logging
import uuid
import traceback
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from fastapi import HTTPException, Depends

from ..model import Organization, User, MailUser, OrganizationSettings
from ..schemas.organization_schema import (
    OrganizationCreate, OrganizationUpdate, OrganizationResponse,
    OrganizationSettings as OrganizationSettingsSchema, OrganizationStats
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
            
            # 설정을 딕셔너리로 변환 (핵심 조직 필드 제외)
            settings_dict = {}
            # 핵심 조직 필드들 (settings에서 제외해야 할 키들)
            core_org_fields = {
                'max_users', 'max_storage_gb', 'timezone', 'name', 'domain', 
                'description', 'is_active', 'org_id', 'org_code', 'subdomain',
                'admin_email', 'created_at', 'updated_at'
            }
            
            if hasattr(new_org, 'settings') and new_org.settings:
                # org.settings가 리스트인 경우 (OrganizationSettings 객체들)
                if isinstance(new_org.settings, list):
                    for setting in new_org.settings:
                        if setting.setting_key not in core_org_fields:
                            settings_dict[setting.setting_key] = setting.setting_value
                # org.settings가 단일 객체인 경우
                elif hasattr(new_org.settings, 'setting_key'):
                    if new_org.settings.setting_key not in core_org_fields:
                        settings_dict[new_org.settings.setting_key] = new_org.settings.setting_value
                # org.settings가 이미 딕셔너리인 경우
                elif isinstance(new_org.settings, dict):
                    for key, value in new_org.settings.items():
                        if key not in core_org_fields:
                            settings_dict[key] = value
            
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
                max_emails_per_day=new_org.max_emails_per_day,
                settings=settings_dict,
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
            logger.info(f"🔍 get_organization 호출 - org_id: {org_id}, 타입: {type(org_id)}")
            org = self.db.query(Organization).filter(
                Organization.org_id == org_id,
                Organization.is_active == True
            ).first()
            
            logger.info(f"🔍 get_organization 쿼리 결과 - org: {org is not None}")
            if not org:
                logger.warning(f"⚠️ get_organization - 조직을 찾을 수 없음: {org_id}")
                return None
            
            # 설정을 딕셔너리로 변환 (핵심 조직 필드 제외 + 허용된 키만 포함)
            settings_dict = {}
            # 핵심 조직 필드들 (settings에서 제외해야 할 키들)
            core_org_fields = {
                'max_users', 'max_storage_gb', 'timezone', 'name', 'domain', 
                'description', 'is_active', 'org_id', 'org_code', 'subdomain',
                'admin_email', 'created_at', 'updated_at'
            }
            
            # 허용된 설정 키 목록 (organization_schema.py와 동일)
            allowed_keys = {
                'mail_retention_days',
                'max_attachment_size_mb',
                'max_mail_size_mb',
                'max_emails_per_day',
                'enable_spam_filter',
                'enable_virus_scan',
                'enable_encryption',
                'backup_enabled',
                'backup_retention_days',
                'notification_settings',
                'security_settings',
                'feature_flags',
                'features',           # 추가된 키
                'theme',              # 추가된 키
                'power',              # 전력/성능 관련 설정
                'imap_enabled',       # IMAP 서버 활성화 설정
                'smtp_enabled',       # SMTP 서버 활성화 설정
                'mail_server_enabled' # 메일 서버 전체 활성화 설정
            }
            
            if hasattr(org, 'settings') and org.settings:
                # org.settings가 리스트인 경우 (OrganizationSettings 객체들)
                if isinstance(org.settings, list):
                    for setting in org.settings:
                        if (setting.setting_key not in core_org_fields and 
                            setting.setting_key in allowed_keys):
                            settings_dict[setting.setting_key] = setting.setting_value
                            logger.debug(f"✅ 허용된 설정 키 포함: {setting.setting_key}")
                        elif setting.setting_key not in core_org_fields:
                            logger.warning(f"⚠️ 허용되지 않은 설정 키 무시: {setting.setting_key}")
                # org.settings가 단일 객체인 경우
                elif hasattr(org.settings, 'setting_key'):
                    if (org.settings.setting_key not in core_org_fields and 
                        org.settings.setting_key in allowed_keys):
                        settings_dict[org.settings.setting_key] = org.settings.setting_value
                        logger.debug(f"✅ 허용된 설정 키 포함: {org.settings.setting_key}")
                    elif org.settings.setting_key not in core_org_fields:
                        logger.warning(f"⚠️ 허용되지 않은 설정 키 무시: {org.settings.setting_key}")
                # org.settings가 이미 딕셔너리인 경우
                elif isinstance(org.settings, dict):
                    for key, value in org.settings.items():
                        if key not in core_org_fields and key in allowed_keys:
                            settings_dict[key] = value
                            logger.debug(f"✅ 허용된 설정 키 포함: {key}")
                        elif key not in core_org_fields:
                            logger.warning(f"⚠️ 허용되지 않은 설정 키 무시: {key}")
            
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
                max_emails_per_day=org.max_emails_per_day,
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
            logger.info(f"🔍 get_organization_by_id 호출 - org_id: {org_id}, 타입: {type(org_id)}")
            
            # 모든 조직 조회해서 디버그
            all_orgs = self.db.query(Organization).all()
            logger.info(f"🔍 전체 조직 수: {len(all_orgs)}")
            for org in all_orgs:
                logger.info(f"🔍 조직 정보 - org_id: {org.org_id}, name: {org.name}, is_active: {org.is_active}")
            
            org = self.db.query(Organization).filter(
                Organization.org_id == org_id,
                Organization.is_active == True
            ).first()
            
            logger.info(f"🔍 get_organization_by_id 쿼리 결과 - org: {org is not None}")
            if not org:
                logger.warning(f"⚠️ get_organization_by_id - 조직을 찾을 수 없음: {org_id}")
                return None
            
            # 설정을 딕셔너리로 변환 (핵심 조직 필드 제외 + 허용된 키만 포함)
            settings_dict = {}
            # 핵심 조직 필드들 (settings에서 제외해야 할 키들)
            core_org_fields = {
                'max_users', 'max_storage_gb', 'timezone', 'name', 'domain', 
                'description', 'is_active', 'org_id', 'org_code', 'subdomain',
                'admin_email', 'created_at', 'updated_at'
            }
            
            # 허용된 설정 키들 (OrganizationBase.validate_settings와 동일)
            allowed_keys = {
                'feature_flags', 'features', 'theme', 'power', 
                'imap_enabled', 'smtp_enabled', 'mail_server_enabled'
            }
            
            if hasattr(org, 'settings') and org.settings:
                # org.settings가 리스트인 경우 (OrganizationSettings 객체들)
                if isinstance(org.settings, list):
                    for setting in org.settings:
                        if setting.setting_key not in core_org_fields and setting.setting_key in allowed_keys:
                            settings_dict[setting.setting_key] = setting.setting_value
                            logger.debug(f"🔧 get_organization_by_id - 포함된 설정: {setting.setting_key} = {setting.setting_value}")
                        elif setting.setting_key not in core_org_fields:
                            logger.warning(f"⚠️ get_organization_by_id - 허용되지 않은 설정 키 무시: {setting.setting_key}")
                # org.settings가 단일 객체인 경우
                elif hasattr(org.settings, 'setting_key'):
                    if org.settings.setting_key not in core_org_fields and org.settings.setting_key in allowed_keys:
                        settings_dict[org.settings.setting_key] = org.settings.setting_value
                        logger.debug(f"🔧 get_organization_by_id - 포함된 설정: {org.settings.setting_key} = {org.settings.setting_value}")
                    elif org.settings.setting_key not in core_org_fields:
                        logger.warning(f"⚠️ get_organization_by_id - 허용되지 않은 설정 키 무시: {org.settings.setting_key}")
                # org.settings가 이미 딕셔너리인 경우
                elif isinstance(org.settings, dict):
                    for key, value in org.settings.items():
                        if key not in core_org_fields and key in allowed_keys:
                            settings_dict[key] = value
                            logger.debug(f"🔧 get_organization_by_id - 포함된 설정: {key} = {value}")
                        elif key not in core_org_fields:
                            logger.warning(f"⚠️ get_organization_by_id - 허용되지 않은 설정 키 무시: {key}")
            
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
                max_emails_per_day=org.max_emails_per_day,
                settings=settings_dict,
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
            
            result = []
            for org in orgs:
                # 설정을 딕셔너리로 변환 (핵심 조직 필드 제외 + 허용된 키만 포함)
                settings_dict = {}
                # settings에서 제외해야 핵심 조직 필드들 (스키마 검증 충돌 방지)
                core_org_fields = {
                    'max_users', 'max_storage_gb', 'timezone', 'name', 'domain', 
                    'description', 'is_active', 'org_id', 'org_code', 'subdomain',
                    'admin_email', 'created_at', 'updated_at'
                }
                
                # 허용된 설정 키들 (OrganizationBase.validate_settings와 동일)
                allowed_keys = {
                    'feature_flags', 'features', 'theme', 'power', 
                    'imap_enabled', 'smtp_enabled', 'mail_server_enabled'
                }

                if hasattr(org, 'settings') and org.settings:
                    # org.settings가 리스트인 경우 (OrganizationSettings 객체들)
                    if isinstance(org.settings, list):
                        for setting in org.settings:
                            if setting.setting_key not in core_org_fields and setting.setting_key in allowed_keys:
                                settings_dict[setting.setting_key] = setting.setting_value
                            elif setting.setting_key not in core_org_fields:
                                logger.warning(f"⚠️ list_organizations - 허용되지 않은 설정 키 무시: {setting.setting_key}")
                    # org.settings가 단일 객체인 경우
                    elif hasattr(org.settings, 'setting_key'):
                        if org.settings.setting_key not in core_org_fields and org.settings.setting_key in allowed_keys:
                            settings_dict[org.settings.setting_key] = org.settings.setting_value
                        elif org.settings.setting_key not in core_org_fields:
                            logger.warning(f"⚠️ list_organizations - 허용되지 않은 설정 키 무시: {org.settings.setting_key}")
                    # org.settings가 이미 딕셔너리인 경우
                    elif isinstance(org.settings, dict):
                        for key, value in org.settings.items():
                            if key not in core_org_fields and key in allowed_keys:
                                settings_dict[key] = value
                            elif key not in core_org_fields:
                                logger.warning(f"⚠️ list_organizations - 허용되지 않은 설정 키 무시: {key}")
                
                result.append(OrganizationResponse(
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
                    max_emails_per_day=org.max_emails_per_day,
                    settings=settings_dict,
                    created_at=org.created_at,
                    updated_at=org.updated_at
                ))
            
            return result
            
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
            
            # 수정 가능한 필드 업데이트 - Pydantic 모델인지 딕셔너리인지 확인
            if hasattr(org_data, 'dict'):
                # Pydantic 모델인 경우
                update_data = org_data.dict(exclude_unset=True)
            else:
                # 이미 딕셔너리인 경우
                update_data = org_data
            
            # settings는 relationship이므로 제외하고 처리
            settings_data = update_data.pop('settings', None)
            
            # 기본 필드 업데이트
            for field, value in update_data.items():
                if hasattr(org, field) and field != 'settings':
                    setattr(org, field, value)
            
            # settings가 있는 경우 별도 처리
            if settings_data is not None:
                await self.update_organization_settings(org_id, settings_data)
            
            org.updated_at = datetime.now(timezone.utc)
            
            self.db.commit()
            
            logger.info(f"✅ 조직 수정 완료: {org.name} (ID: {org.org_id})")
            
            # 설정을 딕셔너리로 변환 (핵심 조직 필드 제외)
            settings_dict = {}
            # 핵심 조직 필드들 (settings에서 제외해야 할 키들)
            core_org_fields = {
                'max_users', 'max_storage_gb', 'timezone', 'name', 'domain', 
                'description', 'is_active', 'org_id', 'org_code', 'subdomain',
                'admin_email', 'created_at', 'updated_at'
            }
            
            if hasattr(org, 'settings') and org.settings:
                # org.settings가 리스트인 경우 (OrganizationSettings 객체들)
                if isinstance(org.settings, list):
                    for setting in org.settings:
                        if setting.setting_key not in core_org_fields:
                            settings_dict[setting.setting_key] = setting.setting_value
                # org.settings가 단일 객체인 경우
                elif hasattr(org.settings, 'setting_key'):
                    if org.settings.setting_key not in core_org_fields:
                        settings_dict[org.settings.setting_key] = org.settings.setting_value
                # org.settings가 이미 딕셔너리인 경우
                elif isinstance(org.settings, dict):
                    for key, value in org.settings.items():
                        if key not in core_org_fields:
                            settings_dict[key] = value
            
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
                max_emails_per_day=org.max_emails_per_day,
                settings=settings_dict,
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
                # 하드 삭제 - CASCADE 설정을 활용하여 관련 데이터 자동 삭제
                logger.warning(f"🗑️ 조직 하드 삭제 시작: {org.name} (ID: {org.org_id})")
                
                # 조직 이름과 ID를 미리 저장 (세션 종료 후 접근 불가)
                org_name = org.name
                org_uuid = org.org_id
                
                # 현재 세션 완전히 종료
                self.db.close()
                
                # 완전히 새로운 세션으로 조직 삭제 (CASCADE 활용)
                from app.database.mail import get_db
                from sqlalchemy import text
                
                new_db = next(get_db())
                try:
                    result = new_db.execute(
                        text("DELETE FROM organizations WHERE org_id = :org_id"),
                        {"org_id": org_uuid}
                    )
                    new_db.commit()
                    
                    if result.rowcount > 0:
                        logger.info(f"🗑️ 조직 삭제 완료 (CASCADE로 관련 데이터 자동 삭제): {org_name}")
                    else:
                        logger.warning(f"⚠️ 삭제할 조직을 찾을 수 없음: {org_uuid}")
                        
                except Exception as e:
                    new_db.rollback()
                    logger.error(f"❌ 조직 삭제 중 오류 발생: {e}")
                    raise
                finally:
                    new_db.close()
                
                # 하드 삭제 완료 - 기존 세션 commit 하지 않음
                logger.info(f"✅ 조직 삭제 완료: {org_name}")
                return True
                
            else:
                # 소프트 삭제 - 비활성화
                logger.info(f"🔒 조직 소프트 삭제: {org.name} (ID: {org.org_id})")
                org.is_active = False
                org.updated_at = datetime.now(timezone.utc)
                org.deleted_at = datetime.now(timezone.utc)
                
                # 소프트 삭제만 기존 세션에서 commit
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
            logger.info(f"🔍 조직 조회 시작 - org_id: {org_id}")
            
            org = self.db.query(Organization).filter(
                Organization.org_id == org_id,
                Organization.is_active == True
            ).first()
            
            if not org:
                logger.warning(f"⚠️ 조직을 찾을 수 없음 - org_id: {org_id}")
                # 모든 조직 목록 확인 (디버깅용)
                all_orgs = self.db.query(Organization).all()
                logger.info(f"📋 전체 조직 목록: {[org.org_id for org in all_orgs]}")
                return None
            
            logger.info(f"✅ 조직 조회 성공 - org_id: {org_id}, name: {org.name}")
            
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
            org_response = await self.get_organization_by_id(org_id)
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
        import json
        
        try:
            # 조직 정보 조회
            org_response = await self.get_organization_by_id(org_id)
            if not org_response:
                return None
            
            # 설정 정보는 OrganizationSettings 테이블에서 가져오거나 기본값 사용
            from ..schemas.organization_schema import OrganizationSettingsResponse
            
            # OrganizationSettings 테이블에서 설정 조회 (모델 사용)
            org_settings = self.db.query(OrganizationSettings).filter(
                OrganizationSettings.org_id == org_id
            ).all()
            
            # 설정 딕셔너리 생성
            settings_dict = {}
            for setting in org_settings:
                setting_key = setting.setting_key
                setting_value = setting.setting_value
                setting_type = setting.setting_type
                
                # 타입에 따라 값 변환
                try:
                    if setting_type == "json":
                        settings_dict[setting_key] = json.loads(setting_value)
                    elif setting_type == "boolean":
                        settings_dict[setting_key] = setting_value.lower() in ['true', '1', 'yes', 'on']
                    elif setting_type == "integer":
                        settings_dict[setting_key] = int(setting_value)
                    elif setting_type == "float":
                        settings_dict[setting_key] = float(setting_value)
                    else:
                        settings_dict[setting_key] = setting_value
                except (ValueError, TypeError, json.JSONDecodeError) as e:
                    logger.warning(f"⚠️ 설정 값 변환 오류 - {setting_key}: {setting_value}, 오류: {str(e)}")
                    settings_dict[setting_key] = setting_value  # 원본 값 사용

            # 핵심 조직 필드 반영: 일일 최대 메일 발송 수
            try:
                if hasattr(org_response, 'max_emails_per_day') and org_response.max_emails_per_day is not None:
                    settings_dict['max_emails_per_day'] = org_response.max_emails_per_day
            except Exception as e:
                logger.warning(f"⚠️ max_emails_per_day 설정 반영 오류: {str(e)}")
            
            # 기본 설정과 데이터베이스 설정을 병합하여 OrganizationSettingsSchema 생성
            try:
                settings = OrganizationSettingsSchema(**settings_dict)
            except Exception as e:
                logger.warning(f"⚠️ 설정 스키마 생성 오류: {str(e)}, 기본 설정 사용")
                settings = OrganizationSettingsSchema()
                # 유효한 필드만 설정
                for key, value in settings_dict.items():
                    if hasattr(settings, key):
                        try:
                            setattr(settings, key, value)
                            logger.debug(f"🔧 설정 적용: {key} = {value}")
                        except Exception as field_error:
                            logger.warning(f"⚠️ 필드 설정 오류 - {key}: {str(field_error)}")
            
            logger.info(f"✅ 조직 설정 조회 완료: {org_id}, 설정 수: {len(settings_dict)}")
            
            return OrganizationSettingsResponse(
                organization=org_response,
                settings=settings
            )
            
        except Exception as e:
            logger.error(f"❌ 조직 설정 조회 오류: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
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
        import json
        
        try:
            org = self.db.query(Organization).filter(
                Organization.org_id == org_id,
                Organization.is_active == True
            ).first()
            
            if not org:
                logger.warning(f"⚠️ 조직을 찾을 수 없음: {org_id}")
                return None
            
            # 업데이트할 설정 적용 - Pydantic 모델인지 딕셔너리인지 확인
            if hasattr(settings_update, 'dict'):
                # Pydantic 모델인 경우
                update_data = settings_update.dict(exclude_unset=True)
            else:
                # 이미 딕셔너리인 경우
                update_data = settings_update
            
            logger.info(f"🔧 조직 설정 업데이트 데이터: {update_data}")
            
            # 허용된 설정 키 목록 (organization_schema.py와 동일하게 유지)
            allowed_keys = {
                'mail_retention_days',
                'max_attachment_size_mb',
                'max_mail_size_mb',
                'max_mailbox_size_mb',
                'enable_spam_filter',
                'enable_virus_scan',
                'enable_encryption',
                'backup_enabled',
                'backup_retention_days',
                'notification_settings',
                'security_settings',
                'feature_flags',
                'features',
                'theme',
                'power',
                'imap_enabled',
                'smtp_enabled',
                'mail_server_enabled'
            }
            
            # 허용되지 않은 키 사전 필터링
            filtered_data = {}
            invalid_keys = []
            
            for setting_key, setting_value in update_data.items():
                if setting_key in allowed_keys or setting_key == "max_emails_per_day":
                    filtered_data[setting_key] = setting_value
                else:
                    invalid_keys.append(setting_key)
                    logger.warning(f"⚠️ 허용되지 않은 설정 키 무시: {setting_key}")
            
            if invalid_keys:
                logger.warning(f"⚠️ 무시된 설정 키들: {invalid_keys}")
            
            # 각 설정을 OrganizationSettings 테이블에 저장/업데이트
            for setting_key, setting_value in filtered_data.items():
                try:
                    # 특수 키 처리: 조직 컬럼에 저장되는 값
                    if setting_key == "max_emails_per_day":
                        try:
                            org.max_emails_per_day = int(setting_value)
                            logger.info(f"🔧 조직 필드 업데이트: max_emails_per_day = {org.max_emails_per_day}")
                        except (ValueError, TypeError) as conv_err:
                            logger.warning(f"⚠️ max_emails_per_day 변환 오류: {str(conv_err)}, 기존 값 유지")
                        # settings 테이블에는 저장하지 않음
                        continue
                    
                    # 기존 설정 찾기
                    existing_setting = self.db.query(OrganizationSettings).filter(
                        OrganizationSettings.org_id == org_id,
                        OrganizationSettings.setting_key == setting_key
                    ).first()
                    
                    # 값의 타입에 따라 적절히 변환 (안전한 변환)
                    setting_value_str = None
                    setting_type = "string"
                    
                    try:
                        if isinstance(setting_value, (dict, list)):
                            # JSON 타입의 경우 JSON 문자열로 변환
                            setting_value_str = json.dumps(setting_value, ensure_ascii=False)
                            setting_type = "json"
                        elif isinstance(setting_value, bool):
                            setting_value_str = str(setting_value).lower()
                            setting_type = "boolean"
                        elif isinstance(setting_value, int):
                            setting_value_str = str(setting_value)
                            setting_type = "integer"
                        elif isinstance(setting_value, float):
                            setting_value_str = str(setting_value)
                            setting_type = "float"
                        else:
                            setting_value_str = str(setting_value)
                            setting_type = "string"
                    except Exception as type_err:
                        logger.warning(f"⚠️ 설정 값 타입 변환 오류 - {setting_key}: {str(type_err)}, 문자열로 처리")
                        setting_value_str = str(setting_value)
                        setting_type = "string"
                    
                    if existing_setting:
                        # 기존 설정 업데이트
                        existing_setting.setting_value = setting_value_str
                        existing_setting.setting_type = setting_type
                        existing_setting.updated_at = datetime.now(timezone.utc)
                        logger.info(f"🔄 설정 업데이트: {setting_key} = {setting_value_str}")
                    else:
                        # 새 설정 생성
                        new_setting = OrganizationSettings(
                            org_id=org_id,
                            setting_key=setting_key,
                            setting_value=setting_value_str,
                            setting_type=setting_type,
                            created_at=datetime.now(timezone.utc)
                        )
                        self.db.add(new_setting)
                        logger.info(f"➕ 새 설정 생성: {setting_key} = {setting_value_str}")
                        
                except Exception as setting_err:
                    logger.error(f"❌ 설정 처리 오류 - {setting_key}: {str(setting_err)}")
                    # 개별 설정 오류는 전체 처리를 중단하지 않고 계속 진행
                    continue
            
            # 조직 업데이트 시간 갱신
            org.updated_at = datetime.now(timezone.utc)
            
            self.db.commit()
            
            logger.info(f"✅ 조직 설정 수정 완료: {org_id}")
            
            # 업데이트된 설정 반환
            return await self.get_organization_settings(org_id)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ 조직 설정 수정 오류: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
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
        from ..model.mail_model import MailFolder, FolderType
        
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
        
        # 기본 메일 폴더들 생성
        await self._create_default_mail_folders(user.user_uuid, org_id)
        
        return mail_user
    
    async def _create_default_mail_folders(self, user_uuid: str, org_id: str):
        """
        사용자의 기본 메일 폴더들을 생성합니다.
        
        Args:
            user_uuid: 사용자 UUID
            org_id: 조직 ID
        """
        from ..model.mail_model import MailFolder, FolderType
        
        # 기본 폴더 정의
        default_folders = [
            {"name": "INBOX", "folder_type": FolderType.INBOX, "is_system": True},
            {"name": "SENT", "folder_type": FolderType.SENT, "is_system": True},
            {"name": "DRAFT", "folder_type": FolderType.DRAFT, "is_system": True},
            {"name": "TRASH", "folder_type": FolderType.TRASH, "is_system": True}
        ]
        
        created_folders = []
        
        for folder_info in default_folders:
            # 이미 존재하는 폴더인지 확인
            existing_folder = self.db.query(MailFolder).filter(
                MailFolder.user_uuid == user_uuid,
                MailFolder.org_id == org_id,
                MailFolder.folder_type == folder_info["folder_type"]
            ).first()
            
            if not existing_folder:
                folder = MailFolder(
                    folder_uuid=str(uuid.uuid4()),
                    user_uuid=user_uuid,
                    org_id=org_id,
                    name=folder_info["name"],
                    folder_type=folder_info["folder_type"],
                    is_system=folder_info["is_system"],
                    created_at=datetime.now(timezone.utc)
                )
                
                self.db.add(folder)
                created_folders.append(folder_info["name"])
        
        if created_folders:
            self.db.flush()
            logger.info(f"📁 기본 메일 폴더 생성 완료 - 사용자: {user_uuid}, 폴더: {created_folders}")
        else:
            logger.info(f"📁 기본 메일 폴더 이미 존재 - 사용자: {user_uuid}")
    
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