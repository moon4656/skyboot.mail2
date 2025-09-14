#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
데이터베이스 테이블 정보 확인 스크립트
"""

from app.database import engine
from sqlalchemy import inspect, text

def check_database_info():
    """데이터베이스 정보를 확인하는 함수"""
    try:
        # 데이터베이스 연결 확인
        with engine.connect() as connection:
            print("=== SkyBoot Mail 데이터베이스 정보 ===")
            print(f"데이터베이스 URL: {engine.url}")
            print(f"데이터베이스 이름: {engine.url.database}")
            print(f"호스트: {engine.url.host}")
            print(f"포트: {engine.url.port}")
            print(f"사용자: {engine.url.username}")
            
            # 테이블 목록 확인
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            print(f"\n=== 테이블 목록 ({len(tables)}개) ===")
            
            if not tables:
                print("생성된 테이블이 없습니다.")
                return
            
            for table in tables:
                print(f"\n📋 {table} 테이블:")
                columns = inspector.get_columns(table)
                
                for col in columns:
                    nullable = "NULL" if col['nullable'] else "NOT NULL"
                    default = f" DEFAULT {col['default']}" if col['default'] else ""
                    print(f"  - {col['name']}: {col['type']} {nullable}{default}")
                
                # 인덱스 정보
                indexes = inspector.get_indexes(table)
                if indexes:
                    print(f"  📊 인덱스:")
                    for idx in indexes:
                        unique = "UNIQUE " if idx['unique'] else ""
                        print(f"    - {unique}{idx['name']}: {', '.join(idx['column_names'])}")
                
                # 외래키 정보
                foreign_keys = inspector.get_foreign_keys(table)
                if foreign_keys:
                    print(f"  🔗 외래키:")
                    for fk in foreign_keys:
                        print(f"    - {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}")
            
            # 데이터 개수 확인
            print(f"\n=== 데이터 개수 ===")
            for table in tables:
                result = connection.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                print(f"  - {table}: {count}개")
                
    except Exception as e:
        print(f"오류 발생: {e}")

if __name__ == "__main__":
    check_database_info()