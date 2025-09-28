#!/usr/bin/env python3
"""
user_model.py와 데이터베이스 테이블 간의 차이점을 수정하는 마이그레이션 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from app.config import settings
import uuid

def migrate_user_table():
    """users 테이블을 user_model.py와 일치하도록 수정합니다."""
    
    try:
        # 데이터베이스 연결
        engine = create_engine(settings.DATABASE_URL)
        
        with engine.connect() as conn:
            print("=== Users 테이블 마이그레이션 시작 ===")
            
            # 트랜잭션 시작
            trans = conn.begin()
            
            try:
                # 1. user_id 컬럼명 변경 (id -> user_id)
                print("1. 컬럼명 변경: id -> user_id")
                conn.execute(text("ALTER TABLE users RENAME COLUMN id TO user_id"))
                
                # 2. user_uuid에 기본값 설정 (NULL인 경우 UUID 생성)
                print("2. user_uuid NULL 값들을 UUID로 업데이트")
                conn.execute(text("""
                    UPDATE users 
                    SET user_uuid = gen_random_uuid()::text 
                    WHERE user_uuid IS NULL
                """))
                
                # user_uuid를 NOT NULL로 변경하고 기본값 설정
                print("3. user_uuid 컬럼을 NOT NULL로 변경")
                conn.execute(text("ALTER TABLE users ALTER COLUMN user_uuid SET NOT NULL"))
                
                # 4. is_active 기본값 설정
                print("4. is_active 기본값 설정")
                conn.execute(text("ALTER TABLE users ALTER COLUMN is_active SET DEFAULT true"))
                conn.execute(text("UPDATE users SET is_active = true WHERE is_active IS NULL"))
                conn.execute(text("ALTER TABLE users ALTER COLUMN is_active SET NOT NULL"))
                
                # 5. is_email_verified 기본값 설정
                print("5. is_email_verified 기본값 설정")
                conn.execute(text("ALTER TABLE users ALTER COLUMN is_email_verified SET DEFAULT false"))
                conn.execute(text("UPDATE users SET is_email_verified = false WHERE is_email_verified IS NULL"))
                conn.execute(text("ALTER TABLE users ALTER COLUMN is_email_verified SET NOT NULL"))
                
                # 6. role 기본값 설정
                print("6. role 기본값 설정")
                conn.execute(text("ALTER TABLE users ALTER COLUMN role SET DEFAULT 'user'"))
                conn.execute(text("UPDATE users SET role = 'user' WHERE role IS NULL"))
                conn.execute(text("ALTER TABLE users ALTER COLUMN role SET NOT NULL"))
                
                # 7. updated_at 컬럼에 onupdate 트리거 생성
                print("7. updated_at 자동 업데이트 트리거 생성")
                
                # 트리거 함수 생성
                conn.execute(text("""
                    CREATE OR REPLACE FUNCTION update_updated_at_column()
                    RETURNS TRIGGER AS $$
                    BEGIN
                        NEW.updated_at = CURRENT_TIMESTAMP;
                        RETURN NEW;
                    END;
                    $$ language 'plpgsql';
                """))
                
                # 기존 트리거가 있다면 삭제
                conn.execute(text("DROP TRIGGER IF EXISTS update_users_updated_at ON users"))
                
                # 새 트리거 생성
                conn.execute(text("""
                    CREATE TRIGGER update_users_updated_at
                        BEFORE UPDATE ON users
                        FOR EACH ROW
                        EXECUTE FUNCTION update_updated_at_column();
                """))
                
                # 8. 인덱스 확인 및 생성
                print("8. 필요한 인덱스 생성")
                
                # user_uuid 인덱스 (이미 unique 제약조건이 있으므로 확인만)
                result = conn.execute(text("""
                    SELECT indexname FROM pg_indexes 
                    WHERE tablename = 'users' AND indexname LIKE '%user_uuid%'
                """))
                if not result.fetchone():
                    conn.execute(text("CREATE UNIQUE INDEX idx_users_user_uuid ON users(user_uuid)"))
                    print("   - user_uuid 인덱스 생성됨")
                
                # email 인덱스
                result = conn.execute(text("""
                    SELECT indexname FROM pg_indexes 
                    WHERE tablename = 'users' AND indexname LIKE '%email%' 
                    AND indexname NOT LIKE '%unique%'
                """))
                if not result.fetchone():
                    conn.execute(text("CREATE INDEX idx_users_email ON users(email)"))
                    print("   - email 인덱스 생성됨")
                
                # username 인덱스
                result = conn.execute(text("""
                    SELECT indexname FROM pg_indexes 
                    WHERE tablename = 'users' AND indexname LIKE '%username%'
                    AND indexname NOT LIKE '%unique%'
                """))
                if not result.fetchone():
                    conn.execute(text("CREATE INDEX idx_users_username ON users(username)"))
                    print("   - username 인덱스 생성됨")
                
                # 트랜잭션 커밋
                trans.commit()
                print("✅ Users 테이블 마이그레이션 완료!")
                
            except Exception as e:
                # 오류 발생 시 롤백
                trans.rollback()
                raise e
                
    except Exception as e:
        print(f'❌ 마이그레이션 오류: {str(e)}')
        import traceback
        traceback.print_exc()
        return False
    
    return True

def verify_migration():
    """마이그레이션 결과를 확인합니다."""
    
    try:
        engine = create_engine(settings.DATABASE_URL)
        
        with engine.connect() as conn:
            print("\n=== 마이그레이션 결과 확인 ===")
            
            # 테이블 구조 확인
            result = conn.execute(text("""
                SELECT 
                    column_name, 
                    data_type, 
                    is_nullable,
                    column_default
                FROM information_schema.columns 
                WHERE table_name = 'users' 
                ORDER BY ordinal_position
            """))
            
            columns = result.fetchall()
            print("Users 테이블 구조:")
            for col in columns:
                nullable = "NULL" if col[2] == "YES" else "NOT NULL"
                default = f" DEFAULT {col[3]}" if col[3] else ""
                print(f'  - {col[0]}: {col[1]} {nullable}{default}')
            
            # 인덱스 확인
            result = conn.execute(text("""
                SELECT indexname, indexdef 
                FROM pg_indexes 
                WHERE tablename = 'users'
                ORDER BY indexname
            """))
            
            indexes = result.fetchall()
            print("\n인덱스 목록:")
            for idx in indexes:
                print(f'  - {idx[0]}')
            
            # 트리거 확인
            result = conn.execute(text("""
                SELECT trigger_name 
                FROM information_schema.triggers 
                WHERE event_object_table = 'users'
            """))
            
            triggers = result.fetchall()
            print("\n트리거 목록:")
            for trigger in triggers:
                print(f'  - {trigger[0]}')
                
    except Exception as e:
        print(f'❌ 확인 중 오류: {str(e)}')

if __name__ == "__main__":
    print("user_model.py와 데이터베이스 동기화 마이그레이션을 시작합니다...")
    
    if migrate_user_table():
        verify_migration()
        print("\n🎉 마이그레이션이 성공적으로 완료되었습니다!")
    else:
        print("\n💥 마이그레이션이 실패했습니다.")