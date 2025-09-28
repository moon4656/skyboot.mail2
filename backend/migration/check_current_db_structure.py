#!/usr/bin/env python3
"""
현재 데이터베이스 테이블 구조를 확인하는 스크립트
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

def get_db_connection():
    """데이터베이스 연결을 반환합니다."""
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
            database=os.getenv("DB_NAME", "skyboot_mail"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "")
        )
        return conn
    except Exception as e:
        print(f"❌ 데이터베이스 연결 실패: {e}")
        return None

def check_table_structure():
    """현재 데이터베이스의 테이블 구조를 확인합니다."""
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # 모든 테이블 목록 조회
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name;
            """)
            tables = cursor.fetchall()
            
            print("📊 현재 데이터베이스 테이블 목록:")
            print("=" * 50)
            
            for table in tables:
                table_name = table['table_name']
                print(f"\n🔹 테이블: {table_name}")
                
                # 테이블의 컬럼 정보 조회
                cursor.execute("""
                    SELECT 
                        column_name,
                        data_type,
                        is_nullable,
                        column_default,
                        character_maximum_length,
                        numeric_precision,
                        numeric_scale
                    FROM information_schema.columns 
                    WHERE table_name = %s 
                    ORDER BY ordinal_position;
                """, (table_name,))
                
                columns = cursor.fetchall()
                
                for col in columns:
                    nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                    data_type = col['data_type']
                    
                    if col['character_maximum_length']:
                        data_type += f"({col['character_maximum_length']})"
                    elif col['numeric_precision']:
                        if col['numeric_scale']:
                            data_type += f"({col['numeric_precision']},{col['numeric_scale']})"
                        else:
                            data_type += f"({col['numeric_precision']})"
                    
                    default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
                    
                    print(f"  - {col['column_name']}: {data_type} {nullable}{default}")
                
                # 인덱스 정보 조회
                cursor.execute("""
                    SELECT 
                        indexname,
                        indexdef
                    FROM pg_indexes 
                    WHERE tablename = %s;
                """, (table_name,))
                
                indexes = cursor.fetchall()
                if indexes:
                    print(f"  📋 인덱스:")
                    for idx in indexes:
                        print(f"    - {idx['indexname']}")
                
                # 외래키 정보 조회
                cursor.execute("""
                    SELECT
                        tc.constraint_name,
                        kcu.column_name,
                        ccu.table_name AS foreign_table_name,
                        ccu.column_name AS foreign_column_name
                    FROM information_schema.table_constraints AS tc
                    JOIN information_schema.key_column_usage AS kcu
                        ON tc.constraint_name = kcu.constraint_name
                    JOIN information_schema.constraint_column_usage AS ccu
                        ON ccu.constraint_name = tc.constraint_name
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                        AND tc.table_name = %s;
                """, (table_name,))
                
                foreign_keys = cursor.fetchall()
                if foreign_keys:
                    print(f"  🔗 외래키:")
                    for fk in foreign_keys:
                        print(f"    - {fk['column_name']} -> {fk['foreign_table_name']}.{fk['foreign_column_name']}")
                
                print("-" * 30)
    
    except Exception as e:
        print(f"❌ 테이블 구조 확인 중 오류: {e}")
    
    finally:
        conn.close()

if __name__ == "__main__":
    print("🔍 현재 데이터베이스 테이블 구조 확인 중...")
    check_table_structure()
    print("\n✅ 테이블 구조 확인 완료!")