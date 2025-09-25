#!/usr/bin/env python3
"""
데이터베이스의 모든 테이블과 컬럼을 확인하는 스크립트
"""

import os
from app.database.base import get_db
from sqlalchemy import text

# 환경 변수 설정
os.environ['DATABASE_URL'] = 'postgresql://postgres:password@localhost:5432/skyboot_mail'

def main():
    # 데이터베이스 연결
    db = next(get_db())

    try:
        # 모든 테이블 목록 확인
        result = db.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name"))
        tables = result.fetchall()
        
        print('데이터베이스 테이블 목록:')
        for table in tables:
            print(f'  - {table[0]}')
            
        print('\n메일 관련 테이블 상세 확인:')
        for table in tables:
            table_name = table[0]
            if 'mail' in table_name.lower():
                print(f'\n테이블: {table_name}')
                col_result = db.execute(text(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table_name}' ORDER BY ordinal_position"))
                columns = col_result.fetchall()
                for col in columns:
                    print(f'  - {col[0]}: {col[1]}')
                    
    except Exception as e:
        print(f'오류 발생: {str(e)}')
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()