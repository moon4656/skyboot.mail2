#!/usr/bin/env python3
"""
현재 데이터베이스의 테이블 목록과 데이터 개수를 확인하는 스크립트
"""

import psycopg2
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

def check_tables_and_data():
    """데이터베이스 테이블 목록과 각 테이블의 데이터 개수를 확인합니다."""
    
    try:
        # 데이터베이스 연결
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            database=os.getenv('DB_NAME', 'skyboot_mail'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'password'),
            port=os.getenv('DB_PORT', '5432')
        )
        
        cursor = conn.cursor()
        
        print("🔍 현재 데이터베이스 테이블 목록 및 데이터 확인")
        print("=" * 60)
        
        # 모든 테이블 목록 조회
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """)
        
        tables = cursor.fetchall()
        
        if not tables:
            print("❌ 테이블이 없습니다.")
            return
        
        print(f"📋 총 {len(tables)}개의 테이블이 있습니다:")
        print()
        
        total_records = 0
        
        for (table_name,) in tables:
            try:
                # 각 테이블의 레코드 수 조회
                cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                count = cursor.fetchone()[0]
                total_records += count
                
                # 테이블 크기 정보 조회
                cursor.execute(f"""
                    SELECT pg_size_pretty(pg_total_relation_size('{table_name}'));
                """)
                size = cursor.fetchone()[0]
                
                print(f"🔹 {table_name:<25} | 레코드: {count:>6}개 | 크기: {size}")
                
                # 데이터가 있는 테이블의 경우 샘플 데이터 확인
                if count > 0:
                    cursor.execute(f"""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name = '{table_name}' 
                        ORDER BY ordinal_position 
                        LIMIT 5;
                    """)
                    columns = [col[0] for col in cursor.fetchall()]
                    print(f"   📝 주요 컬럼: {', '.join(columns)}")
                
            except Exception as e:
                print(f"❌ {table_name} 테이블 조회 오류: {e}")
        
        print()
        print("=" * 60)
        print(f"📊 전체 레코드 수: {total_records:,}개")
        
        # 데이터베이스 전체 크기
        cursor.execute("""
            SELECT pg_size_pretty(pg_database_size(current_database()));
        """)
        db_size = cursor.fetchone()[0]
        print(f"💾 데이터베이스 크기: {db_size}")
        
        cursor.close()
        conn.close()
        
        print("✅ 테이블 및 데이터 확인 완료!")
        
    except Exception as e:
        print(f"❌ 데이터베이스 연결 오류: {e}")

if __name__ == "__main__":
    check_tables_and_data()