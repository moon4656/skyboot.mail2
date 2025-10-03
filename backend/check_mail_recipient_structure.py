#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mail_recipients 테이블 구조 확인 스크립트
"""

import psycopg2
from datetime import datetime

def check_mail_recipient_structure():
    """mail_recipients 테이블 구조를 확인합니다."""
    print("mail_recipients table structure check started")
    print(f"Check time: {datetime.now()}")
    print("=" * 60)
    
    try:
        # 데이터베이스 연결
        conn = psycopg2.connect(
            host="localhost",
            database="skyboot_mail",
            user="skyboot_user",
            password="skyboot_pass",
            port="5432"
        )
        cursor = conn.cursor()
        
        # mail_recipients 테이블 구조 확인
        print("Checking mail_recipients table structure...")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'mail_recipients' 
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        if columns:
            print(f"mail_recipients table structure ({len(columns)} columns):")
            for col in columns:
                print(f"   - {col[0]}: {col[1]} (nullable: {col[2]}, default: {col[3]})")
        else:
            print("mail_recipients table does not exist!")
        
        print()
        
        # 샘플 데이터 확인
        print("Checking mail_recipients table data...")
        cursor.execute("SELECT COUNT(*) FROM mail_recipients;")
        count = cursor.fetchone()[0]
        print(f"Total recipients count: {count}")
        
        if count > 0:
            cursor.execute("SELECT * FROM mail_recipients LIMIT 5;")
            rows = cursor.fetchall()
            print("Sample data (max 5 rows):")
            for row in rows:
                print(f"   {row}")
        
        cursor.close()
        conn.close()
        
        print("mail_recipients table structure check completed!")
        
    except Exception as e:
        print(f"Error occurred: {e}")

if __name__ == "__main__":
    check_mail_recipient_structure()