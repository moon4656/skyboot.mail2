#!/usr/bin/env python3
"""
org_1 조직의 최대 사용자 수를 늘리는 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.model.organization_model import Organization

def increase_org_max_users():
    """org_1 조직의 최대 사용자 수를 늘립니다."""
    
    # 데이터베이스 연결
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # org_1 조직 조회
        org_id = "85ad4d60-d2e3-47cf-947e-e07e8111eae7"
        org = db.query(Organization).filter(Organization.org_id == org_id).first()
        
        if org:
            print(f"📋 현재 조직 정보:")
            print(f"   - 이름: {org.name}")
            print(f"   - 코드: {org.org_code}")
            print(f"   - 현재 최대 사용자 수: {org.max_users}")
            
            # 최대 사용자 수를 50으로 증가
            new_max_users = 50
            org.max_users = new_max_users
            
            db.commit()
            
            print(f"✅ 최대 사용자 수를 {new_max_users}명으로 증가시켰습니다.")
            print(f"   - 새로운 최대 사용자 수: {org.max_users}")
            
        else:
            print(f"❌ 조직 ID {org_id}를 찾을 수 없습니다.")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    increase_org_max_users()