from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    """사용자 기본 스키마"""
    user_id: str = Field(..., description="사용자 ID")
    username: str = Field(..., min_length=3, max_length=100, description="사용자명")
    email: EmailStr = Field(..., description="이메일 주소")
    org_code: str = Field(..., description="조직 코드")

class UserCreate(UserBase):
    """사용자 생성 스키마"""
    username: str = Field(..., min_length=3, max_length=100, description="사용자명")
    email: EmailStr = Field(..., description="이메일 주소")
    password: str = Field(..., min_length=4, description="비밀번호 (개발용: 최소 4자, 프로덕션: 8자 이상 권장)")
    full_name: Optional[str] = Field(None, max_length=100, description="전체 이름")

class UserResponse(BaseModel):
    """사용자 응답 스키마"""
    user_id: str = Field(..., description="사용자 ID")
    username: str = Field(..., description="사용자명")
    email: EmailStr = Field(..., description="이메일 주소")
    org_id: str = Field(..., description="조직 ID")
    user_uuid: str = Field(..., description="사용자 UUID")
    role: str = Field(..., description="사용자 역할")
    is_active: bool = Field(..., description="활성 상태")
    created_at: datetime = Field(..., description="생성 시간")
    updated_at: Optional[datetime] = Field(None, description="수정 시간")
    
    class Config:                                                                                                
        populate_by_name = True

class UserLogin(BaseModel):
    """사용자 로그인 스키마"""
    user_id: str = Field(..., description="사용자 ID")
    password: str = Field(..., description="비밀번호")

class Token(BaseModel):
    """토큰 응답 스키마"""
    access_token: str = Field(..., description="액세스 토큰")
    refresh_token: str = Field(..., description="리프레시 토큰")
    token_type: str = Field(default="bearer", description="토큰 타입")
    expires_in: int = Field(..., description="만료 시간 (초)")

class AccessToken(BaseModel):
    """액세스 토큰 응답 스키마"""
    access_token: str = Field(..., description="액세스 토큰")
    token_type: str = Field(default="bearer", description="토큰 타입")
    expires_in: int = Field(..., description="만료 시간 (초)")

class TokenRefresh(BaseModel):
    """토큰 갱신 요청 스키마"""
    refresh_token: str = Field(..., description="리프레시 토큰")

class MessageResponse(BaseModel):
    """메시지 응답 스키마"""
    message: str = Field(..., description="응답 메시지")
    success: bool = Field(default=True, description="성공 여부")

class ErrorResponse(BaseModel):
    """에러 응답 스키마"""
    error: str = Field(..., description="에러 메시지")
    detail: Optional[str] = Field(None, description="상세 정보")
    success: bool = Field(default=False, description="성공 여부")

class LoginLogCreate(BaseModel):
    """로그인 로그 생성 스키마"""
    user_uuid: Optional[str] = Field(None, description="사용자 UUID (로그인 성공 시)")
    ip_address: Optional[str] = Field(None, description="클라이언트 IP 주소")
    user_agent: Optional[str] = Field(None, description="사용자 에이전트")
    login_status: str = Field(..., description="로그인 상태 (success, failed)")
    failure_reason: Optional[str] = Field(None, description="로그인 실패 사유")