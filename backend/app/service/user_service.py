"""
사용자 관리 서비스

SaaS 다중 조직 지원을 위한 사용자 관리 기능
"""
import logging
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, timezone, date
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, text
from fastapi import HTTPException

from ..model.user_model import User
from ..model.mail_model import MailUser
from ..model.organization_model import Organization, OrganizationUsage
from ..schemas.user_schema import (
    UserCreate, UserResponse, UserLogin
)
from ..config import settings
from .auth_service import AuthService

# 로거 설정
logger = logging.getLogger(__name__)


class UserService:
    """
    사용자 관리 서비스 클래스
    
    조직 내 사용자 생성, 수정, 삭제, 조회 및 관련 기능을 제공합니다.
    """
    
    def __init__(self, db: Session):
        """
        사용자 서비스 초기화
        
        Args:
            db: 데이터베이스 세션
        """
        self.db = db
        logger.debug("👤 사용자 서비스 초기화")

    async def create_user(
        self, 
        org_id: str, 
        user_data: UserCreate,
        created_by_admin: bool = False
    ) -> UserResponse:
        """
        조직 내에 새 사용자를 생성합니다.
        
        Args:
            org_id: 조직 ID
            user_data: 사용자 생성 데이터
            created_by_admin: 관리자에 의한 생성 여부
            
        Returns:
            생성된 사용자 정보
            
        Raises:
            HTTPException: 사용자 생성 실패 시
        """
        try:
            logger.info(f"👤 사용자 생성 시작 - 조직: {org_id}, 이메일: {user_data.email}")
            
            # 1. 조직 존재 확인
            org = self.db.query(Organization).filter(Organization.org_id == org_id).first()
            if not org:
                raise HTTPException(
                    status_code=404,
                    detail="조직을 찾을 수 없습니다."
                )
            
            if not org.is_active:
                raise HTTPException(
                    status_code=400,
                    detail="비활성화된 조직입니다."
                )
            
            # 2. 조직 내 사용자 수 제한 확인
            current_user_count = self.db.query(func.count(User.user_id)).filter(
                User.org_id == org_id,
                User.is_active == True
            ).scalar()
            
            if current_user_count >= org.max_users:
                raise HTTPException(
                    status_code=400,
                    detail=f"조직의 최대 사용자 수({org.max_users})에 도달했습니다."
                )
            
            # 3. 사용자 ID 중복 확인 (조직 내)
            existing_user_id = self.db.query(User).filter(
                and_(
                    User.org_id == org_id,
                    User.user_id == user_data.user_id
                )
            ).first()
            
            if existing_user_id:
                raise HTTPException(
                    status_code=400,
                    detail=f"사용자 ID '{user_data.user_id}'가 이미 사용 중입니다."
                )
            
            # 4. 이메일 중복 확인 (조직 내)
            existing_email = self.db.query(User).filter(
                and_(
                    User.org_id == org_id,
                    User.email == user_data.email
                )
            ).first()
            
            if existing_email:
                raise HTTPException(
                    status_code=400,
                    detail=f"이메일 '{user_data.email}'이 이미 사용 중입니다."
                )
            
            # 5. 사용자명 중복 확인 (조직 내)
            existing_username = self.db.query(User).filter(
                and_(
                    User.org_id == org_id,
                    User.username == user_data.username
                )
            ).first()
            
            if existing_username:
                raise HTTPException(
                    status_code=400,
                    detail=f"사용자명 '{user_data.username}'이 이미 사용 중입니다."
                )
            
            # 6. 사용자 생성
            user_uuid = str(uuid.uuid4())
            password_hash = AuthService.get_password_hash(user_data.password)
            
            new_user = User(
                user_id=user_data.user_id,  # 사용자가 입력한 ID 사용
                user_uuid=user_uuid,
                org_id=org_id,
                username=user_data.username,
                email=user_data.email,
                hashed_password=password_hash,
                is_active=True,
                role="user",  # 기본적으로 일반 사용자
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            
            self.db.add(new_user)
            self.db.flush()  # ID 생성을 위해 flush
            
            logger.info(f"✅ 사용자 생성 완료: {new_user.email} (ID: {new_user.user_id})")
            
            # 7. 메일 사용자 생성
            await self._create_mail_user(
                user_id=new_user.user_id,
                org_id=org_id,
                email=user_data.email,
                password_hash=password_hash
            )
            
            # 8. 조직 사용량 업데이트 (사용자 수 증가)
            await self._update_organization_usage_users(org_id)
            
            self.db.commit()
            
            logger.info(f"🎉 사용자 '{new_user.email}' 생성 및 초기화 완료")
            
            return UserResponse(
                id=new_user.user_id,
                user_id=new_user.user_id,
                user_uuid=new_user.user_uuid,
                email=new_user.email,
                username=new_user.username,
                org_id=new_user.org_id,
                role=new_user.role,
                is_active=new_user.is_active,
                created_at=new_user.created_at,
                updated_at=new_user.updated_at
            )
            
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ 사용자 생성 오류: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"사용자 생성 중 오류가 발생했습니다: {str(e)}"
            )

    async def get_user_by_id(self, org_id: str, user_id: str) -> Optional[UserResponse]:
        """
        조직 내에서 사용자 ID로 사용자를 조회합니다.
        
        Args:
            org_id: 조직 ID
            user_id: 사용자 ID
            
        Returns:
            사용자 정보 또는 None
        """
        try:
            user = self.db.query(User).filter(
                and_(
                    User.org_id == org_id,
                    User.user_id == user_id
                )
            ).first()
            
            if not user:
                return None
            
            return UserResponse(
                id=user.user_id,
                user_id=user.user_id,
                user_uuid=user.user_uuid,
                email=user.email,
                username=user.username,
                org_id=user.org_id,
                role=user.role,
                is_active=user.is_active,
                created_at=user.created_at,
                updated_at=user.updated_at
            )
            
        except Exception as e:
            logger.error(f"❌ 사용자 조회 오류: {str(e)}")
            return None

    async def get_user_by_email(self, org_id: str, email: str) -> Optional[UserResponse]:
        """
        조직 내에서 이메일로 사용자를 조회합니다.
        
        Args:
            org_id: 조직 ID
            email: 이메일 주소
            
        Returns:
            사용자 정보 또는 None
        """
        try:
            user = self.db.query(User).filter(
                and_(
                    User.org_id == org_id,
                    User.email == email
                )
            ).first()
            
            if not user:
                return None
            
            return UserResponse(
                id=user.user_id,
                user_id=user.user_id,
                user_uuid=user.user_uuid,
                email=user.email,
                username=user.username,
                org_id=user.org_id,
                role=user.role,
                is_active=user.is_active,
                created_at=user.created_at,
                updated_at=user.updated_at
            )
            
        except Exception as e:
            logger.error(f"❌ 사용자 조회 오류: {str(e)}")
            return None

    async def get_users_by_org(
        self, 
        org_id: str, 
        page: int = 1, 
        limit: int = 20,
        search: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        조직의 사용자 목록을 조회합니다.
        
        Args:
            org_id: 조직 ID
            page: 페이지 번호
            limit: 페이지당 항목 수
            search: 검색어 (이메일, 사용자명)
            is_active: 활성 상태 필터
            
        Returns:
            사용자 목록과 페이지네이션 정보
        """
        try:
            offset = (page - 1) * limit
            
            # 기본 쿼리
            query = self.db.query(User).filter(User.org_id == org_id)
            
            # 검색 조건 추가
            if search:
                search_filter = or_(
                    User.email.ilike(f"%{search}%"),
                    User.username.ilike(f"%{search}%")
                )
                query = query.filter(search_filter)
            
            # 활성 상태 필터
            if is_active is not None:
                query = query.filter(User.is_active == is_active)
            
            # 전체 개수 조회
            total = query.count()
            
            # 페이지네이션 적용
            users = query.order_by(User.created_at.desc()).offset(offset).limit(limit).all()
            
            # 응답 데이터 구성
            user_list = [
                UserResponse(
                    id=user.user_id,
                    user_id=user.user_id,
                    user_uuid=user.user_uuid,
                    email=user.email,
                    username=user.username,
                    org_id=user.org_id,
                    role=user.role,
                    is_active=user.is_active,
                    created_at=user.created_at,
                    updated_at=user.updated_at
                )
                for user in users
            ]
            
            return {
                "users": user_list,
                "total": total,
                "page": page,
                "limit": limit,
                "total_pages": (total + limit - 1) // limit
            }
            
        except Exception as e:
            logger.error(f"❌ 사용자 목록 조회 오류: {str(e)}")
            return {
                "users": [],
                "total": 0,
                "page": page,
                "limit": limit,
                "total_pages": 0
            }

    async def update_user(
        self, 
        org_id: str, 
        user_id: str, 
        update_data: Dict[str, Any]
    ) -> Optional[UserResponse]:
        """
        조직 내 사용자 정보를 업데이트합니다.
        
        Args:
            org_id: 조직 ID
            user_id: 사용자 ID
            update_data: 업데이트할 데이터
            
        Returns:
            업데이트된 사용자 정보 또는 None
        """
        try:
            user = self.db.query(User).filter(
                and_(
                    User.org_id == org_id,
                    User.user_id == user_id
                )
            ).first()
            
            if not user:
                raise HTTPException(
                    status_code=404,
                    detail="사용자를 찾을 수 없습니다."
                )
            
            # 업데이트 가능한 필드들 (User 모델에 실제로 존재하는 필드만)
            allowed_fields = ['username', 'is_active', 'role']
            
            is_active_changed = False
            old_is_active = user.is_active
            
            # roles 배열을 role 단일 값으로 변환 처리
            if 'roles' in update_data and update_data['roles']:
                # roles 배열의 첫 번째 값을 role로 설정
                if isinstance(update_data['roles'], list) and len(update_data['roles']) > 0:
                    update_data['role'] = update_data['roles'][0]
                    logger.info(f"📝 roles 배열을 role로 변환: {update_data['roles']} → {update_data['role']}")
                # roles 필드는 제거 (role 필드로 대체됨)
                update_data.pop('roles', None)
            
            for field, value in update_data.items():
                if field in allowed_fields and hasattr(user, field):
                    if field == 'is_active' and user.is_active != value:
                        is_active_changed = True
                    setattr(user, field, value)
                    logger.info(f"📝 사용자 필드 업데이트: {field} = {value}")
            
            user.updated_at = datetime.now(timezone.utc)
            
            # is_active 상태가 변경된 경우 조직 사용량 업데이트
            if is_active_changed:
                await self._update_organization_usage_users(user.org_id)
                logger.info(f"📊 사용자 활성화 상태 변경: {user.email} ({old_is_active} → {user.is_active})")
            
            self.db.commit()
            self.db.refresh(user)
            
            logger.info(f"✅ 사용자 업데이트 완료: {user.email}")
            
            return UserResponse(
                id=user.user_id,
                user_id=user.user_id,
                user_uuid=user.user_uuid,
                email=user.email,
                username=user.username,
                org_id=user.org_id,
                role=user.role,
                is_active=user.is_active,
                created_at=user.created_at,
                updated_at=user.updated_at
            )
            
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ 사용자 업데이트 오류: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"사용자 업데이트 중 오류가 발생했습니다: {str(e)}"
            )

    async def delete_user(self, org_id: str, user_id: str) -> bool:
        """
        조직 내 사용자를 삭제합니다 (소프트 삭제).
        
        Args:
            org_id: 조직 ID
            user_id: 사용자 ID
            
        Returns:
            삭제 성공 여부
        """
        try:
            user = self.db.query(User).filter(
                and_(
                    User.org_id == org_id,
                    User.user_id == user_id
                )
            ).first()
            
            if not user:
                raise HTTPException(
                    status_code=404,
                    detail="사용자를 찾을 수 없습니다."
                )
            
            # 소프트 삭제 (is_active = False)
            user.is_active = False
            user.updated_at = datetime.now(timezone.utc)
            
            # 관련 메일 사용자도 비활성화
            mail_user = self.db.query(MailUser).filter(
                and_(
                    MailUser.org_id == org_id,
                    MailUser.user_id == user_id
                )
            ).first()
            
            if mail_user:
                mail_user.is_active = False
                mail_user.updated_at = datetime.now(timezone.utc)
            
            # 조직 사용량 업데이트 (사용자 수 감소)
            await self._update_organization_usage_users(user.org_id)
            
            self.db.commit()
            
            logger.info(f"✅ 사용자 삭제 완료: {user.email}")
            return True
            
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ 사용자 삭제 오류: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"사용자 삭제 중 오류가 발생했습니다: {str(e)}"
            )

    async def authenticate_user(
        self, 
        org_id: str, 
        email: str, 
        password: str
    ):
        """
        조직 내에서 사용자를 인증합니다.
        
        Args:
            org_id: 조직 ID
            email: 이메일 주소
            password: 비밀번호
            
        Returns:
            인증된 사용자 객체 또는 None
        """
        try:
            user = self.db.query(User).filter(
                and_(
                    User.org_id == org_id,
                    User.email == email,
                    User.is_active == True
                )
            ).first()
            
            if not user:
                logger.warning(f"🔐 인증 실패 - 사용자 없음: {email}")
                return None
            
            if not AuthService.verify_password(password, user.hashed_password):
                logger.warning(f"🔐 인증 실패 - 비밀번호 불일치: {email}")
                return None
            
            # 마지막 로그인 시간 업데이트
            user.last_login_at = datetime.now(timezone.utc)
            self.db.commit()
            
            logger.info(f"🔐 인증 성공: {email}")
            return user
            
        except Exception as e:
            logger.error(f"❌ 사용자 인증 오류: {str(e)}")
            return None

    async def change_password(
        self, 
        org_id: str, 
        user_id: str, 
        current_password: str, 
        new_password: str
    ) -> bool:
        """
        사용자 비밀번호를 변경합니다.
        
        Args:
            org_id: 조직 ID
            user_id: 사용자 ID
            current_password: 현재 비밀번호
            new_password: 새 비밀번호
            
        Returns:
            비밀번호 변경 성공 여부
        """
        try:
            user = self.db.query(User).filter(
                and_(
                    User.org_id == org_id,
                    User.user_id == user_id
                )
            ).first()
            
            if not user:
                raise HTTPException(
                    status_code=404,
                    detail="사용자를 찾을 수 없습니다."
                )
            
            # 현재 비밀번호 확인
            if not AuthService.verify_password(current_password, user.hashed_password):
                raise HTTPException(
                    status_code=400,
                    detail="현재 비밀번호가 일치하지 않습니다."
                )
            
            # 새 비밀번호 해시화 및 저장
            new_password_hash = AuthService.get_password_hash(new_password)
            user.hashed_password = new_password_hash
            user.updated_at = datetime.now(timezone.utc)
            
            # 메일 사용자 비밀번호도 동기화
            mail_user = self.db.query(MailUser).filter(
                and_(
                    MailUser.org_id == org_id,
                    MailUser.user_id == user_id
                )
            ).first()
            
            if mail_user:
                mail_user.password_hash = new_password_hash
                mail_user.updated_at = datetime.now(timezone.utc)
            
            self.db.commit()
            
            logger.info(f"✅ 비밀번호 변경 완료: {user.email}")
            return True
            
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ 비밀번호 변경 오류: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"비밀번호 변경 중 오류가 발생했습니다: {str(e)}"
            )

    async def get_user_stats(self, org_id: str) -> Dict[str, Any]:
        """
        조직의 사용자 통계를 조회합니다.
        
        Args:
            org_id: 조직 ID
            
        Returns:
            사용자 통계 정보
        """
        try:
            # 전체 사용자 수
            total_users = self.db.query(func.count(User.user_id)).filter(
                User.org_id == org_id
            ).scalar()
            
            # 활성 사용자 수
            active_users = self.db.query(func.count(User.user_id)).filter(
                and_(
                    User.org_id == org_id,
                    User.is_active == True
                )
            ).scalar()
            
            # 관리자 수
            admin_users = self.db.query(func.count(User.user_id)).filter(
                and_(
                    User.org_id == org_id,
                    User.role == "admin",
                    User.is_active == True
                )
            ).scalar()
            
            # 최근 30일 내 생성된 사용자 수
            thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
            recent_users = self.db.query(func.count(User.user_id)).filter(
                and_(
                    User.org_id == org_id,
                    User.created_at >= thirty_days_ago
                )
            ).scalar()
            
            return {
                "total_users": total_users or 0,
                "active_users": active_users or 0,
                "admin_users": admin_users or 0,
                "recent_users": recent_users or 0,
                "inactive_users": (total_users or 0) - (active_users or 0)
            }
            
        except Exception as e:
            logger.error(f"❌ 사용자 통계 조회 오류: {str(e)}")
            return {
                "total_users": 0,
                "active_users": 0,
                "admin_users": 0,
                "recent_users": 0,
                "inactive_users": 0
            }

    async def _create_mail_user(
        self, 
        user_id: str, 
        org_id: str, 
        email: str, 
        password_hash: str
    ):
        """
        메일 사용자 생성 (내부 헬퍼 함수)
        
        Args:
            user_id: 사용자 ID
            org_id: 조직 ID
            email: 이메일
            password_hash: 비밀번호 해시
            
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
            password_hash=password_hash,
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

    async def _update_organization_usage_users(self, org_id: str):
        """
        조직 사용량의 current_users 필드를 업데이트합니다.
        
        Args:
            org_id: 조직 ID
        """
        try:
            logger.info(f"📊 조직 사용량 업데이트 시작 - 조직: {org_id}")
            
            # 현재 활성 사용자 수 계산
            active_user_count = self.db.query(func.count(User.user_id)).filter(
                User.org_id == org_id,
                User.is_active == True
            ).scalar()
            
            logger.info(f"📈 조직 {org_id} 활성 사용자 수: {active_user_count}명")
            
            # 오늘 날짜의 organization_usage 레코드 확인
            today = date.today()
            usage_record = self.db.query(OrganizationUsage).filter(
                OrganizationUsage.org_id == org_id,
                func.date(OrganizationUsage.usage_date) == today
            ).first()
            
            if usage_record:
                # 기존 레코드 업데이트
                old_count = usage_record.current_users
                usage_record.current_users = active_user_count
                usage_record.updated_at = datetime.now(timezone.utc)
                
                logger.info(f"✅ 조직 사용량 업데이트: {org_id} - {old_count}명 → {active_user_count}명")
            else:
                # 새 레코드 생성
                new_usage = OrganizationUsage(
                    org_id=org_id,
                    usage_date=datetime.now(timezone.utc),
                    current_users=active_user_count,
                    emails_sent_today=0,
                    total_emails_sent=0,
                    current_storage_gb=0,
                    emails_received_today=0,
                    total_emails_received=0,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                )
                
                self.db.add(new_usage)
                logger.info(f"➕ 조직 사용량 생성: {org_id} - {active_user_count}명")
            
            # 변경사항 저장 (별도 커밋하지 않고 현재 트랜잭션에 포함)
            self.db.flush()
            
        except Exception as e:
            logger.error(f"❌ 조직 사용량 업데이트 오류: {str(e)}")
            # 조직 사용량 업데이트 실패가 주요 기능을 방해하지 않도록 예외를 다시 발생시키지 않음

    async def update_microsoft_tokens(
        self, 
        user_id: str, 
        access_token: str, 
        refresh_token: str, 
        expires_at: datetime
    ) -> bool:
        """
        사용자의 Microsoft Graph API 토큰을 업데이트합니다.
        
        Args:
            user_id: 사용자 ID
            access_token: Microsoft 액세스 토큰
            refresh_token: Microsoft 리프레시 토큰
            expires_at: 토큰 만료 시간
        
        Returns:
            업데이트 성공 여부
        """
        try:
            logger.info(f"🔑 Microsoft 토큰 업데이트 시작 - 사용자ID: {user_id}")
            
            user = self.db.query(User).filter(User.user_id == user_id).first()
            if not user:
                logger.error(f"❌ 사용자를 찾을 수 없음 - 사용자ID: {user_id}")
                return False
            
            # Microsoft 토큰 정보 업데이트
            user.microsoft_access_token = access_token
            user.microsoft_refresh_token = refresh_token
            user.microsoft_token_expires_at = expires_at
            user.microsoft_connected_at = datetime.now(timezone.utc)
            user.updated_at = datetime.now(timezone.utc)
            
            self.db.commit()
            
            logger.info(f"✅ Microsoft 토큰 업데이트 완료 - 사용자: {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Microsoft 토큰 업데이트 실패 - 사용자ID: {user_id}, 오류: {str(e)}")
            self.db.rollback()
            return False

    async def get_microsoft_access_token(self, user_id: str) -> Optional[str]:
        """
        사용자의 Microsoft 액세스 토큰을 조회합니다.
        토큰이 만료된 경우 리프레시를 시도합니다.
        
        Args:
            user_id: 사용자 ID
        
        Returns:
            유효한 액세스 토큰 또는 None
        """
        try:
            logger.info(f"🔑 Microsoft 토큰 조회 시작 - 사용자ID: {user_id}")
            
            user = self.db.query(User).filter(User.user_id == user_id).first()
            if not user or not user.microsoft_access_token:
                logger.warning(f"⚠️ Microsoft 토큰 없음 - 사용자ID: {user_id}")
                return None
            
            # 토큰 만료 확인
            if user.microsoft_token_expires_at and user.microsoft_token_expires_at <= datetime.now(timezone.utc):
                logger.info(f"🔄 Microsoft 토큰 만료됨, 리프레시 시도 - 사용자: {user.email}")
                
                # 토큰 리프레시 시도
                refreshed_token = await self._refresh_microsoft_token(user)
                if refreshed_token:
                    return refreshed_token
                else:
                    logger.warning(f"⚠️ Microsoft 토큰 리프레시 실패 - 사용자: {user.email}")
                    return None
            
            logger.info(f"✅ Microsoft 토큰 조회 완료 - 사용자: {user.email}")
            return user.microsoft_access_token
            
        except Exception as e:
            logger.error(f"❌ Microsoft 토큰 조회 실패 - 사용자ID: {user_id}, 오류: {str(e)}")
            return None

    async def _refresh_microsoft_token(self, user: User) -> Optional[str]:
        """
        Microsoft 리프레시 토큰을 사용하여 새로운 액세스 토큰을 획득합니다.
        
        Args:
            user: 사용자 객체
        
        Returns:
            새로운 액세스 토큰 또는 None
        """
        try:
            if not user.microsoft_refresh_token:
                logger.warning(f"⚠️ Microsoft 리프레시 토큰 없음 - 사용자: {user.email}")
                return None
            
            import httpx
            from ..config import settings
            
            # 토큰 리프레시 요청
            token_data = {
                "client_id": settings.MICROSOFT_CLIENT_ID,
                "client_secret": settings.MICROSOFT_CLIENT_SECRET,
                "grant_type": "refresh_token",
                "refresh_token": user.microsoft_refresh_token
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://login.microsoftonline.com/common/oauth2/v2.0/token",
                    data=token_data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
            
            if response.status_code == 200:
                token_info = response.json()
                new_access_token = token_info.get("access_token")
                new_refresh_token = token_info.get("refresh_token", user.microsoft_refresh_token)
                expires_in = token_info.get("expires_in", 3600)
                
                # 새로운 토큰으로 업데이트
                user.microsoft_access_token = new_access_token
                user.microsoft_refresh_token = new_refresh_token
                user.microsoft_token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
                user.updated_at = datetime.now(timezone.utc)
                
                self.db.commit()
                
                logger.info(f"✅ Microsoft 토큰 리프레시 완료 - 사용자: {user.email}")
                return new_access_token
            else:
                logger.error(f"❌ Microsoft 토큰 리프레시 실패 - 사용자: {user.email}, 상태코드: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Microsoft 토큰 리프레시 오류 - 사용자: {user.email}, 오류: {str(e)}")
            return None

    async def clear_microsoft_tokens(self, user_id: str) -> bool:
        """
        사용자의 Microsoft 토큰을 삭제합니다.
        
        Args:
            user_id: 사용자 ID
        
        Returns:
            삭제 성공 여부
        """
        try:
            logger.info(f"🗑️ Microsoft 토큰 삭제 시작 - 사용자ID: {user_id}")
            
            user = self.db.query(User).filter(User.user_id == user_id).first()
            if not user:
                logger.error(f"❌ 사용자를 찾을 수 없음 - 사용자ID: {user_id}")
                return False
            
            # Microsoft 토큰 정보 삭제
            user.microsoft_access_token = None
            user.microsoft_refresh_token = None
            user.microsoft_token_expires_at = None
            user.microsoft_connected_at = None
            user.updated_at = datetime.now(timezone.utc)
            
            self.db.commit()
            
            logger.info(f"✅ Microsoft 토큰 삭제 완료 - 사용자: {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Microsoft 토큰 삭제 실패 - 사용자ID: {user_id}, 오류: {str(e)}")
            self.db.rollback()
            return False

    async def get_microsoft_connection_status(self, user_id: str) -> Dict[str, Any]:
        """
        사용자의 Microsoft 계정 연동 상태를 조회합니다.
        
        Args:
            user_id: 사용자 ID
        
        Returns:
            연동 상태 정보
        """
        try:
            user = self.db.query(User).filter(User.user_id == user_id).first()
            if not user:
                return {
                    "connected": False,
                    "error": "사용자를 찾을 수 없습니다"
                }
            
            is_connected = bool(user.microsoft_access_token)
            is_token_valid = False
            
            if is_connected and user.microsoft_token_expires_at:
                is_token_valid = user.microsoft_token_expires_at > datetime.now(timezone.utc)
            
            return {
                "connected": is_connected,
                "token_valid": is_token_valid,
                "connected_at": user.microsoft_connected_at.isoformat() if user.microsoft_connected_at else None,
                "expires_at": user.microsoft_token_expires_at.isoformat() if user.microsoft_token_expires_at else None
            }
            
        except Exception as e:
            logger.error(f"❌ Microsoft 연동 상태 조회 실패 - 사용자ID: {user_id}, 오류: {str(e)}")
            return {
                "connected": False,
                "error": "연동 상태 조회 중 오류가 발생했습니다"
            }