from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, Dict, Any, List
import os
from enum import Enum

class Environment(str, Enum):
    """환경 타입 정의"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

class SaaSSettings(BaseSettings):
    """SaaS 애플리케이션 설정 클래스"""
    
    # 환경 설정
    ENVIRONMENT: Environment = Environment.DEVELOPMENT
    DEBUG: bool = True
    
    # 애플리케이션 기본 설정
    APP_NAME: str = "SkyBoot Mail SaaS"
    APP_VERSION: str = "2.0.0"
    API_V1_PREFIX: str = "/api/v1"
    
    # 데이터베이스 설정 (다중 테넌트 지원)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:safe70!!@localhost:5432/skybootmail")
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "safe70!!")
    DB_NAME: str = os.getenv("DB_NAME", "skybootmail")
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 30
    DB_POOL_TIMEOUT: int = 30
    
    # Redis 설정 (캐싱 및 세션 관리)
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD")
    
    # JWT 설정 (강화된 보안)
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production-saas")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # SaaS 다중 조직 설정
    DEFAULT_ORG_DOMAIN: str = "skyboot.mail"
    MAX_ORGS_PER_USER: int = 5
    MAX_USERS_PER_ORG: int = 1000
    DEFAULT_MAX_USERS_PER_ORG: int = 1000
    DEFAULT_MAX_STORAGE_PER_ORG: int = 10  # GB
    ORG_SUBDOMAIN_ENABLED: bool = True
    
    # 메일 서버 설정 (조직별 설정 가능)
    # DEFAULT_SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    # DEFAULT_SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    # DEFAULT_SMTP_USER: Optional[str] = os.getenv("SMTP_USER")
    # DEFAULT_SMTP_PASSWORD: Optional[str] = os.getenv("SMTP_PASSWORD")    
    
    # SMTP 설정 (조직별 설정 가능)
    # 개발 환경: Gmail SMTP 사용, 프로덕션: Postfix 사용
    DEFAULT_SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    DEFAULT_SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    DEFAULT_SMTP_USER: Optional[str] = os.getenv("SMTP_USER")
    DEFAULT_SMTP_PASSWORD: Optional[str] = os.getenv("SMTP_PASSWORD")
    DEFAULT_SMTP_FROM_EMAIL: str = os.getenv("SMTP_FROM_EMAIL", "noreply@skyboot.mail")
    DEFAULT_SMTP_FROM_NAME: str = "SkyBoot Mail SaaS"
    
    # 메일 할당량 설정
    DEFAULT_MAIL_QUOTA_MB: int = int(os.getenv("DEFAULT_MAIL_QUOTA_MB", "1000"))  # 기본 1GB
    
    # Postfix 설정 (다중 도메인 지원)
    POSTFIX_CONFIG_DIR: str = "/etc/postfix"
    VIRTUAL_DOMAINS_FILE: str = "/etc/postfix/virtual_domains"
    VIRTUAL_USERS_FILE: str = "/etc/postfix/virtual_users"
    VIRTUAL_ALIASES_FILE: str = "/etc/postfix/virtual_aliases"
    
    # 파일 저장 설정
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")
    MAX_FILE_SIZE_MB: int = 25
    ALLOWED_FILE_TYPES: List[str] = [
        "pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx",
        "txt", "rtf", "csv", "zip", "rar", "7z",
        "jpg", "jpeg", "png", "gif", "bmp", "svg"
    ]
    
    # 보안 설정
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "https://*.skyboot.mail"
    ]
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # 로깅 설정
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "./logs"
    LOG_ROTATION_SIZE: str = "10MB"
    LOG_RETENTION_DAYS: int = 30
    
    # 성능 및 제한 설정
    RATE_LIMIT_PER_MINUTE: int = 60
    MAX_CONCURRENT_REQUESTS: int = 100
    REQUEST_TIMEOUT_SECONDS: int = 30
    
    # 조직별 기본 제한 설정
    DEFAULT_MAX_MAIL_SIZE_MB: int = 25
    DEFAULT_MAX_ATTACHMENT_SIZE_MB: int = 10
    DEFAULT_DAILY_MAIL_LIMIT: int = 1000
    DEFAULT_STORAGE_LIMIT_GB: int = 10
    
    # 백업 설정
    BACKUP_DIR: str = "./backups"
    BACKUP_RETENTION_DAYS: int = 90
    AUTO_BACKUP_ENABLED: bool = True
    BACKUP_SCHEDULE_CRON: str = "0 2 * * *"  # 매일 새벽 2시
    
    # DevOps 설정
    DEVOPS_ENABLED: bool = True
    DEVOPS_BACKUP_COMPRESSION: bool = True
    DEVOPS_BACKUP_ENCRYPTION: bool = False
    DEVOPS_TEST_TIMEOUT: int = 300  # 5분
    DEVOPS_MAX_BACKUP_SIZE_GB: int = 50
    DEVOPS_RESTORE_TIMEOUT: int = 1800  # 30분
    
    # 바이러스 검사 설정
    VIRUS_SCAN_ENABLED: bool = True
    CLAMAV_HOST: str = os.getenv("CLAMAV_HOST", "localhost")
    CLAMAV_PORT: int = int(os.getenv("CLAMAV_PORT", "3310"))
    VIRUS_SCAN_FALLBACK_ENABLED: bool = True  # ClamAV 사용 불가 시 휴리스틱 검사 사용
    VIRUS_SCAN_MAX_FILE_SIZE_MB: int = 100  # 바이러스 검사 최대 파일 크기
    VIRUS_QUARANTINE_DIR: str = os.getenv("VIRUS_QUARANTINE_DIR", "./quarantine")
    VIRUS_SCAN_TIMEOUT_SECONDS: int = 30
    
    # 모니터링 설정
    METRICS_ENABLED: bool = True
    HEALTH_CHECK_INTERVAL: int = 60
    ALERT_EMAIL: Optional[str] = os.getenv("ALERT_EMAIL")
    
    # 외부 API 설정
    WEBHOOK_SECRET: Optional[str] = os.getenv("WEBHOOK_SECRET")
    API_RATE_LIMIT: int = 1000
    
    # 개발 환경 설정
    RELOAD_ON_CHANGE: bool = True if ENVIRONMENT == Environment.DEVELOPMENT else False
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )
        
    def get_database_url(self, org_id: Optional[str] = None) -> str:
        """조직별 데이터베이스 URL 반환 (필요시 샤딩 지원)"""
        if org_id and self.ENVIRONMENT == Environment.PRODUCTION:
            # 프로덕션에서는 조직별 샤딩 가능
            return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}_{org_id}"
        return self.DATABASE_URL
    
    def get_smtp_config(self, org_id: Optional[str] = None) -> Dict[str, Any]:
        """조직별 SMTP 설정 반환 (환경에 따라 다른 설정 사용)"""
        # 환경에 따른 SMTP 설정
        if self.ENVIRONMENT == Environment.PRODUCTION:
            # 프로덕션: Postfix 사용
            host = "172.18.0.233"  # WSL Postfix IP
            port = 25
        else:
            # 개발/스테이징: Gmail SMTP 사용
            host = self.DEFAULT_SMTP_HOST
            port = self.DEFAULT_SMTP_PORT
        
        return {
            "host": host,
            "port": port,
            "user": self.DEFAULT_SMTP_USER,
            "password": self.DEFAULT_SMTP_PASSWORD,
            "from_email": self.DEFAULT_SMTP_FROM_EMAIL,
            "from_name": self.DEFAULT_SMTP_FROM_NAME
        }
    
    def is_production(self) -> bool:
        """프로덕션 환경 여부 확인"""
        return self.ENVIRONMENT == Environment.PRODUCTION
    
    def is_development(self) -> bool:
        """개발 환경 여부 확인"""
        return self.ENVIRONMENT == Environment.DEVELOPMENT

# 전역 설정 인스턴스
settings = SaaSSettings()