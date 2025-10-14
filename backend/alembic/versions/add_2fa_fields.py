"""Add 2FA fields to users table

Revision ID: add_2fa_fields
Revises: 
Create Date: 2024-12-24 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_2fa_fields'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    2FA 관련 필드를 users 테이블에 추가합니다.
    """
    # 2FA 관련 컬럼 추가
    op.add_column('users', sa.Column('is_2fa_enabled', sa.Boolean(), nullable=False, server_default='false', comment='2FA 활성화 여부'))
    op.add_column('users', sa.Column('totp_secret', sa.String(length=32), nullable=True, comment='TOTP 시크릿 키 (암호화됨)'))
    op.add_column('users', sa.Column('backup_codes', sa.JSON(), nullable=True, comment='백업 코드 목록 (암호화됨)'))
    op.add_column('users', sa.Column('last_2fa_at', sa.DateTime(timezone=True), nullable=True, comment='마지막 2FA 인증 시간'))
    
    # 인덱스 추가 (성능 최적화)
    op.create_index('idx_users_2fa_enabled', 'users', ['is_2fa_enabled'])
    op.create_index('idx_users_last_2fa_at', 'users', ['last_2fa_at'])


def downgrade() -> None:
    """
    2FA 관련 필드를 users 테이블에서 제거합니다.
    """
    # 인덱스 제거
    op.drop_index('idx_users_last_2fa_at', table_name='users')
    op.drop_index('idx_users_2fa_enabled', table_name='users')
    
    # 컬럼 제거
    op.drop_column('users', 'last_2fa_at')
    op.drop_column('users', 'backup_codes')
    op.drop_column('users', 'totp_secret')
    op.drop_column('users', 'is_2fa_enabled')