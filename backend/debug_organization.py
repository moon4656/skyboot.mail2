#!/usr/bin/env python3
"""
조직 정보 디버깅 스크립트
데이터베이스에 있는 조직 정보를 확인합니다.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.model.organization_model import Organization, OrganizationSettings
from app.config import settings

# 데이터베이스 연결 설정
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def debug_organizations():
    """데이터베이스의 조직 정보를 확인합니다."""
    
    # 데이터베이스 세션 생성
    db = SessionLocal()
    
    try:
        print("🔍 데이터베이스 조직 정보 확인")
        print("=" * 60)
        
        # 모든 조직 조회
        organizations = db.query(Organization).all()
        
        if not organizations:
            print("❌ 데이터베이스에 조직이 없습니다.")
            return
        
        print(f"📋 총 {len(organizations)}개의 조직이 있습니다:")
        print()
        
        for org in organizations:
            print(f"조직 ID: {org.org_id}")
            print(f"조직명: {org.name}")
            print(f"도메인: {org.domain}")
            print(f"활성화 상태: {org.is_active}")
            print(f"생성일: {org.created_at}")
            
            # 해당 조직의 설정 확인
            settings = db.query(OrganizationSettings).filter(
                OrganizationSettings.org_id == org.org_id
            ).all()
            
            print(f"설정 개수: {len(settings)}")
            if settings:
                print("설정 목록:")
                for setting in settings:
                    print(f"  - {setting.setting_key}: {setting.setting_value} ({setting.setting_type})")
            
            print("-" * 40)
        
        # 특정 조직 ID로 조회 테스트
        test_org_id = "3856a8c1-84a4-4019-9133-655cacab4bc9"
        print(f"\n🔍 특정 조직 ID 조회 테스트: {test_org_id}")
        
        test_org = db.query(Organization).filter(
            Organization.org_id == test_org_id,
            Organization.is_active == True
        ).first()
        
        if test_org:
            print(f"✅ 조직 찾음: {test_org.name}")
        else:
            print(f"❌ 조직을 찾을 수 없음")
            
            # 비활성화된 조직도 확인
            inactive_org = db.query(Organization).filter(
                Organization.org_id == test_org_id
            ).first()
            
            if inactive_org:
                print(f"⚠️ 비활성화된 조직 발견: {inactive_org.name}, 활성화 상태: {inactive_org.is_active}")
            else:
                print(f"❌ 해당 ID의 조직이 전혀 없음")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    debug_organizations()