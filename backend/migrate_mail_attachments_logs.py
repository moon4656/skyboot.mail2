#!/usr/bin/env python3
"""
mail_attachments와 mail_logs 테이블에 mail_uuid 컬럼을 추가하고 데이터를 마이그레이션하는 스크립트

이 스크립트는 다음 작업을 수행합니다:
1. mail_attachments 테이블에 mail_uuid 컬럼 추가
2. mail_logs 테이블에 mail_uuid 컬럼 추가  
3. 기존 mail_id 데이터를 mail_uuid로 마이그레이션
4. 외래 키 제약 조건 추가
5. 기존 mail_id 컬럼 삭제
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 데이터베이스 연결 설정
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'skyboot_mail'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'password')
}

def execute_sql(cursor, sql, description):
    """SQL 실행 및 결과 출력"""
    try:
        print(f"🔄 {description}...")
        cursor.execute(sql)
        print(f"✅ {description} 완료")
        return True
    except Exception as e:
        print(f"❌ {description} 실패: {e}")
        return False

def main():
    """메인 함수"""
    try:
        # 데이터베이스 연결
        print("📊 데이터베이스 연결 중...")
        conn = psycopg2.connect(**DB_CONFIG)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        print("✅ 데이터베이스 연결 성공")
        
        # 1. mail_attachments 테이블 마이그레이션
        print("\n🔧 mail_attachments 테이블 마이그레이션 중...")
        
        # mail_uuid 컬럼이 이미 있는지 확인
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'mail_attachments' AND column_name = 'mail_uuid'
        """)
        has_mail_uuid = cursor.fetchone()
        
        if not has_mail_uuid:
            # mail_uuid 컬럼 추가
            execute_sql(cursor,
                "ALTER TABLE mail_attachments ADD COLUMN mail_uuid VARCHAR(50);",
                "mail_attachments에 mail_uuid 컬럼 추가")
            
            # 데이터 마이그레이션 (mail_id -> mail_uuid)
            # mail_id가 이미 mail_uuid 형태라고 가정
            execute_sql(cursor,
                "UPDATE mail_attachments SET mail_uuid = mail_id;",
                "mail_attachments 데이터 마이그레이션")
            
            # NOT NULL 제약 조건 추가
            execute_sql(cursor,
                "ALTER TABLE mail_attachments ALTER COLUMN mail_uuid SET NOT NULL;",
                "mail_attachments.mail_uuid NOT NULL 제약 조건 추가")
            
            # 외래 키 제약 조건 추가
            execute_sql(cursor,
                """ALTER TABLE mail_attachments 
                   ADD CONSTRAINT fk_mail_attachments_mail_uuid 
                   FOREIGN KEY (mail_uuid) REFERENCES mails(mail_uuid);""",
                "mail_attachments 외래 키 제약 조건 추가")
            
            # 기존 mail_id 컬럼 삭제
            execute_sql(cursor,
                "ALTER TABLE mail_attachments DROP COLUMN mail_id;",
                "mail_attachments.mail_id 컬럼 삭제")
        else:
            print("✅ mail_attachments.mail_uuid 컬럼이 이미 존재합니다.")
        
        # 2. mail_logs 테이블 마이그레이션
        print("\n🔧 mail_logs 테이블 마이그레이션 중...")
        
        # mail_uuid 컬럼이 이미 있는지 확인
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'mail_logs' AND column_name = 'mail_uuid'
        """)
        has_mail_uuid = cursor.fetchone()
        
        if not has_mail_uuid:
            # mail_uuid 컬럼 추가
            execute_sql(cursor,
                "ALTER TABLE mail_logs ADD COLUMN mail_uuid VARCHAR(50);",
                "mail_logs에 mail_uuid 컬럼 추가")
            
            # 데이터 마이그레이션 (mail_id -> mail_uuid)
            execute_sql(cursor,
                "UPDATE mail_logs SET mail_uuid = mail_id;",
                "mail_logs 데이터 마이그레이션")
            
            # NOT NULL 제약 조건 추가
            execute_sql(cursor,
                "ALTER TABLE mail_logs ALTER COLUMN mail_uuid SET NOT NULL;",
                "mail_logs.mail_uuid NOT NULL 제약 조건 추가")
            
            # 외래 키 제약 조건 추가
            execute_sql(cursor,
                """ALTER TABLE mail_logs 
                   ADD CONSTRAINT fk_mail_logs_mail_uuid 
                   FOREIGN KEY (mail_uuid) REFERENCES mails(mail_uuid);""",
                "mail_logs 외래 키 제약 조건 추가")
            
            # 기존 mail_id 컬럼 삭제
            execute_sql(cursor,
                "ALTER TABLE mail_logs DROP COLUMN mail_id;",
                "mail_logs.mail_id 컬럼 삭제")
        else:
            print("✅ mail_logs.mail_uuid 컬럼이 이미 존재합니다.")
        
        # 3. 마이그레이션 결과 확인
        print("\n🔍 마이그레이션 결과 확인 중...")
        
        # 테이블 구조 확인
        for table_name in ['mail_attachments', 'mail_logs']:
            print(f"\n📋 {table_name} 테이블 구조:")
            cursor.execute("""
                SELECT 
                    column_name,
                    data_type,
                    character_maximum_length,
                    is_nullable
                FROM information_schema.columns 
                WHERE table_name = %s
                AND column_name LIKE '%mail%'
                ORDER BY ordinal_position;
            """, (table_name,))
            
            columns = cursor.fetchall()
            for col in columns:
                length_info = f"({col[2]})" if col[2] else ""
                nullable = "NULL" if col[3] == "YES" else "NOT NULL"
                print(f"  {col[0]}: {col[1]}{length_info} {nullable}")
        
        # 외래 키 제약 조건 확인
        print(f"\n🔗 외래 키 제약 조건:")
        cursor.execute("""
            SELECT 
                tc.table_name,
                tc.constraint_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu 
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage ccu 
                ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_name IN ('mail_attachments', 'mail_logs')
            ORDER BY tc.table_name, tc.constraint_name;
        """)
        
        fks = cursor.fetchall()
        for fk in fks:
            print(f"  {fk[0]}.{fk[2]} -> {fk[3]}.{fk[4]} ({fk[1]})")
        
        # 샘플 데이터 확인
        print("\n📊 샘플 데이터 확인:")
        
        # mail_attachments 샘플
        cursor.execute("SELECT id, mail_uuid, filename FROM mail_attachments LIMIT 3;")
        attachments = cursor.fetchall()
        print(f"mail_attachments 샘플: {attachments}")
        
        # mail_logs 샘플
        cursor.execute("SELECT id, mail_uuid, action FROM mail_logs LIMIT 3;")
        logs = cursor.fetchall()
        print(f"mail_logs 샘플: {logs}")
        
        print("\n✅ 마이그레이션 완료!")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
        print("🔌 데이터베이스 연결 종료")

if __name__ == "__main__":
    main()