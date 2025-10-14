#!/usr/bin/env python3
"""
mail_recipients 테이블에 recipient_uuid 컬럼을 추가하는 스크립트
"""

import psycopg2
from app.config import SaaSSettings

def add_recipient_uuid_column():
    """mail_recipients 테이블에 recipient_uuid 컬럼을 추가합니다."""
    settings = SaaSSettings()
    
    try:
        conn = psycopg2.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            database=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD
        )
        cursor = conn.cursor()
        
        # recipient_uuid 컬럼이 이미 존재하는지 확인
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'mail_recipients' 
                AND column_name = 'recipient_uuid'
            );
        """)
        
        column_exists = cursor.fetchone()[0]
        
        if column_exists:
            print('✅ recipient_uuid 컬럼이 이미 존재합니다.')
        else:
            print('📋 recipient_uuid 컬럼을 추가합니다...')
            
            # recipient_uuid 컬럼 추가
            cursor.execute("""
                ALTER TABLE mail_recipients 
                ADD COLUMN recipient_uuid VARCHAR(50);
            """)
            
            # 컬럼 코멘트 추가
            cursor.execute("""
                COMMENT ON COLUMN mail_recipients.recipient_uuid 
                IS '수신자 UUID (mail_users.user_uuid 참조)';
            """)
            
            # 외래키 제약조건 추가 (선택사항 - mail_users 테이블이 존재하는 경우)
            try:
                cursor.execute("""
                    ALTER TABLE mail_recipients 
                    ADD CONSTRAINT mail_recipients_recipient_uuid_fkey 
                    FOREIGN KEY (recipient_uuid) REFERENCES mail_users(user_uuid);
                """)
                print('✅ 외래키 제약조건도 추가되었습니다.')
            except Exception as fk_error:
                print(f'⚠️ 외래키 제약조건 추가 실패 (무시 가능): {fk_error}')
            
            conn.commit()
            print('✅ recipient_uuid 컬럼이 성공적으로 추가되었습니다.')
        
        # 업데이트된 테이블 구조 확인
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'mail_recipients'
            ORDER BY ordinal_position;
        """)
        
        print('\n📋 업데이트된 mail_recipients 테이블 구조:')
        for row in cursor.fetchall():
            print(f'  - {row[0]}: {row[1]} (nullable: {row[2]}, default: {row[3]})')
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f'❌ 오류: {e}')

if __name__ == "__main__":
    add_recipient_uuid_column()