"""
RBAC (Role-Based Access Control) 서비스

다중 조직 지원을 위한 역할 기반 접근 제어 기능을 제공합니다.
조직별 역할 관리, 권한 검증, 리소스 접근 제어 등의 기능을 포함합니다.
"""
import logging
import json
from datetime import datetime
from typing import Optional, Dict, Any, List, Set
from sqlalchemy.orm import Session
from fastapi import HTTPException, status, Depends

from ..model import User, Organization
from ..config import settings

# 로거 설정
logger = logging.getLogger(__name__)


class RBACService:
    """
    RBAC 서비스 클래스
    다중 조직 지원을 위한 역할 기반 접근 제어 기능을 제공합니다.
    """
    
    # 기본 역할 정의
    DEFAULT_ROLES = {
        "super_admin": {
            "name": "슈퍼 관리자",
            "description": "시스템 전체 관리 권한",
            "permissions": [
                "system:*",
                "organization:*",
                "user:*",
                "mail:*",
                "settings:*"
            ],
            "level": 100
        },
        "system_admin": {
            "name": "시스템 관리자",
            "description": "시스템 전체 관리 권한",
            "permissions": [
                "system:*",
                "organization:*",
                "user:*",
                "mail:*",
                "settings:*"
            ],
            "level": 100
        },        
        "org_admin": {
            "name": "조직 관리자",
            "description": "조직 내 모든 관리 권한",
            "permissions": [
                "organization:read",
                "organization:update",
                "user:*",
                "mail:*",
                "settings:read",
                "settings:update"
            ],
            "level": 80
        },
        "mail_admin": {
            "name": "메일 관리자",
            "description": "메일 시스템 관리 권한",
            "permissions": [
                "user:read",
                "mail:*",
                "settings:read"
            ],
            "level": 60
        },
        "user_manager": {
            "name": "사용자 관리자",
            "description": "사용자 관리 권한",
            "permissions": [
                "user:read",
                "user:create",
                "user:update",
                "mail:read",
                "mail:send"
            ],
            "level": 40
        },
        "user": {
            "name": "일반 사용자",
            "description": "기본 사용자 권한",
            "permissions": [
                "mail:read",
                "mail:send",
                "mail:delete_own",
                "user:read_own",
                "user:update_own"
            ],
            "level": 20
        },
        "guest": {
            "name": "게스트",
            "description": "제한된 읽기 권한",
            "permissions": [
                "mail:read_own"
            ],
            "level": 10
        }
    }
    
    # 리소스별 권한 정의
    RESOURCE_PERMISSIONS = {
        "system": ["read", "create", "update", "delete", "manage"],
        "organization": ["read", "create", "update", "delete", "manage"],
        "user": ["read", "create", "update", "delete", "read_own", "update_own"],
        "mail": ["read", "send", "delete", "delete_own", "read_own", "manage"],
        "settings": ["read", "update", "manage"]
    }
    
    def __init__(self, db: Session):
        """
        RBACService 초기화
        
        Args:
            db: 데이터베이스 세션
        """
        self.db = db
    
    def get_role_info(self, role: str) -> Dict[str, Any]:
        """
        역할 정보를 조회합니다.
        
        Args:
            role: 역할명
            
        Returns:
            역할 정보 딕셔너리
        """
        try:
            if role not in self.DEFAULT_ROLES:
                logger.warning(f"❌ 존재하지 않는 역할: {role}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"존재하지 않는 역할입니다: {role}"
                )
            
            role_info = self.DEFAULT_ROLES[role].copy()
            logger.info(f"✅ 역할 정보 조회 성공 - 역할: {role}")
            return role_info
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ 역할 정보 조회 실패: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="역할 정보 조회에 실패했습니다."
            )
    
    def get_all_roles(self) -> Dict[str, Dict[str, Any]]:
        """
        모든 역할 정보를 조회합니다.
        
        Returns:
            모든 역할 정보 딕셔너리
        """
        try:
            logger.info("📋 모든 역할 정보 조회")
            return self.DEFAULT_ROLES.copy()
            
        except Exception as e:
            logger.error(f"❌ 모든 역할 정보 조회 실패: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="역할 정보 조회에 실패했습니다."
            )
    
    def get_user_permissions(self, user: User) -> Set[str]:
        """
        사용자의 권한 목록을 조회합니다.
        
        Args:
            user: 사용자 객체
            
        Returns:
            권한 집합
        """
        try:
            permissions = set()
            
            # 기본 역할 권한
            if user.role in self.DEFAULT_ROLES:
                role_permissions = self.DEFAULT_ROLES[user.role]["permissions"]
                permissions.update(role_permissions)
            
            # 추가 권한 (JSON 형태로 저장된 경우)
            if user.permissions:
                try:
                    additional_permissions = json.loads(user.permissions) if isinstance(user.permissions, str) else user.permissions
                    if isinstance(additional_permissions, list):
                        permissions.update(additional_permissions)
                except (json.JSONDecodeError, TypeError):
                    logger.warning(f"⚠️ 사용자 추가 권한 파싱 실패 - 사용자: {user.user_uuid}")
            
            logger.info(f"✅ 사용자 권한 조회 성공 - 사용자: {user.user_uuid}, 권한 수: {len(permissions)}")
            return permissions
            
        except Exception as e:
            logger.error(f"❌ 사용자 권한 조회 실패: {str(e)}")
            return set()
    
    def has_permission(self, user: User, permission: str) -> bool:
        """
        사용자가 특정 권한을 가지고 있는지 확인합니다.
        
        Args:
            user: 사용자 객체
            permission: 확인할 권한 (예: "mail:send", "user:read")
            
        Returns:
            권한 보유 여부
        """
        try:
            user_permissions = self.get_user_permissions(user)
            
            # 직접 권한 확인
            if permission in user_permissions:
                return True
            
            # 와일드카드 권한 확인 (예: "mail:*")
            resource, action = permission.split(":", 1) if ":" in permission else (permission, "")
            wildcard_permission = f"{resource}:*"
            if wildcard_permission in user_permissions:
                return True
            
            # 전체 권한 확인 (예: "system:*")
            if "system:*" in user_permissions:
                return True
            
            logger.debug(f"🔍 권한 확인 - 사용자: {user.user_uuid}, 권한: {permission}, 결과: False")
            return False
            
        except Exception as e:
            logger.error(f"❌ 권한 확인 실패: {str(e)}")
            return False
    
    def check_permission(self, user: User, permission: str) -> None:
        """
        사용자 권한을 확인하고, 권한이 없으면 예외를 발생시킵니다.
        
        Args:
            user: 사용자 객체
            permission: 확인할 권한
            
        Raises:
            HTTPException: 권한이 없는 경우
        """
        try:
            if not self.has_permission(user, permission):
                logger.warning(f"❌ 권한 부족 - 사용자: {user.user_uuid}, 권한: {permission}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"해당 작업을 수행할 권한이 없습니다: {permission}"
                )
            
            logger.debug(f"✅ 권한 확인 성공 - 사용자: {user.user_uuid}, 권한: {permission}")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ 권한 확인 실패: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="권한 확인에 실패했습니다."
            )
    
    def can_access_organization(self, user: User, target_org_id: str) -> bool:
        """
        사용자가 특정 조직에 접근할 수 있는지 확인합니다.
        
        Args:
            user: 사용자 객체
            target_org_id: 대상 조직 ID
            
        Returns:
            접근 가능 여부
        """
        try:
            # 슈퍼 관리자는 모든 조직 접근 가능
            if user.role == "super_admin":
                return True
            
            # 같은 조직 사용자는 접근 가능
            if user.org_id == target_org_id:
                return True
            
            # 조직 간 접근 권한 확인 (추가 권한이 있는 경우)
            if self.has_permission(user, "organization:*"):
                return True
            
            logger.debug(f"🔍 조직 접근 확인 - 사용자: {user.user_uuid}, 대상 조직: {target_org_id}, 결과: False")
            return False
            
        except Exception as e:
            logger.error(f"❌ 조직 접근 확인 실패: {str(e)}")
            return False
    
    def check_organization_access(self, user: User, target_org_id: str) -> None:
        """
        조직 접근 권한을 확인하고, 권한이 없으면 예외를 발생시킵니다.
        
        Args:
            user: 사용자 객체
            target_org_id: 대상 조직 ID
            
        Raises:
            HTTPException: 접근 권한이 없는 경우
        """
        try:
            if not self.can_access_organization(user, target_org_id):
                logger.warning(f"❌ 조직 접근 권한 부족 - 사용자: {user.user_uuid}, 대상 조직: {target_org_id}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="해당 조직에 접근할 권한이 없습니다."
                )
            
            logger.debug(f"✅ 조직 접근 권한 확인 성공 - 사용자: {user.user_uuid}, 대상 조직: {target_org_id}")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ 조직 접근 권한 확인 실패: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="조직 접근 권한 확인에 실패했습니다."
            )
    
    def can_manage_user(self, manager: User, target_user: User) -> bool:
        """
        관리자가 대상 사용자를 관리할 수 있는지 확인합니다.
        
        Args:
            manager: 관리자 사용자
            target_user: 대상 사용자
            
        Returns:
            관리 가능 여부
        """
        try:
            # 슈퍼 관리자와 시스템 관리자는 모든 사용자 관리 가능
            if manager.role in ["super_admin", "system_admin"]:
                return True
            
            # 같은 조직 내에서만 관리 가능
            if manager.org_id != target_user.org_id:
                return False
            
            # 역할 레벨 확인
            manager_level = self.DEFAULT_ROLES.get(manager.role, {}).get("level", 0)
            target_level = self.DEFAULT_ROLES.get(target_user.role, {}).get("level", 0)
            
            # 자신보다 높은 레벨의 사용자는 관리할 수 없음
            if manager_level <= target_level:
                return False
            
            # 사용자 관리 권한 확인
            if not self.has_permission(manager, "user:update"):
                return False
            
            logger.debug(f"🔍 사용자 관리 권한 확인 - 관리자: {manager.user_uuid}, 대상: {target_user.user_uuid}, 결과: True")
            return True
            
        except Exception as e:
            logger.error(f"❌ 사용자 관리 권한 확인 실패: {str(e)}")
            return False
    
    def update_user_role(self, admin_user: User, target_user: User, new_role: str) -> User:
        """
        사용자의 역할을 업데이트합니다.
        
        Args:
            admin_user: 관리자 사용자
            target_user: 대상 사용자
            new_role: 새로운 역할
            
        Returns:
            업데이트된 사용자 객체
        """
        try:
            # 새 역할 유효성 확인
            if new_role not in self.DEFAULT_ROLES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"존재하지 않는 역할입니다: {new_role}"
                )
            
            # 관리 권한 확인
            if not self.can_manage_user(admin_user, target_user):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="해당 사용자의 역할을 변경할 권한이 없습니다."
                )
            
            # 새 역할 레벨 확인 (자신보다 높은 레벨로 승격 불가)
            admin_level = self.DEFAULT_ROLES.get(admin_user.role, {}).get("level", 0)
            new_role_level = self.DEFAULT_ROLES.get(new_role, {}).get("level", 0)
            
            if admin_user.role not in ["super_admin", "system_admin"] and new_role_level >= admin_level:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="자신보다 높은 권한의 역할로 변경할 수 없습니다."
                )
            
            # 역할 업데이트
            old_role = target_user.role
            target_user.role = new_role
            target_user.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(target_user)
            
            logger.info(f"✅ 사용자 역할 업데이트 성공 - 사용자: {target_user.user_uuid}, {old_role} → {new_role}")
            return target_user
            
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ 사용자 역할 업데이트 실패: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="사용자 역할 업데이트에 실패했습니다."
            )
    
    def get_organization_users_by_role(self, org_id: str, role: Optional[str] = None) -> List[User]:
        """
        조직 내 사용자를 역할별로 조회합니다.
        
        Args:
            org_id: 조직 ID
            role: 역할 (선택사항, None이면 모든 역할)
            
        Returns:
            사용자 목록
        """
        try:
            query = self.db.query(User).filter(User.org_id == org_id)
            
            if role:
                if role not in self.DEFAULT_ROLES:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"존재하지 않는 역할입니다: {role}"
                    )
                query = query.filter(User.role == role)
            
            users = query.all()
            
            logger.info(f"✅ 조직 사용자 조회 성공 - 조직: {org_id}, 역할: {role}, 사용자 수: {len(users)}")
            return users
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ 조직 사용자 조회 실패: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="조직 사용자 조회에 실패했습니다."
            )
    
    def get_role_statistics(self, org_id: str) -> Dict[str, int]:
        """
        조직 내 역할별 사용자 통계를 조회합니다.
        
        Args:
            org_id: 조직 ID
            
        Returns:
            역할별 사용자 수 딕셔너리
        """
        try:
            users = self.db.query(User).filter(User.org_id == org_id).all()
            
            role_stats = {}
            for role in self.DEFAULT_ROLES.keys():
                role_stats[role] = 0
            
            for user in users:
                if user.role in role_stats:
                    role_stats[user.role] += 1
                else:
                    role_stats["unknown"] = role_stats.get("unknown", 0) + 1
            
            logger.info(f"✅ 역할 통계 조회 성공 - 조직: {org_id}")
            return role_stats
            
        except Exception as e:
            logger.error(f"❌ 역할 통계 조회 실패: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="역할 통계 조회에 실패했습니다."
            )