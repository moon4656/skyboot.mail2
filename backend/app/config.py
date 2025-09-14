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
    
    # SMTP 설정 (Postfix)
    SMTP_HOST: str = "172.26.71.122"
    SMTP_PORT: int = 25
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: str = "noreply@skyboot.local"
    SMTP_FROM_NAME: str = "SkyBoot Mail System"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()