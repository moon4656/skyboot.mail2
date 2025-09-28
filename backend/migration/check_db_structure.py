#!/usr/bin/env python3
"""
현재 데이터베이스 테이블 구조를 확인하는 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from app.config import settings

def check_database_structure():
    """현재 데이터베이스의 테이블 구조를 확인합니다."""
    
    try:
        # 데이터베이스 연결
        engine = create_engine(settings.DATABASE_URL)
        
        with engine.connect() as conn:
            # 모든 테이블 목록 조회
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name
            """))
            
            tables = result.fetchall()
            print('=== 현재 데이터베이스 테이블 목록 ===')
            for table in tables:
                print(f'- {table[0]}')
            
            print(f'\n총 {len(tables)}개의 테이블이 존재합니다.\n')
            
            # 각 테이블의 컬럼 정보 확인
            for table in tables:
                table_name = table[0]
                print(f'=== 테이블: {table_name} ===')
                
                # 컬럼 정보 조회
                col_result = conn.execute(text(f"""
                    SELECT 
                        column_name, 
                        data_type, 
                        is_nullable,
                        column_default,
                        character_maximum_length
                    FROM information_schema.columns 
                    WHERE table_name = '{table_name}' 
                    ORDER BY ordinal_position
                """))
                
                columns = col_result.fetchall()
                for col in columns:
                    nullable = "NULL" if col[2] == "YES" else "NOT NULL"
                    default = f" DEFAULT {col[3]}" if col[3] else ""
                    length = f"({col[4]})" if col[4] else ""
                    print(f'  - {col[0]}: {col[1]}{length} {nullable}{default}')
                
                # 제약조건 확인
                constraint_result = conn.execute(text(f"""
                    SELECT 
                        tc.constraint_name,
                        tc.constraint_type,
                        kcu.column_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu 
                        ON tc.constraint_name = kcu.constraint_name
                    WHERE tc.table_name = '{table_name}'
                    ORDER BY tc.constraint_type, kcu.column_name
                """))
                
                constraints = constraint_result.fetchall()
                if constraints:
                    print('  제약조건:')
                    for constraint in constraints:
                        print(f'    - {constraint[1]}: {constraint[0]} ({constraint[2]})')
                
                print()
                
    except Exception as e:
        print(f'❌ 데이터베이스 연결 오류: {str(e)}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_database_structure()