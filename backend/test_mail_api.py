import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import os
import tempfile
from datetime import datetime
from unittest.mock import patch, MagicMock

from main import app
from app.database.base import get_db, Base
from app.model.base_model import User
from app.model.mail_model import MailUser, Mail, MailFolder
from app.service.auth_service import create_access_token

# 테스트용 인메모리 SQLite 데이터베이스 설정
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 테스트용 데이터베이스 의존성 오버라이드
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# 테스트 클라이언트 생성
@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture(scope="function")
def setup_database():
    """각 테스트마다 새로운 데이터베이스 테이블 생성"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def test_user(setup_database):
    """테스트용 사용자 생성"""
    db = TestingSessionLocal()
    try:
        # User 테이블에 사용자 생성
        user = User(
            id=1,
            username="testuser",
            email="test@example.com",
            hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "secret" 해시
            is_active=True
        )
        db.add(user)
        
        # MailUser 테이블에도 사용자 생성
        mail_user = MailUser(
            id=1,
            user_uuid="test-uuid-123",
            email="test@example.com",
            password_hash="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
            is_active=True,
            created_at=datetime(2024, 1, 1, 0, 0, 0)
        )
        db.add(mail_user)
        
        # 기본 폴더들 생성
        folders = [
            MailFolder(id=1, user_id=1, name="받은편지함", folder_type="inbox", created_at=datetime(2024, 1, 1, 0, 0, 0)),
            MailFolder(id=2, user_id=1, name="보낸편지함", folder_type="sent", created_at=datetime(2024, 1, 1, 0, 0, 0)),
            MailFolder(id=3, user_id=1, name="임시보관함", folder_type="drafts", created_at=datetime(2024, 1, 1, 0, 0, 0)),
            MailFolder(id=4, user_id=1, name="휴지통", folder_type="trash", created_at=datetime(2024, 1, 1, 0, 0, 0)),
        ]
        for folder in folders:
            db.add(folder)
        
        db.commit()
        db.refresh(user)
        return user
    finally:
        db.close()

@pytest.fixture
def auth_headers(test_user):
    """인증 헤더 생성"""
    access_token = create_access_token(data={"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {access_token}"}

def test_send_mail(client, test_user, auth_headers):
    """메일 발송 API 테스트"""
    # 메일 서비스 모킹
    with patch('app.router.mail_router.mail_service.create_mail') as mock_create_mail:
        # 모킹된 메일 객체 설정
        mock_mail = MagicMock()
        mock_mail.id = 123
        mock_mail.mail_uuid = "test-mail-uuid-123"
        mock_mail.sent_at = datetime.utcnow()
        mock_mail.created_at = datetime.utcnow()
        mock_create_mail.return_value = mock_mail
        
        # 메일 발송 요청 데이터
        mail_data = {
            "to_emails": "recipient@example.com",
            "subject": "테스트 메일",
            "content": "안녕하세요, 테스트 메일입니다.",
            "priority": "normal"
        }
        
        # API 호출
        response = client.post(
            "/mail/send",
            data=mail_data,
            headers=auth_headers
        )
        
        # 응답 검증
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["mail_uuid"] == "test-mail-uuid-123"
        assert response_data["success"] == True
        assert "성공적으로 발송" in response_data["message"]
        
        # 메일 서비스가 올바른 파라미터로 호출되었는지 확인
        mock_create_mail.assert_called_once()
        call_args = mock_create_mail.call_args
        db_session = call_args[0][0]  # 첫 번째 인자 (db)
        mail_data_arg = call_args[0][1]  # 두 번째 인자 (mail_data)
        sender_id = call_args[0][2]  # 세 번째 인자 (sender_id)
        
        assert mail_data_arg.subject == "테스트 메일"
        assert mail_data_arg.body_text == "안녕하세요, 테스트 메일입니다."
        assert sender_id == test_user.id
        assert len(mail_data_arg.recipients) == 1
        assert mail_data_arg.recipients[0].email == "recipient@example.com"
        assert mail_data_arg.recipients[0].recipient_type == "to"

def test_send_mail_missing_required_fields(client, test_user, auth_headers):
    """필수 필드 누락 시 422 오류 테스트"""
    # 필수 필드 누락 (subject 없음)
    mail_data = {
        "to_emails": "recipient@example.com",
        "content": "테스트 메일 내용"
    }
    
    response = client.post(
        "/mail/send",
        data=mail_data,
        headers=auth_headers
    )
    
    # 422 Unprocessable Entity 응답 확인
    assert response.status_code == 422

def test_send_mail_invalid_email_format(client, test_user, auth_headers):
    """잘못된 이메일 형식 테스트"""
    mail_data = {
        "to_emails": "invalid-email-format",
        "subject": "테스트 메일",
        "content": "테스트 메일 내용"
    }
    
    response = client.post(
        "/mail/send",
        data=mail_data,
        headers=auth_headers
    )
    
    # 400 또는 422 오류 응답 확인
    assert response.status_code in [400, 422, 500]

def test_send_mail_unauthorized(client):
    """인증되지 않은 사용자의 메일 발송 시도 테스트"""
    mail_data = {
        "to_emails": "recipient@example.com",
        "subject": "테스트 메일",
        "content": "테스트 메일 내용"
    }
    
    response = client.post(
        "/mail/send",
        data=mail_data
    )
    
    # 403 Forbidden 응답 확인 (인증 헤더 없음)
    assert response.status_code == 403

def test_get_inbox_mails(client, test_user, auth_headers):
    """받은 메일함 조회 API 테스트"""
    response = client.get(
        "/mail/inbox",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    response_data = response.json()
    assert "mails" in response_data
    assert "pagination" in response_data
    assert isinstance(response_data["mails"], list)

def test_get_inbox_mail_detail(client, test_user, auth_headers):
    """받은 메일 상세 조회 API 테스트"""
    # 존재하지 않는 메일 ID로 테스트
    response = client.get(
        "/mail/inbox/nonexistent-mail-id",
        headers=auth_headers
    )
    
    # 404 Not Found 응답 확인
    assert response.status_code == 404

def test_get_sent_mails(client, test_user, auth_headers):
    """보낸 메일함 조회 API 테스트"""
    response = client.get(
        "/mail/sent",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    response_data = response.json()
    assert "mails" in response_data
    assert "pagination" in response_data
    assert isinstance(response_data["mails"], list)

def test_get_sent_mail_detail(client, test_user, auth_headers):
    """보낸 메일 상세 조회 API 테스트"""
    # 존재하지 않는 메일 ID로 테스트
    response = client.get(
        "/mail/sent/nonexistent-mail-id",
        headers=auth_headers
    )
    
    # 404 Not Found 응답 확인
    assert response.status_code == 404

def test_get_draft_mails(client, test_user, auth_headers):
    """임시보관함 조회 API 테스트"""
    response = client.get(
        "/mail/drafts",
        headers=auth_headers
    )
    
    if response.status_code != 200:
        print(f"Error response: {response.text}")
    
    assert response.status_code == 200
    response_data = response.json()
    assert "mails" in response_data
    assert "pagination" in response_data
    assert isinstance(response_data["mails"], list)

def test_get_draft_mail_detail(client, test_user, auth_headers):
    """임시보관함 상세 조회 API 테스트"""
    # 존재하지 않는 메일 ID로 테스트
    response = client.get(
        "/mail/drafts/999",
        headers=auth_headers
    )
    
    # 404 Not Found 응답 확인
    assert response.status_code == 404

def test_get_trash_mails(client, test_user, auth_headers):
    """휴지통 조회 API 테스트"""
    response = client.get(
        "/mail/trash",
        headers=auth_headers
    )
    
    if response.status_code != 200:
        print(f"Error response: {response.text}")
    assert response.status_code == 200
    response_data = response.json()
    assert "mails" in response_data
    assert "pagination" in response_data
    assert isinstance(response_data["mails"], list)

def test_get_trash_mail_detail(client, test_user, auth_headers):
    """휴지통 메일 상세 조회 API 테스트"""
    # 존재하지 않는 메일 ID로 테스트
    response = client.get(
        "/mail/trash/nonexistent-mail-id",
        headers=auth_headers
    )
    
    # 404 Not Found 응답 확인
    assert response.status_code == 404

if __name__ == "__main__":
    pytest.main(["-v", __file__])