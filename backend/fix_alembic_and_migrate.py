#!/usr/bin/env python3
"""Alembic 버전 문제를 해결하고 login_logs 테이블을 수정하는 스크립트"""

import asyncio
import asyncpg
from app.config import settings

async def fix_alembic_and_migrate():
    """Alembic 버전을 수정하고 login_logs 테이블의 email 컬럼을 user_id로 변경합니다."""
    
    try:
        conn = await asyncpg.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            database=settings.DB_NAME
        )
        
        print("🔍 현재 Alembic 버전 확인...")
        
        # alembic_version 테이블 확인
        try:
            current_version = await conn.fetchval("SELECT version_num FROM alembic_version;")
            print(f"현재 Alembic 버전: {current_version}")
        except Exception as e:
            print(f"Alembic 버전 테이블 오류: {e}")
            current_version = None
        
        # 올바른 버전으로 업데이트 (최신 버전으로 설정)
        print("📝 Alembic 버전을 최신으로 업데이트...")
        await conn.execute("UPDATE alembic_version SET version_num = '3d3bb6444234';")
        print("✅ Alembic 버전 업데이트 완료")
        
        # login_logs 테이블 백업
        print("💾 login_logs 테이블 백업 중...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS login_logs_backup AS 
            SELECT * FROM login_logs;
        """)
        print("✅ 백업 완료")
        
        # email 컬럼을 user_id로 변경
        print("🔄 email 컬럼을 user_id로 변경 중...")
        
        # 1. 새 user_id 컬럼 추가
        await conn.execute("""
            ALTER TABLE login_logs 
            ADD COLUMN IF NOT EXISTS user_id VARCHAR(50);
        """)
        
        # 2. 기존 email 데이터를 user_id로 복사 (이메일에서 @ 앞부분 추출)
        await conn.execute("""
            UPDATE login_logs 
            SET user_id = SPLIT_PART(email, '@', 1) 
            WHERE user_id IS NULL AND email IS NOT NULL;
        """)
        
        # 3. email 컬럼 삭제
        await conn.execute("""
            ALTER TABLE login_logs 
            DROP COLUMN IF EXISTS email;
        """)
        
        # 4. user_id 컬럼을 NOT NULL로 설정
        await conn.execute("""
            ALTER TABLE login_logs 
            ALTER COLUMN user_id SET NOT NULL;
        """)
        
        print("✅ login_logs 테이블 스키마 변경 완료")
        
        # 변경된 테이블 구조 확인
        print("\n📊 변경된 테이블 구조:")
        result = await conn.fetch("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'login_logs'
            ORDER BY ordinal_position;
        """)
        
        for row in result:
            col_name = row['column_name']
            data_type = row['data_type']
            nullable = row['is_nullable']
            default = row['column_default']
            print(f'{col_name:20} | {data_type:15} | nullable: {nullable:3} | default: {default}')
        
        await conn.close()
        print("\n🎉 모든 작업이 성공적으로 완료되었습니다!")
        
    except Exception as e:
        print(f'❌ 오류 발생: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(fix_alembic_and_migrate())