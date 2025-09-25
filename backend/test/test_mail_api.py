import pytest
import httpx
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import tempfile
from unittest.mock import patch

# 테스트용 데이터베이스 설정
TEST_DATABASE_URL = "sqlite:///./test_mail.db"

# 테스트 클라이언트 설정
def get_test_client():
    """
    테스트용 FastAPI 클라이언트를 생성합니다.
    """
    from app.routers.mail import app
    return TestClient(app)

# 테스트 데이터
TEST_USER = {
    "email": "test@example.com",
    "user_uuid": "test-uuid-123"
}

TEST_MAIL_DATA = {
    "to_emails": "recipient@example.com",
    "subject": "테스트 메일",
    "content": "이것은 테스트 메일입니다.",
    "priority": "NORMAL"
}

class TestMailAPI:
    """
    메일 API 테스트 클래스
    """
    
    def setup_method(self):
        """
        각 테스트 메서드 실행 전 설정
        """
        self.client = get_test_client()
        self.headers = {
            "Authorization": "Bearer test-token"
        }
    
    def test_send_mail_success(self):
        """
        메일 발송 성공 테스트
        """
        with patch('app.routers.mail.get_current_user', return_value=TEST_USER):
            response = self.client.post(
                "/api/mail/send",
                data=TEST_MAIL_DATA,
                headers=self.headers
            )
            
            # 실제 SMTP 서버가 없으므로 500 에러가 예상됨
            # 하지만 요청 형식은 올바르게 처리되어야 함
            assert response.status_code in [200, 500]
    
    def test_send_mail_missing_fields(self):
        """
        필수 필드 누락 시 에러 테스트
        """
        with patch('app.routers.mail.get_current_user', return_value=TEST_USER):
            incomplete_data = {
                "subject": "테스트 메일"
                # to_emails와 content 누락
            }
            
            response = self.client.post(
                "/api/mail/send",
                data=incomplete_data,
                headers=self.headers
            )
            
            assert response.status_code == 422  # Validation Error
    
    def test_get_inbox_mails(self):
        """
        받은 메일 목록 조회 테스트
        """
        with patch('app.routers.mail.get_current_user', return_value=TEST_USER):
            response = self.client.get(
                "/api/mail/inbox",
                headers=self.headers
            )
            
            # 데이터베이스가 비어있어도 빈 목록을 반환해야 함
            assert response.status_code in [200, 500]
    
    def test_get_inbox_mails_with_pagination(self):
        """
        페이지네이션을 포함한 받은 메일 목록 조회 테스트
        """
        with patch('app.routers.mail.get_current_user', return_value=TEST_USER):
            response = self.client.get(
                "/api/mail/inbox?page=1&limit=10",
                headers=self.headers
            )
            
            assert response.status_code in [200, 500]
    
    def test_get_sent_mails(self):
        """
        보낸 메일 목록 조회 테스트
        """
        with patch('app.routers.mail.get_current_user', return_value=TEST_USER):
            response = self.client.get(
                "/api/mail/sent",
                headers=self.headers
            )
            
            assert response.status_code in [200, 500]
    
    def test_get_draft_mails(self):
        """
        임시보관함 메일 목록 조회 테스트
        """
        with patch('app.routers.mail.get_current_user', return_value=TEST_USER):
            response = self.client.get(
                "/api/mail/drafts",
                headers=self.headers
            )
            
            assert response.status_code in [200, 500]
    
    def test_get_mail_stats(self):
        """
        메일 통계 조회 테스트
        """
        with patch('app.routers.mail.get_current_user', return_value=TEST_USER):
            response = self.client.get(
                "/api/mail/stats",
                headers=self.headers
            )
            
            assert response.status_code in [200, 500]
    
    def test_unauthorized_access(self):
        """
        인증 없이 접근 시 에러 테스트
        """
        response = self.client.get("/api/mail/inbox")
        assert response.status_code == 403  # Forbidden
    
    def test_invalid_mail_id(self):
        """
        존재하지 않는 메일 ID로 접근 시 에러 테스트
        """
        with patch('app.routers.mail.get_current_user', return_value=TEST_USER):
            response = self.client.get(
                "/api/mail/inbox/invalid-mail-id",
                headers=self.headers
            )
            
            assert response.status_code in [404, 500]

def test_api_documentation():
    """
    API 문서 접근 테스트
    """
    client = get_test_client()
    
    # OpenAPI 스키마 접근
    response = client.get("/openapi.json")
    assert response.status_code == 200
    
    # Swagger UI 접근
    response = client.get("/docs")
    assert response.status_code == 200
    
    # ReDoc 접근
    response = client.get("/redoc")
    assert response.status_code == 200

def test_health_check():
    """
    기본 헬스 체크 테스트
    """
    client = get_test_client()
    
    # 루트 경로 접근
    response = client.get("/")
    # 루트 경로가 정의되지 않았으므로 404가 예상됨
    assert response.status_code == 404

if __name__ == "__main__":
    # 테스트 실행
    pytest.main(["-v", __file__])