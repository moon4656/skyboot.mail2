#!/usr/bin/env python3
"""
메일 관련 테이블 구조 확인 스크립트
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.config import settings

def check_mail_tables():
    """메일 관련 테이블 구조 확인"""
    try:
        # 데이터베이스 연결
        engine = create_engine(settings.get_database_url())
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # 메일 관련 테이블 목록
        mail_tables = [
            'mail_users',
            'mails', 
            'mail_recipients',
            'mail_attachments',
            'mail_folders',
            'mail_in_folders',
            'mail_logs'
        ]
        
        print("=== 메일 관련 테이블 존재 여부 확인 ===")
        for table_name in mail_tables:
            result = session.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = :table_name
                );
            """), {"table_name": table_name})
            
            exists = result.scalar()
            status = "존재" if exists else "없음"
            print(f"- {table_name}: {status}")
        
        print("\n=== 존재하는 테이블의 구조 확인 ===")
        for table_name in mail_tables:
            # 테이블 존재 여부 확인
            result = session.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = :table_name
                );
            """), {"table_name": table_name})
            
            if result.scalar():
                print(f"\n--- {table_name} 테이블 구조 ---")
                
                # 컬럼 정보 조회
                columns_result = session.execute(text("""
                    SELECT 
                        column_name,
                        data_type,
                        is_nullable,
                        column_default,
                        character_maximum_length
                    FROM information_schema.columns 
                    WHERE table_schema = 'public' 
                    AND table_name = :table_name
                    ORDER BY ordinal_position;
                """), {"table_name": table_name})
                
                for row in columns_result:
                    nullable = "NULL" if row.is_nullable == "YES" else "NOT NULL"
                    max_length = f"({row.character_maximum_length})" if row.character_maximum_length else ""
                    default = f" DEFAULT {row.column_default}" if row.column_default else ""
                    print(f"  {row.column_name}: {row.data_type}{max_length} {nullable}{default}")
                
                # 인덱스 정보 조회
                indexes_result = session.execute(text("""
                    SELECT 
                        indexname,
                        indexdef
                    FROM pg_indexes 
                    WHERE tablename = :table_name
                    AND schemaname = 'public';
                """), {"table_name": table_name})
                
                indexes = list(indexes_result)
                if indexes:
                    print(f"  인덱스:")
                    for idx in indexes:
                        print(f"    - {idx.indexname}")
                
                # 외래 키 정보 조회
                fk_result = session.execute(text("""
                    SELECT
                        tc.constraint_name,
                        kcu.column_name,
                        ccu.table_name AS foreign_table_name,
                        ccu.column_name AS foreign_column_name
                    FROM information_schema.table_constraints AS tc
                    JOIN information_schema.key_column_usage AS kcu
                        ON tc.constraint_name = kcu.constraint_name
                        AND tc.table_schema = kcu.table_schema
                    JOIN information_schema.constraint_column_usage AS ccu
                        ON ccu.constraint_name = tc.constraint_name
                        AND ccu.table_schema = tc.table_schema
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                        AND tc.table_name = :table_name
                        AND tc.table_schema = 'public';
                """), {"table_name": table_name})
                
                fks = list(fk_result)
                if fks:
                    print(f"  외래 키:")
                    for fk in fks:
                        print(f"    - {fk.column_name} -> {fk.foreign_table_name}.{fk.foreign_column_name}")
                
                # 데이터 개수 확인
                count_result = session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                count = count_result.scalar()
                print(f"  데이터 개수: {count}개")
        
        session.close()
        print("\n=== 테이블 구조 확인 완료 ===")
        
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_mail_tables()