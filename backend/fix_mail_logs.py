#!/usr/bin/env python3
"""
MailLog 테이블에 org_id 컬럼을 추가하는 스크립트
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def main():
    """메인 함수"""
    try:
        # 데이터베이스 연결 정보
        conn_params = {
            'host': 'localhost',
            'port': 5432,
            'database': 'skybootmail',
            'user': 'postgres',
            'password': 'safe70!!'
        }
        
        # 데이터베이스 연결
        conn = psycopg2.connect(**conn_params)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        print("🔗 데이터베이스 연결 성공")
        
        # 1. mail_logs 테이블 현재 구조 확인
        print("\n📋 mail_logs 테이블 현재 구조 확인...")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'mail_logs' 
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        print("현재 컬럼들:")
        for col in columns:
            print(f"  - {col[0]}: {col[1]} ({'NULL' if col[2] == 'YES' else 'NOT NULL'})")
        
        # org_id 컬럼이 이미 있는지 확인
        has_org_id = any(col[0] == 'org_id' for col in columns)
        
        if has_org_id:
            print("✅ org_id 컬럼이 이미 존재합니다.")
            return
        
        # 2. 기존 데이터 확인
        print("\n📊 기존 mail_logs 데이터 확인...")
        cursor.execute("SELECT COUNT(*) FROM mail_logs;")
        count = cursor.fetchone()[0]
        print(f"기존 mail_logs 레코드 수: {count}")
        
        # 3. org_id 컬럼 추가 (nullable로 먼저 추가)
        print("\n🔧 org_id 컬럼 추가 중...")
        cursor.execute("ALTER TABLE mail_logs ADD COLUMN org_id VARCHAR(36);")
        print("✅ org_id 컬럼 추가 완료")
        
        # 4. 기존 데이터가 있다면 org_id 값 설정
        if count > 0:
            print("\n🔄 기존 데이터의 org_id 값 설정 중...")
            cursor.execute("""
                UPDATE mail_logs 
                SET org_id = (
                    SELECT m.org_id 
                    FROM mails m 
                    WHERE m.mail_uuid = mail_logs.mail_uuid
                )
                WHERE org_id IS NULL;
            """)
            
            # 업데이트된 레코드 수 확인
            cursor.execute("SELECT COUNT(*) FROM mail_logs WHERE org_id IS NOT NULL;")
            updated_count = cursor.fetchone()[0]
            print(f"✅ {updated_count}개 레코드의 org_id 값 설정 완료")
            
            # org_id가 NULL인 레코드가 있는지 확인
            cursor.execute("SELECT COUNT(*) FROM mail_logs WHERE org_id IS NULL;")
            null_count = cursor.fetchone()[0]
            if null_count > 0:
                print(f"⚠️ {null_count}개 레코드의 org_id가 여전히 NULL입니다.")
                print("해당 레코드들을 기본 조직으로 설정합니다...")
                
                # 기본 조직 ID 가져오기
                cursor.execute("SELECT org_id FROM organizations LIMIT 1;")
                result = cursor.fetchone()
                
                if result:
                    default_org_id = result[0]
                    cursor.execute("""
                        UPDATE mail_logs 
                        SET org_id = %s 
                        WHERE org_id IS NULL;
                    """, (default_org_id,))
                    print(f"✅ NULL 레코드들을 기본 조직 {default_org_id}로 설정 완료")
        
        # 5. org_id 컬럼을 NOT NULL로 변경
        print("\n🔒 org_id 컬럼을 NOT NULL로 변경 중...")
        cursor.execute("ALTER TABLE mail_logs ALTER COLUMN org_id SET NOT NULL;")
        print("✅ org_id 컬럼 NOT NULL 제약 조건 추가 완료")
        
        # 6. 외래 키 제약 조건 추가
        print("\n🔗 외래 키 제약 조건 추가 중...")
        cursor.execute("""
            ALTER TABLE mail_logs 
            ADD CONSTRAINT fk_mail_logs_org_id 
            FOREIGN KEY (org_id) REFERENCES organizations(org_id);
        """)
        print("✅ 외래 키 제약 조건 추가 완료")
        
        # 7. 최종 확인
        print("\n📋 최종 mail_logs 테이블 구조 확인...")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'mail_logs' 
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        print("최종 컬럼들:")
        for col in columns:
            print(f"  - {col[0]}: {col[1]} ({'NULL' if col[2] == 'YES' else 'NOT NULL'})")
        
        print("\n🎉 mail_logs 테이블 org_id 컬럼 추가 작업 완료!")
        
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        sys.exit(1)
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main()