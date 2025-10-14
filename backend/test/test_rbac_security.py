"""
RBAC (Role-Based Access Control) 보안 기능 테스트

이 모듈은 RBAC 관련 모든 기능을 테스트합니다:
- 역할 정의 및 권한 관리
- 사용자 역할 할당
- 권한 검증
- 조직별 접근 제어
- 리소스별 권한 확인
"""

import pytest
from unittest.mock import Mock, patch
from typing import List, Dict, Any

from app.service.rbac_service import RBACService
from app.model.user_model import User, UserRole
from app.model.organization_model import Organization
from app.schemas.auth_schema import RoleRequest


class TestRBACService:
    """RBAC 서비스 테스트 클래스"""
    
    def setup_method(self):
        """테스트 메서드 실행 전 초기화"""
        self.rbac_service = RBACService()
        
        # 테스트용 조직 생성
        self.test_org = Organization(
            id=1,
            org_uuid="test-org-uuid",
            name="Test Organization",
            domain="test.com"
        )
        
        # 테스트용 사용자들 생성 (다양한 역할)
        self.super_admin_user = User(
            id=1,
            user_uuid="super-admin-uuid",
            email="superadmin@test.com",
            password_hash="hashed_password",
            organization_id=1,
            role=UserRole.SUPER_ADMIN,
            is_active=True
        )
        
        self.org_admin_user = User(
            id=2,
            user_uuid="org-admin-uuid",
            email="orgadmin@test.com",
            password_hash="hashed_password",
            organization_id=1,
            role=UserRole.ORG_ADMIN,
            is_active=True
        )
        
        self.mail_admin_user = User(
            id=3,
            user_uuid="mail-admin-uuid",
            email="mailadmin@test.com",
            password_hash="hashed_password",
            organization_id=1,
            role=UserRole.MAIL_ADMIN,
            is_active=True
        )
        
        self.user_manager_user = User(
            id=4,
            user_uuid="user-manager-uuid",
            email="usermanager@test.com",
            password_hash="hashed_password",
            organization_id=1,
            role=UserRole.USER_MANAGER,
            is_active=True
        )
        
        self.regular_user = User(
            id=5,
            user_uuid="regular-user-uuid",
            email="user@test.com",
            password_hash="hashed_password",
            organization_id=1,
            role=UserRole.USER,
            is_active=True
        )
        
        self.guest_user = User(
            id=6,
            user_uuid="guest-user-uuid",
            email="guest@test.com",
            password_hash="hashed_password",
            organization_id=1,
            role=UserRole.GUEST,
            is_active=True
        )

    def test_get_all_roles(self):
        """모든 역할 조회 테스트"""
        roles = self.rbac_service.get_all_roles()
        
        # 모든 역할이 반환되는지 확인
        expected_roles = ["super_admin", "org_admin", "mail_admin", "user_manager", "user", "guest"]
        assert len(roles) == len(expected_roles)
        
        for role in expected_roles:
            assert role in roles
            assert "name" in roles[role]
            assert "description" in roles[role]
            assert "level" in roles[role]
            assert "permissions" in roles[role]

    def test_get_role_info_valid(self):
        """유효한 역할 정보 조회 테스트"""
        role_info = self.rbac_service.get_role_info("super_admin")
        
        assert role_info is not None
        assert role_info["name"] == "super_admin"
        assert role_info["description"] == "시스템 최고 관리자"
        assert role_info["level"] == 100
        assert isinstance(role_info["permissions"], list)
        assert len(role_info["permissions"]) > 0

    def test_get_role_info_invalid(self):
        """잘못된 역할 정보 조회 테스트"""
        role_info = self.rbac_service.get_role_info("invalid_role")
        
        assert role_info is None

    def test_get_user_permissions_super_admin(self):
        """슈퍼 관리자 권한 조회 테스트"""
        permissions = self.rbac_service.get_user_permissions(self.super_admin_user)
        
        # 슈퍼 관리자는 모든 권한을 가져야 함
        expected_permissions = [
            "system:manage", "organization:create", "organization:delete",
            "organization:manage", "user:create", "user:delete", "user:manage",
            "mail:send", "mail:receive", "mail:delete", "mail:manage",
            "mail:setup", "mail:config", "settings:manage", "logs:view",
            "monitoring:view", "backup:manage"
        ]
        
        for permission in expected_permissions:
            assert permission in permissions

    def test_get_user_permissions_org_admin(self):
        """조직 관리자 권한 조회 테스트"""
        permissions = self.rbac_service.get_user_permissions(self.org_admin_user)
        
        # 조직 관리자 권한 확인
        expected_permissions = [
            "organization:manage", "user:create", "user:delete", "user:manage",
            "mail:send", "mail:receive", "mail:delete", "mail:manage",
            "mail:setup", "mail:config", "settings:manage", "logs:view"
        ]
        
        for permission in expected_permissions:
            assert permission in permissions
        
        # 시스템 레벨 권한은 없어야 함
        assert "system:manage" not in permissions
        assert "organization:create" not in permissions

    def test_get_user_permissions_regular_user(self):
        """일반 사용자 권한 조회 테스트"""
        permissions = self.rbac_service.get_user_permissions(self.regular_user)
        
        # 일반 사용자 권한 확인
        expected_permissions = ["mail:send", "mail:receive", "mail:delete"]
        
        for permission in expected_permissions:
            assert permission in permissions
        
        # 관리자 권한은 없어야 함
        assert "user:manage" not in permissions
        assert "organization:manage" not in permissions
        assert "system:manage" not in permissions

    def test_get_user_permissions_guest(self):
        """게스트 사용자 권한 조회 테스트"""
        permissions = self.rbac_service.get_user_permissions(self.guest_user)
        
        # 게스트는 읽기 권한만 가져야 함
        expected_permissions = ["mail:receive"]
        
        for permission in expected_permissions:
            assert permission in permissions
        
        # 쓰기 권한은 없어야 함
        assert "mail:send" not in permissions
        assert "mail:delete" not in permissions

    def test_check_permission_allowed(self):
        """권한 허용 테스트"""
        # 슈퍼 관리자는 모든 권한 허용
        assert self.rbac_service.check_permission(self.super_admin_user, "system:manage") is True
        assert self.rbac_service.check_permission(self.super_admin_user, "organization:create") is True
        
        # 조직 관리자는 조직 관리 권한 허용
        assert self.rbac_service.check_permission(self.org_admin_user, "organization:manage") is True
        assert self.rbac_service.check_permission(self.org_admin_user, "user:manage") is True
        
        # 일반 사용자는 메일 기본 권한 허용
        assert self.rbac_service.check_permission(self.regular_user, "mail:send") is True
        assert self.rbac_service.check_permission(self.regular_user, "mail:receive") is True

    def test_check_permission_denied(self):
        """권한 거부 테스트"""
        # 일반 사용자는 관리자 권한 거부
        assert self.rbac_service.check_permission(self.regular_user, "system:manage") is False
        assert self.rbac_service.check_permission(self.regular_user, "organization:manage") is False
        assert self.rbac_service.check_permission(self.regular_user, "user:manage") is False
        
        # 게스트는 쓰기 권한 거부
        assert self.rbac_service.check_permission(self.guest_user, "mail:send") is False
        assert self.rbac_service.check_permission(self.guest_user, "mail:delete") is False
        
        # 조직 관리자는 시스템 권한 거부
        assert self.rbac_service.check_permission(self.org_admin_user, "system:manage") is False

    def test_check_resource_permission_mail_own(self):
        """자신의 메일 리소스 권한 테스트"""
        mail_resource = {
            "type": "mail",
            "owner_id": self.regular_user.id,
            "organization_id": self.regular_user.organization_id
        }
        
        # 자신의 메일에 대한 권한
        assert self.rbac_service.check_resource_permission(
            self.regular_user, "mail:read", mail_resource
        ) is True
        assert self.rbac_service.check_resource_permission(
            self.regular_user, "mail:delete", mail_resource
        ) is True

    def test_check_resource_permission_mail_others(self):
        """다른 사용자의 메일 리소스 권한 테스트"""
        mail_resource = {
            "type": "mail",
            "owner_id": self.org_admin_user.id,  # 다른 사용자의 메일
            "organization_id": self.regular_user.organization_id
        }
        
        # 다른 사용자의 메일에 대한 권한 (일반 사용자는 거부)
        assert self.rbac_service.check_resource_permission(
            self.regular_user, "mail:read", mail_resource
        ) is False
        assert self.rbac_service.check_resource_permission(
            self.regular_user, "mail:delete", mail_resource
        ) is False
        
        # 메일 관리자는 허용
        assert self.rbac_service.check_resource_permission(
            self.mail_admin_user, "mail:read", mail_resource
        ) is True

    def test_check_resource_permission_organization_access(self):
        """조직 리소스 접근 권한 테스트"""
        org_resource = {
            "type": "organization",
            "organization_id": self.test_org.id
        }
        
        # 같은 조직 사용자는 허용
        assert self.rbac_service.check_resource_permission(
            self.regular_user, "organization:view", org_resource
        ) is True
        
        # 다른 조직 사용자 생성
        other_org_user = User(
            id=99,
            user_uuid="other-org-user",
            email="other@other.com",
            organization_id=999,  # 다른 조직
            role=UserRole.USER
        )
        
        # 다른 조직 사용자는 거부
        assert self.rbac_service.check_resource_permission(
            other_org_user, "organization:view", org_resource
        ) is False

    def test_check_organization_access_allowed(self):
        """조직 접근 허용 테스트"""
        # 같은 조직 사용자
        assert self.rbac_service.check_organization_access(
            self.regular_user, self.test_org.id
        ) is True
        
        # 슈퍼 관리자는 모든 조직 접근 가능
        assert self.rbac_service.check_organization_access(
            self.super_admin_user, 999  # 다른 조직
        ) is True

    def test_check_organization_access_denied(self):
        """조직 접근 거부 테스트"""
        # 다른 조직 사용자
        other_org_user = User(
            id=99,
            user_uuid="other-org-user",
            email="other@other.com",
            organization_id=999,
            role=UserRole.USER
        )
        
        assert self.rbac_service.check_organization_access(
            other_org_user, self.test_org.id
        ) is False

    @patch('app.service.rbac_service.RBACService._get_user_by_id')
    @patch('app.service.rbac_service.RBACService._update_user_role')
    def test_update_user_role_success(self, mock_update_role, mock_get_user):
        """사용자 역할 업데이트 성공 테스트"""
        mock_get_user.return_value = self.regular_user
        mock_update_role.return_value = True
        
        result = self.rbac_service.update_user_role(
            user_id=self.regular_user.id,
            new_role="mail_admin",
            admin_user=self.org_admin_user,
            organization_id=self.test_org.id
        )
        
        assert result["success"] is True
        assert "역할이 성공적으로 업데이트되었습니다" in result["message"]
        
        # 메서드 호출 검증
        mock_get_user.assert_called_once_with(self.regular_user.id, self.test_org.id)
        mock_update_role.assert_called_once()

    @patch('app.service.rbac_service.RBACService._get_user_by_id')
    def test_update_user_role_user_not_found(self, mock_get_user):
        """사용자 역할 업데이트 시 사용자 없음 테스트"""
        mock_get_user.return_value = None
        
        with pytest.raises(ValueError, match="사용자를 찾을 수 없습니다"):
            self.rbac_service.update_user_role(
                user_id=999,
                new_role="mail_admin",
                admin_user=self.org_admin_user,
                organization_id=self.test_org.id
            )

    @patch('app.service.rbac_service.RBACService._get_user_by_id')
    def test_update_user_role_invalid_role(self, mock_get_user):
        """잘못된 역할로 업데이트 테스트"""
        mock_get_user.return_value = self.regular_user
        
        with pytest.raises(ValueError, match="유효하지 않은 역할입니다"):
            self.rbac_service.update_user_role(
                user_id=self.regular_user.id,
                new_role="invalid_role",
                admin_user=self.org_admin_user,
                organization_id=self.test_org.id
            )

    @patch('app.service.rbac_service.RBACService._get_user_by_id')
    def test_update_user_role_insufficient_permission(self, mock_get_user):
        """권한 부족으로 역할 업데이트 실패 테스트"""
        mock_get_user.return_value = self.regular_user
        
        # 일반 사용자가 다른 사용자의 역할을 변경하려고 시도
        with pytest.raises(ValueError, match="역할을 변경할 권한이 없습니다"):
            self.rbac_service.update_user_role(
                user_id=self.org_admin_user.id,
                new_role="user",
                admin_user=self.regular_user,  # 권한 없는 사용자
                organization_id=self.test_org.id
            )

    @patch('app.service.rbac_service.RBACService._get_users_by_organization')
    def test_get_organization_users_success(self, mock_get_users):
        """조직 사용자 목록 조회 성공 테스트"""
        mock_users = [self.org_admin_user, self.regular_user, self.guest_user]
        mock_get_users.return_value = mock_users
        
        result = self.rbac_service.get_organization_users(
            organization_id=self.test_org.id,
            admin_user=self.org_admin_user
        )
        
        assert len(result) == 3
        for user_info in result:
            assert "id" in user_info
            assert "email" in user_info
            assert "role" in user_info
            assert "is_active" in user_info

    @patch('app.service.rbac_service.RBACService._get_users_by_organization')
    def test_get_organization_users_with_role_filter(self, mock_get_users):
        """역할 필터링으로 조직 사용자 조회 테스트"""
        mock_users = [self.org_admin_user, self.regular_user, self.guest_user]
        mock_get_users.return_value = mock_users
        
        result = self.rbac_service.get_organization_users(
            organization_id=self.test_org.id,
            admin_user=self.org_admin_user,
            role_filter="user"
        )
        
        # 필터링된 결과 확인
        assert len(result) == 1
        assert result[0]["role"] == "user"

    def test_get_organization_users_insufficient_permission(self):
        """권한 부족으로 조직 사용자 조회 실패 테스트"""
        with pytest.raises(ValueError, match="조직 사용자를 조회할 권한이 없습니다"):
            self.rbac_service.get_organization_users(
                organization_id=self.test_org.id,
                admin_user=self.regular_user  # 권한 없는 사용자
            )

    @patch('app.service.rbac_service.RBACService._get_users_by_organization')
    def test_get_role_statistics(self, mock_get_users):
        """역할별 통계 조회 테스트"""
        mock_users = [
            self.super_admin_user, self.org_admin_user, self.mail_admin_user,
            self.user_manager_user, self.regular_user, self.guest_user
        ]
        mock_get_users.return_value = mock_users
        
        result = self.rbac_service.get_role_statistics(
            organization_id=self.test_org.id,
            admin_user=self.org_admin_user
        )
        
        # 통계 결과 확인
        assert "total_users" in result
        assert "role_counts" in result
        assert result["total_users"] == 6
        
        role_counts = result["role_counts"]
        assert role_counts["super_admin"] == 1
        assert role_counts["org_admin"] == 1
        assert role_counts["mail_admin"] == 1
        assert role_counts["user_manager"] == 1
        assert role_counts["user"] == 1
        assert role_counts["guest"] == 1

    def test_can_manage_role_super_admin(self):
        """슈퍼 관리자 역할 관리 권한 테스트"""
        # 슈퍼 관리자는 모든 역할 관리 가능
        assert self.rbac_service._can_manage_role(self.super_admin_user, "org_admin") is True
        assert self.rbac_service._can_manage_role(self.super_admin_user, "user") is True
        assert self.rbac_service._can_manage_role(self.super_admin_user, "guest") is True

    def test_can_manage_role_org_admin(self):
        """조직 관리자 역할 관리 권한 테스트"""
        # 조직 관리자는 자신보다 낮은 역할만 관리 가능
        assert self.rbac_service._can_manage_role(self.org_admin_user, "mail_admin") is True
        assert self.rbac_service._can_manage_role(self.org_admin_user, "user") is True
        assert self.rbac_service._can_manage_role(self.org_admin_user, "guest") is True
        
        # 같거나 높은 역할은 관리 불가
        assert self.rbac_service._can_manage_role(self.org_admin_user, "super_admin") is False
        assert self.rbac_service._can_manage_role(self.org_admin_user, "org_admin") is False

    def test_can_manage_role_regular_user(self):
        """일반 사용자 역할 관리 권한 테스트"""
        # 일반 사용자는 역할 관리 불가
        assert self.rbac_service._can_manage_role(self.regular_user, "guest") is False
        assert self.rbac_service._can_manage_role(self.regular_user, "user") is False

    def test_get_role_level(self):
        """역할 레벨 조회 테스트"""
        assert self.rbac_service._get_role_level("super_admin") == 100
        assert self.rbac_service._get_role_level("org_admin") == 80
        assert self.rbac_service._get_role_level("mail_admin") == 60
        assert self.rbac_service._get_role_level("user_manager") == 50
        assert self.rbac_service._get_role_level("user") == 20
        assert self.rbac_service._get_role_level("guest") == 10
        assert self.rbac_service._get_role_level("invalid_role") == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])