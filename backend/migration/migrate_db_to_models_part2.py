#!/usr/bin/env python3
"""
데이터베이스를 모델 파일에 맞게 마이그레이션하는 스크립트 (2단계)
메일 관련 테이블들을 생성합니다.
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

def migrate_mail_tables():
    """메일 관련 테이블들을 생성합니다."""
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        print("🚀 메일 테이블 마이그레이션 시작...")
        
        # 1. mail_recipients 테이블 생성
        print("\n📋 1. mail_recipients 테이블 생성")
        mail_recipients_sql = """
        CREATE TABLE IF NOT EXISTS mail_recipients (
            id BIGSERIAL PRIMARY KEY,
            mail_id VARCHAR(50) NOT NULL,
            recipient_id VARCHAR(36) NOT NULL,
            recipient_type VARCHAR(10) DEFAULT 'to',
            is_read BOOLEAN DEFAULT false,
            read_at TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        -- 외래키 제약조건 추가 (mail_id는 나중에 추가)
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.table_constraints 
                WHERE constraint_name = 'mail_recipients_recipient_id_fkey'
            ) THEN
                ALTER TABLE mail_recipients ADD CONSTRAINT mail_recipients_recipient_id_fkey 
                FOREIGN KEY (recipient_id) REFERENCES mail_users(user_uuid);
            END IF;
        END $$;
        
        -- 인덱스 추가
        CREATE INDEX IF NOT EXISTS ix_mail_recipients_mail_id ON mail_recipients(mail_id);
        CREATE INDEX IF NOT EXISTS ix_mail_recipients_recipient_id ON mail_recipients(recipient_id);
        CREATE INDEX IF NOT EXISTS ix_mail_recipients_is_read ON mail_recipients(is_read);
        
        -- 컬럼 코멘트 추가
        COMMENT ON TABLE mail_recipients IS '메일 수신자 모델';
        COMMENT ON COLUMN mail_recipients.mail_id IS '메일 ID';
        COMMENT ON COLUMN mail_recipients.recipient_id IS '수신자 UUID';
        COMMENT ON COLUMN mail_recipients.recipient_type IS '수신자 타입';
        COMMENT ON COLUMN mail_recipients.is_read IS '읽음 여부';
        COMMENT ON COLUMN mail_recipients.read_at IS '읽은 시간';
        COMMENT ON COLUMN mail_recipients.created_at IS '생성 시간';
        """
        execute_sql(conn, mail_recipients_sql, "mail_recipients 테이블 생성")
        
        # 2. mail_attachments 테이블 생성
        print("\n📋 2. mail_attachments 테이블 생성")
        mail_attachments_sql = """
        CREATE TABLE IF NOT EXISTS mail_attachments (
            id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
            attachment_uuid VARCHAR(36) UNIQUE DEFAULT gen_random_uuid()::text,
            mail_id VARCHAR(50) NOT NULL,
            filename VARCHAR(255) NOT NULL,
            original_filename VARCHAR(255) NOT NULL,
            file_path VARCHAR(500) NOT NULL,
            file_size INTEGER NOT NULL,
            content_type VARCHAR(100),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        -- 인덱스 추가
        CREATE INDEX IF NOT EXISTS ix_mail_attachments_mail_id ON mail_attachments(mail_id);
        CREATE INDEX IF NOT EXISTS ix_mail_attachments_attachment_uuid ON mail_attachments(attachment_uuid);
        
        -- 컬럼 코멘트 추가
        COMMENT ON TABLE mail_attachments IS '메일 첨부파일 모델';
        COMMENT ON COLUMN mail_attachments.attachment_uuid IS '첨부파일 UUID';
        COMMENT ON COLUMN mail_attachments.mail_id IS '메일 ID';
        COMMENT ON COLUMN mail_attachments.filename IS '파일명';
        COMMENT ON COLUMN mail_attachments.original_filename IS '원본 파일명';
        COMMENT ON COLUMN mail_attachments.file_path IS '파일 경로';
        COMMENT ON COLUMN mail_attachments.file_size IS '파일 크기';
        COMMENT ON COLUMN mail_attachments.content_type IS '콘텐츠 타입';
        COMMENT ON COLUMN mail_attachments.created_at IS '생성 시간';
        """
        execute_sql(conn, mail_attachments_sql, "mail_attachments 테이블 생성")
        
        # 3. mail_folders 테이블 생성
        print("\n📋 3. mail_folders 테이블 생성")
        mail_folders_sql = """
        CREATE TABLE IF NOT EXISTS mail_folders (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(50) NOT NULL,
            name VARCHAR(100) NOT NULL,
            folder_type VARCHAR(20) DEFAULT 'custom',
            parent_id INTEGER REFERENCES mail_folders(id),
            is_system BOOLEAN DEFAULT false,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        -- 외래키 제약조건 추가
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.table_constraints 
                WHERE constraint_name = 'mail_folders_user_id_fkey'
            ) THEN
                ALTER TABLE mail_folders ADD CONSTRAINT mail_folders_user_id_fkey 
                FOREIGN KEY (user_id) REFERENCES mail_users(user_id);
            END IF;
        END $$;
        
        -- 인덱스 추가
        CREATE INDEX IF NOT EXISTS ix_mail_folders_user_id ON mail_folders(user_id);
        CREATE INDEX IF NOT EXISTS ix_mail_folders_folder_type ON mail_folders(folder_type);
        CREATE INDEX IF NOT EXISTS ix_mail_folders_parent_id ON mail_folders(parent_id);
        
        -- 컬럼 코멘트 추가
        COMMENT ON TABLE mail_folders IS '메일 폴더 모델';
        COMMENT ON COLUMN mail_folders.user_id IS '사용자 ID';
        COMMENT ON COLUMN mail_folders.name IS '폴더명';
        COMMENT ON COLUMN mail_folders.folder_type IS '폴더 타입';
        COMMENT ON COLUMN mail_folders.parent_id IS '상위 폴더 ID';
        COMMENT ON COLUMN mail_folders.is_system IS '시스템 폴더 여부';
        COMMENT ON COLUMN mail_folders.created_at IS '생성 시간';
        COMMENT ON COLUMN mail_folders.updated_at IS '수정 시간';
        """
        execute_sql(conn, mail_folders_sql, "mail_folders 테이블 생성")
        
        # 4. mail_in_folders 테이블 생성
        print("\n📋 4. mail_in_folders 테이블 생성")
        mail_in_folders_sql = """
        CREATE TABLE IF NOT EXISTS mail_in_folders (
            id BIGSERIAL PRIMARY KEY,
            mail_id VARCHAR(50) NOT NULL,
            folder_id INTEGER NOT NULL REFERENCES mail_folders(id),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        -- 인덱스 추가
        CREATE INDEX IF NOT EXISTS ix_mail_in_folders_mail_id ON mail_in_folders(mail_id);
        CREATE INDEX IF NOT EXISTS ix_mail_in_folders_folder_id ON mail_in_folders(folder_id);
        
        -- 컬럼 코멘트 추가
        COMMENT ON TABLE mail_in_folders IS '메일-폴더 관계 모델';
        COMMENT ON COLUMN mail_in_folders.mail_id IS '메일 ID';
        COMMENT ON COLUMN mail_in_folders.folder_id IS '폴더 ID';
        COMMENT ON COLUMN mail_in_folders.created_at IS '생성 시간';
        """
        execute_sql(conn, mail_in_folders_sql, "mail_in_folders 테이블 생성")
        
        # 5. mail_logs 테이블 생성
        print("\n📋 5. mail_logs 테이블 생성")
        mail_logs_sql = """
        CREATE TABLE IF NOT EXISTS mail_logs (
            id BIGSERIAL PRIMARY KEY,
            mail_id VARCHAR(50) NOT NULL,
            user_uuid VARCHAR(36),
            action VARCHAR(50) NOT NULL,
            details TEXT,
            ip_address VARCHAR(45),
            user_agent VARCHAR(500),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        -- 외래키 제약조건 추가
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.table_constraints 
                WHERE constraint_name = 'mail_logs_user_uuid_fkey'
            ) THEN
                ALTER TABLE mail_logs ADD CONSTRAINT mail_logs_user_uuid_fkey 
                FOREIGN KEY (user_uuid) REFERENCES mail_users(user_uuid);
            END IF;
        END $$;
        
        -- 인덱스 추가
        CREATE INDEX IF NOT EXISTS ix_mail_logs_mail_id ON mail_logs(mail_id);
        CREATE INDEX IF NOT EXISTS ix_mail_logs_user_uuid ON mail_logs(user_uuid);
        CREATE INDEX IF NOT EXISTS ix_mail_logs_action ON mail_logs(action);
        CREATE INDEX IF NOT EXISTS ix_mail_logs_created_at ON mail_logs(created_at);
        
        -- 컬럼 코멘트 추가
        COMMENT ON TABLE mail_logs IS '메일 로그 모델';
        COMMENT ON COLUMN mail_logs.mail_id IS '메일 ID';
        COMMENT ON COLUMN mail_logs.user_uuid IS '사용자 UUID';
        COMMENT ON COLUMN mail_logs.action IS '수행된 작업';
        COMMENT ON COLUMN mail_logs.details IS '상세 정보';
        COMMENT ON COLUMN mail_logs.ip_address IS 'IP 주소';
        COMMENT ON COLUMN mail_logs.user_agent IS '사용자 에이전트';
        COMMENT ON COLUMN mail_logs.created_at IS '생성 시간';
        """
        execute_sql(conn, mail_logs_sql, "mail_logs 테이블 생성")
        
        # 6. refresh_tokens 테이블 수정
        print("\n📋 6. refresh_tokens 테이블 수정")
        refresh_tokens_modify_sql = """
        -- user_id를 user_uuid로 변경
        ALTER TABLE refresh_tokens RENAME COLUMN user_id TO user_uuid;
        
        -- 외래키 제약조건 추가
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.table_constraints 
                WHERE constraint_name = 'refresh_tokens_user_uuid_fkey'
            ) THEN
                ALTER TABLE refresh_tokens ADD CONSTRAINT refresh_tokens_user_uuid_fkey 
                FOREIGN KEY (user_uuid) REFERENCES users(user_uuid);
            END IF;
        END $$;
        """
        execute_sql(conn, refresh_tokens_modify_sql, "refresh_tokens 테이블 수정")
        
        # 7. login_logs 테이블 수정
        print("\n📋 7. login_logs 테이블 수정")
        login_logs_modify_sql = """
        -- 추가 컬럼들
        ALTER TABLE login_logs ADD COLUMN IF NOT EXISTS user_uuid VARCHAR(50);
        ALTER TABLE login_logs ADD COLUMN IF NOT EXISTS email VARCHAR(255) NOT NULL DEFAULT '';
        ALTER TABLE login_logs ADD COLUMN IF NOT EXISTS ip_address VARCHAR(45);
        ALTER TABLE login_logs ADD COLUMN IF NOT EXISTS user_agent TEXT;
        ALTER TABLE login_logs ADD COLUMN IF NOT EXISTS login_status VARCHAR(20) NOT NULL DEFAULT 'failed';
        ALTER TABLE login_logs ADD COLUMN IF NOT EXISTS failure_reason VARCHAR(255);
        ALTER TABLE login_logs ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
        
        -- 컬럼 코멘트 추가
        COMMENT ON COLUMN login_logs.user_uuid IS '사용자 UUID (로그인 성공 시)';
        COMMENT ON COLUMN login_logs.email IS '로그인 시도 이메일';
        COMMENT ON COLUMN login_logs.ip_address IS '클라이언트 IP 주소';
        COMMENT ON COLUMN login_logs.user_agent IS '사용자 에이전트';
        COMMENT ON COLUMN login_logs.login_status IS '로그인 상태 (success, failed)';
        COMMENT ON COLUMN login_logs.failure_reason IS '로그인 실패 사유';
        COMMENT ON COLUMN login_logs.created_at IS '로그인 시도 시간';
        """
        execute_sql(conn, login_logs_modify_sql, "login_logs 테이블 수정")
        
        # 8. 외래키 제약조건 추가 (mail_id 관련)
        print("\n📋 8. 외래키 제약조건 추가")
        foreign_keys_sql = """
        -- mail_recipients의 mail_id 외래키
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.table_constraints 
                WHERE constraint_name = 'mail_recipients_mail_id_fkey'
            ) THEN
                ALTER TABLE mail_recipients ADD CONSTRAINT mail_recipients_mail_id_fkey 
                FOREIGN KEY (mail_id) REFERENCES mails(mail_id);
            END IF;
        END $$;
        
        -- mail_attachments의 mail_id 외래키
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.table_constraints 
                WHERE constraint_name = 'mail_attachments_mail_id_fkey'
            ) THEN
                ALTER TABLE mail_attachments ADD CONSTRAINT mail_attachments_mail_id_fkey 
                FOREIGN KEY (mail_id) REFERENCES mails(mail_id);
            END IF;
        END $$;
        
        -- mail_in_folders의 mail_id 외래키
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.table_constraints 
                WHERE constraint_name = 'mail_in_folders_mail_id_fkey'
            ) THEN
                ALTER TABLE mail_in_folders ADD CONSTRAINT mail_in_folders_mail_id_fkey 
                FOREIGN KEY (mail_id) REFERENCES mails(mail_id);
            END IF;
        END $$;
        
        -- mail_logs의 mail_id 외래키
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.table_constraints 
                WHERE constraint_name = 'mail_logs_mail_id_fkey'
            ) THEN
                ALTER TABLE mail_logs ADD CONSTRAINT mail_logs_mail_id_fkey 
                FOREIGN KEY (mail_id) REFERENCES mails(mail_id);
            END IF;
        END $$;
        
        -- mails의 sender_uuid 외래키
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
        """
        execute_sql(conn, foreign_keys_sql, "외래키 제약조건 추가")
        
        print("\n✅ 메일 테이블 마이그레이션 2단계 완료!")
        
    except Exception as e:
        print(f"❌ 마이그레이션 중 오류: {e}")
        conn.rollback()
    
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_mail_tables()