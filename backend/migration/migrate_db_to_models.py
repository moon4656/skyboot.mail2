#!/usr/bin/env python3
"""
데이터베이스를 모델 파일에 맞게 마이그레이션하는 스크립트
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

def migrate_database():
    """데이터베이스를 모델에 맞게 마이그레이션합니다."""
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        print("🚀 데이터베이스 마이그레이션 시작...")
        
        # 1. organizations 테이블 생성
        print("\n📋 1. organizations 테이블 생성")
        organizations_sql = """
        CREATE TABLE IF NOT EXISTS organizations (
            org_id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
            org_code VARCHAR(50) UNIQUE NOT NULL,
            name VARCHAR(200) NOT NULL,
            display_name VARCHAR(200),
            description TEXT,
            domain VARCHAR(100),
            subdomain VARCHAR(50) UNIQUE NOT NULL,
            admin_email VARCHAR(255) NOT NULL,
            admin_name VARCHAR(100),
            phone VARCHAR(20),
            address TEXT,
            max_users INTEGER DEFAULT 10,
            max_storage_gb INTEGER DEFAULT 10,
            max_emails_per_day INTEGER DEFAULT 1000,
            status VARCHAR(20) DEFAULT 'trial',
            is_active BOOLEAN DEFAULT true,
            trial_ends_at TIMESTAMP WITH TIME ZONE,
            features TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            deleted_at TIMESTAMP WITH TIME ZONE
        );
        
        COMMENT ON TABLE organizations IS '조직/기업 모델 - SaaS의 핵심 테넌트';
        COMMENT ON COLUMN organizations.org_id IS '조직 고유 ID';
        COMMENT ON COLUMN organizations.org_code IS '조직 코드 (subdomain용)';
        COMMENT ON COLUMN organizations.name IS '조직명';
        COMMENT ON COLUMN organizations.display_name IS '표시용 조직명';
        COMMENT ON COLUMN organizations.description IS '조직 설명';
        COMMENT ON COLUMN organizations.domain IS '메일 도메인 (예: company.com)';
        COMMENT ON COLUMN organizations.subdomain IS '서브도메인 (예: company)';
        COMMENT ON COLUMN organizations.admin_email IS '관리자 이메일';
        COMMENT ON COLUMN organizations.admin_name IS '관리자 이름';
        COMMENT ON COLUMN organizations.phone IS '연락처';
        COMMENT ON COLUMN organizations.address IS '주소';
        COMMENT ON COLUMN organizations.max_users IS '최대 사용자 수';
        COMMENT ON COLUMN organizations.max_storage_gb IS '최대 저장 용량(GB)';
        COMMENT ON COLUMN organizations.max_emails_per_day IS '일일 최대 메일 발송 수';
        COMMENT ON COLUMN organizations.status IS '조직 상태';
        COMMENT ON COLUMN organizations.is_active IS '활성 상태';
        COMMENT ON COLUMN organizations.trial_ends_at IS '체험판 종료일';
        COMMENT ON COLUMN organizations.features IS '활성화된 기능 목록 JSON';
        COMMENT ON COLUMN organizations.created_at IS '생성 시간';
        COMMENT ON COLUMN organizations.updated_at IS '수정 시간';
        COMMENT ON COLUMN organizations.deleted_at IS '삭제 시간';
        
        CREATE INDEX IF NOT EXISTS ix_organizations_org_code ON organizations(org_code);
        CREATE INDEX IF NOT EXISTS ix_organizations_subdomain ON organizations(subdomain);
        CREATE INDEX IF NOT EXISTS ix_organizations_status ON organizations(status);
        """
        execute_sql(conn, organizations_sql, "organizations 테이블 생성")
        
        # 2. organization_settings 테이블 생성
        print("\n📋 2. organization_settings 테이블 생성")
        org_settings_sql = """
        CREATE TABLE IF NOT EXISTS organization_settings (
            id SERIAL PRIMARY KEY,
            org_id VARCHAR(36) NOT NULL REFERENCES organizations(org_id),
            setting_key VARCHAR(100) NOT NULL,
            setting_value TEXT,
            setting_type VARCHAR(20) DEFAULT 'string',
            description VARCHAR(500),
            is_public BOOLEAN DEFAULT false,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            CONSTRAINT unique_org_setting UNIQUE(org_id, setting_key)
        );
        
        COMMENT ON TABLE organization_settings IS '조직별 상세 설정';
        COMMENT ON COLUMN organization_settings.org_id IS '조직 ID';
        COMMENT ON COLUMN organization_settings.setting_key IS '설정 키';
        COMMENT ON COLUMN organization_settings.setting_value IS '설정 값';
        COMMENT ON COLUMN organization_settings.setting_type IS '설정 타입 (string, number, boolean, json)';
        COMMENT ON COLUMN organization_settings.description IS '설정 설명';
        COMMENT ON COLUMN organization_settings.is_public IS '공개 설정 여부';
        COMMENT ON COLUMN organization_settings.created_at IS '생성 시간';
        COMMENT ON COLUMN organization_settings.updated_at IS '수정 시간';
        """
        execute_sql(conn, org_settings_sql, "organization_settings 테이블 생성")
        
        # 3. organization_usage 테이블 생성
        print("\n📋 3. organization_usage 테이블 생성")
        org_usage_sql = """
        CREATE TABLE IF NOT EXISTS organization_usage (
            id SERIAL PRIMARY KEY,
            org_id VARCHAR(36) NOT NULL REFERENCES organizations(org_id),
            usage_date TIMESTAMP WITH TIME ZONE NOT NULL,
            current_users INTEGER DEFAULT 0,
            current_storage_gb INTEGER DEFAULT 0,
            emails_sent_today INTEGER DEFAULT 0,
            emails_received_today INTEGER DEFAULT 0,
            total_emails_sent INTEGER DEFAULT 0,
            total_emails_received INTEGER DEFAULT 0,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            CONSTRAINT unique_org_usage_date UNIQUE(org_id, usage_date)
        );
        
        COMMENT ON TABLE organization_usage IS '조직 사용량 추적';
        COMMENT ON COLUMN organization_usage.org_id IS '조직 ID';
        COMMENT ON COLUMN organization_usage.usage_date IS '사용량 기준일';
        COMMENT ON COLUMN organization_usage.current_users IS '현재 사용자 수';
        COMMENT ON COLUMN organization_usage.current_storage_gb IS '현재 저장 용량(GB)';
        COMMENT ON COLUMN organization_usage.emails_sent_today IS '오늘 발송된 메일 수';
        COMMENT ON COLUMN organization_usage.emails_received_today IS '오늘 수신된 메일 수';
        COMMENT ON COLUMN organization_usage.total_emails_sent IS '총 발송 메일 수';
        COMMENT ON COLUMN organization_usage.total_emails_received IS '총 수신 메일 수';
        COMMENT ON COLUMN organization_usage.created_at IS '생성 시간';
        COMMENT ON COLUMN organization_usage.updated_at IS '수정 시간';
        """
        execute_sql(conn, org_usage_sql, "organization_usage 테이블 생성")
        
        # 4. 기본 조직 데이터 삽입
        print("\n📋 4. 기본 조직 데이터 삽입")
        default_org_sql = """
        INSERT INTO organizations (org_id, org_code, name, subdomain, admin_email, admin_name)
        VALUES ('default-org-id', 'default', 'Default Organization', 'default', 'admin@skyboot.com', 'System Admin')
        ON CONFLICT (org_code) DO NOTHING;
        """
        execute_sql(conn, default_org_sql, "기본 조직 데이터 삽입")
        
        # 5. users 테이블 수정
        print("\n📋 5. users 테이블 수정")
        users_modify_sql = """
        -- org_id 컬럼 추가 (기본값으로 default-org-id 설정)
        ALTER TABLE users ADD COLUMN IF NOT EXISTS org_id VARCHAR(36) DEFAULT 'default-org-id';
        
        -- 외래키 제약조건 추가
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.table_constraints 
                WHERE constraint_name = 'users_org_id_fkey'
            ) THEN
                ALTER TABLE users ADD CONSTRAINT users_org_id_fkey 
                FOREIGN KEY (org_id) REFERENCES organizations(org_id);
            END IF;
        END $$;
        
        -- 기존 데이터의 org_id 업데이트
        UPDATE users SET org_id = 'default-org-id' WHERE org_id IS NULL;
        
        -- org_id를 NOT NULL로 변경
        ALTER TABLE users ALTER COLUMN org_id SET NOT NULL;
        
        -- 추가 컬럼들
        ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(50) DEFAULT 'user';
        ALTER TABLE users ADD COLUMN IF NOT EXISTS permissions TEXT;
        ALTER TABLE users ADD COLUMN IF NOT EXISTS is_email_verified BOOLEAN DEFAULT false;
        ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMP WITH TIME ZONE;
        
        -- 고유 제약조건 추가
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.table_constraints 
                WHERE constraint_name = 'unique_org_email'
            ) THEN
                ALTER TABLE users ADD CONSTRAINT unique_org_email UNIQUE(org_id, email);
            END IF;
        END $$;
        
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.table_constraints 
                WHERE constraint_name = 'unique_org_username'
            ) THEN
                ALTER TABLE users ADD CONSTRAINT unique_org_username UNIQUE(org_id, username);
            END IF;
        END $$;
        
        -- 컬럼 코멘트 추가
        COMMENT ON COLUMN users.org_id IS '소속 조직 ID';
        COMMENT ON COLUMN users.role IS '사용자 역할 (admin, user, viewer)';
        COMMENT ON COLUMN users.permissions IS '권한 JSON';
        COMMENT ON COLUMN users.is_email_verified IS '이메일 인증 여부';
        COMMENT ON COLUMN users.last_login_at IS '마지막 로그인 시간';
        """
        execute_sql(conn, users_modify_sql, "users 테이블 수정")
        
        # 6. mail_users 테이블 수정
        print("\n📋 6. mail_users 테이블 수정")
        mail_users_modify_sql = """
        -- 기존 테이블 구조 확인 후 수정
        ALTER TABLE mail_users ADD COLUMN IF NOT EXISTS org_id VARCHAR(36) DEFAULT 'default-org-id';
        ALTER TABLE mail_users ADD COLUMN IF NOT EXISTS display_name VARCHAR(100);
        ALTER TABLE mail_users ADD COLUMN IF NOT EXISTS signature TEXT;
        ALTER TABLE mail_users ADD COLUMN IF NOT EXISTS auto_reply_enabled BOOLEAN DEFAULT false;
        ALTER TABLE mail_users ADD COLUMN IF NOT EXISTS auto_reply_message TEXT;
        ALTER TABLE mail_users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT true;
        ALTER TABLE mail_users ADD COLUMN IF NOT EXISTS storage_used_mb INTEGER DEFAULT 0;
        ALTER TABLE mail_users ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
        ALTER TABLE mail_users ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
        
        -- user_id를 VARCHAR(50)으로 변경
        ALTER TABLE mail_users ALTER COLUMN user_id TYPE VARCHAR(50);
        
        -- 기존 데이터의 org_id 업데이트
        UPDATE mail_users SET org_id = 'default-org-id' WHERE org_id IS NULL;
        
        -- org_id를 NOT NULL로 변경
        ALTER TABLE mail_users ALTER COLUMN org_id SET NOT NULL;
        
        -- 외래키 제약조건 추가
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.table_constraints 
                WHERE constraint_name = 'mail_users_org_id_fkey'
            ) THEN
                ALTER TABLE mail_users ADD CONSTRAINT mail_users_org_id_fkey 
                FOREIGN KEY (org_id) REFERENCES organizations(org_id);
            END IF;
        END $$;
        
        -- 고유 제약조건 추가
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.table_constraints 
                WHERE constraint_name = 'unique_org_mail_email'
            ) THEN
                ALTER TABLE mail_users ADD CONSTRAINT unique_org_mail_email UNIQUE(org_id, email);
            END IF;
        END $$;
        
        -- 컬럼 코멘트 추가
        COMMENT ON COLUMN mail_users.user_id IS '연결된 사용자 ID';
        COMMENT ON COLUMN mail_users.user_uuid IS '사용자 UUID';
        COMMENT ON COLUMN mail_users.org_id IS '소속 조직 ID';
        COMMENT ON COLUMN mail_users.email IS '이메일 주소';
        COMMENT ON COLUMN mail_users.display_name IS '표시 이름';
        COMMENT ON COLUMN mail_users.signature IS '메일 서명';
        COMMENT ON COLUMN mail_users.auto_reply_enabled IS '자동 응답 활성화';
        COMMENT ON COLUMN mail_users.auto_reply_message IS '자동 응답 메시지';
        COMMENT ON COLUMN mail_users.is_active IS '활성 상태';
        COMMENT ON COLUMN mail_users.storage_used_mb IS '사용 중인 저장 용량(MB)';
        COMMENT ON COLUMN mail_users.created_at IS '생성 시간';
        COMMENT ON COLUMN mail_users.updated_at IS '수정 시간';
        """
        execute_sql(conn, mail_users_modify_sql, "mail_users 테이블 수정")
        
        # 7. mails 테이블 수정
        print("\n📋 7. mails 테이블 수정")
        mails_modify_sql = """
        -- 새로운 컬럼들 추가
        ALTER TABLE mails ADD COLUMN IF NOT EXISTS mail_id VARCHAR(50) UNIQUE;
        ALTER TABLE mails ADD COLUMN IF NOT EXISTS org_id VARCHAR(36) DEFAULT 'default-org-id';
        ALTER TABLE mails ADD COLUMN IF NOT EXISTS sender_uuid VARCHAR(36);
        ALTER TABLE mails ADD COLUMN IF NOT EXISTS message_id VARCHAR(255) UNIQUE;
        ALTER TABLE mails ADD COLUMN IF NOT EXISTS in_reply_to VARCHAR(255);
        ALTER TABLE mails ADD COLUMN IF NOT EXISTS references TEXT;
        
        -- 기존 컬럼 타입 수정
        ALTER TABLE mails ALTER COLUMN priority TYPE VARCHAR(10);
        ALTER TABLE mails ALTER COLUMN status TYPE VARCHAR(20);
        
        -- 기본값 설정
        UPDATE mails SET org_id = 'default-org-id' WHERE org_id IS NULL;
        UPDATE mails SET priority = 'normal' WHERE priority IS NULL;
        UPDATE mails SET status = 'draft' WHERE status IS NULL;
        UPDATE mails SET is_draft = false WHERE is_draft IS NULL;
        
        -- mail_id 생성 (기존 데이터용)
        UPDATE mails SET mail_id = 'mail_' || id::text WHERE mail_id IS NULL;
        
        -- org_id를 NOT NULL로 변경
        ALTER TABLE mails ALTER COLUMN org_id SET NOT NULL;
        
        -- 외래키 제약조건 추가
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.table_constraints 
                WHERE constraint_name = 'mails_org_id_fkey'
            ) THEN
                ALTER TABLE mails ADD CONSTRAINT mails_org_id_fkey 
                FOREIGN KEY (org_id) REFERENCES organizations(org_id);
            END IF;
        END $$;
        
        -- 인덱스 추가
        CREATE INDEX IF NOT EXISTS ix_mails_mail_id ON mails(mail_id);
        CREATE INDEX IF NOT EXISTS ix_mails_sender_uuid ON mails(sender_uuid);
        CREATE INDEX IF NOT EXISTS ix_mails_org_id ON mails(org_id);
        
        -- 컬럼 코멘트 추가
        COMMENT ON COLUMN mails.mail_id IS '메일 ID (년월일_시분초_uuid)';
        COMMENT ON COLUMN mails.org_id IS '소속 조직 ID';
        COMMENT ON COLUMN mails.sender_uuid IS '발송자 UUID';
        COMMENT ON COLUMN mails.subject IS '메일 제목';
        COMMENT ON COLUMN mails.body_text IS '메일 본문 (텍스트)';
        COMMENT ON COLUMN mails.body_html IS '메일 본문 (HTML)';
        COMMENT ON COLUMN mails.priority IS '우선순위';
        COMMENT ON COLUMN mails.status IS '메일 상태';
        COMMENT ON COLUMN mails.is_draft IS '임시보관함 여부';
        COMMENT ON COLUMN mails.message_id IS '메시지 ID';
        COMMENT ON COLUMN mails.in_reply_to IS '답장 대상 메시지 ID';
        COMMENT ON COLUMN mails.references IS '참조 메시지 ID들';
        COMMENT ON COLUMN mails.sent_at IS '발송 시간';
        COMMENT ON COLUMN mails.created_at IS '생성 시간';
        COMMENT ON COLUMN mails.updated_at IS '수정 시간';
        """
        execute_sql(conn, mails_modify_sql, "mails 테이블 수정")
        
        print("\n✅ 데이터베이스 마이그레이션 1단계 완료!")
        
    except Exception as e:
        print(f"❌ 마이그레이션 중 오류: {e}")
        conn.rollback()
    
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()