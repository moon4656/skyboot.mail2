#!/usr/bin/env python3
"""
데이터베이스 구조 확인 스크립트 (SQLAlchemy 사용)
"""
from sqlalchemy import create_engine, inspect, text
from app.config import settings

def check_database_structure():
    """현재 데이터베이스의 테이블 구조를 확인합니다."""
    
    # 데이터베이스 연결
    engine = create_engine(settings.DATABASE_URL)
    inspector = inspect(engine)
    
    # 모든 테이블 목록 조회
    tables = inspector.get_table_names()
    print(f'=== 현재 데이터베이스 테이블 목록 ({len(tables)}개) ===')
    for table in sorted(tables):
        print(f'- {table}')
    
    print('\n=== 각 테이블의 컬럼 구조 ===')
    for table in sorted(tables):
        columns = inspector.get_columns(table)
        print(f'\n[{table}] 테이블:')
        for col in columns:
            nullable = 'NULL' if col['nullable'] else 'NOT NULL'
            col_type = str(col['type'])
            default = f' DEFAULT {col["default"]}' if col['default'] else ''
            print(f'  - {col["name"]}: {col_type} {nullable}{default}')
    
    print('\n=== 모델 파일에서 정의된 테이블들 ===')
    expected_tables = [
        'organizations',
        'organization_settings', 
        'organization_usage',
        'users',
        'refresh_tokens',
        'login_logs',
        'mail_users',
        'mails',
        'mail_recipients',
        'mail_attachments',
        'mail_folders',
        'mail_in_folders',
        'mail_logs',
        'departments',
        'groups',
        'contacts',
        'contact_groups'
    ]
    
    print('모델에서 정의된 테이블들:')
    for table in expected_tables:
        exists = table in tables
        status = '✓' if exists else '✗'
        print(f'  {status} {table}')
    
    missing_tables = set(expected_tables) - set(tables)
    extra_tables = set(tables) - set(expected_tables)
    
    if missing_tables:
        print(f'\n❌ 누락된 테이블: {missing_tables}')
    if extra_tables:
        print(f'\n⚠️ 추가된 테이블: {extra_tables}')
    
    if missing_tables or extra_tables:
        print('\n🔄 데이터베이스 재생성이 필요합니다.')
        return False
    else:
        print('\n✅ 모든 테이블이 모델과 일치합니다.')
        return True

if __name__ == "__main__":
    check_database_structure()