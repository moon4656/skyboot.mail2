#!/usr/bin/env python3
"""
완전한 마이그레이션 스크립트
모든 테이블을 올바른 순서로 생성하고 수정합니다.
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

def get_db_connection():
    """데이터베이스 연결을 반환합니다."""
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
            database=os.getenv("DB_NAME", "skyboot_mail"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "")
        )
        return conn
    except Exception as e:
        print(f"❌ 데이터베이스 연결 실패: {e}")
        return None

def execute_sql(conn, sql, description):
    """SQL을 실행하고 결과를 출력합니다."""
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql)
            conn.commit()
            print(f"✅ {description}")
            return True
    except Exception as e:
        print(f"❌ {description} 실패: {e}")
        conn.rollback()
        return False

def complete_migration():
    """완전한 마이그레이션을 수행합니다."""
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        print("🚀 완전한 마이그레이션 시작...")
        
        # 1. organizations 테이블이 없으면 생성
        print("\n📋 1. organizations 테이블 확인 및 생성")
        organizations_sql = """
        CREATE TABLE IF NOT EXISTS organizations (
            id SERIAL PRIMARY KEY,
            organization_uuid VARCHAR(36) UNIQUE DEFAULT gen_random_uuid()::text,
            name VARCHAR(255) NOT NULL,
            domain VARCHAR(255) UNIQUE NOT NULL,
            description TEXT,
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        -- 기본 조직 데이터 삽입
        INSERT INTO organizations (id, name, domain, description) 
        VALUES (1, 'Default Organization', 'default.local', 'Default organization for mail system')
        ON CONFLICT (id) DO NOTHING;
        
        -- 인덱스 추가
        CREATE INDEX IF NOT EXISTS ix_organizations_organization_uuid ON organizations(organization_uuid);
        CREATE INDEX IF NOT EXISTS ix_organizations_domain ON organizations(domain);
        
        -- 컬럼 코멘트 추가
        COMMENT ON TABLE organizations IS '조직 모델';
        COMMENT ON COLUMN organizations.organization_uuid IS '조직 UUID';
        COMMENT ON COLUMN organizations.name IS '조직명';
        COMMENT ON COLUMN organizations.domain IS '조직 도메인';
        COMMENT ON COLUMN organizations.description IS '조직 설명';
        COMMENT ON COLUMN organizations.is_active IS '활성 상태';
        COMMENT ON COLUMN organizations.created_at IS '생성 시간';
        COMMENT ON COLUMN organizations.updated_at IS '수정 시간';
        """
        execute_sql(conn, organizations_sql, "organizations 테이블 생성")
        
        # 2. mails 테이블 수정 (references 컬럼명 변경)
        print("\n📋 2. mails 테이블 수정")
        mails_fix_sql = """
        -- mail_id 컬럼 추가 (기본키로 사용)
        ALTER TABLE mails ADD COLUMN IF NOT EXISTS mail_id VARCHAR(50) UNIQUE DEFAULT gen_random_uuid()::text;
        
        -- sender_uuid 컬럼 추가
        ALTER TABLE mails ADD COLUMN IF NOT EXISTS sender_uuid VARCHAR(36);
        
        -- 기존 sender_id를 기반으로 sender_uuid 업데이트
        UPDATE mails 
        SET sender_uuid = (
            SELECT user_uuid 
            FROM mail_users 
            WHERE mail_users.id = mails.sender_id
        )
        WHERE sender_uuid IS NULL;
        
        -- 추가 컬럼들
        ALTER TABLE mails ADD COLUMN IF NOT EXISTS recipient_emails TEXT[];
        ALTER TABLE mails ADD COLUMN IF NOT EXISTS cc_emails TEXT[];
        ALTER TABLE mails ADD COLUMN IF NOT EXISTS bcc_emails TEXT[];
        ALTER TABLE mails ADD COLUMN IF NOT EXISTS reply_to VARCHAR(255);
        ALTER TABLE mails ADD COLUMN IF NOT EXISTS message_id VARCHAR(255);
        ALTER TABLE mails ADD COLUMN IF NOT EXISTS in_reply_to VARCHAR(255);
        ALTER TABLE mails ADD COLUMN IF NOT EXISTS mail_references TEXT;  -- references 대신 mail_references 사용
        ALTER TABLE mails ADD COLUMN IF NOT EXISTS has_attachments BOOLEAN DEFAULT false;
        ALTER TABLE mails ADD COLUMN IF NOT EXISTS size_bytes INTEGER DEFAULT 0;
        ALTER TABLE mails ADD COLUMN IF NOT EXISTS organization_id INTEGER DEFAULT 1;
        
        -- 컬럼 코멘트 추가
        COMMENT ON COLUMN mails.mail_id IS '메일 고유 ID';
        COMMENT ON COLUMN mails.sender_uuid IS '발송자 UUID';
        COMMENT ON COLUMN mails.recipient_emails IS '수신자 이메일 목록';
        COMMENT ON COLUMN mails.cc_emails IS 'CC 이메일 목록';
        COMMENT ON COLUMN mails.bcc_emails IS 'BCC 이메일 목록';
        COMMENT ON COLUMN mails.reply_to IS '답장 주소';
        COMMENT ON COLUMN mails.message_id IS '메시지 ID';
        COMMENT ON COLUMN mails.in_reply_to IS '답장 대상 메시지 ID';
        COMMENT ON COLUMN mails.mail_references IS '참조 메시지 ID들';
        COMMENT ON COLUMN mails.has_attachments IS '첨부파일 존재 여부';
        COMMENT ON COLUMN mails.size_bytes IS '메일 크기 (바이트)';
        COMMENT ON COLUMN mails.organization_id IS '조직 ID';
        """
        execute_sql(conn, mails_fix_sql, "mails 테이블 수정")
        
        # 3. users 테이블 수정
        print("\n📋 3. users 테이블 수정")
        users_fix_sql = """
        -- organization_id 컬럼 추가
        ALTER TABLE users ADD COLUMN IF NOT EXISTS organization_id INTEGER DEFAULT 1;
        
        -- 기본 조직에 모든 사용자 할당
        UPDATE users SET organization_id = 1 WHERE organization_id IS NULL;
        
        -- 컬럼 코멘트 추가
        COMMENT ON COLUMN users.organization_id IS '조직 ID';
        """
        execute_sql(conn, users_fix_sql, "users 테이블 수정")
        
        # 4. mail_users 테이블 수정
        print("\n📋 4. mail_users 테이블 수정")
        mail_users_fix_sql = """
        -- organization_id 컬럼 추가
        ALTER TABLE mail_users ADD COLUMN IF NOT EXISTS organization_id INTEGER DEFAULT 1;
        
        -- 기본 조직에 모든 메일 사용자 할당
        UPDATE mail_users SET organization_id = 1 WHERE organization_id IS NULL;
        
        -- 컬럼 코멘트 추가
        COMMENT ON COLUMN mail_users.organization_id IS '조직 ID';
        """
        execute_sql(conn, mail_users_fix_sql, "mail_users 테이블 수정")
        
        # 5. 기본 데이터 업데이트
        print("\n📋 5. 기본 데이터 업데이트")
        default_data_sql = """
        -- mails 테이블의 organization_id 업데이트
        UPDATE mails SET organization_id = 1 WHERE organization_id IS NULL;
        
        -- mail_id가 없는 메일에 UUID 생성
        UPDATE mails SET mail_id = gen_random_uuid()::text WHERE mail_id IS NULL OR mail_id = '';
        """
        execute_sql(conn, default_data_sql, "기본 데이터 업데이트")
        
        # 6. 외래키 제약조건 추가
        print("\n📋 6. 외래키 제약조건 추가")
        foreign_keys_sql = """
        -- users 테이블의 organization_id 외래키
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.table_constraints 
                WHERE constraint_name = 'users_organization_id_fkey'
            ) THEN
                ALTER TABLE users ADD CONSTRAINT users_organization_id_fkey 
                FOREIGN KEY (organization_id) REFERENCES organizations(id);
            END IF;
        END $$;
        
        -- mail_users 테이블의 organization_id 외래키
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.table_constraints 
                WHERE constraint_name = 'mail_users_organization_id_fkey'
            ) THEN
                ALTER TABLE mail_users ADD CONSTRAINT mail_users_organization_id_fkey 
                FOREIGN KEY (organization_id) REFERENCES organizations(id);
            END IF;
        END $$;
        
        -- mails 테이블의 organization_id 외래키
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.table_constraints 
                WHERE constraint_name = 'mails_organization_id_fkey'
            ) THEN
                ALTER TABLE mails ADD CONSTRAINT mails_organization_id_fkey 
                FOREIGN KEY (organization_id) REFERENCES organizations(id);
            END IF;
        END $$;
        
        -- mails 테이블의 sender_uuid 외래키
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.table_constraints 
                WHERE constraint_name = 'mails_sender_uuid_fkey'
            ) THEN
                ALTER TABLE mails ADD CONSTRAINT mails_sender_uuid_fkey 
                FOREIGN KEY (sender_uuid) REFERENCES mail_users(user_uuid);
            END IF;
        END $$;
        
        -- refresh_tokens 테이블의 user_uuid 외래키
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.table_constraints 
                WHERE constraint_name = 'refresh_tokens_user_uuid_fkey'
            ) THEN
                ALTER TABLE refresh_tokens ADD CONSTRAINT refresh_tokens_user_uuid_fkey 
                FOREIGN KEY (user_uuid) REFERENCES users(id);
            END IF;
        END $$;
        """
        execute_sql(conn, foreign_keys_sql, "외래키 제약조건 추가")
        
        # 7. 인덱스 추가
        print("\n📋 7. 인덱스 추가")
        indexes_sql = """
        -- mails 테이블 인덱스
        CREATE INDEX IF NOT EXISTS ix_mails_mail_id ON mails(mail_id);
        CREATE INDEX IF NOT EXISTS ix_mails_sender_uuid ON mails(sender_uuid);
        CREATE INDEX IF NOT EXISTS ix_mails_organization_id ON mails(organization_id);
        CREATE INDEX IF NOT EXISTS ix_mails_status ON mails(status);
        CREATE INDEX IF NOT EXISTS ix_mails_sent_at ON mails(sent_at);
        
        -- users 테이블 인덱스
        CREATE INDEX IF NOT EXISTS ix_users_organization_id ON users(organization_id);
        
        -- mail_users 테이블 인덱스
        CREATE INDEX IF NOT EXISTS ix_mail_users_organization_id ON mail_users(organization_id);
        """
        execute_sql(conn, indexes_sql, "인덱스 추가")
        
        # 8. organization_settings 테이블 생성
        print("\n📋 8. organization_settings 테이블 생성")
        org_settings_sql = """
        CREATE TABLE IF NOT EXISTS organization_settings (
            id SERIAL PRIMARY KEY,
            organization_id INTEGER NOT NULL REFERENCES organizations(id),
            setting_key VARCHAR(100) NOT NULL,
            setting_value TEXT,
            data_type VARCHAR(20) DEFAULT 'string',
            description TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            UNIQUE(organization_id, setting_key)
        );
        
        -- 인덱스 추가
        CREATE INDEX IF NOT EXISTS ix_organization_settings_organization_id ON organization_settings(organization_id);
        CREATE INDEX IF NOT EXISTS ix_organization_settings_setting_key ON organization_settings(setting_key);
        
        -- 컬럼 코멘트 추가
        COMMENT ON TABLE organization_settings IS '조직 설정 모델';
        COMMENT ON COLUMN organization_settings.organization_id IS '조직 ID';
        COMMENT ON COLUMN organization_settings.setting_key IS '설정 키';
        COMMENT ON COLUMN organization_settings.setting_value IS '설정 값';
        COMMENT ON COLUMN organization_settings.data_type IS '데이터 타입';
        COMMENT ON COLUMN organization_settings.description IS '설정 설명';
        """
        execute_sql(conn, org_settings_sql, "organization_settings 테이블 생성")
        
        # 9. organization_usage 테이블 생성
        print("\n📋 9. organization_usage 테이블 생성")
        org_usage_sql = """
        CREATE TABLE IF NOT EXISTS organization_usage (
            id SERIAL PRIMARY KEY,
            organization_id INTEGER NOT NULL REFERENCES organizations(id),
            usage_date DATE NOT NULL,
            emails_sent INTEGER DEFAULT 0,
            emails_received INTEGER DEFAULT 0,
            storage_used_mb INTEGER DEFAULT 0,
            active_users INTEGER DEFAULT 0,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            UNIQUE(organization_id, usage_date)
        );
        
        -- 인덱스 추가
        CREATE INDEX IF NOT EXISTS ix_organization_usage_organization_id ON organization_usage(organization_id);
        CREATE INDEX IF NOT EXISTS ix_organization_usage_usage_date ON organization_usage(usage_date);
        
        -- 컬럼 코멘트 추가
        COMMENT ON TABLE organization_usage IS '조직 사용량 모델';
        COMMENT ON COLUMN organization_usage.organization_id IS '조직 ID';
        COMMENT ON COLUMN organization_usage.usage_date IS '사용량 날짜';
        COMMENT ON COLUMN organization_usage.emails_sent IS '발송 메일 수';
        COMMENT ON COLUMN organization_usage.emails_received IS '수신 메일 수';
        COMMENT ON COLUMN organization_usage.storage_used_mb IS '사용 저장공간 (MB)';
        COMMENT ON COLUMN organization_usage.active_users IS '활성 사용자 수';
        """
        execute_sql(conn, org_usage_sql, "organization_usage 테이블 생성")
        
        print("\n✅ 완전한 마이그레이션 완료!")
        
    except Exception as e:
        print(f"❌ 마이그레이션 중 오류: {e}")
        conn.rollback()
    
    finally:
        conn.close()

if __name__ == "__main__":
    complete_migration()