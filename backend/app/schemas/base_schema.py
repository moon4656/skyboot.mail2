from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

# 사용자 관련 스키마
class UserBase(BaseModel):
    """사용자 기본 스키마"""
    email: EmailStr
    username: str

class UserCreate(UserBase):
    """사용자 생성 스키마"""
    password: str

class UserResponse(UserBase):
    """사용자 응답 스키마"""
    id: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# 인증 관련 스키마
class UserLogin(BaseModel):
    """로그인 스키마"""
    email: EmailStr
    password: str

class Token(BaseModel):
    """토큰 응답 스키마"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenRefresh(BaseModel):
    """토큰 갱신 스키마"""
    refresh_token: str

class AccessToken(BaseModel):
    """액세스 토큰 응답 스키마"""
    access_token: str
    token_type: str = "bearer"

# 메일 관련 스키마는 app.mail.schemas로 이동됨

# 공통 응답 스키마
class MessageResponse(BaseModel):
    """메시지 응답 스키마"""
    message: str