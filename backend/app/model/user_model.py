from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database.user import Base
import uuid

def generate_user_uuid(ctx=None):
    """사용자 UUID 생성 함수"""
    return str(uuid.uuid4())

class User(Base):
    """사용자 모델 - 조직 연결"""
    __tablename__ = "users"

    user_id = Column(String(50), primary_key=True, index=True, comment="사용자 ID")
    user_uuid = Column(String(36), unique=True, index=True, default=generate_user_uuid)
    org_id = Column(String(36), ForeignKey("organizations.org_id"), nullable=False, comment="소속 조직 ID")
    
    email = Column(String(255), index=True, nullable=False, comment="이메일 주소")
    username = Column(String(100), index=True, nullable=False, comment="사용자명")
    hashed_password = Column(String(255), nullable=False, comment="해시된 비밀번호")
    
    # 역할 및 권한
    role = Column(String(50), default="user", comment="사용자 역할 (admin, user, viewer)")
    permissions = Column(Text, comment="권한 JSON")
    
    # 상태 정보
    is_active = Column(Boolean, default=True, comment="활성 상태")
    is_email_verified = Column(Boolean, default=False, comment="이메일 인증 여부")
    last_login_at = Column(DateTime(timezone=True), comment="마지막 로그인 시간")
    
    # 2FA 관련 필드
    is_2fa_enabled = Column(Boolean, default=False, comment="2FA 활성화 여부")
    totp_secret = Column(String(32), comment="TOTP 시크릿 키")
    backup_codes = Column(Text, comment="백업 코드 JSON")
    last_2fa_at = Column(DateTime(timezone=True), comment="마지막 2FA 인증 시간")
    
    # 시간 정보
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="생성 시간")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="수정 시간")
    
    # 관계 설정
    organization = relationship("Organization", back_populates="users")
    
    __table_args__ = (
        UniqueConstraint('org_id', 'email', name='unique_org_email'),
        UniqueConstraint('org_id', 'username', name='unique_org_username'),
    )

class RefreshToken(Base):
    """리프레시 토큰 모델"""
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_uuid = Column(String(36), ForeignKey("users.user_uuid"), nullable=False)
    token = Column(Text, unique=True, index=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_revoked = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class LoginLog(Base):
    """로그인 로그 모델"""
    __tablename__ = "login_logs"
    
    id = Column(Integer, primary_key=True, index=True, comment="로그 ID")
    user_uuid = Column(String(50), nullable=True, comment="사용자 UUID (로그인 성공 시)")
    user_id = Column(String(50), nullable=False, comment="로그인 시도 사용자 ID")
    ip_address = Column(String(45), nullable=True, comment="클라이언트 IP 주소")
    user_agent = Column(Text, nullable=True, comment="사용자 에이전트")
    login_status = Column(String(20), nullable=False, comment="로그인 상태 (success, failed)")
    failure_reason = Column(String(255), nullable=True, comment="로그인 실패 사유")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="로그인 시도 시간")

# MailLog 모델은 app.mail.models로 이동됨