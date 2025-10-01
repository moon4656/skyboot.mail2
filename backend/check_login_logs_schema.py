#!/usr/bin/env python3
"""login_logs 테이블 스키마 확인 스크립트"""

import asyncio
import asyncpg
from app.config import settings

async def check_table_schema():
    """login_logs 테이블의 현재 스키마를 확인합니다."""
    
    try:
        conn = await asyncpg.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            database=settings.DB_NAME
        )
        
        # login_logs 테이블 구조 확인
        result = await conn.fetch("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'login_logs'
            ORDER BY ordinal_position;
        """)
        
        print('=== login_logs 테이블 구조 ===')
        if result:
            for row in result:
                col_name = row['column_name']
                data_type = row['data_type']
                nullable = row['is_nullable']
                default = row['column_default']
                print(f'{col_name:20} | {data_type:15} | nullable: {nullable:3} | default: {default}')
        else:
            print('login_logs 테이블이 존재하지 않습니다.')
        
        await conn.close()
        
    except Exception as e:
        print(f'오류 발생: {e}')

if __name__ == "__main__":
    asyncio.run(check_table_schema())