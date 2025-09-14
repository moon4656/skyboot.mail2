from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.sql import func
from app.database import Base

class User(Base):
    """사용자 모델"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class RefreshToken(Base):
    """리프레시 토큰 모델"""
    __tablename__ = "refresh_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    token = Column(String(255), unique=True, index=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_revoked = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class MailLog(Base):
    """메일 발송 로그 모델"""
    __tablename__ = "mail_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    to_email = Column(String(255), nullable=False)
    subject = Column(String(500), nullable=False)
    body = Column(Text, nullable=False)
    status = Column(String(50), default="sent")  # sent, failed
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())