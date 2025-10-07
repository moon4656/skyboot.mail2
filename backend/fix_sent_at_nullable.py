#!/usr/bin/env python3
"""
sent_at 필드를 nullable로 수정하는 스크립트
"""

import os
import sys
from sqlalchemy import create_engine, text
from app.config import settings

def fix_sent_at_nullable():
    """sent_at 필드를 nullable로 수정"""
    try:
        # 설정 로드 (이미 인스턴스화됨)
        
        # 데이터베이스 연결
        engine = create_engine(settings.DATABASE_URL)
        
        print("🔧 sent_at 필드를 nullable로 수정 중...")
        
        with engine.connect() as connection:
            # 트랜잭션 시작
            trans = connection.begin()
            
            try:
                # sent_at 필드를 nullable로 수정
                sql = text("ALTER TABLE mails ALTER COLUMN sent_at DROP NOT NULL;")
                connection.execute(sql)
                
                # 변경사항 확인
                check_sql = text("""
                    SELECT column_name, is_nullable 
                    FROM information_schema.columns 
                    WHERE table_name = 'mails' AND column_name = 'sent_at';
                """)
                result = connection.execute(check_sql)
                row = result.fetchone()
                
                if row and row[1] == 'YES':
                    print("✅ sent_at 필드가 성공적으로 nullable로 수정되었습니다!")
                    trans.commit()
                    return True
                else:
                    print("❌ sent_at 필드 수정에 실패했습니다.")
                    trans.rollback()
                    return False
                    
            except Exception as e:
                print(f"❌ 데이터베이스 수정 중 오류 발생: {str(e)}")
                trans.rollback()
                return False
                
    except Exception as e:
        print(f"❌ 데이터베이스 연결 오류: {str(e)}")
        return False

if __name__ == "__main__":
    print("📧 SkyBoot Mail - sent_at 필드 수정 도구")
    print("=" * 50)
    
    success = fix_sent_at_nullable()
    
    if success:
        print("\n🎉 sent_at 필드 수정이 완료되었습니다!")
        print("이제 서버를 재시작하여 변경사항을 적용하세요.")
    else:
        print("\n💥 sent_at 필드 수정에 실패했습니다.")
        sys.exit(1)