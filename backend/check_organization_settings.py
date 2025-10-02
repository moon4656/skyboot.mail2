#!/usr/bin/env python3
"""
조직 설정 테이블의 중복 데이터 확인 및 정리 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.config import settings as app_settings
from app.model.organization_model import Organization, OrganizationSettings
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_organization_settings():
    """조직 설정 테이블의 중복 데이터 확인"""
    try:
        # 데이터베이스 연결
        engine = create_engine(app_settings.DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        print("🔍 조직 설정 중복 데이터 확인 시작")
        print("=" * 60)
        
        # 1. 전체 조직 수 확인
        total_orgs = db.query(Organization).count()
        print(f"📊 전체 조직 수: {total_orgs}")
        
        # 2. 전체 조직 설정 수 확인
        total_settings = db.query(OrganizationSettings).count()
        print(f"📊 전체 조직 설정 수: {total_settings}")
        
        # 3. 조직별 설정 개수 확인
        print("\n📋 조직별 설정 개수:")
        result = db.execute(text("""
            SELECT 
                org_id,
                COUNT(*) as setting_count,
                STRING_AGG(setting_key, ', ') as setting_keys
            FROM organization_settings 
            GROUP BY org_id 
            ORDER BY setting_count DESC
        """))
        
        duplicate_orgs = []
        for row in result:
            org_id, count, keys = row
            print(f"  조직 {org_id}: {count}개 설정 ({keys})")
            if count > 1:
                duplicate_orgs.append(org_id)
        
        # 4. 중복 설정이 있는 조직 상세 확인
        if duplicate_orgs:
            print(f"\n⚠️ 중복 설정이 있는 조직: {len(duplicate_orgs)}개")
            for org_id in duplicate_orgs:
                print(f"\n📋 조직 {org_id} 상세:")
                settings_list = db.query(OrganizationSettings).filter(
                    OrganizationSettings.org_id == org_id
                ).all()
                
                for i, setting in enumerate(settings_list, 1):
                    print(f"  {i}. ID: {setting.id}, Key: {setting.setting_key}, "
                          f"Value: {setting.setting_value}, Created: {setting.created_at}")
        else:
            print("\n✅ 중복 설정이 있는 조직이 없습니다.")
        
        # 5. 조직 정보와 설정 관계 확인
        print("\n🔗 조직-설정 관계 확인:")
        orgs_with_settings = db.query(Organization).join(OrganizationSettings).all()
        print(f"  설정이 있는 조직 수: {len(orgs_with_settings)}")
        
        # 6. SQLAlchemy 관계 테스트
        print("\n🧪 SQLAlchemy 관계 테스트:")
        test_org = db.query(Organization).first()
        if test_org:
            try:
                # 이 부분에서 경고가 발생할 수 있음
                settings = test_org.settings
                print(f"  테스트 조직 {test_org.org_code}의 설정: {type(settings)}")
                if settings:
                    if hasattr(settings, 'setting_key'):
                        print(f"    설정 키: {settings.setting_key}")
                    else:
                        print(f"    설정 타입: {type(settings)}")
            except Exception as e:
                print(f"  ❌ 관계 접근 오류: {str(e)}")
        
        db.close()
        print("\n✅ 조직 설정 확인 완료")
        
    except Exception as e:
        logger.error(f"❌ 조직 설정 확인 오류: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_organization_settings()