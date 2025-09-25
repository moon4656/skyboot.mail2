#!/usr/bin/env python3
"""
테이블 구조 확인 스크립트
"""

import sys
import os

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.config import settings

def check_table_structure():
    """
    테이블 구조를 확인합니다.
    """
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        print("=== mail_users 테이블 구조 ===")
        result = conn.execute(text("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'mail_users' 
            ORDER BY ordinal_position
        """))
        for row in result:
            nullable = "NULL" if row[2] == "YES" else "NOT NULL"
            print(f"{row[0]}: {row[1]} ({nullable})")
        
        print("\n=== mail_folders 테이블 구조 ===")
        result = conn.execute(text("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'mail_folders' 
            ORDER BY ordinal_position
        """))
        for row in result:
            nullable = "NULL" if row[2] == "YES" else "NOT NULL"
            print(f"{row[0]}: {row[1]} ({nullable})")
        
        print("\n=== mail_recipients 테이블 구조 ===")
        result = conn.execute(text("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'mail_recipients' 
            ORDER BY ordinal_position
        """))
        for row in result:
            nullable = "NULL" if row[2] == "YES" else "NOT NULL"
            print(f"{row[0]}: {row[1]} ({nullable})")
        
        print("\n=== mails 테이블 구조 ===")
        result = conn.execute(text("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'mails' 
            ORDER BY ordinal_position
        """))
        for row in result:
            nullable = "NULL" if row[2] == "YES" else "NOT NULL"
            print(f"{row[0]}: {row[1]} ({nullable})")

if __name__ == "__main__":
    check_table_structure()