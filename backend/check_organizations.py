#!/usr/bin/env python3
"""
기존 조직 확인 스크립트
"""

import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.model.organization_model import Organization

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_organizations():
    """기존 조직 확인"""
    try:
        # 데이터베이스 연결
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        with SessionLocal() as session:
            # 모든 조직 조회
            organizations = session.query(Organization).all()
            
            print("=== 기존 조직 목록 ===")
            if not organizations:
                print("❌ 조직이 없습니다.")
                return None
            
            for org in organizations:
                print(f"조직 ID: {org.org_id}")
                print(f"조직명: {org.name}")
                print(f"도메인: {org.domain}")
                print(f"서브도메인: {org.subdomain}")
                print(f"활성 상태: {org.is_active}")
                print("---")
            
            return organizations[0] if organizations else None
                
    except Exception as e:
        print(f"❌ 조직 조회 오류: {e}")
        return None

if __name__ == "__main__":
    print("=== 조직 확인 ===")
    check_organizations()