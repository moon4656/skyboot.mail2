#!/usr/bin/env python3
"""
PostgreSQL 데이터베이스 테이블 확인 스크립트
"""
import psycopg2

def check_postgresql_tables():
    try:
        conn = psycopg2.connect(
            host='172.18.0.1',
            database='skybootmail',
            user='postgres',
            password='safe70!!'
        )
        cur = conn.cursor()
        
        print('=== 현재 데이터베이스 테이블 목록 ===')
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = cur.fetchall()
        for table in tables:
            print(f'테이블: {table[0]}')
        
        print('\n=== 메일 관련 테이블 확인 ===')
        mail_tables = ['organizations', 'users', 'mails', 'mail_users', 'mail_recipients']
        for table_name in mail_tables:
            try:
                cur.execute(f'SELECT COUNT(*) FROM {table_name};')
                count = cur.fetchone()[0]
                print(f'{table_name}: {count}개 레코드')
            except Exception as e:
                print(f'{table_name}: 테이블 없음')
        
        print('\n=== Postfix 가상 테이블 확인 ===')
        postfix_tables = ['virtual_domains', 'virtual_users', 'virtual_aliases']
        for table_name in postfix_tables:
            try:
                cur.execute(f'SELECT COUNT(*) FROM {table_name};')
                count = cur.fetchone()[0]
                print(f'{table_name}: {count}개 레코드')
            except Exception as e:
                print(f'{table_name}: 테이블 없음 - 생성 필요!')
        
        conn.close()
        print('\n✅ 데이터베이스 조회 완료')
        
    except Exception as e:
        print(f'❌ 데이터베이스 연결 실패: {e}')

if __name__ == "__main__":
    check_postgresql_tables()