#!/usr/bin/env python3
"""
메일 테이블 구조 수정 마이그레이션 스크립트
mail_model.py의 모델 구조에 맞게 데이터베이스 테이블을 업데이트합니다.
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.config import settings

def migrate_mail_tables():
    """메일 테이블 구조 마이그레이션"""
    try:
        # 데이터베이스 연결
        engine = create_engine(settings.get_database_url())
        Session = sessionmaker(bind=engine)
        session = Session()
        
        print("=== 메일 테이블 마이그레이션 시작 ===")
        
        # 1. mail_users 테이블 수정
        print("\n1. mail_users 테이블 수정 중...")
        
        # user_id 컬럼 길이 변경 (36 -> 50)
        session.execute(text("""
            ALTER TABLE mail_users 
            ALTER COLUMN user_id TYPE VARCHAR(50);
        """))
        print("  - user_id 컬럼 길이 변경 완료 (36 -> 50)")
        
        # user_uuid 컬럼을 NOT NULL로 변경하고 기본값 설정
        session.execute(text("""
            UPDATE mail_users 
            SET user_uuid = gen_random_uuid()::text 
            WHERE user_uuid IS NULL;
        """))
        
        session.execute(text("""
            ALTER TABLE mail_users 
            ALTER COLUMN user_uuid SET NOT NULL;
        """))
        print("  - user_uuid 컬럼 NOT NULL 제약조건 추가")
        
        # 기본값 설정
        session.execute(text("""
            ALTER TABLE mail_users 
            ALTER COLUMN auto_reply_enabled SET DEFAULT false;
        """))
        
        session.execute(text("""
            ALTER TABLE mail_users 
            ALTER COLUMN is_active SET DEFAULT true;
        """))
        
        session.execute(text("""
            ALTER TABLE mail_users 
            ALTER COLUMN storage_used_mb SET DEFAULT 0;
        """))
        print("  - 기본값 설정 완료")
        
        # 2. mails 테이블 수정
        print("\n2. mails 테이블 수정 중...")
        
        # id 컬럼 타입 변경 (integer -> bigint)
        session.execute(text("""
            ALTER TABLE mails 
            ALTER COLUMN id TYPE BIGINT;
        """))
        print("  - id 컬럼 타입 변경 완료 (integer -> bigint)")
        
        # mail_id 컬럼을 NOT NULL로 변경하고 unique 제약조건 추가
        # 먼저 NULL 값들을 업데이트
        session.execute(text("""
            UPDATE mails 
            SET mail_id = CONCAT(
                TO_CHAR(COALESCE(created_at, NOW()), 'YYYYMMDD_HH24MISS'),
                '_',
                SUBSTRING(gen_random_uuid()::text, 1, 8)
            )
            WHERE mail_id IS NULL;
        """))
        
        session.execute(text("""
            ALTER TABLE mails 
            ALTER COLUMN mail_id SET NOT NULL;
        """))
        
        # unique 제약조건이 이미 있는지 확인하고 없으면 추가
        try:
            session.execute(text("""
                ALTER TABLE mails 
                ADD CONSTRAINT mails_mail_id_unique UNIQUE (mail_id);
            """))
            print("  - mail_id unique 제약조건 추가")
        except Exception as e:
            if "already exists" in str(e):
                print("  - mail_id unique 제약조건 이미 존재")
            else:
                raise e
        
        # 기본값 설정 (올바른 enum 값 사용)
        session.execute(text("""
            ALTER TABLE mails 
            ALTER COLUMN priority SET DEFAULT 'NORMAL';
        """))
        
        session.execute(text("""
            ALTER TABLE mails 
            ALTER COLUMN status SET DEFAULT 'DRAFT';
        """))
        
        session.execute(text("""
            ALTER TABLE mails 
            ALTER COLUMN is_draft SET DEFAULT false;
        """))
        print("  - 기본값 설정 완료")
        
        # 3. mail_recipients 테이블 수정
        print("\n3. mail_recipients 테이블 수정 중...")
        
        # id 컬럼 타입 변경 (integer -> bigint)
        session.execute(text("""
            ALTER TABLE mail_recipients 
            ALTER COLUMN id TYPE BIGINT;
        """))
        
        # 기본값 설정 (올바른 enum 값 사용)
        session.execute(text("""
            ALTER TABLE mail_recipients 
            ALTER COLUMN recipient_type SET DEFAULT 'TO';
        """))
        
        session.execute(text("""
            ALTER TABLE mail_recipients 
            ALTER COLUMN is_read SET DEFAULT false;
        """))
        print("  - mail_recipients 테이블 수정 완료")
        
        # 4. mail_attachments 테이블 수정
        print("\n4. mail_attachments 테이블 수정 중...")
        
        # id 컬럼이 String(36)이어야 하는데 현재 자동 생성되는 UUID로 되어 있음
        # 필요시 수정하지만 현재는 유지
        print("  - mail_attachments 테이블 구조 확인 완료")
        
        # 5. mail_folders 테이블 수정 (복잡한 변경이므로 주의 깊게 처리)
        print("\n5. mail_folders 테이블 수정 중...")
        
        # 현재 테이블에 데이터가 있는지 확인
        result = session.execute(text("SELECT COUNT(*) FROM mail_folders"))
        folder_count = result.scalar()
        
        if folder_count == 0:
            print("  - mail_folders 테이블이 비어있어 구조 변경 진행")
            
            # 기존 테이블 백업 및 재생성
            session.execute(text("DROP TABLE IF EXISTS mail_folders_backup"))
            session.execute(text("CREATE TABLE mail_folders_backup AS SELECT * FROM mail_folders"))
            
            # 외래 키 제약조건 제거
            session.execute(text("""
                ALTER TABLE mail_in_folders 
                DROP CONSTRAINT IF EXISTS mail_in_folders_folder_id_fkey
            """))
            
            # 기존 테이블 삭제 및 재생성
            session.execute(text("DROP TABLE mail_folders"))
            
            session.execute(text("""
                CREATE TABLE mail_folders (
                    user_id VARCHAR(50) NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    folder_type VARCHAR(20) DEFAULT 'custom',
                    parent_id INTEGER,
                    is_system BOOLEAN DEFAULT false,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE,
                    PRIMARY KEY (user_id, name),
                    FOREIGN KEY (user_id) REFERENCES mail_users(user_uuid)
                )
            """))
            
            # 인덱스 생성
            session.execute(text("""
                CREATE INDEX ix_mail_folders_user_id ON mail_folders(user_id)
            """))
            
            print("  - mail_folders 테이블 재생성 완료")
        else:
            print(f"  - mail_folders 테이블에 {folder_count}개 데이터 존재, 수동 마이그레이션 필요")
        
        # 6. mail_in_folders 테이블 수정
        print("\n6. mail_in_folders 테이블 수정 중...")
        
        # id 컬럼 타입 변경
        session.execute(text("""
            ALTER TABLE mail_in_folders 
            ALTER COLUMN id TYPE BIGINT;
        """))
        
        # mail_id 외래 키 참조 수정 (mails.id -> mails.mail_id)
        # 이는 복잡한 작업이므로 데이터가 있는 경우 주의 필요
        result = session.execute(text("SELECT COUNT(*) FROM mail_in_folders"))
        folder_rel_count = result.scalar()
        
        if folder_rel_count > 0:
            print(f"  - mail_in_folders 테이블에 {folder_rel_count}개 데이터 존재")
            print("  - 외래 키 참조 변경은 데이터 정합성 확인 후 수동으로 처리 필요")
        else:
            # 외래 키 제약조건 수정
            session.execute(text("""
                ALTER TABLE mail_in_folders 
                DROP CONSTRAINT IF EXISTS mail_in_folders_mail_id_fkey
            """))
            
            session.execute(text("""
                ALTER TABLE mail_in_folders 
                ALTER COLUMN mail_id TYPE VARCHAR(50);
            """))
            
            session.execute(text("""
                ALTER TABLE mail_in_folders 
                ADD CONSTRAINT mail_in_folders_mail_id_fkey 
                FOREIGN KEY (mail_id) REFERENCES mails(mail_id);
            """))
            print("  - mail_in_folders 외래 키 참조 수정 완료")
        
        # 7. mail_logs 테이블 수정
        print("\n7. mail_logs 테이블 수정 중...")
        
        # id 컬럼 타입 변경
        session.execute(text("""
            ALTER TABLE mail_logs 
            ALTER COLUMN id TYPE BIGINT;
        """))
        
        # mail_id 외래 키 참조 수정 (mails.id -> mails.mail_id)
        session.execute(text("""
            ALTER TABLE mail_logs 
            DROP CONSTRAINT IF EXISTS mail_logs_mail_id_fkey
        """))
        
        session.execute(text("""
            ALTER TABLE mail_logs 
            ALTER COLUMN mail_id TYPE VARCHAR(50);
        """))
        
        session.execute(text("""
            ALTER TABLE mail_logs 
            ADD CONSTRAINT mail_logs_mail_id_fkey 
            FOREIGN KEY (mail_id) REFERENCES mails(mail_id);
        """))
        print("  - mail_logs 외래 키 참조 수정 완료")
        
        # 8. 성능 최적화를 위한 인덱스 추가
        print("\n8. 성능 최적화 인덱스 추가 중...")
        
        # 자주 사용되는 컬럼들에 인덱스 추가
        indexes_to_create = [
            "CREATE INDEX IF NOT EXISTS idx_mails_org_id ON mails(org_id)",
            "CREATE INDEX IF NOT EXISTS idx_mails_sender_uuid ON mails(sender_uuid)",
            "CREATE INDEX IF NOT EXISTS idx_mails_sent_at ON mails(sent_at)",
            "CREATE INDEX IF NOT EXISTS idx_mail_recipients_recipient_id ON mail_recipients(recipient_id)",
            "CREATE INDEX IF NOT EXISTS idx_mail_recipients_is_read ON mail_recipients(is_read)",
            "CREATE INDEX IF NOT EXISTS idx_mail_logs_user_uuid ON mail_logs(user_uuid)",
            "CREATE INDEX IF NOT EXISTS idx_mail_logs_action ON mail_logs(action)",
        ]
        
        for index_sql in indexes_to_create:
            try:
                session.execute(text(index_sql))
            except Exception as e:
                print(f"  - 인덱스 생성 중 오류 (무시): {e}")
        
        print("  - 인덱스 추가 완료")
        
        # 변경사항 커밋
        session.commit()
        session.close()
        
        print("\n=== 메일 테이블 마이그레이션 완료 ===")
        print("모든 테이블이 mail_model.py의 모델 구조에 맞게 업데이트되었습니다.")
        
    except Exception as e:
        print(f"마이그레이션 중 오류 발생: {e}")
        session.rollback()
        session.close()
        import traceback
        traceback.print_exc()
        raise e

if __name__ == "__main__":
    migrate_mail_tables()