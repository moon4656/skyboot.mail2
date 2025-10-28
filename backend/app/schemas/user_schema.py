from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime

from sqlalchemy.sql import roles

class UserBase(BaseModel):
    """사용자 기본 스키마"""
    user_id: str = Field(..., description="사용자 ID")
    username: str = Field(..., min_length=3, max_length=100, description="사용자명")
    email: EmailStr = Field(..., description="이메일 주소")
    org_code: str = Field(..., description="조직 코드")

class UserCreate(BaseModel):
    """사용자 생성 스키마"""
    user_id: str = Field(..., min_length=3, max_length=50, description="사용자 ID")
    username: str = Field(..., min_length=3, max_length=100, description="사용자명")
    email: EmailStr = Field(..., description="이메일 주소")
    password: str = Field(..., min_length=4, description="비밀번호 (개발용: 최소 4자, 프로덕션: 8자 이상 권장)")
    full_name: Optional[str] = Field(None, max_length=100, description="전체 이름")
    # org_code는 서버에서 자동 설정됨
    
    # Pydantic v2 구성 및 Swagger 예시
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "user_id": "user02",
                "username": "김철수",
                "email": "user02@example.com",
                "password": "test1234",
                "full_name": "김철수 대리"
            }
        }
    )

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
    
    # Pydantic v2 구성 및 Swagger 예시
    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "user_id": "user01",
                "username": "이성용",
                "email": "user01@example.com",
                "org_id": "3856a8c1-84a4-4019-9133-655cacab4bc9",
                "user_uuid": "3b959219-da10-42bb-9693-0aa3ed502cd3",
                "role": "user",
                "is_active": True
            }
        }
    )

class UserUpdate(BaseModel):
    """사용자 수정 요청 스키마 (Edit Value Schema)"""
    username: Optional[str] = Field(None, min_length=3, max_length=100, description="사용자명")
    full_name: Optional[str] = Field(None, max_length=100, description="전체 이름")
    is_active: Optional[bool] = Field(None, description="활성 상태")
    roles: Optional[list[str]] = Field(None, description="사용자 역할")
    
    # Pydantic v2 구성 및 Swagger 예시
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "username": "이성용",
                "full_name": "이성용 과장",
                "is_active": True,
                "roles": ["user"]
            }
        }
    )

class UserLogin(BaseModel):
    """사용자 로그인 스키마"""
    user_id: str = Field(..., description="사용자 ID")
    password: str = Field(..., description="비밀번호")
    
    # Pydantic v2 구성 및 Swagger 예시
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "user_id": "user01",
                "password": "test",
            }
        }
    )    

class UserChangePassword(BaseModel):
    """비밀번호 변경 요청 스키마"""
    current_password: str = Field(..., min_length=4, description="현재 비밀번호")
    new_password: str = Field(..., min_length=4, description="새 비밀번호")

    # Pydantic v2 구성 및 Swagger 예시
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "current_password": "old-pass-1234",
                "new_password": "new-pass-5678"
            }
        }
    )

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