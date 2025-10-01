#!/usr/bin/env python3
"""사용자 테이블의 스키마를 확인하는 스크립트"""

import asyncio
import asyncpg
from app.config import settings

async def check_users_schema():
    """사용자 테이블의 스키마를 확인합니다."""
    
    try:
        conn = await asyncpg.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            database=settings.DB_NAME
        )
        
        print("📊 users 테이블 스키마 확인...")
        
        # users 테이블 구조 확인
        result = await conn.fetch("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'users'
            ORDER BY ordinal_position;
        """)
        
        if result:
            print('=== users 테이블 구조 ===')
            for row in result:
                col_name = row['column_name']
                data_type = row['data_type']
                nullable = row['is_nullable']
                default = row['column_default']
                print(f'{col_name:20} | {data_type:15} | nullable: {nullable:3} | default: {default}')
        else:
            print('❌ users 테이블이 존재하지 않습니다.')
        
        # 테이블 목록 확인
        print(f"\n📋 데이터베이스의 모든 테이블:")
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        
        for table in tables:
            print(f"  - {table['table_name']}")
        
        await conn.close()
        
    except Exception as e:
        print(f'❌ 오류 발생: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_users_schema())