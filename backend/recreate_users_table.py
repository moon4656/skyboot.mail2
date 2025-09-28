#!/usr/bin/env python3
"""
users 테이블 재생성 스크립트
- 기존 users 테이블 삭제
- user_model.py 기반으로 새 테이블 생성
- 백업된 데이터 복원
"""

import os
import sys
import json
import psycopg2
from datetime import datetime
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
            password=os.getenv("DB_PASSWORD", "1234")
        )
        return conn
    except Exception as e:
        print(f"❌ 데이터베이스 연결 실패: {e}")
        return None

def drop_existing_tables():
    """기존 테이블들을 삭제합니다."""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cursor:
            print("🗑️ 기존 테이블 삭제를 시작합니다...")
            
            # 외래 키 제약 조건 때문에 순서대로 삭제
            tables_to_drop = [
                "refresh_tokens",
                "login_logs", 
                "users"
            ]
            
            for table in tables_to_drop:
                try:
                    cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
                    print(f"   ✅ {table} 테이블 삭제 완료")
                except Exception as e:
                    print(f"   ⚠️ {table} 테이블 삭제 중 오류: {e}")
            
            conn.commit()
            print("✅ 기존 테이블 삭제 완료!")
            return True
            
    except Exception as e:
        print(f"❌ 테이블 삭제 중 오류 발생: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def create_new_tables():
    """user_model.py 기반으로 새 테이블들을 생성합니다."""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cursor:
            print("🏗️ 새 테이블 생성을 시작합니다...")
            
            # users 테이블 생성 (user_model.py 기반)
            create_users_sql = """
            CREATE TABLE users (
                user_id VARCHAR(50) PRIMARY KEY,
                user_uuid VARCHAR(36) UNIQUE NOT NULL DEFAULT gen_random_uuid()::text,
                org_id VARCHAR(36) NOT NULL,
                email VARCHAR(255) NOT NULL,
                username VARCHAR(100) NOT NULL,
                hashed_password VARCHAR(255) NOT NULL,
                role VARCHAR(50) DEFAULT 'user',
                permissions TEXT,
                is_active BOOLEAN DEFAULT true,
                is_email_verified BOOLEAN DEFAULT false,
                last_login_at TIMESTAMP WITH TIME ZONE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE,
                
                CONSTRAINT unique_org_email UNIQUE (org_id, email),
                CONSTRAINT unique_org_username UNIQUE (org_id, username)
            );
            
            -- 인덱스 생성
            CREATE INDEX idx_users_user_id ON users(user_id);
            CREATE INDEX idx_users_user_uuid ON users(user_uuid);
            CREATE INDEX idx_users_email ON users(email);
            CREATE INDEX idx_users_username ON users(username);
            
            -- 컬럼 코멘트 추가
            COMMENT ON COLUMN users.user_id IS '사용자 ID';
            COMMENT ON COLUMN users.user_uuid IS '사용자 UUID';
            COMMENT ON COLUMN users.org_id IS '소속 조직 ID';
            COMMENT ON COLUMN users.email IS '이메일 주소';
            COMMENT ON COLUMN users.username IS '사용자명';
            COMMENT ON COLUMN users.hashed_password IS '해시된 비밀번호';
            COMMENT ON COLUMN users.role IS '사용자 역할 (admin, user, viewer)';
            COMMENT ON COLUMN users.permissions IS '권한 JSON';
            COMMENT ON COLUMN users.is_active IS '활성 상태';
            COMMENT ON COLUMN users.is_email_verified IS '이메일 인증 여부';
            COMMENT ON COLUMN users.last_login_at IS '마지막 로그인 시간';
            COMMENT ON COLUMN users.created_at IS '생성 시간';
            COMMENT ON COLUMN users.updated_at IS '수정 시간';
            """
            
            cursor.execute(create_users_sql)
            print("   ✅ users 테이블 생성 완료")
            
            # refresh_tokens 테이블 생성
            create_refresh_tokens_sql = """
            CREATE TABLE refresh_tokens (
                id SERIAL PRIMARY KEY,
                user_uuid VARCHAR(36) NOT NULL,
                token VARCHAR(255) UNIQUE NOT NULL,
                expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                is_revoked BOOLEAN DEFAULT false,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE INDEX idx_refresh_tokens_user_uuid ON refresh_tokens(user_uuid);
            CREATE INDEX idx_refresh_tokens_token ON refresh_tokens(token);
            """
            
            cursor.execute(create_refresh_tokens_sql)
            print("   ✅ refresh_tokens 테이블 생성 완료")
            
            # login_logs 테이블 생성
            create_login_logs_sql = """
            CREATE TABLE login_logs (
                id SERIAL PRIMARY KEY,
                user_uuid VARCHAR(50),
                email VARCHAR(255) NOT NULL,
                ip_address VARCHAR(45),
                user_agent TEXT,
                login_status VARCHAR(20) NOT NULL,
                failure_reason VARCHAR(255),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE INDEX idx_login_logs_user_uuid ON login_logs(user_uuid);
            CREATE INDEX idx_login_logs_email ON login_logs(email);
            CREATE INDEX idx_login_logs_created_at ON login_logs(created_at);
            
            -- 컬럼 코멘트 추가
            COMMENT ON COLUMN login_logs.id IS '로그 ID';
            COMMENT ON COLUMN login_logs.user_uuid IS '사용자 UUID (로그인 성공 시)';
            COMMENT ON COLUMN login_logs.email IS '로그인 시도 이메일';
            COMMENT ON COLUMN login_logs.ip_address IS '클라이언트 IP 주소';
            COMMENT ON COLUMN login_logs.user_agent IS '사용자 에이전트';
            COMMENT ON COLUMN login_logs.login_status IS '로그인 상태 (success, failed)';
            COMMENT ON COLUMN login_logs.failure_reason IS '로그인 실패 사유';
            COMMENT ON COLUMN login_logs.created_at IS '로그인 시도 시간';
            """
            
            cursor.execute(create_login_logs_sql)
            print("   ✅ login_logs 테이블 생성 완료")
            
            conn.commit()
            print("✅ 새 테이블 생성 완료!")
            return True
            
    except Exception as e:
        print(f"❌ 테이블 생성 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return False
    finally:
        conn.close()

def restore_backup_data():
    """백업된 데이터를 새 테이블 구조에 맞게 복원합니다."""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        # 가장 최근 백업 파일 찾기
        backup_dir = "table_backups"
        backup_files = [f for f in os.listdir(backup_dir) if f.startswith("users_backup_") and f.endswith(".json")]
        if not backup_files:
            print("❌ 백업 파일을 찾을 수 없습니다.")
            return False
        
        latest_backup = sorted(backup_files)[-1]
        backup_path = os.path.join(backup_dir, latest_backup)
        
        print(f"📥 백업 데이터 복원을 시작합니다: {latest_backup}")
        
        # 백업 데이터 로드
        with open(backup_path, 'r', encoding='utf-8') as f:
            backup_info = json.load(f)
        
        backup_data = backup_info['data']
        print(f"   - 복원할 레코드 수: {len(backup_data)}개")
        
        with conn.cursor() as cursor:
            for user in backup_data:
                # 새 테이블 구조에 맞게 데이터 매핑
                insert_sql = """
                INSERT INTO users (
                    user_id, user_uuid, org_id, email, username, hashed_password,
                    role, is_active, created_at, updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                """
                
                # org_id는 기본값 1로 설정 (organizations 테이블이 있다고 가정)
                org_id = user.get('organization_id', '1')
                if org_id is None:
                    org_id = '1'
                
                values = (
                    user['user_id'],
                    user['user_uuid'],
                    str(org_id),  # org_id는 VARCHAR(36)로 변경됨
                    user['email'],
                    user['username'],
                    user['hashed_password'],
                    'user',  # 기본 역할
                    user.get('is_active', True),
                    user.get('created_at'),
                    user.get('updated_at')
                )
                
                cursor.execute(insert_sql, values)
            
            conn.commit()
            print("✅ 백업 데이터 복원 완료!")
            return True
            
    except Exception as e:
        print(f"❌ 데이터 복원 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return False
    finally:
        conn.close()

def main():
    """메인 실행 함수"""
    print("🚀 users 테이블 재생성 프로세스를 시작합니다...")
    print("=" * 60)
    
    # 1. 기존 테이블 삭제
    if not drop_existing_tables():
        print("💥 테이블 삭제에 실패했습니다.")
        return False
    
    print()
    
    # 2. 새 테이블 생성
    if not create_new_tables():
        print("💥 새 테이블 생성에 실패했습니다.")
        return False
    
    print()
    
    # 3. 백업 데이터 복원
    if not restore_backup_data():
        print("💥 데이터 복원에 실패했습니다.")
        return False
    
    print()
    print("🎉 users 테이블 재생성이 성공적으로 완료되었습니다!")
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)