#!/usr/bin/env python3
"""
데이터베이스 초기화 스크립트
"""

import os
import sys
from sqlalchemy import create_engine, text
from app.config import settings

def reset_database():
    """데이터베이스를 초기화합니다."""
    
    # 데이터베이스 연결
    engine = create_engine(settings.DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            # 모든 테이블 삭제
            print("🗑️ 기존 테이블 삭제 중...")
            conn.execute(text("DROP SCHEMA public CASCADE;"))
            conn.execute(text("CREATE SCHEMA public;"))
            conn.execute(text("GRANT ALL ON SCHEMA public TO postgres;"))
            conn.execute(text("GRANT ALL ON SCHEMA public TO public;"))
            conn.commit()
            print("✅ 기존 테이블 삭제 완료")
            
        print("🔄 Alembic 마이그레이션 실행 중...")
        os.system("alembic upgrade head")
        print("✅ 데이터베이스 초기화 완료")
        
    except Exception as e:
        print(f"❌ 데이터베이스 초기화 실패: {e}")
        sys.exit(1)

if __name__ == "__main__":
    reset_database()