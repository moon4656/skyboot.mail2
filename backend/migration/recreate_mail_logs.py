#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mail_logs 테이블 재생성 스크립트
"""

from app.database import engine
from app.model.mail_model import Base, MailLog
from sqlalchemy import text

def recreate_mail_logs_table():
    """mail_logs 테이블을 삭제하고 다시 생성합니다."""
    try:
        # 기존 테이블 삭제
        with engine.connect() as conn:
            conn.execute(text('DROP TABLE IF EXISTS mail_logs CASCADE;'))
            conn.commit()
            print("✅ 기존 mail_logs 테이블 삭제 완료")
        
        # 새 테이블 생성
        MailLog.__table__.create(engine, checkfirst=True)
        print("✅ 새로운 mail_logs 테이블 생성 완료")
        
        # 테이블 구조 확인
        with engine.connect() as conn:
            result = conn.execute(text("SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name = 'mail_logs' ORDER BY ordinal_position;"))
            columns = result.fetchall()
            
            print("\n📋 mail_logs 테이블 구조:")
            for col in columns:
                print(f"  - {col[0]}: {col[1]} ({'NULL' if col[2] == 'YES' else 'NOT NULL'})")
                
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        raise

if __name__ == "__main__":
    recreate_mail_logs_table()