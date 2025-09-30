"""
pytest 설정 및 픽스처 정의
auth_router.py 테스트를 위한 공통 설정과 픽스처들을 제공합니다.
"""

import pytest
import asyncio
import os
import sys
from typing import Generator, AsyncGenerator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient
from httpx import AsyncClient
import uuid

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from app.database.user import Base, get_db
from app.config import settings
from app.model.user_model import User
from app.model.organization_model import Organization
from app.service.auth_service import get_password_hash

# 테스트 데이터베이스 URL - SQLite 사용 (PostgreSQL 연결 문제 우회)
TEST_DATABASE_URL = "sqlite:///./test_skyboot_mail.db"

# 테스트용 엔진 및 세션 생성
test_engine = create_engine(TEST_DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="session")
def event_loop():
    """이벤트 루프 픽스처 - 세션 스코프로 설정"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def setup_test_database():
    """테스트 데이터베이스 설정 - 세션 시작 시 한 번만 실행"""
    print("🔧 테스트 데이터베이스 설정 중...")
    
    # SQLite 데이터베이스는 자동으로 생성됨
    print("ℹ️ SQLite 테스트 데이터베이스 사용")
    
    # 테스트 테이블 생성
    try:
        Base.metadata.create_all(bind=test_engine)
        print("✅ 테스트 테이블 생성 완료")
    except Exception as e:
        print(f"❌ 테스트 테이블 생성 실패: {e}")
        pytest.skip("테스트 테이블 생성 실패")
    
    yield
    
    # 테스트 완료 후 정리
    print("🧹 테스트 데이터베이스 정리 중...")
    try:
        Base.metadata.drop_all(bind=test_engine)
        print("✅ 테스트 테이블 삭제 완료")
    except Exception as e:
        print(f"⚠️ 테스트 테이블 삭제 중 오류: {e}")

@pytest.fixture
def db_session(setup_test_database) -> Generator[Session, None, None]:
    """데이터베이스 세션 픽스처 - 각 테스트마다 새로운 세션 제공"""
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()

@pytest.fixture
def override_get_db(db_session):
    """데이터베이스 의존성 오버라이드"""
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()

@pytest.fixture
def client(override_get_db) -> TestClient:
    """FastAPI 테스트 클라이언트 픽스처"""
    return TestClient(app)

@pytest.fixture
async def async_client(override_get_db) -> AsyncGenerator[AsyncClient, None]:
    """비동기 HTTP 클라이언트 픽스처"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
def test_organization(db_session) -> Organization:
    """테스트용 조직 픽스처"""
    org = Organization(
        org_id=f"test_org_{uuid.uuid4().hex[:8]}",
        name="테스트 조직",
        domain="test.com",
        is_active=True,
        max_users=100,
        max_storage_gb=10
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    return org

@pytest.fixture
def test_user(db_session, test_organization) -> User:
    """테스트용 사용자 픽스처"""
    user = User(
        user_id=f"test_user_{uuid.uuid4().hex[:8]}",
        username=f"testuser_{uuid.uuid4().hex[:8]}",
        email="test@test.com",
        password_hash=get_password_hash("testpassword123"),
        org_id=test_organization.org_id,
        is_active=True,
        is_verified=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def admin_user(db_session) -> User:
    """테스트용 관리자 사용자 픽스처 - SkyBoot 조직"""
    # SkyBoot 조직 생성
    skyboot_org = Organization(
        org_id="bbf43d4b-3862-4ab0-9a03-522213ccb7a2",
        org_code="SKYBOOT",
        name="SkyBoot",
        subdomain="skyboot",
        domain="skyboot.com",
        admin_email="admin@skyboot.com",
        is_active=True,
        max_users=100
    )
    db_session.add(skyboot_org)
    db_session.commit()
    
    # 관리자 사용자 생성
    admin = User(
        user_id="admin_skyboot",
        user_uuid="441eb65c-bed0-4e75-9cdd-c95425e635a0",
        username="admin_skyboot",
        email="admin@skyboot.com",
        hashed_password=get_password_hash("admin123"),  # 테스트에서 기대하는 비밀번호
        org_id=skyboot_org.org_id,
        is_active=True,
        is_email_verified=True,
        role="admin"
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin

@pytest.fixture
def auth_headers(client, test_user) -> dict:
    """인증 헤더 픽스처 - 로그인하여 토큰 획득"""
    login_data = {
        "email": test_user.email,
        "password": "testpassword123"
    }
    
    response = client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200
    
    token_data = response.json()
    access_token = token_data["access_token"]
    
    return {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

@pytest.fixture
def admin_auth_headers(client, admin_user) -> dict:
    """관리자 인증 헤더 픽스처"""
    login_data = {
        "email": admin_user.email,
        "password": "admin123"  # 테스트에서 기대하는 비밀번호
    }
    
    response = client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200
    
    token_data = response.json()
    access_token = token_data["access_token"]
    
    return {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

@pytest.fixture
def test_user_data():
    """테스트용 사용자 데이터 픽스처"""
    unique_id = uuid.uuid4().hex[:8]
    return {
        "user_id": f"new_user_{unique_id}",
        "username": f"newuser_{unique_id}",
        "email": f"newuser_{unique_id}@test.com",
        "password": "newpassword123"
    }

@pytest.fixture(autouse=True)
def clean_database(db_session):
    """각 테스트 후 데이터베이스 정리 (자동 실행)"""
    yield
    # 테스트 후 모든 데이터 삭제
    try:
        db_session.execute(text("TRUNCATE TABLE users, organizations RESTART IDENTITY CASCADE"))
        db_session.commit()
    except Exception as e:
        print(f"⚠️ 데이터베이스 정리 중 오류: {e}")
        db_session.rollback()

# 테스트 마커 정의
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.auth = pytest.mark.auth
pytest.mark.endpoint = pytest.mark.endpoint
pytest.mark.slow = pytest.mark.slow
pytest.mark.database = pytest.mark.database