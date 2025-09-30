#!/usr/bin/env python3
"""
mail_recipients 테이블 구조 확인 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text, inspect
from app.config import settings

def check_mail_recipients_table():
    """mail_recipients 테이블 구조 확인"""
    
    # 데이터베이스 연결
    engine = create_engine(settings.DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            # 테이블 존재 확인
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            
            print("📋 데이터베이스의 모든 테이블:")
            for table in sorted(tables):
                print(f"   - {table}")
            
            if 'mail_recipients' in tables:
                print(f"\n📧 mail_recipients 테이블 구조:")
                columns = inspector.get_columns('mail_recipients')
                for column in columns:
                    print(f"   - {column['name']}: {column['type']} (nullable: {column['nullable']})")
                
                # 샘플 데이터 확인
                result = conn.execute(text("SELECT COUNT(*) FROM mail_recipients"))
                count = result.scalar()
                print(f"\n📊 mail_recipients 테이블 레코드 수: {count}")
                
                if count > 0:
                    result = conn.execute(text("SELECT * FROM mail_recipients LIMIT 3"))
                    rows = result.fetchall()
                    print(f"\n📄 샘플 데이터:")
                    for i, row in enumerate(rows, 1):
                        print(f"   {i}. {dict(row._mapping)}")
            else:
                print("\n❌ mail_recipients 테이블이 존재하지 않습니다.")
                
            # MailRecipient 모델과 비교
            print(f"\n🔍 MailRecipient 모델 정의 확인:")
            from app.model.mail_model import MailRecipient
            from sqlalchemy import inspect as sqlalchemy_inspect
            
            mapper = sqlalchemy_inspect(MailRecipient)
            print(f"   테이블명: {mapper.local_table.name}")
            for column in mapper.local_table.columns:
                print(f"   - {column.name}: {column.type} (nullable: {column.nullable})")
                
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("📧 mail_recipients 테이블 구조 확인 시작")
    check_mail_recipients_table()