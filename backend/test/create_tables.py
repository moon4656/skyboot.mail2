#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
데이터베이스 테이블 생성 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.user import engine, Base
from sqlalchemy import text

def create_tables():
    """데이터베이스 테이블을 생성합니다"""
    
    try:
        print("🗄️ 데이터베이스 테이블 생성 시작...")
        
        # 모든 테이블 생성
        Base.metadata.create_all(bind=engine)
        
        print("✅ 데이터베이스 테이블 생성 완료")
        
        # 생성된 테이블 목록 확인
        with engine.connect() as conn:
            result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
            tables = [row[0] for row in result]
            
            print(f"📋 생성된 테이블 목록 ({len(tables)}개):")
            for table in sorted(tables):
                print(f"  - {table}")
        
        return True
        
    except Exception as e:
        print(f"❌ 테이블 생성 중 오류 발생: {str(e)}")
        return False

if __name__ == "__main__":
    success = create_tables()
    
    if success:
        print("🎉 테이블 생성 완료!")
    else:
        print("❌ 테이블 생성 실패")
        sys.exit(1)