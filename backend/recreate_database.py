#!/usr/bin/env python3
"""
데이터베이스 완전 재생성 스크립트
모든 테이블을 삭제하고 모델 파일을 기반으로 새로 생성합니다.
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.model.user_model import Base as UserBase
from app.model.mail_model import Base as MailBase
from app.model.organization_model import Base as OrgBase
from app.model.addressbook_model import Base as AddressBase

def recreate_database():
    """데이터베이스를 완전히 재생성합니다."""
    
    # 데이터베이스 연결
    engine = create_engine(settings.DATABASE_URL, echo=True)
    
    print("🗑️ 기존 데이터베이스 테이블 삭제 중...")
    
    try:
        # 모든 테이블 삭제 (CASCADE로 외래 키 제약 조건 무시)
        with engine.connect() as conn:
            # 모든 테이블 목록 조회
            result = conn.execute(text("""
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'public'
            """))
            tables = result.fetchall()
            
            # 각 테이블 삭제
            for table in tables:
                table_name = table[0]
                print(f"  - 테이블 삭제: {table_name}")
                conn.execute(text(f"DROP TABLE IF EXISTS {table_name} CASCADE"))
            
            # Alembic 버전 테이블도 삭제
            conn.execute(text("DROP TABLE IF EXISTS alembic_version CASCADE"))
            conn.commit()
        
        print("✅ 모든 테이블이 성공적으로 삭제되었습니다.")
        
    except Exception as e:
        print(f"❌ 테이블 삭제 중 오류 발생: {e}")
        return False
    
    print("\n🏗️ 새로운 데이터베이스 테이블 생성 중...")
    
    try:
        # 모든 모델의 테이블 생성
        UserBase.metadata.create_all(bind=engine)
        MailBase.metadata.create_all(bind=engine)
        OrgBase.metadata.create_all(bind=engine)
        AddressBase.metadata.create_all(bind=engine)
        
        print("✅ 모든 테이블이 성공적으로 생성되었습니다.")
        
    except Exception as e:
        print(f"❌ 테이블 생성 중 오류 발생: {e}")
        return False
    
    print("\n📊 생성된 테이블 목록 확인...")
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'public'
                ORDER BY tablename
            """))
            tables = result.fetchall()
            
            print(f"총 {len(tables)}개의 테이블이 생성되었습니다:")
            for table in tables:
                print(f"  - {table[0]}")
        
    except Exception as e:
        print(f"❌ 테이블 목록 조회 중 오류 발생: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("🔄 SkyBoot Mail 데이터베이스 재생성 시작")
    print("=" * 60)
    
    success = recreate_database()
    
    if success:
        print("\n" + "=" * 60)
        print("✅ 데이터베이스 재생성이 완료되었습니다!")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ 데이터베이스 재생성에 실패했습니다.")
        print("=" * 60)
        sys.exit(1)