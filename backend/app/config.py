from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    """애플리케이션 설정 클래스"""
    
    # 데이터베이스 설정
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:safe70!!@localhost:5432/skyboot_mail")
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "safe70!!"
    DB_NAME: str = "skyboot_mail"
    
    # JWT 설정
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # SMTP 설정 (Gmail for testing)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = "test@gmail.com"  # 테스트용 - 실제 사용 시 변경 필요
    SMTP_PASSWORD: Optional[str] = "test_password"  # 테스트용 - 실제 사용 시 변경 필요
    SMTP_FROM_EMAIL: str = "test@gmail.com"
    SMTP_FROM_NAME: str = "SkyBoot Mail System"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()