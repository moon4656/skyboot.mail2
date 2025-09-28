#!/usr/bin/env python3
"""
users 테이블 구조 확인 스크립트
"""

import sys
import os
from pathlib import Path

# backend 폴더를 sys.path에 추가
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine, text
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_users_table():
    """users 테이블 구조를 확인합니다."""
    
    # 환경변수에서 DATABASE_URL 읽기
    database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:safe70%21%21@localhost:5432/skybootmail')
    
    try:
        # 데이터베이스 엔진 생성
        engine = create_engine(database_url, echo=False)
        
        logger.info("🚀 데이터베이스 연결 시도...")
        
        # 연결 테스트
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            logger.info("✅ 데이터베이스 연결 성공!")
        
        # users 테이블 구조 확인
        with engine.connect() as connection:
            logger.info("📋 users 테이블 구조 확인...")
            
            # 테이블 존재 여부 확인
            result = connection.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'users'
                );
            """))
            table_exists = result.fetchone()[0]
            
            if not table_exists:
                logger.error("❌ users 테이블이 존재하지 않습니다!")
                return False
            
            # 컬럼 정보 조회
            result = connection.execute(text("""
                SELECT 
                    column_name, 
                    data_type, 
                    is_nullable, 
                    column_default,
                    character_maximum_length
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = 'users'
                ORDER BY ordinal_position;
            """))
            
            columns = result.fetchall()
            
            logger.info("📊 users 테이블 컬럼 정보:")
            for col in columns:
                column_name, data_type, is_nullable, column_default, max_length = col
                length_info = f"({max_length})" if max_length else ""
                nullable_info = "NULL" if is_nullable == "YES" else "NOT NULL"
                default_info = f" DEFAULT {column_default}" if column_default else ""
                
                logger.info(f"  - {column_name}: {data_type}{length_info} {nullable_info}{default_info}")
            
            # 인덱스 정보 조회
            result = connection.execute(text("""
                SELECT 
                    indexname, 
                    indexdef
                FROM pg_indexes 
                WHERE tablename = 'users'
                ORDER BY indexname;
            """))
            
            indexes = result.fetchall()
            
            if indexes:
                logger.info("🔍 users 테이블 인덱스 정보:")
                for idx in indexes:
                    indexname, indexdef = idx
                    logger.info(f"  - {indexname}: {indexdef}")
            else:
                logger.info("ℹ️ users 테이블에 인덱스가 없습니다.")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 테이블 구조 확인 실패: {e}")
        return False

if __name__ == "__main__":
    success = check_users_table()
    if success:
        print("\n🎉 테이블 구조 확인이 완료되었습니다!")
    else:
        print("\n💥 테이블 구조 확인에 실패했습니다.")
        sys.exit(1)