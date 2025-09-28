#!/usr/bin/env python3
"""
Organization 관련 테이블 구조 확인 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from app.config import settings

def check_organization_tables():
    """Organization 관련 테이블 구조를 확인합니다."""
    try:
        engine = create_engine(settings.DATABASE_URL)
        
        with engine.connect() as conn:
            print("=== Organization 관련 테이블 확인 ===\n")
            
            # 테이블 목록 조회
            tables_query = text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE '%organization%'
                ORDER BY table_name;
            """)
            
            result = conn.execute(tables_query)
            tables = [row[0] for row in result.fetchall()]
            
            if not tables:
                print("❌ Organization 관련 테이블이 존재하지 않습니다.")
                return
            
            print(f"📋 발견된 테이블: {', '.join(tables)}\n")
            
            # 각 테이블의 구조 확인
            for table_name in tables:
                print(f"=== 테이블: {table_name} ===")
                
                # 컬럼 정보 조회
                columns_query = text(f"""
                    SELECT 
                        column_name,
                        data_type,
                        character_maximum_length,
                        is_nullable,
                        column_default,
                        col_description(pgc.oid, ordinal_position) as comment
                    FROM information_schema.columns c
                    LEFT JOIN pg_class pgc ON pgc.relname = c.table_name
                    WHERE table_name = '{table_name}' 
                    AND table_schema = 'public'
                    ORDER BY ordinal_position;
                """)
                
                result = conn.execute(columns_query)
                columns = result.fetchall()
                
                for col in columns:
                    col_name, data_type, max_length, nullable, default, comment = col
                    length_info = f"({max_length})" if max_length else ""
                    null_info = "NULL" if nullable == "YES" else "NOT NULL"
                    default_info = f" DEFAULT {default}" if default else ""
                    comment_info = f" -- {comment}" if comment else ""
                    
                    print(f"  - {col_name}: {data_type}{length_info} {null_info}{default_info}{comment_info}")
                
                # 제약조건 확인
                constraints_query = text(f"""
                    SELECT 
                        tc.constraint_name,
                        tc.constraint_type,
                        kcu.column_name,
                        ccu.table_name AS foreign_table_name,
                        ccu.column_name AS foreign_column_name
                    FROM information_schema.table_constraints tc
                    LEFT JOIN information_schema.key_column_usage kcu 
                        ON tc.constraint_name = kcu.constraint_name
                    LEFT JOIN information_schema.constraint_column_usage ccu 
                        ON ccu.constraint_name = tc.constraint_name
                    WHERE tc.table_name = '{table_name}' 
                    AND tc.table_schema = 'public'
                    ORDER BY tc.constraint_type, tc.constraint_name;
                """)
                
                result = conn.execute(constraints_query)
                constraints = result.fetchall()
                
                if constraints:
                    print("  제약조건:")
                    for constraint in constraints:
                        constraint_name, constraint_type, column_name, foreign_table, foreign_column = constraint
                        if constraint_type == 'FOREIGN KEY':
                            print(f"    - FOREIGN KEY: {constraint_name} ({column_name}) -> {foreign_table}({foreign_column})")
                        elif constraint_type == 'PRIMARY KEY':
                            print(f"    - PRIMARY KEY: {constraint_name} ({column_name})")
                        elif constraint_type == 'UNIQUE':
                            print(f"    - UNIQUE: {constraint_name} ({column_name})")
                        else:
                            print(f"    - {constraint_type}: {constraint_name} ({column_name})")
                
                print()
            
            # 인덱스 확인
            print("=== 인덱스 정보 ===")
            for table_name in tables:
                indexes_query = text(f"""
                    SELECT 
                        indexname,
                        indexdef
                    FROM pg_indexes 
                    WHERE tablename = '{table_name}'
                    AND schemaname = 'public'
                    ORDER BY indexname;
                """)
                
                result = conn.execute(indexes_query)
                indexes = result.fetchall()
                
                if indexes:
                    print(f"테이블 {table_name}의 인덱스:")
                    for index_name, index_def in indexes:
                        print(f"  - {index_name}")
                    print()
    
    except Exception as e:
        print(f"❌ 데이터베이스 연결 오류: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    check_organization_tables()