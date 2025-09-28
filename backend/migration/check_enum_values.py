#!/usr/bin/env python3
"""
데이터베이스의 enum 타입 값들을 확인하는 스크립트
"""

import os
import sys
from sqlalchemy import create_engine, text

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.config import settings

def check_enum_values():
    """enum 타입 값들 확인"""
    try:
        engine = create_engine(settings.get_database_url())
        
        with engine.connect() as conn:
            # mailpriority enum 값들 확인
            result = conn.execute(text("""
                SELECT enumlabel 
                FROM pg_enum 
                WHERE enumtypid = (
                    SELECT oid 
                    FROM pg_type 
                    WHERE typname = 'mailpriority'
                )
                ORDER BY enumsortorder
            """))
            priority_values = [row[0] for row in result]
            print("Priority enum values:", priority_values)
            
            # mailstatus enum 값들 확인
            result = conn.execute(text("""
                SELECT enumlabel 
                FROM pg_enum 
                WHERE enumtypid = (
                    SELECT oid 
                    FROM pg_type 
                    WHERE typname = 'mailstatus'
                )
                ORDER BY enumsortorder
            """))
            status_values = [row[0] for row in result]
            print("Status enum values:", status_values)
            
            # recipienttype enum 값들 확인
            result = conn.execute(text("""
                SELECT enumlabel 
                FROM pg_enum 
                WHERE enumtypid = (
                    SELECT oid 
                    FROM pg_type 
                    WHERE typname = 'recipienttype'
                )
                ORDER BY enumsortorder
            """))
            recipient_values = [row[0] for row in result]
            print("Recipient type enum values:", recipient_values)
            
            # 모든 enum 타입 확인
            result = conn.execute(text("""
                SELECT typname 
                FROM pg_type 
                WHERE typtype = 'e'
                ORDER BY typname
            """))
            enum_types = [row[0] for row in result]
            print("All enum types:", enum_types)
            
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_enum_values()