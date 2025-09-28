"""
SkyBoot Mail SaaS - Alembic 환경 설정

이 파일은 Alembic 마이그레이션 환경을 설정합니다.
SaaS 구조에 맞는 다중 조직 지원 및 데이터 격리를 고려합니다.
"""

from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
import sys

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 애플리케이션 모델 및 설정 임포트
from app.config import settings
from app.database.user import Base

# 모든 모델을 import하여 메타데이터에 포함
from app.model.user_model import User
from app.model.organization_model import Organization, OrganizationStatus, OrganizationSettings, OrganizationUsage
from app.model.mail_model import MailUser, Mail, MailRecipient

# Alembic Config 객체
config = context.config

# 로깅 설정
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 메타데이터 설정 (모든 모델 포함)
target_metadata = Base.metadata

# 데이터베이스 URL 설정
config.set_main_option("sqlalchemy.url", settings.get_database_url())

def run_migrations_offline() -> None:
    """
    오프라인 모드에서 마이그레이션 실행
    
    이 모드에서는 Engine이나 Connection 없이 SQL 스크립트만 생성합니다.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
        include_schemas=True,
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """
    온라인 모드에서 마이그레이션 실행
    
    이 모드에서는 실제 데이터베이스 연결을 통해 마이그레이션을 실행합니다.
    """
    # 데이터베이스 연결 설정
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = settings.get_database_url()
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            include_schemas=True,
            # SaaS 관련 설정
            render_as_batch=True,  # SQLite 호환성을 위해
            transaction_per_migration=True,  # 각 마이그레이션을 별도 트랜잭션으로
        )

        with context.begin_transaction():
            context.run_migrations()

def include_object(object, name, type_, reflected, compare_to):
    """
    마이그레이션에 포함할 객체를 필터링합니다.
    
    SaaS 환경에서 특정 테이블이나 인덱스를 제외하고 싶을 때 사용합니다.
    """
    # 시스템 테이블 제외
    if type_ == "table" and name.startswith("pg_"):
        return False
    
    # 임시 테이블 제외
    if type_ == "table" and name.endswith("_temp"):
        return False
    
    # 백업 테이블 제외 (마이그레이션 스크립트에서 생성된)
    if type_ == "table" and "_backup_" in name:
        return False
    
    return True

# 마이그레이션 실행
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()