#!/usr/bin/env python3
"""
데이터베이스 테이블 구조 확인 스크립트
"""

import os
from app.database.base import get_db
from sqlalchemy import text

def check_mail_in_folder_schema():
    """MailInFolder 테이블 구조 확인"""
    # 환경 변수 설정
    os.environ['DATABASE_URL'] = 'postgresql://postgres:password@localhost:5432/skyboot_mail'
    
    # 데이터베이스 연결
    db = next(get_db())
    
    try:
        # MailInFolder 테이블 구조 확인
        query = """
        SELECT column_name, data_type, is_nullable 
        FROM information_schema.columns 
        WHERE table_name = 'mail_in_folder' 
        ORDER BY ordinal_position
        """
        result = db.execute(text(query))
        columns = result.fetchall()
        
        print('MailInFolder 테이블 컬럼:')
        for col in columns:
            print(f'  - {col[0]}: {col[1]} (nullable: {col[2]})')
            
        # moved_at 컬럼이 있는지 확인
        moved_at_exists = any(col[0] == 'moved_at' for col in columns)
        print(f'\nmoved_at 컬럼 존재 여부: {moved_at_exists}')
        
        if moved_at_exists:
            print('moved_at 컬럼을 제거해야 합니다.')
            
            # moved_at 컬럼 제거
            drop_query = "ALTER TABLE mail_in_folder DROP COLUMN IF EXISTS moved_at"
            db.execute(text(drop_query))
            db.commit()
            print('✅ moved_at 컬럼이 성공적으로 제거되었습니다.')
        else:
            print('moved_at 컬럼이 이미 제거되었습니다.')
            
    except Exception as e:
        print(f'❌ 오류 발생: {str(e)}')
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    check_mail_in_folder_schema()