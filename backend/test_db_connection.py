#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PostgreSQL 데이터베이스 연결 테스트 스크립트
"""

import os
import sys
import psycopg2
from psycopg2 import sql

def test_postgresql_connection():
    """PostgreSQL 데이터베이스 연결을 테스트합니다."""
    try:
        # 환경 변수 설정
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        
        # 데이터베이스 연결 정보
        connection_params = {
            'host': 'localhost',
            'port': 5432,
            'database': 'skyboot_mail',
            'user': 'postgres',
            'password': 'postgres123'
        }
        
        print("PostgreSQL 연결을 시도합니다...")
        print(f"Host: {connection_params['host']}")
        print(f"Port: {connection_params['port']}")
        print(f"Database: {connection_params['database']}")
        print(f"User: {connection_params['user']}")
        
        # 데이터베이스 연결
        conn = psycopg2.connect(**connection_params)
        cursor = conn.cursor()
        
        # 연결 테스트 쿼리
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✅ PostgreSQL 연결 성공!")
        print(f"PostgreSQL 버전: {version[0]}")
        
        # 기존 테이블 확인
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        
        if tables:
            print(f"\n📋 기존 테이블 목록 ({len(tables)}개):")
            for table in tables:
                print(f"  - {table[0]}")
        else:
            print("\n📋 테이블이 없습니다. 새로 생성해야 합니다.")
        
        cursor.close()
        conn.close()
        return True
        
    except psycopg2.Error as e:
        print(f"❌ PostgreSQL 연결 실패: {e}")
        return False
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        return False

if __name__ == "__main__":
    success = test_postgresql_connection()
    sys.exit(0 if success else 1)