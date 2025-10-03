"""
사용자 관리 서비스

SaaS 다중 조직 지원을 위한 사용자 관리 기능
"""
import logging
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from fastapi import HTTPException

from ..model.user_model import User
from ..model.mail_model import MailUser
from ..model.organization_model import Organization
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
            
            # 3. 이메일 중복 확인 (조직 내)
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
            
            # 4. 사용자명 중복 확인 (조직 내)
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
            
            # 5. 사용자 생성
            user_uuid = str(uuid.uuid4())
            password_hash = AuthService.get_password_hash(user_data.password)
            
            new_user = User(
                user_id=user_data.user_id,  # UUID로 ID 생성
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
            
            # 6. 메일 사용자 생성
            await self._create_mail_user(
                user_id=new_user.user_id,
                org_id=org_id,
                email=user_data.email,
                password_hash=password_hash
            )
            
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
            
            # 업데이트 가능한 필드들
            allowed_fields = ['username', 'full_name', 'is_active']
            
            for field, value in update_data.items():
                if field in allowed_fields and hasattr(user, field):
                    setattr(user, field, value)
            
            user.updated_at = datetime.now(timezone.utc)
            
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
        return mail_user