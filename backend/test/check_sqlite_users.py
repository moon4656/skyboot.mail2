#!/usr/bin/env python3
"""
SQLite 테스트 데이터베이스의 테이블 및 사용자 정보를 확인하는 스크립트
"""
import sqlite3
import os
from passlib.context import CryptContext

# 패스워드 해싱 컨텍스트
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def check_sqlite_users():
    """SQLite 데이터베이스의 사용자 정보 확인"""
    db_path = "test_skyboot_mail.db"
    
    if not os.path.exists(db_path):
        print(f"❌ 데이터베이스 파일이 존재하지 않습니다: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 테이블 목록 확인
        print("=== 테이블 목록 ===")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        if tables:
            for table in tables:
                print(f"테이블: {table[0]}")
        else:
            print("❌ 테이블이 없습니다.")
        
        # 각 테이블의 데이터 확인
        for table in tables:
            table_name = table[0]
            print(f"\n=== {table_name} 테이블 데이터 ===")
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            if rows:
                for row in rows:
                    print(f"  {row}")
            else:
                print(f"  {table_name} 테이블이 비어있습니다.")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")

if __name__ == "__main__":
    check_sqlite_users()