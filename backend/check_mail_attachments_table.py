#!/usr/bin/env python3
"""
mail_attachments 테이블 구조 확인 스크립트
"""

import psycopg2
from app.config import settings

def check_mail_attachments_table():
    """mail_attachments 테이블의 현재 구조를 확인합니다."""
    try:
        conn = psycopg2.connect(
            host=settings.DB_HOST,
            database=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            port=settings.DB_PORT
        )
        cur = conn.cursor()

        # mail_attachments 테이블 구조 확인
        cur.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'mail_attachments'
            ORDER BY ordinal_position;
        """)

        print('=== mail_attachments 테이블 구조 ===')
        rows = cur.fetchall()
        if rows:
            for row in rows:
                print(f'{row[0]}: {row[1]} (nullable: {row[2]}, default: {row[3]})')
        else:
            print('mail_attachments 테이블이 존재하지 않습니다.')

        # 테이블 존재 여부 확인
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'mail_attachments'
            );
        """)
        
        table_exists = cur.fetchone()[0]
        print(f'\nmail_attachments 테이블 존재 여부: {table_exists}')

        cur.close()
        conn.close()

    except Exception as e:
        print(f"오류 발생: {e}")

if __name__ == "__main__":
    check_mail_attachments_table()