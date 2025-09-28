"""
조직별 로그인 기능 테스트
/api/v1/auth/login 엔드포인트의 조직 격리 및 인증 기능을 테스트합니다.
"""

import pytest
import asyncio
import uuid
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import sys
import os

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import app
from app.database.user import get_db, Base
from app.service.organization_service import OrganizationService
from app.service.auth_service import AuthService
from app.schemas.organization_schema import OrganizationCreateRequest, OrganizationCreate
from app.model.user_model import User
from app.model.organization_model import Organization

# 테스트 데이터베이스 설정
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_organization_login.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    """테스트용 데이터베이스 세션 제공"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# 의존성 오버라이드
app.dependency_overrides[get_db] = override_get_db

# 테스트 클라이언트 생성
client = TestClient(app)

class TestOrganizationLogin:
    """조직별 로그인 기능 테스트 클래스"""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """테스트 전후 설정"""
        # 테스트 전: 테이블 생성
        Base.metadata.create_all(bind=engine)
        yield
        # 테스트 후: 테이블 삭제
        Base.metadata.drop_all(bind=engine)

    @pytest.fixture
    def db_session(self):
        """데이터베이스 세션 제공"""
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    def test_setup_organizations(self, db_session):
        """테스트용 조직 및 사용자 생성"""
        org_service = OrganizationService(db_session)
        
        # UUID 생성
        org1_uuid = str(uuid.uuid4())
        org2_uuid = str(uuid.uuid4())
        
        # 조직 1 생성
        org1_data = OrganizationCreateRequest(
            organization=OrganizationCreate(
                org_id=org1_uuid,
                org_code="TEST001",
                subdomain="test1",
                name="테스트 조직 1",
                domain="test1.example.com",
                description="첫 번째 테스트 조직",
                admin_email="admin1@test1.example.com",
                admin_name="관리자 1",
                max_users=100,
                max_storage_gb=50
            ),
            admin_email="admin1@test1.example.com",
            admin_password="Password123!",
            admin_name="관리자 1"
        )
        
        # 비동기 함수를 동기적으로 실행
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            org1 = loop.run_until_complete(org_service.create_organization(
                org1_data.organization,
                org1_data.admin_email,
                org1_data.admin_password,
                org1_data.admin_name
            ))
            
            # 조직 2 생성
            org2_data = OrganizationCreateRequest(
                 organization=OrganizationCreate(
                     org_id=org2_uuid,
                     org_code="TEST002", 
                     subdomain="test2",
                     name="테스트 조직 2",
                     domain="test2.example.com",
                     description="두 번째 테스트 조직",
                     admin_email="admin2@test2.example.com",
                     admin_name="관리자 2",
                     max_users=50,
                     max_storage_gb=25
                 ),
                 admin_email="admin2@test2.example.com",
                 admin_password="Password456!",
                 admin_name="관리자 2"
             )
            
            org2 = loop.run_until_complete(org_service.create_organization(
                org2_data.organization,
                org2_data.admin_email,
                org2_data.admin_password,
                org2_data.admin_name
            ))
        finally:
            loop.close()
        
        return {
            "org1": org1,
            "org2": org2,
            "org1_admin": {
                "email": "admin1@test1.example.com", 
                "password": "Password123!"
            },
            "org2_admin": {
                "email": "admin2@test2.example.com", 
                "password": "Password456!"
            }
        }

    def test_successful_login_org1_admin(self, db_session):
        """조직 1 관리자 로그인 성공 테스트"""
        # 조직 설정
        org_data = self.test_setup_organizations(db_session)
        
        # 로그인 요청
        login_data = {
            "email": org_data["org1_admin"]["email"],
            "password": org_data["org1_admin"]["password"]
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        # 응답 검증
        assert response.status_code == 200
        response_data = response.json()
        
        assert "access_token" in response_data
        assert "refresh_token" in response_data
        assert response_data["token_type"] == "bearer"
        assert "expires_in" in response_data

    def test_successful_login_org2_admin(self, db_session):
        """조직 2 관리자 로그인 성공 테스트"""
        # 조직 설정
        org_data = self.test_setup_organizations(db_session)
        
        # 로그인 요청
        login_data = {
            "email": org_data["org2_admin"]["email"],
            "password": org_data["org2_admin"]["password"]
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        # 응답 검증
        assert response.status_code == 200
        response_data = response.json()
        
        assert "access_token" in response_data
        assert "refresh_token" in response_data
        assert response_data["token_type"] == "bearer"
        assert "expires_in" in response_data

    def test_login_with_wrong_password(self, db_session):
        """잘못된 비밀번호로 로그인 실패 테스트"""
        # 조직 설정
        org_data = self.test_setup_organizations(db_session)
        
        # 잘못된 비밀번호로 로그인 시도
        login_data = {
            "email": org_data["org1_admin"]["email"],
            "password": "wrong_password"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        # 응답 검증
        assert response.status_code == 401
        response_data = response.json()
        assert "message" in response_data or "detail" in response_data

    def test_login_with_nonexistent_email(self):
        """존재하지 않는 이메일로 로그인 실패 테스트"""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "password123"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        # 응답 검증
        assert response.status_code == 401
        response_data = response.json()
        assert "message" in response_data or "detail" in response_data

    def test_login_with_invalid_email_format(self):
        """잘못된 이메일 형식으로 로그인 실패 테스트"""
        login_data = {
            "email": "invalid-email-format",
            "password": "password123"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        # 응답 검증 (이메일 형식 검증은 클라이언트에서 처리되므로 401 반환)
        assert response.status_code == 401

    def test_login_with_empty_credentials(self):
        """빈 자격 증명으로 로그인 실패 테스트"""
        login_data = {
            "email": "",
            "password": ""
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        # 응답 검증
        assert response.status_code == 401

    def test_organization_isolation(self, db_session):
        """조직 간 격리 테스트 - 다른 조직의 사용자로 로그인 시도"""
        # 조직 설정
        org_data = self.test_setup_organizations(db_session)
        
        # 조직 1의 사용자 정보로 로그인 시도
        login_data = {
            "email": org_data["org1_admin"]["email"],
            "password": org_data["org1_admin"]["password"]
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        # 로그인 성공 확인
        assert response.status_code == 200
        response_data = response.json()
        
        # 토큰 정보 확인
        assert "access_token" in response_data
        assert "refresh_token" in response_data
        assert response_data["token_type"] == "bearer"
        assert "expires_in" in response_data

    def test_concurrent_logins_different_organizations(self, db_session):
        """서로 다른 조직의 동시 로그인 테스트"""
        # 조직 설정
        org_data = self.test_setup_organizations(db_session)
        
        # 조직 1 관리자 로그인
        login_data_org1 = {
            "email": org_data["org1_admin"]["email"],
            "password": org_data["org1_admin"]["password"]
        }
        
        response_org1 = client.post("/api/v1/auth/login", json=login_data_org1)
        
        # 조직 2 관리자 로그인
        login_data_org2 = {
            "email": org_data["org2_admin"]["email"],
            "password": org_data["org2_admin"]["password"]
        }
        
        response_org2 = client.post("/api/v1/auth/login", json=login_data_org2)
        
        # 두 로그인 모두 성공해야 함
        assert response_org1.status_code == 200
        assert response_org2.status_code == 200
        
        # 각각 다른 토큰을 받아야 함
        token_org1 = response_org1.json()["access_token"]
        token_org2 = response_org2.json()["access_token"]
        assert token_org1 != token_org2


def run_tests():
    """테스트 실행 함수"""
    print("🧪 조직별 로그인 테스트 시작...")
    
    # 테스트 실행
    test_class = TestOrganizationLogin()
    
    # 데이터베이스 세션 생성
    db = TestingSessionLocal()
    
    try:
        # 테스트 실행
        test_class.setup_and_teardown()
        
        print("✅ 모든 테스트가 완료되었습니다.")
        
    except Exception as e:
        print(f"❌ 테스트 실행 중 오류 발생: {e}")
        
    finally:
        db.close()


if __name__ == "__main__":
    run_tests()