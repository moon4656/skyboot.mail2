#!/usr/bin/env python3
"""
조직 확인 스크립트
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.model.organization_model import Organization

def check_organizations():
    """조직 목록 확인"""
    
    # 데이터베이스 연결
    engine = create_engine(settings.get_database_url())
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # 모든 조직 조회
        organizations = db.query(Organization).all()
        
        print(f"📊 총 {len(organizations)}개의 조직이 있습니다:")
        print()
        
        for org in organizations:
            print(f"🏢 조직: {org.name}")
            print(f"   - org_id: {org.org_id}")
            print(f"   - org_code: {org.org_code}")
            print(f"   - domain: {org.domain}")
            print(f"   - is_active: {org.is_active}")
            print(f"   - created_at: {org.created_at}")
            print()
        
        if not organizations:
            print("⚠️ 조직이 없습니다. 조직을 먼저 생성해야 합니다.")
            
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_organizations()