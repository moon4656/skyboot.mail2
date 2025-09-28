#!/usr/bin/env python3
"""
데이터베이스 재생성 스크립트
한글 문자 처리를 위해 UTF-8 collation으로 데이터베이스를 재생성합니다.
"""

import psycopg2
from sqlalchemy import create_engine, text
import sys

def recreate_database():
    """UTF-8 collation으로 데이터베이스를 재생성합니다."""
    
    # 관리자 권한으로 PostgreSQL에 연결
    admin_url = 'postgresql://postgres:postgres@localhost:5432/postgres'
    admin_engine = create_engine(admin_url)

    print('현재 데이터베이스 목록 및 인코딩 설정:')
    with admin_engine.connect() as conn:
        result = conn.execute(text("""
            SELECT datname, encoding, datcollate, datctype 
            FROM pg_database 
            WHERE datname LIKE '%skyboot%' OR datname = 'postgres'
        """))
        for row in result:
            print(f'DB: {row[0]}, Encoding: {row[1]}, Collate: {row[2]}, Ctype: {row[3]}')

    print('\n새로운 UTF-8 데이터베이스 생성 시도...')
    try:
        with admin_engine.connect() as conn:
            # autocommit 모드로 설정
            conn.execute(text("COMMIT"))
            
            # 기존 연결 종료
            print('기존 연결 종료 중...')
            conn.execute(text("""
                SELECT pg_terminate_backend(pid) 
                FROM pg_stat_activity 
                WHERE datname = 'skyboot.mail' AND pid <> pg_backend_pid()
            """))
            
            # 기존 데이터베이스 백업 (이름 변경)
            print('기존 데이터베이스 백업 중...')
            conn.execute(text('ALTER DATABASE "skyboot.mail" RENAME TO "skyboot.mail.backup"'))
            
            # 새로운 UTF-8 데이터베이스 생성
            print('새로운 UTF-8 데이터베이스 생성 중...')
            conn.execute(text("""
                CREATE DATABASE "skyboot.mail" 
                WITH ENCODING='UTF8' 
                LC_COLLATE='C' 
                LC_CTYPE='C' 
                TEMPLATE=template0
            """))
            
            print('✅ 새로운 UTF-8 데이터베이스 생성 완료')
            
            # 새 데이터베이스 설정 확인
            result = conn.execute(text("""
                SELECT datname, encoding, datcollate, datctype 
                FROM pg_database 
                WHERE datname = 'skyboot.mail'
            """))
            for row in result:
                print(f'새 DB: {row[0]}, Encoding: {row[1]}, Collate: {row[2]}, Ctype: {row[3]}')
            
            return True
            
    except Exception as e:
        print(f'❌ 데이터베이스 생성 실패: {e}')
        print('기존 데이터베이스를 사용합니다.')
        return False

if __name__ == "__main__":
    success = recreate_database()
    if success:
        print('\n데이터베이스 재생성이 완료되었습니다.')
        print('이제 서버를 재시작하고 테이블을 다시 생성해야 합니다.')
    else:
        print('\n데이터베이스 재생성에 실패했습니다.')
        sys.exit(1)