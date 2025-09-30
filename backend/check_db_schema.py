#!/usr/bin/env python3
"""
SQLAlchemy를 사용한 데이터베이스 스키마 확인 스크립트
"""
import os
import sys
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

# 환경 변수 설정
os.environ['PYTHONIOENCODING'] = 'utf-8'

def check_organizations_table():
    """organizations 테이블의 스키마를 확인합니다."""
    try:
        # 데이터베이스 연결 URL
        DATABASE_URL = "postgresql://skyboot_user:skyboot123!@localhost:5432/skyboot_mail"
        
        # SQLAlchemy 엔진 생성
        engine = create_engine(DATABASE_URL, echo=False)
        
        # Inspector 생성
        inspector = inspect(engine)
        
        print("🔍 organizations 테이블 스키마 확인...")
        print("=" * 60)
        
        # 테이블 존재 확인
        tables = inspector.get_table_names()
        if 'organizations' not in tables:
            print("❌ organizations 테이블이 존재하지 않습니다.")
            print(f"📋 사용 가능한 테이블: {', '.join(tables)}")
            return
        
        # 컬럼 정보 조회
        columns = inspector.get_columns('organizations')
        
        print(f"📋 총 {len(columns)}개의 컬럼이 있습니다:")
        print()
        
        for col in columns:
            nullable = "NULL" if col['nullable'] else "NOT NULL"
            col_type = str(col['type'])
            default = f" DEFAULT {col['default']}" if col['default'] else ""
            
            print(f"  {col['name']:<20} {col_type:<15} {nullable}{default}")
        
        print()
        print("🔑 기본 키 및 인덱스 확인...")
        
        # 기본 키 확인
        pk_constraint = inspector.get_pk_constraint('organizations')
        if pk_constraint and pk_constraint['constrained_columns']:
            print(f"  기본 키: {', '.join(pk_constraint['constrained_columns'])}")
        
        # 인덱스 확인
        indexes = inspector.get_indexes('organizations')
        if indexes:
            print("  인덱스:")
            for idx in indexes:
                unique = " (UNIQUE)" if idx['unique'] else ""
                print(f"    {idx['name']}: {', '.join(idx['column_names'])}{unique}")
        
        print()
        print("📊 테이블 데이터 확인...")
        
        # 세션 생성
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # 데이터 개수 확인
        count_result = session.execute(text("SELECT COUNT(*) as count FROM organizations")).fetchone()
        print(f"  총 레코드 수: {count_result[0]}")
        
        # 샘플 데이터 확인 (있다면)
        if count_result[0] > 0:
            sample_data = session.execute(text("SELECT * FROM organizations LIMIT 3")).fetchall()
            print("  샘플 데이터:")
            for i, row in enumerate(sample_data, 1):
                print(f"    레코드 {i}:")
                # 컬럼명과 값을 매핑
                for j, col in enumerate(columns):
                    value = row[j] if j < len(row) else None
                    print(f"      {col['name']}: {value}")
                print()
        
        session.close()
        
        print("✅ 스키마 확인 완료")
        
    except Exception as e:
        print(f"❌ 데이터베이스 연결 오류: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_organizations_table()