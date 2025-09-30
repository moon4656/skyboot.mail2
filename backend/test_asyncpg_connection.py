#!/usr/bin/env python3
"""
asyncpg를 사용한 PostgreSQL 연결 테스트
"""

import asyncio
import asyncpg

async def test_connection():
    """PostgreSQL 연결 테스트"""
    try:
        # PostgreSQL 연결
        conn = await asyncpg.connect('postgresql://postgres:postgres123@localhost:5432/postgres')
        print('✅ asyncpg PostgreSQL 연결 성공')
        
        # 간단한 쿼리 테스트
        result = await conn.fetchval('SELECT version()')
        print(f'📊 PostgreSQL 버전: {result}')
        
        # 연결 종료
        await conn.close()
        print('🔌 연결 종료 완료')
        
    except Exception as e:
        print(f'❌ PostgreSQL 연결 실패: {e}')
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_connection())
    if success:
        print('🎯 asyncpg 연결 테스트 성공!')
    else:
        print('💥 asyncpg 연결 테스트 실패!')