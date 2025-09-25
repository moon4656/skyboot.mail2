#!/usr/bin/env python3
"""
Organization 모델과 데이터베이스 테이블 구조를 동기화하는 마이그레이션 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from app.config import settings

def migrate_organization_tables():
    """Organization 관련 테이블을 모델 구조에 맞게 수정합니다."""
    try:
        engine = create_engine(settings.DATABASE_URL)
        
        with engine.connect() as conn:
            print("🚀 Organization 테이블 마이그레이션 시작...")
            
            # 1. Organizations 테이블 수정
            print("\n📝 Organizations 테이블 수정 중...")
            
            # 1-1. 누락된 컬럼 추가
            print("  - 누락된 컬럼 추가...")
            conn.execute(text("""
                -- name 컬럼 추가 (display_name과 별도)
                ALTER TABLE organizations 
                ADD COLUMN IF NOT EXISTS name VARCHAR(200);
                
                -- description 컬럼 추가
                ALTER TABLE organizations 
                ADD COLUMN IF NOT EXISTS description TEXT;
                
                -- domain 컬럼 추가
                ALTER TABLE organizations 
                ADD COLUMN IF NOT EXISTS domain VARCHAR(100);
                
                -- admin_name 컬럼 추가
                ALTER TABLE organizations 
                ADD COLUMN IF NOT EXISTS admin_name VARCHAR(100);
                
                -- phone 컬럼 추가
                ALTER TABLE organizations 
                ADD COLUMN IF NOT EXISTS phone VARCHAR(20);
                
                -- address 컬럼 추가
                ALTER TABLE organizations 
                ADD COLUMN IF NOT EXISTS address TEXT;
                
                -- trial_ends_at 컬럼 추가
                ALTER TABLE organizations 
                ADD COLUMN IF NOT EXISTS trial_ends_at TIMESTAMP WITH TIME ZONE;
            """))
            
            # 1-2. 기본값 설정
            print("  - 기본값 설정...")
            conn.execute(text("""
                -- max_users 기본값 설정
                ALTER TABLE organizations 
                ALTER COLUMN max_users SET DEFAULT 10;
                
                -- max_storage_gb 기본값 설정
                ALTER TABLE organizations 
                ALTER COLUMN max_storage_gb SET DEFAULT 10;
                
                -- max_emails_per_day 기본값 설정
                ALTER TABLE organizations 
                ALTER COLUMN max_emails_per_day SET DEFAULT 1000;
                
                -- status 기본값 설정
                ALTER TABLE organizations 
                ALTER COLUMN status SET DEFAULT 'trial';
                
                -- is_active 기본값 설정
                ALTER TABLE organizations 
                ALTER COLUMN is_active SET DEFAULT true;
            """))
            
            # 1-3. NULL 값 업데이트
            print("  - NULL 값 업데이트...")
            conn.execute(text("""
                -- NULL 값들을 기본값으로 업데이트
                UPDATE organizations 
                SET 
                    max_users = COALESCE(max_users, 10),
                    max_storage_gb = COALESCE(max_storage_gb, 10),
                    max_emails_per_day = COALESCE(max_emails_per_day, 1000),
                    status = COALESCE(status, 'trial'),
                    is_active = COALESCE(is_active, true),
                    name = COALESCE(name, display_name, org_code);
            """))
            
            # 1-4. NOT NULL 제약조건 추가
            print("  - NOT NULL 제약조건 추가...")
            conn.execute(text("""
                -- name 컬럼을 NOT NULL로 설정
                ALTER TABLE organizations 
                ALTER COLUMN name SET NOT NULL;
            """))
            
            # 2. Organization_settings 테이블 수정
            print("\n📝 Organization_settings 테이블 수정 중...")
            
            # 2-1. 기본값 설정
            print("  - 기본값 설정...")
            conn.execute(text("""
                -- setting_type 기본값 설정
                ALTER TABLE organization_settings 
                ALTER COLUMN setting_type SET DEFAULT 'string';
                
                -- is_public 기본값이 이미 false로 설정되어 있음 확인
                -- updated_at 기본값 설정 (onupdate 트리거는 별도 생성)
                ALTER TABLE organization_settings 
                ALTER COLUMN updated_at SET DEFAULT now();
            """))
            
            # 2-2. NULL 값 업데이트
            print("  - NULL 값 업데이트...")
            conn.execute(text("""
                UPDATE organization_settings 
                SET 
                    setting_type = COALESCE(setting_type, 'string'),
                    is_public = COALESCE(is_public, false);
            """))
            
            # 3. Organization_usage 테이블 수정
            print("\n📝 Organization_usage 테이블 수정 중...")
            
            # 3-1. 컬럼명 변경 및 기본값 설정
            print("  - 컬럼명 변경 및 기본값 설정...")
            conn.execute(text("""
                -- 컬럼명 변경 (모델과 일치시키기)
                -- current_users는 이미 존재
                -- current_storage_gb는 이미 존재
                -- emails_sent_today는 이미 존재
                -- emails_received_today는 이미 존재
                -- total_emails_sent는 이미 존재
                -- total_emails_received는 이미 존재
                
                -- 기본값 설정
                ALTER TABLE organization_usage 
                ALTER COLUMN current_users SET DEFAULT 0;
                
                ALTER TABLE organization_usage 
                ALTER COLUMN current_storage_gb SET DEFAULT 0;
                
                ALTER TABLE organization_usage 
                ALTER COLUMN emails_sent_today SET DEFAULT 0;
                
                ALTER TABLE organization_usage 
                ALTER COLUMN emails_received_today SET DEFAULT 0;
                
                ALTER TABLE organization_usage 
                ALTER COLUMN total_emails_sent SET DEFAULT 0;
                
                ALTER TABLE organization_usage 
                ALTER COLUMN total_emails_received SET DEFAULT 0;
                
                -- updated_at 기본값 설정
                ALTER TABLE organization_usage 
                ALTER COLUMN updated_at SET DEFAULT now();
            """))
            
            # 3-2. NULL 값 업데이트
            print("  - NULL 값 업데이트...")
            conn.execute(text("""
                UPDATE organization_usage 
                SET 
                    current_users = COALESCE(current_users, 0),
                    current_storage_gb = COALESCE(current_storage_gb, 0),
                    emails_sent_today = COALESCE(emails_sent_today, 0),
                    emails_received_today = COALESCE(emails_received_today, 0),
                    total_emails_sent = COALESCE(total_emails_sent, 0),
                    total_emails_received = COALESCE(total_emails_received, 0);
            """))
            
            # 4. updated_at 자동 업데이트 트리거 생성
            print("\n🔧 updated_at 자동 업데이트 트리거 생성...")
            
            # 트리거 함수 생성 (이미 존재할 수 있으므로 OR REPLACE 사용)
            conn.execute(text("""
                CREATE OR REPLACE FUNCTION update_updated_at_column()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.updated_at = now();
                    RETURN NEW;
                END;
                $$ language 'plpgsql';
            """))
            
            # 각 테이블에 트리거 생성
            for table_name in ['organizations', 'organization_settings', 'organization_usage']:
                print(f"  - {table_name} 테이블 트리거 생성...")
                conn.execute(text(f"""
                    DROP TRIGGER IF EXISTS update_{table_name}_updated_at ON {table_name};
                    CREATE TRIGGER update_{table_name}_updated_at
                        BEFORE UPDATE ON {table_name}
                        FOR EACH ROW
                        EXECUTE FUNCTION update_updated_at_column();
                """))
            
            # 5. 인덱스 추가 (성능 최적화)
            print("\n📊 성능 최적화 인덱스 추가...")
            
            # Organizations 테이블 인덱스
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_organizations_status ON organizations(status);
                CREATE INDEX IF NOT EXISTS idx_organizations_is_active ON organizations(is_active);
                CREATE INDEX IF NOT EXISTS idx_organizations_domain ON organizations(domain);
                CREATE INDEX IF NOT EXISTS idx_organizations_created_at ON organizations(created_at);
            """))
            
            # Organization_settings 테이블 인덱스
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_organization_settings_org_id ON organization_settings(org_id);
                CREATE INDEX IF NOT EXISTS idx_organization_settings_key ON organization_settings(setting_key);
                CREATE INDEX IF NOT EXISTS idx_organization_settings_type ON organization_settings(setting_type);
            """))
            
            # Organization_usage 테이블 인덱스
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_organization_usage_org_id ON organization_usage(org_id);
                CREATE INDEX IF NOT EXISTS idx_organization_usage_date ON organization_usage(usage_date);
            """))
            
            # 트랜잭션 커밋
            conn.commit()
            
            print("\n✅ Organization 테이블 마이그레이션 완료!")
            print("\n📋 주요 변경사항:")
            print("  1. Organizations 테이블:")
            print("     - name, description, domain, admin_name, phone, address, trial_ends_at 컬럼 추가")
            print("     - max_users, max_storage_gb, max_emails_per_day, status, is_active 기본값 설정")
            print("     - name 컬럼 NOT NULL 제약조건 추가")
            print("  2. Organization_settings 테이블:")
            print("     - setting_type, is_public 기본값 설정")
            print("     - updated_at 기본값 설정")
            print("  3. Organization_usage 테이블:")
            print("     - 모든 사용량 컬럼 기본값 0 설정")
            print("     - updated_at 기본값 설정")
            print("  4. 모든 테이블에 updated_at 자동 업데이트 트리거 추가")
            print("  5. 성능 최적화를 위한 인덱스 추가")
            
    except Exception as e:
        print(f"❌ 마이그레이션 중 오류 발생: {e}")
        raise

if __name__ == "__main__":
    migrate_organization_tables()